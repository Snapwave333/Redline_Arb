using System;
using System.Collections.Generic;
using CalmCadence.Core.Enums;

namespace CalmCadence.Core.Models;

public class Habit
{
    public Guid Id { get; set; } = Guid.NewGuid();
    public string Name { get; set; } = string.Empty;
    public string? Description { get; set; }

    public HabitType Type { get; set; } = HabitType.Binary;
    public double? TargetValue { get; set; }
    public string? Unit { get; set; }

    public string? ScheduleJson { get; set; }
    public string? ColorHex { get; set; }

    public bool IsArchived { get; set; }
    public DateTimeOffset CreatedAt { get; set; } = DateTimeOffset.UtcNow;

    public ICollection<HabitLog> Logs { get; set; } = new List<HabitLog>();
}
