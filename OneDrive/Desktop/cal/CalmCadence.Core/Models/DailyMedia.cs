using System;

namespace CalmCadence.Core.Models;

public class DailyMedia
{
    public Guid Id { get; set; } = Guid.NewGuid();
    public DateTimeOffset Date { get; set; }

    // File paths
    public string? AudioFilePath { get; set; }
    public string? VideoFilePath { get; set; }

    // Metadata
    public string? Title { get; set; }
    public string? Description { get; set; }
    public TimeSpan? Duration { get; set; }

    // Generation details
    public string? GenerationMethod { get; set; } // "notebooklm", "gemini-tts", "offline"
    public string? ApiResponse { get; set; } // JSON response from API
    public bool IsFallbackUsed { get; set; }

    // Brief data (cached)
    public string? BriefJson { get; set; }
    public string? BriefHash { get; set; }

    // Retention
    public DateTimeOffset ExpiresAt { get; set; }
    public bool IsArchived { get; set; }

    public DateTimeOffset CreatedAt { get; set; } = DateTimeOffset.UtcNow;
    public DateTimeOffset UpdatedAt { get; set; } = DateTimeOffset.UtcNow;
}
