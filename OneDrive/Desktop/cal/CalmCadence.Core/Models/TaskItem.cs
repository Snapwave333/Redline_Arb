using System;
using CalmCadence.Core.Enums;

namespace CalmCadence.Core.Models;

public class TaskItem
{
    public Guid Id { get; set; } = Guid.NewGuid();
    public Guid? ProjectId { get; set; }

    public string Title { get; set; } = string.Empty;
    public string? Notes { get; set; }

    public DateTimeOffset? DueAt { get; set; }
    public DateTimeOffset? StartAt { get; set; }
    public DateTimeOffset? CompletedAt { get; set; }

    public TaskPriority Priority { get; set; } = TaskPriority.Normal;
    public TodoStatus Status { get; set; } = TodoStatus.Inbox;

    public int? EstimateMinutes { get; set; }
    public int OrderIndex { get; set; } = 0;
    public bool IsArchived { get; set; }

    public DateTimeOffset CreatedAt { get; set; } = DateTimeOffset.UtcNow;
    public DateTimeOffset UpdatedAt { get; set; } = DateTimeOffset.UtcNow;

    // Navigation
    public Project? Project { get; set; }
}
