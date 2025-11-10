using System;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using CalmCadence.Core.Interfaces;
using CalmCadence.Core.Models;
using Microsoft.Extensions.Logging;

namespace CalmCadence.Core.Services;

public class GeminiService : IGeminiService
{
    private readonly HttpClient _httpClient;
    private readonly ILogger<GeminiService> _logger;
    private readonly string? _apiKey;

    public GeminiService(HttpClient httpClient, ILogger<GeminiService> logger, string? apiKey = null)
    {
        _httpClient = httpClient;
        _logger = logger;
        _apiKey = apiKey;
    }

    public async Task<BriefOutput?> GenerateBriefAsync(BriefInput input)
    {
        if (string.IsNullOrEmpty(_apiKey))
        {
            _logger.LogWarning("Gemini API key not configured");
            return null;
        }

        try
        {
            var prompt = BuildBriefPrompt(input);
            var response = await GenerateTextAsync(prompt, 0.2);

            if (string.IsNullOrEmpty(response))
            {
                _logger.LogWarning("No response from Gemini API, using offline fallback");
                return GenerateOfflineBrief(input);
            }

            // Try to extract JSON from the response
            var jsonStart = response.IndexOf('{');
            var jsonEnd = response.LastIndexOf('}');

            if (jsonStart >= 0 && jsonEnd > jsonStart)
            {
                var jsonContent = response.Substring(jsonStart, jsonEnd - jsonStart + 1);

                // Parse the JSON response
                var briefOutput = JsonSerializer.Deserialize<BriefOutput>(jsonContent, new JsonSerializerOptions
                {
                    PropertyNameCaseInsensitive = true
                });

                return briefOutput;
            }
            else
            {
                _logger.LogWarning("No JSON found in Gemini response, using offline fallback");
                return GenerateOfflineBrief(input);
            }
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to generate brief with Gemini, using offline fallback");
            return GenerateOfflineBrief(input);
        }
    }

    public async Task<byte[]?> GenerateAudioAsync(string text, string voice = "en-US-Neural2-D")
    {
        if (string.IsNullOrEmpty(_apiKey))
        {
            _logger.LogWarning("Gemini API key not configured");
            return null;
        }

        try
        {
            // Note: This is a placeholder - actual Gemini TTS API implementation would go here
            // The Gemini API doesn't currently have TTS, so this would need to be implemented
            // with a different service or when Gemini adds TTS support
            _logger.LogInformation("Gemini TTS not yet implemented - using placeholder");
            return null;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to generate audio with Gemini TTS");
            return null;
        }
    }

    public async Task<string?> GenerateTextAsync(string prompt, double temperature = 0.2)
    {
        if (string.IsNullOrEmpty(_apiKey))
        {
            _logger.LogWarning("Gemini API key not configured");
            return null;
        }

        try
        {
            var requestBody = new
            {
                contents = new[]
                {
                    new
                    {
                        parts = new[]
                        {
                            new { text = prompt }
                        }
                    }
                },
                generationConfig = new
                {
                    temperature = temperature,
                    maxOutputTokens = 2048
                }
            };

            var json = JsonSerializer.Serialize(requestBody);
            var content = new StringContent(json, Encoding.UTF8, "application/json");

            var url = $"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent?key={_apiKey}";
            var response = await _httpClient.PostAsync(url, content);

            if (!response.IsSuccessStatusCode)
            {
                _logger.LogError("Gemini API request failed with status {StatusCode}", response.StatusCode);
                return null;
            }

            var responseJson = await response.Content.ReadAsStringAsync();
            var responseObj = JsonSerializer.Deserialize<JsonElement>(responseJson);

            // Extract the text from the response
            if (responseObj.TryGetProperty("candidates", out var candidates) &&
                candidates[0].TryGetProperty("content", out var contentProp) &&
                contentProp.TryGetProperty("parts", out var parts) &&
                parts[0].TryGetProperty("text", out var text))
            {
                return text.GetString();
            }

            return null;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to generate text with Gemini");
            return null;
        }
    }

