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
using CalmCadence.Data.Context;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;

namespace CalmCadence.App.Services;

public class DailyStudioService : IDailyStudioService
{
    private readonly CalmCadenceDbContext _dbContext;
    private readonly IGeminiService _geminiService;
    private readonly IGoogleApiService _googleApiService;
    private readonly ICalendarProvider _calendarProvider;
    private readonly ILogger<DailyStudioService> _logger;
    private readonly Settings _settings;

    public DailyStudioService(
        CalmCadenceDbContext dbContext,
        IGeminiService geminiService,
        IGoogleApiService googleApiService,
        ICalendarProvider calendarProvider,
        ILogger<DailyStudioService> logger,
        Settings settings)
    {
        _dbContext = dbContext;
        _geminiService = geminiService;
        _googleApiService = googleApiService;
        _calendarProvider = calendarProvider;
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

    private async Task<BriefInput?> CollectBriefDataAsync(DateTimeOffset date)
    {
        var startOfDay = date.Date;
        var endOfDay = startOfDay.AddDays(1);

        // Get events from local DB within the day window
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
                           t.Status != CalmCadence.Core.Enums.TodoStatus.Completed)
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
        var inputHash = GenerateBriefHash(input);

        // Check cache first
        var cachedBrief = await _dbContext.BriefCache
            .FirstOrDefaultAsync(c => c.Hash == inputHash);

        if (cachedBrief != null)
        {
            _logger.LogInformation("Using cached brief for hash {Hash}", inputHash);

            // Update access statistics
            cachedBrief.LastAccessedAt = DateTimeOffset.UtcNow;
            cachedBrief.AccessCount++;
            await _dbContext.SaveChangesAsync();

            // Parse and return cached brief
            try
            {
                return JsonSerializer.Deserialize<BriefOutput>(cachedBrief.BriefJson);
            }
            catch (Exception ex)
            {
                _logger.LogWarning(ex, "Failed to parse cached brief, regenerating");
            }
        }

        // Generate new brief
        BriefOutput? briefOutput = null;

        // Try preferred method first
        if (_settings.DailyStudioPreferredMethod == "notebooklm")
        {
            // TODO: Implement NotebookLM brief generation
            _logger.LogInformation("NotebookLM brief generation not yet implemented, falling back to Gemini");
        }

        // Fallback to Gemini
        briefOutput = await _geminiService.GenerateBriefAsync(input);

        if (briefOutput != null)
        {
            // Cache the result
            var briefJson = JsonSerializer.Serialize(briefOutput);
            var cacheEntry = new BriefCache
            {
                Hash = inputHash,
                BriefJson = briefJson,
                CreatedAt = DateTimeOffset.UtcNow,
                LastAccessedAt = DateTimeOffset.UtcNow,
                AccessCount = 1
            };

            _dbContext.BriefCache.Add(cacheEntry);
            await _dbContext.SaveChangesAsync();

            _logger.LogInformation("Cached new brief for hash {Hash}", inputHash);
        }

        return briefOutput;
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
            var audioPath = await SaveAudioFileAsync(date, audioContent, "mp3");
            if (audioPath != null)
            {
                media.AudioFilePath = audioPath;
                media.Duration = TimeSpan.FromSeconds(90); // Estimate
            }
        }
        else
        {
            // Fallback: generate a short silent WAV so video can still be muxed cleanly
            var silentWav = GenerateSilentWavBytes(seconds: 6);
            var audioPath = await SaveAudioFileAsync(date, silentWav, "wav");
            if (audioPath != null)
            {
                media.AudioFilePath = audioPath;
                media.IsFallbackUsed = true;
                media.Duration = TimeSpan.FromSeconds(6);
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
        var briefText = BuildBriefText(output);

        // Try preferred method first
        if (_settings.DailyStudioPreferredMethod == "notebooklm")
        {
            try
            {
                _logger.LogInformation("Attempting NotebookLM audio generation");

                // Create or update notebook with brief content
                var notebookId = await _googleApiService.CreateOrUpdateNotebookAsync(
                    "your-project-id", // TODO: Get from settings
                    "us-central1",     // TODO: Get from settings
                    "daily-brief-notebook",
                    briefText);

                if (!string.IsNullOrEmpty(notebookId))
                {
                    // Generate audio overview
                    var audioResult = await _googleApiService.GenerateAudioOverviewAsync(
                        "your-project-id", // TODO: Get from settings
                        "us-central1",     // TODO: Get from settings
                        notebookId,
                        "Daily productivity brief and planning overview",
                        new[] { "brief-content" });

                    if (!string.IsNullOrEmpty(audioResult))
                    {
                        _logger.LogInformation("Successfully generated audio with NotebookLM");
                        // TODO: Download the actual audio file from the result URL
                        // No placeholder bytes here. If the download is not implemented yet,
                        // return null to trigger the valid silent WAV fallback downstream.
                        return null;
                    }
                }

                _logger.LogWarning("NotebookLM audio generation failed, falling back to Gemini");
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "NotebookLM audio generation failed");
            }
        }

        // Fallback to Gemini TTS
        _logger.LogInformation("Using Gemini TTS for audio generation");
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
            var stderrTask = proc.StandardError.ReadToEndAsync();
            var stdoutTask = proc.StandardOutput.ReadToEndAsync();
            await proc.WaitForExitAsync();
            var stderr = await stderrTask;
            var stdout = await stdoutTask;

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

    private async Task<string?> SaveAudioFileAsync(DateTimeOffset date, byte[] audioData, string extension = "mp3")
    {
        try
        {
            var mediaDir = Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
                "CalmCadence",
                "DailyMedia"
            );

            Directory.CreateDirectory(mediaDir);

            var safeExt = extension.StartsWith(".") ? extension : "." + extension;
            var fileName = $"daily-brief-{date:yyyy-MM-dd}{safeExt}";
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

    private byte[] GenerateSilentWavBytes(int seconds = 3, int sampleRate = 44100, short channels = 1)
    {
        // Generate a valid PCM WAV buffer with silence
        var bitsPerSample = (short)16;
        var bytesPerSample = bitsPerSample / 8;
        var blockAlign = (short)(channels * bytesPerSample);
        var byteRate = sampleRate * blockAlign;
        var totalSamples = seconds * sampleRate * channels;
        var dataSize = totalSamples * bytesPerSample;
        var fileSizeMinus8 = 36 + dataSize;

        using var ms = new MemoryStream(44 + dataSize);
        using var bw = new BinaryWriter(ms, Encoding.ASCII, leaveOpen: true);

        // RIFF header
        bw.Write(Encoding.ASCII.GetBytes("RIFF"));
        bw.Write(fileSizeMinus8);
        bw.Write(Encoding.ASCII.GetBytes("WAVE"));

        // fmt chunk
        bw.Write(Encoding.ASCII.GetBytes("fmt "));
        bw.Write(16); // PCM header size
        bw.Write((short)1); // PCM format
        bw.Write(channels);
        bw.Write(sampleRate);
        bw.Write(byteRate);
        bw.Write(blockAlign);
        bw.Write(bitsPerSample);

        // data chunk
        bw.Write(Encoding.ASCII.GetBytes("data"));
        bw.Write(dataSize);

        // Silent samples
        for (int i = 0; i < dataSize; i++) bw.Write((byte)0);

        return ms.ToArray();
    }

    private string GenerateBriefHash(BriefInput input)
    {
        var json = JsonSerializer.Serialize(input);
        using var sha256 = SHA256.Create();
        var hash = sha256.ComputeHash(Encoding.UTF8.GetBytes(json));
        return Convert.ToHexString(hash);
    }

    public async Task<DailyBriefStatus> GetStatusAsync(DateOnly date)
    {
        var localMidnight = new DateTime(date.Year, date.Month, date.Day, 0, 0, 0, DateTimeKind.Local);
        var dtoDate = new DateTimeOffset(localMidnight);

        var media = await _dbContext.DailyMedia
            .FirstOrDefaultAsync(m => m.Date.Date == dtoDate.Date && !m.IsArchived);

        bool hasAudio = false;
        bool hasVideo = false;

        if (media != null)
        {
            try
            {
                // Verify audio
                if (!string.IsNullOrEmpty(media.AudioFilePath) && File.Exists(media.AudioFilePath))
                {
                    hasAudio = true;
                }
                else
                {
                    var audioPath = await FindAudioForDateAsync(dtoDate);
                    if (!string.IsNullOrEmpty(audioPath) && File.Exists(audioPath))
                    {
                        hasAudio = true;
                        if (string.IsNullOrEmpty(media.AudioFilePath))
                        {
                            media.AudioFilePath = audioPath;
                            media.UpdatedAt = DateTimeOffset.UtcNow;
                            await _dbContext.SaveChangesAsync();
                        }
                    }
                }

                // Verify video
                if (!string.IsNullOrEmpty(media.VideoFilePath) && File.Exists(media.VideoFilePath))
                {
                    hasVideo = true;
                }
                else
                {
                    var baseDir = Path.Combine(
                        Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
                        "CalmCadence",
                        "DailyMedia"
                    );
                    var expectedVideoPath = Path.Combine(baseDir, $"daily-brief-{dtoDate:yyyy-MM-dd}.mp4");
                    if (File.Exists(expectedVideoPath))
                    {
                        hasVideo = true;
                        if (string.IsNullOrEmpty(media.VideoFilePath))
                        {
                            media.VideoFilePath = expectedVideoPath;
                            media.UpdatedAt = DateTimeOffset.UtcNow;
                            await _dbContext.SaveChangesAsync();
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                _logger.LogWarning(ex, "Error while verifying media file existence for {Date}", dtoDate);
            }
        }

        var isGenerated = media != null && (hasAudio || hasVideo);
        var lastRun = media != null ? media.UpdatedAt : (DateTimeOffset?)null;

        return new DailyBriefStatus
        {
            IsGenerated = isGenerated,
            LastRun = lastRun
        };
    }

    public async Task<DailyMedia?> GetLatestMediaAsync()
    {
        var latest = await _dbContext.DailyMedia
            .Where(m => !m.IsArchived)
            .OrderByDescending(m => m.Date)
            .FirstOrDefaultAsync();

        if (latest == null) return null;

        try
        {
            // Try to fill missing or outdated audio path
            if (string.IsNullOrEmpty(latest.AudioFilePath) || !File.Exists(latest.AudioFilePath))
            {
                var audioPath = await FindAudioForDateAsync(latest.Date);
                if (!string.IsNullOrEmpty(audioPath) && File.Exists(audioPath))
                {
                    latest.AudioFilePath = audioPath;
                }
            }

            // Try to fill missing or outdated video path
            if (string.IsNullOrEmpty(latest.VideoFilePath) || !File.Exists(latest.VideoFilePath))
            {
                var baseDir = Path.Combine(
                    Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
                    "CalmCadence",
                    "DailyMedia"
                );
                var expectedVideoPath = Path.Combine(baseDir, $"daily-brief-{latest.Date:yyyy-MM-dd}.mp4");
                if (File.Exists(expectedVideoPath))
                {
                    latest.VideoFilePath = expectedVideoPath;
                }
            }
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "Error while verifying latest media files");
        }

        return latest;
    }


}
