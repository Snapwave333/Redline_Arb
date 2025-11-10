using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using CalmCadence.Core.Interfaces;
using CalmCadence.Core.Models;
using CalmCadence.Core.Enums;
using CalmCadence.Data.Context;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;

namespace CalmCadence.Data.Services;

public class DailyStudioService : IDailyStudioService
{
    private readonly CalmCadenceDbContext _dbContext;
    private readonly IGeminiService _geminiService;
    private readonly IGoogleApiService _googleApiService;
    private readonly ICalendarService _calendarService;
    private readonly ILogger<DailyStudioService> _logger;
    private readonly Settings _settings;

    public DailyStudioService(
        CalmCadenceDbContext dbContext,
        IGeminiService geminiService,
        IGoogleApiService googleApiService,
        ICalendarService calendarService,
        ILogger<DailyStudioService> logger,
        Settings settings)
    {
        _dbContext = dbContext;
        _geminiService = geminiService;
        _googleApiService = googleApiService;
        _calendarService = calendarService;
        _logger = logger;
        _settings = settings;
    }

    public async Task<DailyMedia?> GenerateDailyBriefAsync(DateTimeOffset date)
    {
        try
        {
            _logger.LogInformation("Starting daily brief generation for {Date}", date);

            // Check if we already have media for this date
            var existingMedia = await GetDailyMediaAsync(date);
            if (existingMedia != null && !existingMedia.IsArchived)
            {
                _logger.LogInformation("Daily media already exists for {Date}", date);
                return existingMedia;
            }

            // Collect data for the brief
            var briefInput = await CollectBriefDataAsync(date);
            if (briefInput == null)
            {
                _logger.LogWarning("Failed to collect brief data for {Date}", date);
                return null;
            }

            // Generate hash for caching
            var inputHash = GenerateBriefHash(briefInput);

            // Check cache
            var cachedMedia = await _dbContext.DailyMedia
                .FirstOrDefaultAsync(m => m.Date.Date == date.Date && m.BriefHash == inputHash && !m.IsArchived);

            if (cachedMedia != null)
            {
                _logger.LogInformation("Using cached daily media for {Date}", date);
                return cachedMedia;
            }

            // Generate brief content
            var briefOutput = await GenerateBriefContentAsync(briefInput);
            if (briefOutput == null)
            {
                _logger.LogWarning("Failed to generate brief content for {Date}", date);
                return null;
            }

            // Generate media (audio/video)
            var media = await GenerateMediaAsync(date, briefInput, briefOutput, inputHash);
            if (media == null)
            {
                _logger.LogWarning("Failed to generate media for {Date}", date);
                return null;
            }

            // Save to database
            _dbContext.DailyMedia.Add(media);
            await _dbContext.SaveChangesAsync();

            _logger.LogInformation("Successfully generated daily brief for {Date}", date);
            return media;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to generate daily brief for {Date}", date);
            return null;
        }
    }

    public async Task<bool> IsBriefAvailableAsync(DateTimeOffset date)
    {
        var media = await _dbContext.DailyMedia
            .FirstOrDefaultAsync(m => m.Date.Date == date.Date && !m.IsArchived);

        return media != null && (File.Exists(media.AudioFilePath) || File.Exists(media.VideoFilePath));
    }

    public async Task<DailyMedia?> GetDailyMediaAsync(DateTimeOffset date)
    {
        return await _dbContext.DailyMedia
            .FirstOrDefaultAsync(m => m.Date.Date == date.Date && !m.IsArchived);
    }

