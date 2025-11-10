using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using CalmCadence.Core.Interfaces;
using CalmCadence.Core.Models;
using Google.Apis.Calendar.v3;
using Google.Apis.Calendar.v3.Data;
using Google.Apis.Services;
using Microsoft.Extensions.Logging;

namespace CalmCadence.Core.Services;

public class GoogleCalendarProvider : ICalendarProvider
{
    private readonly IGoogleOAuthService _oauth;
    private readonly ILogger<GoogleCalendarProvider> _logger;
    private CalendarService? _service;
    private string? _defaultCalendarId;

    public GoogleCalendarProvider(IGoogleOAuthService oauth, ILogger<GoogleCalendarProvider> logger)
    {
        _oauth = oauth;
        _logger = logger;
    }

    private async Task<bool> EnsureServiceAsync()
    {
        if (_service != null) return true;
        var cred = await _oauth.GetCredentialAsync();
        if (cred == null) return false;
        _service = new CalendarService(new BaseClientService.Initializer
        {
            HttpClientInitializer = cred,
            ApplicationName = "CalmCadence"
        });

        // Determine primary calendar id
        try
        {
            var list = await _service.CalendarList.List().ExecuteAsync();
            var primary = list.Items?.FirstOrDefault(c => c.Primary == true) ?? list.Items?.FirstOrDefault();
            _defaultCalendarId = primary?.Id ?? "primary";
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to load calendar list");
            _defaultCalendarId = "primary";
        }
        return true;
    }

    public async Task<IList<EventItem>> GetEventsAsync(DateTimeOffset start, DateTimeOffset end)
    {
        var result = new List<EventItem>();
        if (!await EnsureServiceAsync()) return result;
        try
        {
            var req = _service!.Events.List(_defaultCalendarId);
            // Use DateTimeOffset-based properties to avoid obsolete APIs
            req.TimeMinDateTimeOffset = start;
            req.TimeMaxDateTimeOffset = end;
            req.ShowDeleted = false;
            req.SingleEvents = true;
            req.MaxResults = 2500;
            var resp = await req.ExecuteAsync();
            foreach (var ev in resp.Items ?? Enumerable.Empty<Event>())
            {
                result.Add(MapFromGoogleEvent(ev));
            }
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "GetEventsAsync failed");
        }
        return result;
    }

    public async Task<EventItem?> GetEventAsync(string eventId)
    {
        if (!await EnsureServiceAsync()) return null;
        try
        {
            var ev = await _service!.Events.Get(_defaultCalendarId, eventId).ExecuteAsync();
            return MapFromGoogleEvent(ev);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "GetEventAsync failed for {EventId}", eventId);
            return null;
        }
    }

    public async Task<bool> CreateEventAsync(EventItem eventItem)
    {
        if (!await EnsureServiceAsync()) return false;
        try
        {
            var ev = MapToGoogleEvent(eventItem);
            var created = await _service!.Events.Insert(ev, _defaultCalendarId).ExecuteAsync();
            eventItem.ExternalId = created.Id;
            eventItem.CalendarId = _defaultCalendarId;
            eventItem.Source = Enums.EventSource.Google;
            return true;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "CreateEventAsync failed for {Title}", eventItem.Title);
            return false;
        }
    }

    public async Task<bool> UpdateEventAsync(EventItem eventItem)
    {
        if (!await EnsureServiceAsync()) return false;
        if (string.IsNullOrWhiteSpace(eventItem.ExternalId)) return false;
        try
        {
            var ev = MapToGoogleEvent(eventItem);
            await _service!.Events.Update(ev, eventItem.CalendarId ?? _defaultCalendarId, eventItem.ExternalId).ExecuteAsync();
            return true;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "UpdateEventAsync failed for {ExternalId}", eventItem.ExternalId);
            return false;
        }
    }

    public async Task<bool> DeleteEventAsync(string eventId)
    {
        if (!await EnsureServiceAsync()) return false;
        try
        {
            await _service!.Events.Delete(_defaultCalendarId, eventId).ExecuteAsync();
            return true;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "DeleteEventAsync failed for {EventId}", eventId);
            return false;
        }
    }

    private static EventItem MapFromGoogleEvent(Event ev)
    {
        var start = ev.Start.DateTimeRaw != null ? DateTimeOffset.Parse(ev.Start.DateTimeRaw) : DateTimeOffset.Parse(ev.Start.Date!);
        var end = ev.End.DateTimeRaw != null ? DateTimeOffset.Parse(ev.End.DateTimeRaw) : DateTimeOffset.Parse(ev.End.Date!);
        var isAllDay = ev.Start.Date != null && ev.End.Date != null && ev.Start.Date.Length == 10;
        return new EventItem
        {
            Title = ev.Summary ?? string.Empty,
            Description = ev.Description,
            Location = ev.Location,
            Start = start,
            End = end,
            IsAllDay = isAllDay,
            ExternalId = ev.Id,
            // CalendarId is not present on Event.Organizer in the Google API.
            // We rely on provider-level default calendar ID; leave this null.
            CalendarId = null,
            Source = Enums.EventSource.Google,
            RecurrenceRule = ev.Recurrence?.FirstOrDefault()
        };
    }

    private static Event MapToGoogleEvent(EventItem item)
    {
        var ev = new Event
        {
            Summary = item.Title,
            Description = item.Description,
            Location = item.Location,
        };
        if (item.IsAllDay)
        {
            ev.Start = new EventDateTime { Date = item.Start.ToString("yyyy-MM-dd") };
            ev.End = new EventDateTime { Date = item.End.ToString("yyyy-MM-dd") };
        }
        else
        {
            // Use new DateTimeDateTimeOffset properties to avoid obsolete warnings.
            ev.Start = new EventDateTime { DateTimeDateTimeOffset = item.Start };
            ev.End = new EventDateTime { DateTimeDateTimeOffset = item.End };
        }
        if (!string.IsNullOrWhiteSpace(item.RecurrenceRule))
        {
            ev.Recurrence = new[] { item.RecurrenceRule };
        }
        return ev;
    }
}