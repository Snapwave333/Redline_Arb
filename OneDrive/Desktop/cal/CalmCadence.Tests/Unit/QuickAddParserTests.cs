using System;
using CalmCadence.Core.Enums;
using CalmCadence.Core.Services;
using Xunit;

namespace CalmCadence.Tests.Unit;

public class QuickAddParserTests
{
    [Fact]
    public void ParsesBasicTitle()
    {
        var parser = new QuickAddParser();
        var task = parser.ParseTask("Buy milk");
        Assert.Equal("Buy milk", task.Title);
        Assert.Equal(TodoStatus.Inbox, task.Status);
    }

    [Fact]
    public void ParsesDateAndTimeAndPriority()
    {
        var parser = new QuickAddParser();
        var task = parser.ParseTask("Pay bills tomorrow 6pm !high");
        Assert.Equal(TodoStatus.Scheduled, task.Status);
        Assert.Equal(TaskPriority.High, task.Priority);
        Assert.True(task.DueAt.HasValue);
        // Due should be tomorrow local date at 18:00
        var now = DateTimeOffset.Now;
        var expectedDate = now.Date.AddDays(1).AddHours(18);
        Assert.Equal(expectedDate, task.DueAt!.Value.DateTime);
    }
}
