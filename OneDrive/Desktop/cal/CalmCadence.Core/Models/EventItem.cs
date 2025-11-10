using System;
using CalmCadence.Core.Enums;

namespace CalmCadence.Core.Models;

public class EventItem
{
    public Guid Id { get; set; } = Guid.NewGuid();

    public string Title { get; set; } = string.Empty;
    public string? Description { get; set; }

    public DateTimeOffset Start { get; set; }
    public DateTimeOffset End { get; set; }
    public bool IsAllDay { get; set; }

    public string? Location { get; set; }
    public string? ExternalId { get; set; }
    public EventSource Source { get; set; } = EventSource.Local;
    public string? CalendarId { get; set; }
    public string? RecurrenceRule { get; set; }

    public DateTimeOffset CreatedAt { get; set; } = DateTimeOffset.UtcNow;
    public DateTimeOffset UpdatedAt { get; set; } = DateTimeOffset.UtcNow;
}
