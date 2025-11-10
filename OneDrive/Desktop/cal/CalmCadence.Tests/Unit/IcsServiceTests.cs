using System;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using CalmCadence.Data.Services;
using CalmCadence.Core.Models;
using CalmCadence.Data.Context;
using Microsoft.EntityFrameworkCore;
using Xunit;

namespace CalmCadence.Tests.Unit;

public class IcsServiceTests
{
    private CalmCadenceDbContext CreateInMemoryContext()
    {
        var options = new DbContextOptionsBuilder<CalmCadenceDbContext>()
            .UseInMemoryDatabase(Guid.NewGuid().ToString())
            .Options;
        return new CalmCadenceDbContext(options);
    }

    [Fact]
    public async Task ExportThenImport_RoundTripsBasicEvent()
    {
        using var ctx = CreateInMemoryContext();

        var ev = new EventItem
        {
            Title = "Test Event",
            Description = "Desc",
            Location = "Home",
            Start = new DateTimeOffset(new DateTime(2025, 10, 31, 14, 0, 0, DateTimeKind.Utc)),
            End = new DateTimeOffset(new DateTime(2025, 10, 31, 15, 0, 0, DateTimeKind.Utc)),
            Source = CalmCadence.Core.Enums.EventSource.Local,
            CreatedAt = DateTimeOffset.UtcNow,
            UpdatedAt = DateTimeOffset.UtcNow,
        };
        ctx.Events.Add(ev);
        await ctx.SaveChangesAsync();

        var svc = new SimpleIcsService(ctx);
        var tmp = Path.GetTempFileName();
        try
        {
            var start = new DateOnly(2025, 10, 31);
            var end = new DateOnly(2025, 11, 1);
            await svc.ExportEventsAsync(start, end, tmp);

            // Clear events then import
            ctx.Events.RemoveRange(ctx.Events);
            await ctx.SaveChangesAsync();

            var importedCount = await svc.ImportEventsAsync(tmp);
            Assert.True(importedCount >= 1);

            var imported = ctx.Events.FirstOrDefault();
            Assert.NotNull(imported);
            Assert.Equal("Test Event", imported!.Title);
            Assert.Equal("Desc", imported.Description);
            Assert.Equal("Home", imported.Location);
            Assert.Equal(new DateTimeOffset(new DateTime(2025, 10, 31, 14, 0, 0, DateTimeKind.Utc)), imported.Start);
            Assert.Equal(new DateTimeOffset(new DateTime(2025, 10, 31, 15, 0, 0, DateTimeKind.Utc)), imported.End);
        }
        finally
        {
            try { File.Delete(tmp); } catch { }
        }
    }
}