    private string BuildBriefPrompt(BriefInput input)
    {
        var sb = new StringBuilder();
        sb.AppendLine("Generate a daily brief in the following JSON format:");
        sb.AppendLine("{");
        sb.AppendLine("  \"summary\": \"Brief overview of the day\",");
        sb.AppendLine("  \"agenda\": [\"Key agenda items\"],");
        sb.AppendLine("  \"topTasks\": [{\"title\": \"Task name\", \"priority\": \"high|medium|low\", \"reason\": \"Why this matters\"}],");
        sb.AppendLine("  \"habits\": [{\"name\": \"Habit name\", \"completed\": true|false, \"note\": \"Optional note\"}],");
        sb.AppendLine("  \"notes\": [\"Important notes\"],");
        sb.AppendLine("  \"focusAreas\": \"Key focus areas for today\",");
        sb.AppendLine("  \"energyLevel\": \"Expected energy level\"");
        sb.AppendLine("}");
        sb.AppendLine();
        sb.AppendLine($"Date: {input.Date:yyyy-MM-dd}");
        sb.AppendLine();

        if (input.Events.Any())
        {
            sb.AppendLine("Calendar Events:");
            foreach (var evt in input.Events)
            {
                var location = input.RedactPrivateInfo ? "[REDACTED]" : evt.Location;
                sb.AppendLine($"- {evt.Title} at {evt.Start:t} ({location})");
            }
            sb.AppendLine();
        }

        if (input.Tasks.Any())
        {
            sb.AppendLine("Tasks:");
            foreach (var task in input.Tasks.Where(t => t.Status != Enums.TodoStatus.Completed))
            {
                sb.AppendLine($"- {task.Title} (Priority: {task.Priority})");
            }
            sb.AppendLine();
        }

        if (input.Habits.Any())
        {
            sb.AppendLine("Habits:");
            foreach (var habit in input.Habits)
            {
                var completed = input.HabitLogs.Any(hl => hl.HabitId == habit.Id && hl.Date == DateOnly.FromDateTime(input.Date.DateTime));
                sb.AppendLine($"- {habit.Name}: {(completed ? "Completed" : "Pending")}");
            }
            sb.AppendLine();
        }

        sb.AppendLine("Please provide a structured daily brief that helps prioritize the day effectively.");
        return sb.ToString();
    }

    private BriefOutput GenerateOfflineBrief(BriefInput input)
    {
        _logger.LogInformation("Generating offline brief for {Date}", input.Date);

        var output = new BriefOutput();

        // Basic summary
        var eventCount = input.Events.Count;
        var taskCount = input.Tasks.Count(t => t.Status != Enums.TodoStatus.Completed);
        var habitCount = input.Habits.Count;
        var completedHabits = input.HabitLogs.Count;

        output.Summary = $"You have {eventCount} calendar events, {taskCount} pending tasks, and {completedHabits}/{habitCount} habits completed today.";

        // Agenda from events
        output.Agenda = input.Events
            .OrderBy(e => e.Start)
            .Select(e => $"{e.Title} at {e.Start:t}")
            .ToList();

        // Top tasks
        output.TopTasks = input.Tasks
            .Where(t => t.Status != Enums.TodoStatus.Completed)
            .OrderByDescending(t => t.Priority)
            .Take(3)
            .Select(t => new TopTaskPriority
            {
                Title = t.Title ?? "Untitled Task",
                Priority = t.Priority.ToString().ToLower(),
                Reason = $"Due: {t.DueAt?.ToString("d") ?? "No due date"}"
            })
            .ToList();

        // Habit status
        output.Habits = input.Habits
            .Select(h =>
            {
                var completed = input.HabitLogs.Any(hl => hl.HabitId == h.Id && hl.Date == DateOnly.FromDateTime(input.Date.DateTime));
                return new HabitStatus
                {
                    Name = h.Name ?? "Unnamed Habit",
                    Completed = completed
                };
            })
            .ToList();

        // Basic focus areas and energy level
        output.FocusAreas = taskCount > 0 ? "Focus on completing your highest priority tasks" : "Take time to plan your day";
        output.EnergyLevel = "Moderate - good day for steady progress";

        return output;
    }
}
