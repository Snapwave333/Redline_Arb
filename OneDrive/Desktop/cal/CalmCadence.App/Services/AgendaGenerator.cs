using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using CalmCadence.Core.Interfaces;
using CalmCadence.Core.Models;
using CalmCadence.Data.Context;
using Microsoft.EntityFrameworkCore;

namespace CalmCadence.App.Services;

public class AgendaGenerator : IAgendaGenerator
{
    private readonly CalmCadenceDbContext _db;

    public AgendaGenerator(CalmCadenceDbContext db)
    {
        _db = db;
    }

    public async Task<IReadOnlyList<AgendaEntry>> GenerateAsync(DateOnly date)
    {
        var start = new DateTime(date.Year, date.Month, date.Day, 0, 0, 0, DateTimeKind.Local);
        var end = start.AddDays(1);

        var entries = new List<AgendaEntry>();

        // Tasks due today
        var tasks = await _db.Tasks.AsNoTracking()
            .Where(t => t.DueAt.HasValue && t.DueAt.Value >= start && t.DueAt.Value < end)
            .OrderBy(t => t.DueAt)
            .ToListAsync();
        entries.AddRange(tasks.Select(t => new AgendaEntry
        {
            Type = AgendaItemType.Task,
            Title = t.Title,
            Start = t.DueAt,
            SourceId = t.Id.ToString(),
            Notes = t.Notes
        }));

        // Events starting today
        var eventsToday = await _db.Events.AsNoTracking()
            .Where(ev => ev.Start >= start && ev.Start < end)
            .OrderBy(ev => ev.Start)
            .ToListAsync();
        entries.AddRange(eventsToday.Select(ev => new AgendaEntry
        {
            Type = AgendaItemType.Event,
            Title = ev.Title,
            Start = ev.Start,
            End = ev.End,
            SourceId = ev.Id.ToString(),
            Notes = ev.Description
        }));

        // Simple routines (Enabled only, scheduling to be refined)
        var routines = await _db.Routines.AsNoTracking()
            .Where(r => r.Enabled)
            .OrderBy(r => r.Name)
            .ToListAsync();
        entries.AddRange(routines.Select(r => new AgendaEntry
        {
            Type = AgendaItemType.Routine,
            Title = r.Name,
            SourceId = r.Id.ToString(),
            Notes = r.Description
        }));

        // Habits: show active (not archived)
        var habits = await _db.Habits.AsNoTracking()
            .Where(h => !h.IsArchived)
            .OrderBy(h => h.Name)
            .ToListAsync();
        entries.AddRange(habits.Select(h => new AgendaEntry
        {
            Type = AgendaItemType.Habit,
            Title = h.Name,
            SourceId = h.Id.ToString(),
            Notes = h.Description
        }));

        return entries
            .OrderBy(e => e.Start ?? DateTimeOffset.MaxValue)
            .ThenBy(e => e.Type)
            .ToList();
    }
}