    public async Task CleanupExpiredMediaAsync()
    {
        var expiredMedia = await _dbContext.DailyMedia
            .Where(m => m.ExpiresAt < DateTimeOffset.UtcNow)
            .ToListAsync();

        foreach (var media in expiredMedia)
        {
            try
            {
                // Delete files
                if (!string.IsNullOrEmpty(media.AudioFilePath) && File.Exists(media.AudioFilePath))
                    File.Delete(media.AudioFilePath);

                if (!string.IsNullOrEmpty(media.VideoFilePath) && File.Exists(media.VideoFilePath))
                    File.Delete(media.VideoFilePath);

                // Mark as archived
                media.IsArchived = true;
                media.UpdatedAt = DateTimeOffset.UtcNow;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Failed to cleanup media {MediaId}", media.Id);
            }
        }

        await _dbContext.SaveChangesAsync();
        _logger.LogInformation("Cleaned up {Count} expired media items", expiredMedia.Count);
    }

    public async Task<bool> RegenerateBriefAsync(DateTimeOffset date)
    {
        var existingMedia = await GetDailyMediaAsync(date);
        if (existingMedia != null)
        {
            // Archive existing media
            existingMedia.IsArchived = true;
            existingMedia.UpdatedAt = DateTimeOffset.UtcNow;
            await _dbContext.SaveChangesAsync();
        }

        // Generate new brief
        var newMedia = await GenerateDailyBriefAsync(date);
        return newMedia != null;
    }

    public async Task<DailyBriefStatus> GetStatusAsync(DateOnly date)
    {
        var dateTimeOffset = new DateTimeOffset(date.ToDateTime(TimeOnly.MinValue));
        var media = await GetDailyMediaAsync(dateTimeOffset);

        return new DailyBriefStatus
        {
            IsGenerated = media != null,
            LastRun = media?.CreatedAt
        };
    }

    public async Task<DailyMedia?> GetLatestMediaAsync()
    {
        return await _dbContext.DailyMedia
            .Where(m => !m.IsArchived)
            .OrderByDescending(m => m.Date)
            .FirstOrDefaultAsync();
    }

    private async Task<BriefInput?> CollectBriefDataAsync(DateTimeOffset date)
    {
        var startOfDay = date.Date;
        var endOfDay = startOfDay.AddDays(1);

        // Get events (from local DB)
        var events = _settings.DailyStudioIncludeCalendar
            ? await _dbContext.Events
                .Where(e => e.Start >= startOfDay && e.Start < endOfDay)
                .OrderBy(e => e.Start)
                .ToListAsync()
            : new List<EventItem>();

        // Get tasks
        var tasks = _settings.DailyStudioIncludeTasks
            ? await _dbContext.Tasks
                .Where(t => !t.IsArchived &&
                           (t.DueAt == null || t.DueAt.Value.Date == date.Date) &&
                           t.Status != TodoStatus.Completed)
                .ToListAsync()
            : new List<TaskItem>();

        // Get habits
        var habits = _settings.DailyStudioIncludeHabits
            ? await _dbContext.Habits
                .Where(h => !h.IsArchived)
                .ToListAsync()
            : new List<Habit>();

        // Get habit logs for the date
        var habitLogs = habits.Any()
            ? await _dbContext.HabitLogs
                .Where(hl => hl.Date == DateOnly.FromDateTime(date.DateTime))
                .ToListAsync()
            : new List<HabitLog>();

        return new BriefInput
        {
            Date = date,
            Events = events,
            Tasks = tasks,
            Habits = habits,
            HabitLogs = habitLogs,
            Settings = _settings,
            RedactPrivateInfo = _settings.DailyStudioRedactPrivateInfo
        };
    }

    private async Task<BriefOutput?> GenerateBriefContentAsync(BriefInput input)
    {
        // Try preferred method first
        if (_settings.DailyStudioPreferredMethod == "notebooklm")
        {
            // TODO: Implement NotebookLM brief generation
            _logger.LogInformation("NotebookLM brief generation not yet implemented, falling back to Gemini");
        }

        // Fallback to Gemini
        return await _geminiService.GenerateBriefAsync(input);
    }

