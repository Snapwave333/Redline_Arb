using System;

namespace CalmCadence.Core.Models;

public enum AgendaItemType
{
    Task,
    Event,
    Routine,
    Habit
}

public class AgendaEntry
{
    public AgendaItemType Type { get; set; }
    public string Title { get; set; } = string.Empty;
    public DateTimeOffset? Start { get; set; }
    public DateTimeOffset? End { get; set; }
    public string? SourceId { get; set; }
    public string? Notes { get; set; }
}
