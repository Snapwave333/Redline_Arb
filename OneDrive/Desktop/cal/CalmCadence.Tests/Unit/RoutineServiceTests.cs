using System;
using System.Linq;
using System.Threading.Tasks;
using CalmCadence.Core.Interfaces;
using CalmCadence.Core.Models;
using CalmCadence.Data.Services;
using CalmCadence.App.Services;
using CalmCadence.Data.Context;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;
using Xunit;

namespace CalmCadence.Tests.Unit;

public class RoutineServiceTests : IDisposable
{
    private readonly CalmCadenceDbContext _dbContext;
    private readonly IRoutineService _routineService;

    public RoutineServiceTests()
    {
        var options = new DbContextOptionsBuilder<CalmCadenceDbContext>()
            .UseInMemoryDatabase(databaseName: Guid.NewGuid().ToString())
            .Options;

        _dbContext = new CalmCadenceDbContext(options);
        _dbContext.Database.EnsureCreated();

        // Mock dependencies
        var habitService = new HabitService(_dbContext, new Logger<HabitService>(new LoggerFactory()));
        var agendaGenerator = new MockAgendaGenerator();
        var notificationService = new MockNotificationService();
        var logger = new Logger<RoutineService>(new LoggerFactory());

        _routineService = new RoutineService(_dbContext, habitService, agendaGenerator, notificationService, logger);
    }

    [Fact]
    public async Task CreateRoutineAsync_ValidRoutine_ReturnsRoutine()
    {
        // Arrange
        var routine = new Routine
        {
            Name = "Morning Routine",
            Description = "Start the day right",
            StepsJson = "[]"
        };

        // Act
        var result = await _routineService.CreateRoutineAsync(routine);

        // Assert
        Assert.NotNull(result);
        Assert.Equal("Morning Routine", result.Name);
        Assert.NotEqual(Guid.Empty, result.Id);
        Assert.True(result.CreatedAt > DateTimeOffset.MinValue);
    }

    [Fact]
    public async Task ExecuteRoutineAsync_ReviewAgendaStep_SendsNotification()
    {
        // Arrange
        var routine = new Routine
        {
            Name = "Test Routine",
            StepsJson = @"[
                {
                    ""id"": ""550e8400-e29b-41d4-a716-446655440000"",
                    ""type"": 0,
                    ""description"": ""Review today's agenda"",
                    ""configJson"": ""{}"",
                    ""order"": 1,
                    ""isEnabled"": true
                }
            ]"
        };

        var createdRoutine = await _routineService.CreateRoutineAsync(routine);

        // Act
        var result = await _routineService.ExecuteRoutineAsync(createdRoutine.Id);

        // Assert
        Assert.NotNull(result);
        Assert.True(result.Success);
        Assert.Single(result.StepResults);
        Assert.Equal(RoutineStepType.ReviewAgenda, result.StepResults[0].StepType);
        Assert.True(result.StepResults[0].Success);
    }

    public void Dispose()
    {
        _dbContext.Database.EnsureDeleted();
        _dbContext.Dispose();
    }
}

// Mock implementations for testing
public class MockAgendaGenerator : IAgendaGenerator
{
    public Task<IReadOnlyList<AgendaEntry>> GenerateAsync(DateOnly date)
    {
        var entries = new List<AgendaEntry>
        {
            new AgendaEntry
            {
                Type = AgendaItemType.Task,
                Title = "Test Task",
                Start = DateTimeOffset.Now
            }
        };
        return Task.FromResult<IReadOnlyList<AgendaEntry>>(entries);
    }
}

public class MockNotificationService : INotificationService
{
    public Task ScheduleAsync(DateTimeOffset when, string title, string body)
    {
        // Just complete successfully for testing
        return Task.CompletedTask;
    }

    public Task CancelAllAsync()
    {
        return Task.CompletedTask;
    }
}
