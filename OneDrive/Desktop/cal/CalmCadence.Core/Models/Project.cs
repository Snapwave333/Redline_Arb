using System;
using System.Collections.Generic;

namespace CalmCadence.Core.Models;

public class Project
{
    public Guid Id { get; set; } = Guid.NewGuid();
    public string Name { get; set; } = string.Empty;
    public string? Description { get; set; }
    public string? ColorHex { get; set; }
    public DateTimeOffset CreatedAt { get; set; } = DateTimeOffset.UtcNow;
    public DateTimeOffset? ArchivedAt { get; set; }

    public ICollection<TaskItem> Tasks { get; set; } = new List<TaskItem>();
}
