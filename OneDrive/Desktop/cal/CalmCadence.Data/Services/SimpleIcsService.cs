using System;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using CalmCadence.Core.Interfaces;
using CalmCadence.Data.Context;
using Microsoft.EntityFrameworkCore;

namespace CalmCadence.Data.Services;

public class SimpleIcsService : ICalendarService
{
    private readonly CalmCadenceDbContext _db;

    public SimpleIcsService(CalmCadenceDbContext db)
    {
        _db = db;
    }

    public async Task ExportEventsAsync(DateOnly start, DateOnly end, string filePath)
    {
        var from = new DateTimeOffset(new DateTime(start.Year, start.Month, start.Day, 0, 0, 0, DateTimeKind.Utc));
        var to = new DateTimeOffset(new DateTime(end.Year, end.Month, end.Day, 0, 0, 0, DateTimeKind.Utc));

        var events = await _db.Events.AsNoTracking()
            .Where(e => e.Start >= from && e.Start < to)
            .OrderBy(e => e.Start)
            .ToListAsync();

        var sb = new StringBuilder();
        sb.AppendLine("BEGIN:VCALENDAR");
        sb.AppendLine("VERSION:2.0");
        sb.AppendLine("PRODID:-//CalmCadence//EN");

        foreach (var ev in events)
        {
            sb.AppendLine("BEGIN:VEVENT");
            sb.AppendLine($"UID:{ev.Id}@calmcadence");
            sb.AppendLine($"DTSTAMP:{DateTime.UtcNow.ToString("yyyyMMdd'T'HHmmss'Z'", CultureInfo.InvariantCulture)}");
            sb.AppendLine($"DTSTART:{ev.Start.ToUniversalTime().ToString("yyyyMMdd'T'HHmmss'Z'", CultureInfo.InvariantCulture)}");
            sb.AppendLine($"DTEND:{ev.End.ToUniversalTime().ToString("yyyyMMdd'T'HHmmss'Z'", CultureInfo.InvariantCulture)}");
            sb.AppendLine($"SUMMARY:{EscapeText(ev.Title)}");
            if (!string.IsNullOrWhiteSpace(ev.Description))
            {
                sb.AppendLine($"DESCRIPTION:{EscapeText(ev.Description)}");
            }
            if (!string.IsNullOrWhiteSpace(ev.Location))
            {
                sb.AppendLine($"LOCATION:{EscapeText(ev.Location)}");
            }
            sb.AppendLine("END:VEVENT");
        }

        sb.AppendLine("END:VCALENDAR");

        File.WriteAllText(filePath, sb.ToString());
    }

    public async Task<int> ImportEventsAsync(string filePath)
    {
        // Very simple importer: reads SUMMARY, DTSTART, DTEND, DESCRIPTION, LOCATION per VEVENT
        var content = await File.ReadAllLinesAsync(filePath);
        int imported = 0;
        int i = 0;
        while (i < content.Length)
        {
            if (content[i].StartsWith("BEGIN:VEVENT", StringComparison.OrdinalIgnoreCase))
            {
                string? summary = null;
                string? description = null;
                string? location = null;
                DateTime? dtstart = null;
                DateTime? dtend = null;

                i++;
                while (i < content.Length && !content[i].StartsWith("END:VEVENT", StringComparison.OrdinalIgnoreCase))
                {
                    var line = content[i];
                    if (line.StartsWith("SUMMARY:", StringComparison.OrdinalIgnoreCase))
                        summary = UnescapeText(line.Substring(8));
                    else if (line.StartsWith("DESCRIPTION:", StringComparison.OrdinalIgnoreCase))
                        description = UnescapeText(line.Substring(12));
                    else if (line.StartsWith("LOCATION:", StringComparison.OrdinalIgnoreCase))
                        location = UnescapeText(line.Substring(9));
                    else if (line.StartsWith("DTSTART:", StringComparison.OrdinalIgnoreCase))
                        dtstart = ParseIcsDate(line.Substring(8));
                    else if (line.StartsWith("DTEND:", StringComparison.OrdinalIgnoreCase))
                        dtend = ParseIcsDate(line.Substring(6));
                    i++;
                }

                if (!string.IsNullOrWhiteSpace(summary) && dtstart.HasValue)
                {
                    var startOffset = new DateTimeOffset(dtstart!.Value, TimeSpan.Zero);
                    var endOffset = dtend.HasValue ? new DateTimeOffset(dtend!.Value, TimeSpan.Zero) : startOffset;

                    _db.Events.Add(new global::CalmCadence.Core.Models.EventItem
                    {
                        Title = summary!,
                        Description = description,
                        Location = location,
                        Start = startOffset,
                        End = endOffset,
                        Source = global::CalmCadence.Core.Enums.EventSource.Ics,
                        CreatedAt = DateTimeOffset.UtcNow,
                        UpdatedAt = DateTimeOffset.UtcNow
                    });
                    imported++;
                }
            }
            i++;
        }

        await _db.SaveChangesAsync();
        return imported;
    }

    private static string EscapeText(string text)
    {
        return text.Replace("\\", "\\\\").Replace(";", "\\;").Replace(",", "\\,").Replace("\n", "\\n");
    }

    private static string UnescapeText(string text)
    {
        return text.Replace("\\n", "\n").Replace("\\,", ",").Replace("\\;", ";").Replace("\\\\", "\\");
    }

    private static DateTime? ParseIcsDate(string ics)
    {
        // Supports Zulu UTC format yyyyMMdd'T'HHmmss'Z'
        if (DateTime.TryParseExact(ics, "yyyyMMdd'T'HHmmss'Z'", CultureInfo.InvariantCulture, DateTimeStyles.AssumeUniversal, out var dt))
        {
            return dt.ToUniversalTime();
        }
        return null;
    }
}
