using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using CalmCadence.Core.Interfaces;
using CalmCadence.Core.Models;
using Ical.Net;
using Ical.Net.CalendarComponents;
using Ical.Net.DataTypes;
using Microsoft.Extensions.Logging;

namespace CalmCadence.Core.Services;

public class IcsCalendarProvider : ICalendarProvider
{
    private readonly ILogger<IcsCalendarProvider> _logger;
    private readonly string _icsFilePath;

    public IcsCalendarProvider(ILogger<IcsCalendarProvider> logger, string icsFilePath)
    {
        _logger = logger;
        _icsFilePath = icsFilePath;
    }

    public async Task<IList<EventItem>> GetEventsAsync(DateTimeOffset start, DateTimeOffset end)
    {
        try
        {
            if (!File.Exists(_icsFilePath))
            {
                _logger.LogWarning("ICS file not found: {Path}", _icsFilePath);
                return new List<EventItem>();
            }

            var icsContent = await File.ReadAllTextAsync(_icsFilePath);
            var calendar = Calendar.Load(icsContent);

            if (calendar == null)
            {
                _logger.LogWarning("Failed to parse ICS file: {Path}", _icsFilePath);
                return new List<EventItem>();
            }

            var events = calendar.Events
                .Where(e => e.Start.Value >= start.DateTime && e.Start.Value < end.DateTime)
                .Select(e => new EventItem
                {
                    Id = Guid.NewGuid(),
                    Title = e.Summary ?? "Untitled Event",
                    Description = e.Description,
                    Start = new DateTimeOffset(e.Start.Value),
                    End = new DateTimeOffset(e.End?.Value ?? e.Start.Value.AddHours(1)),
                    IsAllDay = e.IsAllDay,
                    Location = e.Location,
                    ExternalId = e.Uid,
                    Source = Enums.EventSource.Ics,
                    CreatedAt = DateTimeOffset.UtcNow,
                    UpdatedAt = DateTimeOffset.UtcNow
                })
                .ToList();

            _logger.LogInformation("Loaded {Count} events from ICS file for date range {Start} to {End}", events.Count, start, end);
            return events;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to load events from ICS file");
            return new List<EventItem>();
        }
    }

    public async Task<EventItem?> GetEventAsync(string eventId)
    {
        // For ICS files, we don't have individual event lookup by ID
        // This would require parsing the entire file and finding by UID
        _logger.LogWarning("GetEventAsync not implemented for ICS provider");
        return null;
    }

    public async Task<bool> CreateEventAsync(EventItem eventItem)
    {
        // ICS files are typically read-only for import
        _logger.LogWarning("CreateEventAsync not implemented for ICS provider");
        return false;
    }

    public async Task<bool> UpdateEventAsync(EventItem eventItem)
    {
        // ICS files are typically read-only for import
        _logger.LogWarning("UpdateEventAsync not implemented for ICS provider");
        return false;
    }

    public async Task<bool> DeleteEventAsync(string eventId)
    {
        // ICS files are typically read-only for import
        _logger.LogWarning("DeleteEventAsync not implemented for ICS provider");
        return false;
    }
}
