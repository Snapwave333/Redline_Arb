using System;
using System.Linq;
using System.Threading.Tasks;
using CalmCadence.Core.Enums;
using CalmCadence.Core.Interfaces;
using CalmCadence.Core.Models;
using CalmCadence.Data.Context;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;

namespace CalmCadence.Data.Services;

public class GoogleCalendarSyncService : IGoogleCalendarSyncService
{
    private readonly CalmCadenceDbContext _db;
    private readonly ICalendarProvider _googleProvider;
    private readonly ILogger<GoogleCalendarSyncService> _logger;

    public GoogleCalendarSyncService(CalmCadenceDbContext db, ICalendarProvider googleProvider, ILogger<GoogleCalendarSyncService> logger)
    {
        _db = db;
        _googleProvider = googleProvider;
        _logger = logger;
    }

    public async Task<int> SyncAsync(DateOnly start, DateOnly end)
    {
        var startDt = start.ToDateTime(TimeOnly.MinValue);
        var endDt = end.ToDateTime(TimeOnly.MaxValue);
        var startOffset = new DateTimeOffset(startDt, TimeZoneInfo.Local.GetUtcOffset(startDt));
        var endOffset = new DateTimeOffset(endDt, TimeZoneInfo.Local.GetUtcOffset(endDt));

        int changes = 0;

        try
        {
            // Preload local Google-sourced events for matching/deletion
            var localGoogleEvents = await _db.Events
                .Where(e => e.Source == EventSource.Google && e.ExternalId != null)
                .ToListAsync();
            var localByExternalId = localGoogleEvents
                .Where(e => e.ExternalId != null)
                .ToDictionary(e => e.ExternalId!);

            // 1) Pull remote events in range and upsert locally with dirty check
            var remote = (await _googleProvider.GetEventsAsync(startOffset, endOffset)).ToList();
            var processedRemoteIds = new System.Collections.Generic.HashSet<string>();
            var toCreate = new System.Collections.Generic.List<EventItem>();
            var toUpdate = new System.Collections.Generic.List<EventItem>();

            foreach (var re in remote)
            {
                if (string.IsNullOrWhiteSpace(re.ExternalId))
                    continue;

                processedRemoteIds.Add(re.ExternalId);

                if (!localByExternalId.TryGetValue(re.ExternalId, out var existing))
                {
                    re.Source = EventSource.Google;
                    re.CreatedAt = DateTimeOffset.UtcNow;
                    re.UpdatedAt = DateTimeOffset.UtcNow;
                    toCreate.Add(re);
                    changes++;
                    continue;
                }

                // Dirty check for core properties
                if (existing.Title != re.Title ||
                    existing.Description != re.Description ||
                    existing.Location != re.Location ||
                    existing.Start != re.Start ||
                    existing.End != re.End ||
                    existing.IsAllDay != re.IsAllDay ||
                    existing.RecurrenceRule != re.RecurrenceRule ||
                    existing.CalendarId != re.CalendarId)
                {
                    existing.Title = re.Title;
                    existing.Description = re.Description;
                    existing.Location = re.Location;
                    existing.Start = re.Start;
                    existing.End = re.End;
                    existing.IsAllDay = re.IsAllDay;
                    existing.RecurrenceRule = re.RecurrenceRule;
                    existing.CalendarId = re.CalendarId;
                    existing.Source = EventSource.Google;
                    existing.UpdatedAt = DateTimeOffset.UtcNow;
                    toUpdate.Add(existing);
                    changes++;
                }
            }

            // 2) DELETE: Remove local Google events missing from remote within the sync window
            var toRemove = localGoogleEvents
                .Where(e => e.ExternalId != null &&
                            e.Start >= startOffset && e.End <= endOffset &&
                            !processedRemoteIds.Contains(e.ExternalId!))
                .ToList();
            if (toRemove.Count > 0)
            {
                _db.Events.RemoveRange(toRemove);
                _logger.LogInformation("GoogleCalendarSyncService: Removing {Count} local events no longer present remotely.", toRemove.Count);
                changes += toRemove.Count;
            }

            if (toCreate.Count > 0)
            {
                await _db.Events.AddRangeAsync(toCreate);
            }
            if (toUpdate.Count > 0)
            {
                _db.Events.UpdateRange(toUpdate);
            }

            await _db.SaveChangesAsync();

            // 3) PUSH: Create/update remote based on local edits
            var localsInRange = await _db.Events
                .Where(e => e.Start >= startOffset && e.End <= endOffset)
                .ToListAsync();

            foreach (var ev in localsInRange)
            {
                if (ev.Source == EventSource.Google)
                {
                    if (!string.IsNullOrWhiteSpace(ev.ExternalId))
                    {
                        var ok = await _googleProvider.UpdateEventAsync(ev);
                        if (ok) changes++;
                    }
                }
                else if (ev.Source == EventSource.Local)
                {
                    if (string.IsNullOrWhiteSpace(ev.ExternalId))
                    {
                        var ok = await _googleProvider.CreateEventAsync(ev);
                        if (ok) changes++;
                    }
                    else
                    {
                        var ok = await _googleProvider.UpdateEventAsync(ev);
                        if (ok) changes++;
                    }
                }
            }

            // 4) Persist last successful sync timestamp
            var settings = await _db.Settings.FirstOrDefaultAsync();
            if (settings != null)
            {
                settings.GoogleLastSync = DateTimeOffset.UtcNow;
                _db.Settings.Update(settings);
                await _db.SaveChangesAsync();
            }

            _logger.LogInformation("GoogleCalendarSyncService: Sync completed. Total local changes: {Changes}", changes);
            return changes;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "GoogleCalendarSyncService.SyncAsync failed");
            return changes;
        }
    }
}