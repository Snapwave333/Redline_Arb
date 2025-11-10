using System.Collections.Generic;

namespace CalmCadence.Core.Models;

public class BriefOutput
{
    public string Summary { get; set; } = string.Empty;
    public List<string> Agenda { get; set; } = new();
    public List<TopTaskPriority> TopTasks { get; set; } = new();
    public List<HabitStatus> Habits { get; set; } = new();
    public List<string> Notes { get; set; } = new();
    public string? FocusAreas { get; set; }
    public string? EnergyLevel { get; set; }
}

public class TopTaskPriority
{
    public string Title { get; set; } = string.Empty;
    public string Priority { get; set; } = string.Empty; // "high", "medium", "low"
    public string? Reason { get; set; }
}

public class HabitStatus
{
    public string Name { get; set; } = string.Empty;
    public bool Completed { get; set; }
    public string? Note { get; set; }
}
