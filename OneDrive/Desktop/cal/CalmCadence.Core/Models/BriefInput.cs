using System;
using System.Collections.Generic;

namespace CalmCadence.Core.Models;

public class BriefInput
{
    public DateTimeOffset Date { get; set; }
    public List<EventItem> Events { get; set; } = new();
    public List<TaskItem> Tasks { get; set; } = new();
    public List<Habit> Habits { get; set; } = new();
    public List<HabitLog> HabitLogs { get; set; } = new();
    public Settings? Settings { get; set; }
    public bool RedactPrivateInfo { get; set; }
}
