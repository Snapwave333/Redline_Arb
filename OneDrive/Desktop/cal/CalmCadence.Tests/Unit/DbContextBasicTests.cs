using System;
using CalmCadence.Core.Models;
using CalmCadence.Core.Enums;
using CalmCadence.Data.Context;
using Microsoft.EntityFrameworkCore;
using Xunit;

namespace CalmCadence.Tests.Unit;

public class DbContextBasicTests
{
    private CalmCadenceDbContext CreateInMemoryContext()
    {
        var options = new DbContextOptionsBuilder<CalmCadenceDbContext>()
            .UseInMemoryDatabase(Guid.NewGuid().ToString())
            .Options;
        return new CalmCadenceDbContext(options);
    }

    [Fact]
    public void CanCreateAndRetrieveTask()
    {
        using var ctx = CreateInMemoryContext();
        var task = new TaskItem
        {
            Title = "Test Task",
            Priority = TaskPriority.High,
            Status = TodoStatus.Next,
        };

        ctx.Tasks.Add(task);
        ctx.SaveChanges();

        var loaded = ctx.Tasks.Find(task.Id);
        Assert.NotNull(loaded);
        Assert.Equal("Test Task", loaded!.Title);
        Assert.Equal(TaskPriority.High, loaded.Priority);
        Assert.Equal(TodoStatus.Next, loaded.Status);
    }
}
