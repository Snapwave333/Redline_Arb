using System;

namespace CalmCadence.Core.Models;

public class BriefCache
{
    public Guid Id { get; set; } = Guid.NewGuid();
    public string Hash { get; set; } = string.Empty;
    public string BriefJson { get; set; } = string.Empty;
    public DateTimeOffset CreatedAt { get; set; } = DateTimeOffset.UtcNow;
    public DateTimeOffset LastAccessedAt { get; set; } = DateTimeOffset.UtcNow;
    public int AccessCount { get; set; } = 0;
}
