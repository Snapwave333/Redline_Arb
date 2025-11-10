using System;

namespace CalmCadence.Core.Models;

public class HabitLog
{
    public Guid Id { get; set; } = Guid.NewGuid();
    public Guid HabitId { get; set; }

    // Stored as DateOnly via EF Core value converter (SQLite doesn't have DateOnly)
    public DateOnly Date { get; set; } = DateOnly.FromDateTime(DateTime.UtcNow);

    public double? Value { get; set; }
    public string? Note { get; set; }

    public DateTimeOffset CreatedAt { get; set; } = DateTimeOffset.UtcNow;

    // Navigation
    public Habit? Habit { get; set; }
}
