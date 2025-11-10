using System;
using System.Collections.Generic;

namespace CalmCadence.Core.Models;

public class Routine
{
    public Guid Id { get; set; } = Guid.NewGuid();
    public string Name { get; set; } = string.Empty;
    public string? Description { get; set; }

    // JSON array of RoutineStep objects
    public string StepsJson { get; set; } = "[]";

    public bool Enabled { get; set; } = true;
    public string? ColorHex { get; set; }
    public int SortOrder { get; set; }

    public DateTimeOffset CreatedAt { get; set; } = DateTimeOffset.UtcNow;
    public DateTimeOffset? UpdatedAt { get; set; }

    // Navigation property for easier access (not stored in DB)
    public List<RoutineStep> Steps { get; set; } = new();
}

public class RoutineStep
{
    public Guid Id { get; set; } = Guid.NewGuid();
    public RoutineStepType Type { get; set; }

    // Human-readable description
    public string Description { get; set; } = string.Empty;

    // Configuration data as JSON (varies by step type)
    public string ConfigJson { get; set; } = "{}";

    // Execution order within the routine
    public int Order { get; set; }

    // Optional duration for timed steps (in minutes)
    public int? DurationMinutes { get; set; }

    // Whether this step is enabled
    public bool IsEnabled { get; set; } = true;
}

public enum RoutineStepType
{
    // Information steps
    ReviewAgenda = 0,
    ReviewTasks = 1,
    ReviewHabits = 2,

    // Action steps
    MarkHabitComplete = 3,
    StartTimer = 4,
    OpenApplication = 5,

    // Workflow steps
    WaitForUserInput = 6,
    ShowNotification = 7,

    // Future extensibility
    CustomAction = 99
}
