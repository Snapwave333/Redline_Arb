using System;
using System.Text.RegularExpressions;
using CalmCadence.Core.Enums;
using CalmCadence.Core.Interfaces;
using CalmCadence.Core.Models;

namespace CalmCadence.Core.Services;

public class QuickAddParser : IQuickAddParser
{
    // Patterns: due date keywords (today, tomorrow, yyyy-mm-dd), time (HH:mm or 5pm), priority (!low|!high|!crit), project #tag
    private static readonly Regex DateRegex = new(
        @"\b(?:(today|tomorrow)|(?:(\d{4})-(\d{2})-(\d{2})))\b",
        RegexOptions.IgnoreCase | RegexOptions.Compiled);

    private static readonly Regex TimeRegex = new(
        @"\b(?:(\d{1,2}):(\d{2})|(\d{1,2})\s?(am|pm))\b",
        RegexOptions.IgnoreCase | RegexOptions.Compiled);

    private static readonly Regex PriorityRegex = new(
        @"!(low|normal|high|crit|critical)\b",
        RegexOptions.IgnoreCase | RegexOptions.Compiled);

    public TaskItem ParseTask(string input)
    {
        var task = new TaskItem
        {
            Title = input.Trim(),
        };

        var now = DateTimeOffset.Now;
        var due = ParseDate(input, now);
        if (due is not null)
        {
            var time = ParseTime(input);
            if (time is not null)
            {
                due = new DateTimeOffset(due.Value.Date + time.Value, now.Offset);
            }
            task.DueAt = due;
        }

        var pr = ParsePriority(input);
        if (pr is not null)
        {
            task.Priority = pr.Value;
        }

        task.Status = due.HasValue ? TodoStatus.Scheduled : TodoStatus.Inbox;
        return task;
    }

    private static DateTimeOffset? ParseDate(string input, DateTimeOffset now)
    {
        var m = DateRegex.Match(input);
        if (!m.Success) return null;

        if (m.Groups[1].Success)
        {
            var word = m.Groups[1].Value.ToLowerInvariant();
            if (word == "today") return new DateTimeOffset(now.Date, now.Offset);
            if (word == "tomorrow") return new DateTimeOffset(now.Date.AddDays(1), now.Offset);
        }
        else if (m.Groups[2].Success)
        {
            var y = int.Parse(m.Groups[2].Value);
            var mo = int.Parse(m.Groups[3].Value);
            var d = int.Parse(m.Groups[4].Value);
            return new DateTimeOffset(new DateTime(y, mo, d), now.Offset);
        }
        return null;
    }

    private static TimeSpan? ParseTime(string input)
    {
        var m = TimeRegex.Match(input);
        if (!m.Success) return null;
        if (m.Groups[1].Success && m.Groups[2].Success)
        {
            var h = int.Parse(m.Groups[1].Value);
            var mi = int.Parse(m.Groups[2].Value);
            return new TimeSpan(h, mi, 0);
        }
        if (m.Groups[3].Success && m.Groups[4].Success)
        {
            var h = int.Parse(m.Groups[3].Value);
            var ampm = m.Groups[4].Value.ToLowerInvariant();
            if (ampm == "pm" && h < 12) h += 12;
            if (ampm == "am" && h == 12) h = 0;
            return new TimeSpan(h, 0, 0);
        }
        return null;
    }

    private static TaskPriority? ParsePriority(string input)
    {
        var m = PriorityRegex.Match(input);
        if (!m.Success) return null;
        var val = m.Groups[1].Value.ToLowerInvariant();
        return val switch
        {
            "low" => TaskPriority.Low,
            "high" => TaskPriority.High,
            "crit" => TaskPriority.Critical,
            "critical" => TaskPriority.Critical,
            _ => TaskPriority.Normal,
        };
    }
}
