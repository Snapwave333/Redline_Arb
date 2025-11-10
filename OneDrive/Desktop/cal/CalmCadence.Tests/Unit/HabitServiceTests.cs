using System;
using System.Linq;
using System.Threading.Tasks;
using CalmCadence.Core.Interfaces;
using CalmCadence.Core.Models;
using CalmCadence.Core.Enums;
using CalmCadence.Data.Services;
using CalmCadence.Data.Context;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;
using Xunit;

namespace CalmCadence.Tests.Unit;

public class HabitServiceTests : IDisposable
{
    private readonly CalmCadenceDbContext _dbContext;
    private readonly IHabitService _habitService;

    public HabitServiceTests()
    {
        var options = new DbContextOptionsBuilder<CalmCadenceDbContext>()
            .UseInMemoryDatabase(databaseName: Guid.NewGuid().ToString())
            .Options;

        _dbContext = new CalmCadenceDbContext(options);

        // Ensure database is created
        _dbContext.Database.EnsureCreated();

        var logger = new Logger<HabitService>(new LoggerFactory());
        _habitService = new HabitService(_dbContext, logger);
    }

    [Fact]
    public async Task CreateHabitAsync_ValidHabit_ReturnsHabit()
    {
        // Arrange
        var habit = new Habit
        {
            Name = "Drink Water",
            Description = "Drink 8 glasses of water daily",
            Type = HabitType.Binary
        };

        // Act
        var result = await _habitService.CreateHabitAsync(habit);

        // Assert
        Assert.NotNull(result);
        Assert.Equal("Drink Water", result.Name);
        Assert.Equal(HabitType.Binary, result.Type);
        Assert.NotEqual(Guid.Empty, result.Id);
        Assert.True(result.CreatedAt > DateTimeOffset.MinValue);
    }

    [Fact]
    public async Task CreateHabitAsync_ScalarHabitWithoutTarget_ThrowsException()
    {
        // Arrange
        var habit = new Habit
        {
            Name = "Run Miles",
            Type = HabitType.Scalar
            // Missing TargetValue
        };

        // Act & Assert
        await Assert.ThrowsAsync<ArgumentException>(() =>
            _habitService.CreateHabitAsync(habit));
    }

    [Fact]
    public async Task LogHabitAsync_BinaryHabit_SetsValueToOne()
    {
        // Arrange
        var habit = new Habit
        {
            Name = "Exercise",
            Type = HabitType.Binary
        };
        var createdHabit = await _habitService.CreateHabitAsync(habit);
        var date = DateOnly.FromDateTime(DateTime.UtcNow);

        // Act
        var log = await _habitService.LogHabitAsync(createdHabit.Id, date);

        // Assert
        Assert.NotNull(log);
        Assert.Equal(1, log.Value);
        Assert.Equal(createdHabit.Id, log.HabitId);
        Assert.Equal(date, log.Date);
    }

    [Fact]
    public async Task LogHabitAsync_ScalarHabit_RequiresValue()
    {
        // Arrange
        var habit = new Habit
        {
            Name = "Read Pages",
            Type = HabitType.Scalar,
            TargetValue = 50
        };
        var createdHabit = await _habitService.CreateHabitAsync(habit);
        var date = DateOnly.FromDateTime(DateTime.UtcNow);

        // Act & Assert
        await Assert.ThrowsAsync<ArgumentException>(() =>
            _habitService.LogHabitAsync(createdHabit.Id, date));
    }

    [Fact]
    public async Task GetHabitStatusAsync_CompletedHabit_ReturnsCorrectStatus()
    {
        // Arrange
        var habit = new Habit
        {
            Name = "Meditate",
            Type = HabitType.Binary
        };
        var createdHabit = await _habitService.CreateHabitAsync(habit);
        var date = DateOnly.FromDateTime(DateTime.UtcNow);

        // Log the habit as completed
        await _habitService.LogHabitAsync(createdHabit.Id, date);

        // Act
        var status = await _habitService.GetHabitStatusAsync(createdHabit.Id, date);

        // Assert
        Assert.NotNull(status);
        Assert.Equal(createdHabit.Id, status.HabitId);
        Assert.Equal("Meditate", status.HabitName);
        Assert.True(status.IsCompleted);
        Assert.Equal(1, status.Value);
    }

    [Fact]
    public async Task GetCurrentStreakAsync_ConsecutiveDays_ReturnsCorrectStreak()
    {
        // Arrange
        var habit = new Habit
        {
            Name = "Write Code",
            Type = HabitType.Binary
        };
        var createdHabit = await _habitService.CreateHabitAsync(habit);
        var today = DateOnly.FromDateTime(DateTime.UtcNow);

        // Log habit for today and yesterday
        await _habitService.LogHabitAsync(createdHabit.Id, today);
        await _habitService.LogHabitAsync(createdHabit.Id, today.AddDays(-1));

        // Act
        var streak = await _habitService.GetCurrentStreakAsync(createdHabit.Id, today);

        // Assert
        Assert.Equal(2, streak);
    }

    [Fact]
    public async Task GetAllHabitsAsync_ExcludesArchived()
    {
        // Arrange
        var habit1 = new Habit { Name = "Active Habit", Type = HabitType.Binary };
        var habit2 = new Habit { Name = "Archived Habit", Type = HabitType.Binary, IsArchived = true };

        await _habitService.CreateHabitAsync(habit1);
        await _habitService.CreateHabitAsync(habit2);

        // Act
        var habits = await _habitService.GetAllHabitsAsync();

        // Assert
        Assert.Single(habits);
        Assert.Equal("Active Habit", habits.First().Name);
    }

    public void Dispose()
    {
        _dbContext.Database.EnsureDeleted();
        _dbContext.Dispose();
    }
}
