using System;

namespace CalmCadence.Core.Models;

public class Settings
{
    // Single-row table; Id always 1
    public int Id { get; set; } = 1;

    public TimeSpan QuietHoursStart { get; set; } = TimeSpan.FromHours(22);
    public TimeSpan QuietHoursEnd { get; set; } = TimeSpan.FromHours(7);

    public bool LowSensoryModeEnabled { get; set; }
    public bool HighContrastEnabled { get; set; }
    public bool ToastsEnabled { get; set; } = true;
    public bool UndoEnabled { get; set; } = true;

    public string TimeZone { get; set; } = "UTC";
    public DayOfWeek FirstDayOfWeek { get; set; } = DayOfWeek.Monday;
    public TimeSpan? DailyBriefTime { get; set; }

    // Daily Studio Settings
    public bool DailyStudioEnabled { get; set; } = true;
    public TimeSpan DailyStudioTime { get; set; } = TimeSpan.FromHours(7.5); // 07:30
    public string DailyStudioTimeZone { get; set; } = "America/Denver"; // MDT
    public bool DailyStudioIncludeCalendar { get; set; } = true;
    public bool DailyStudioIncludeTasks { get; set; } = true;
    public bool DailyStudioIncludeHabits { get; set; } = true;
    public bool DailyStudioRedactPrivateInfo { get; set; } = false;
    public bool DailyStudioOfflineFallback { get; set; } = true;
    public string DailyStudioPreferredMethod { get; set; } = "notebooklm"; // "notebooklm", "gemini", "offline"
    public bool DailyStudioGenerateVideo { get; set; } = true;
    public int DailyStudioRetentionDays { get; set; } = 30;
    public string? GoogleServiceAccountKeyPath { get; set; }
    public string? GeminiApiKey { get; set; }

    // Calendar Sync Fields
    // Tracks last successful Google Calendar sync
    public DateTimeOffset? GoogleLastSync { get; set; }
    public bool GoogleSyncEnabled { get; set; } = false;

    // Use deterministic defaults to avoid EF Core HasData nondeterminism
    public DateTimeOffset CreatedAt { get; set; } = DateTimeOffset.UnixEpoch;
    public DateTimeOffset UpdatedAt { get; set; } = DateTimeOffset.UnixEpoch;
}
