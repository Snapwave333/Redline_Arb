using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using CalmCadence.Core.Models;

namespace CalmCadence.Core.Interfaces;

public interface ICalendarProvider
{
    Task<IList<EventItem>> GetEventsAsync(DateTimeOffset start, DateTimeOffset end);
    Task<EventItem?> GetEventAsync(string eventId);
    Task<bool> CreateEventAsync(EventItem eventItem);
    Task<bool> UpdateEventAsync(EventItem eventItem);
    Task<bool> DeleteEventAsync(string eventId);
}