    private async Task<DailyMedia?> GenerateMediaAsync(DateTimeOffset date, BriefInput input, BriefOutput output, string inputHash)
    {
        var media = new DailyMedia
        {
            Date = date,
            BriefJson = JsonSerializer.Serialize(output),
            BriefHash = inputHash,
            ExpiresAt = date.AddDays(_settings.DailyStudioRetentionDays),
            GenerationMethod = _settings.DailyStudioPreferredMethod,
            IsFallbackUsed = false
        };

        // Generate audio
        var audioContent = await GenerateAudioContentAsync(output);
        if (audioContent != null)
        {
            var audioPath = await SaveAudioFileAsync(date, audioContent);
            if (audioPath != null)
            {
                media.AudioFilePath = audioPath;
                media.Duration = TimeSpan.FromSeconds(90); // Estimate
            }
        }

        // Generate video if requested
        if (_settings.DailyStudioGenerateVideo)
        {
            var videoPath = await GenerateVideoAsync(date, output);
            if (videoPath != null)
            {
                media.VideoFilePath = videoPath;
            }
        }

        return media;
    }

    private async Task<byte[]?> GenerateAudioContentAsync(BriefOutput output)
    {
        // Try preferred method
        if (_settings.DailyStudioPreferredMethod == "notebooklm")
        {
            // TODO: Implement NotebookLM audio generation
            _logger.LogInformation("NotebookLM audio generation not yet implemented");
        }

        // Fallback to Gemini TTS
        var briefText = BuildBriefText(output);
        return await _geminiService.GenerateAudioAsync(briefText);
    }

    private async Task<string?> GenerateVideoAsync(DateTimeOffset date, BriefOutput output)
    {
        // Generate a simple slideshow video using System.Drawing for slides and FFmpeg for assembly.
        // Graceful fallback: if FFmpeg is not found or fails, return null.
        try
        {
            var baseDir = Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
                "CalmCadence",
                "DailyMedia"
            );

            Directory.CreateDirectory(baseDir);

            var dayDir = Path.Combine(baseDir, date.ToString("yyyy-MM-dd"));
            Directory.CreateDirectory(dayDir);

            var slidesDir = Path.Combine(dayDir, "slides");
            Directory.CreateDirectory(slidesDir);

            // Build slides
            int idx = 0;
            await CreateSlideAsync(Path.Combine(slidesDir, $"slide_{idx++:000}.png"),
                $"Daily Brief — {date:dddd, MMMM d}",
                new[] { output.Summary });

            var agendaLines = (output.Agenda?.Any() == true)
                ? output.Agenda.Take(6).Select(a => "• " + a)
                : Enumerable.Empty<string>();
            await CreateSlideAsync(Path.Combine(slidesDir, $"slide_{idx++:000}.png"),
                "Agenda",
                agendaLines);

            var taskLines = (output.TopTasks?.Any() == true)
                ? output.TopTasks.Take(4).Select(t => "• " + t.Title + (string.IsNullOrEmpty(t.Reason) ? string.Empty : $" — {t.Reason}"))
                : Enumerable.Empty<string>();
            await CreateSlideAsync(Path.Combine(slidesDir, $"slide_{idx++:000}.png"),
                "Top Tasks",
                taskLines);

            var habitLines = (output.Habits?.Any() == true)
                ? output.Habits.Take(6).Select(h => $"• {h.Name}: {(h.Completed ? "Completed" : "Pending")}" )
                : Enumerable.Empty<string>();
            await CreateSlideAsync(Path.Combine(slidesDir, $"slide_{idx++:000}.png"),
                "Habits",
                habitLines);

            var notesLines = (output.Notes?.Any() == true)
                ? output.Notes.Take(6).Select(n => "• " + n)
                : Enumerable.Empty<string>();
            if (notesLines.Any())
            {
                await CreateSlideAsync(Path.Combine(slidesDir, $"slide_{idx++:000}.png"),
                    "Notes",
                    notesLines);
            }

            // Assemble video with FFmpeg from slides
            var videoTemp = Path.Combine(dayDir, "daily-brief-temp.mp4");
            var videoOut = Path.Combine(baseDir, $"daily-brief-{date:yyyy-MM-dd}.mp4");

            var slidePattern = Path.Combine(slidesDir, "slide_%03d.png");
            var ffmpegArgs = $"-y -framerate 1/6 -i \"{slidePattern}\" -c:v libx264 -r 30 -pix_fmt yuv420p \"{videoTemp}\"";
            var ok = await RunFfmpegAsync(ffmpegArgs);
            if (!ok || !File.Exists(videoTemp))
            {
                _logger.LogWarning("FFmpeg not available or video assembly failed; skipping video generation");
                return null;
            }

            // Combine audio if available
            var audioPath = await FindAudioForDateAsync(date);
            if (!string.IsNullOrEmpty(audioPath) && File.Exists(audioPath))
            {
                var ffmpegArgs2 = $"-y -i \"{videoTemp}\" -i \"{audioPath}\" -c:v copy -c:a aac -shortest \"{videoOut}\"";
                ok = await RunFfmpegAsync(ffmpegArgs2);
                if (!ok)
                {
                    _logger.LogWarning("FFmpeg failed to mux audio; falling back to silent video");
                    File.Copy(videoTemp, videoOut, overwrite: true);
                }
            }
            else
            {
                File.Copy(videoTemp, videoOut, overwrite: true);
            }

            // Cleanup temp
            try { File.Delete(videoTemp); } catch { /* ignore */ }

            return File.Exists(videoOut) ? videoOut : null;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to generate video for {Date}", date);
            return null;
        }
    }

    private async Task<bool> RunFfmpegAsync(string args)
    {
        try
        {
            var psi = new System.Diagnostics.ProcessStartInfo("ffmpeg", args)
            {
                UseShellExecute = false,
                CreateNoWindow = true,
                RedirectStandardError = true,
                RedirectStandardOutput = true
            };

            using var proc = new System.Diagnostics.Process { StartInfo = psi };
            proc.Start();
            var stderr = await proc.StandardError.ReadToEndAsync();
            var stdout = await proc.StandardOutput.ReadToEndAsync();
            proc.WaitForExit();

            if (proc.ExitCode != 0)
            {
                _logger.LogWarning("ffmpeg exited with code {Code}. stderr: {Stderr}", proc.ExitCode, stderr);
            }
            return proc.ExitCode == 0;
        }
        catch (System.ComponentModel.Win32Exception)
        {
            // ffmpeg not found on PATH
            _logger.LogWarning("ffmpeg executable not found on PATH");
            return false;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error running ffmpeg");
            return false;
        }
    }

    private Task<string?> FindAudioForDateAsync(DateTimeOffset date)
    {
        var mediaDir = Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
            "CalmCadence",
            "DailyMedia"
        );
        var mp3Path = Path.Combine(mediaDir, $"daily-brief-{date:yyyy-MM-dd}.mp3");
        if (File.Exists(mp3Path)) return Task.FromResult<string?>(mp3Path);
        var wavPath = Path.Combine(mediaDir, $"daily-brief-{date:yyyy-MM-dd}.wav");
        return Task.FromResult<string?>(File.Exists(wavPath) ? wavPath : null);
    }

    private Task<string?> FindAudioForDateAsync(DateOnly date)
    {
        var localMidnight = new DateTime(date.Year, date.Month, date.Day, 0, 0, 0, DateTimeKind.Local);
        var dto = new DateTimeOffset(localMidnight);
        return FindAudioForDateAsync(dto);
    }

    private async Task CreateSlideAsync(string path, string title, IEnumerable<string> lines)
    {
        await Task.Run(() =>
        {
            const int width = 1920;
            const int height = 1080;
            using var bmp = new System.Drawing.Bitmap(width, height);
            using var g = System.Drawing.Graphics.FromImage(bmp);
            g.SmoothingMode = System.Drawing.Drawing2D.SmoothingMode.AntiAlias;
            g.Clear(System.Drawing.Color.FromArgb(24, 26, 32));

            using var headerBg = new System.Drawing.SolidBrush(System.Drawing.Color.FromArgb(40, 44, 52));
            using var accent = new System.Drawing.SolidBrush(System.Drawing.Color.FromArgb(50, 130, 255));
            using var white = new System.Drawing.SolidBrush(System.Drawing.Color.White);

            // Header bar
            g.FillRectangle(headerBg, 0, 0, width, 120);
            using var titleFont = new System.Drawing.Font("Segoe UI Semibold", 48, System.Drawing.FontStyle.Bold, System.Drawing.GraphicsUnit.Pixel);
            var titleRect = new System.Drawing.RectangleF(60, 30, width - 120, 90);
            g.DrawString(title, titleFont, white, titleRect);

            // Body text
            using var bodyFont = new System.Drawing.Font("Segoe UI", 32, System.Drawing.GraphicsUnit.Pixel);
            float y = 160f;
            foreach (var line in WrapTextLines(lines, 60))
            {
                if (y > height - 80) break;
                var rect = new System.Drawing.RectangleF(60, y, width - 120, 60);
                g.DrawString(line, bodyFont, white, rect);
                y += 70f;
            }

            bmp.Save(path, System.Drawing.Imaging.ImageFormat.Png);
        });
    }

    private IEnumerable<string> WrapTextLines(IEnumerable<string> lines, int maxChars)
    {
        foreach (var line in lines)
        {
            if (string.IsNullOrWhiteSpace(line)) continue;
            var text = line.Trim();
            while (text.Length > maxChars)
            {
                var breakPos = text.LastIndexOf(' ', Math.Min(maxChars, text.Length - 1));
                if (breakPos <= 0) breakPos = maxChars;
                yield return text.Substring(0, breakPos);
                text = text.Substring(breakPos).Trim();
            }
            if (text.Length > 0) yield return text;
        }
    }

    private async Task<string?> SaveAudioFileAsync(DateTimeOffset date, byte[] audioData)
    {
        try
        {
            var mediaDir = Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
                "CalmCadence",
                "DailyMedia"
            );

            Directory.CreateDirectory(mediaDir);

            var fileName = $"daily-brief-{date:yyyy-MM-dd}.mp3";
            var filePath = Path.Combine(mediaDir, fileName);

            await File.WriteAllBytesAsync(filePath, audioData);
            return filePath;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to save audio file for {Date}", date);
            return null;
        }
    }

    private string BuildBriefText(BriefOutput output)
    {
        var sb = new StringBuilder();
        sb.AppendLine($"Good morning. Here's your daily brief for today.");
        sb.AppendLine();
        sb.AppendLine(output.Summary);
        sb.AppendLine();

        if (output.Agenda.Any())
        {
            sb.AppendLine("Your agenda for today:");
            foreach (var item in output.Agenda)
            {
                sb.AppendLine($"- {item}");
            }
            sb.AppendLine();
        }

        if (output.TopTasks.Any())
        {
            sb.AppendLine("Top priority tasks:");
            foreach (var task in output.TopTasks)
            {
                sb.AppendLine($"- {task.Title}: {task.Reason}");
            }
            sb.AppendLine();
        }

        if (output.Habits.Any())
        {
            sb.AppendLine("Habit status:");
            foreach (var habit in output.Habits)
            {
                sb.AppendLine($"- {habit.Name}: {(habit.Completed ? "Completed" : "Pending")}");
            }
            sb.AppendLine();
        }

        if (!string.IsNullOrEmpty(output.EnergyLevel))
        {
            sb.AppendLine($"Energy level: {output.EnergyLevel}");
        }

        return sb.ToString();
    }

    private string GenerateBriefHash(BriefInput input)
    {
        var json = JsonSerializer.Serialize(input);
        using var sha256 = SHA256.Create();
        var hash = sha256.ComputeHash(Encoding.UTF8.GetBytes(json));
        return Convert.ToHexString(hash);
    }
}
