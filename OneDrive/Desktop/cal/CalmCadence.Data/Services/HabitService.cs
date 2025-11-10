using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using CalmCadence.Core.Interfaces;
using CalmCadence.Core.Models;
using CalmCadence.Core.Enums;
using CalmCadence.Data.Context;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;

namespace CalmCadence.Data.Services;

public class HabitService : IHabitService
{
    private readonly CalmCadenceDbContext _dbContext;
    private readonly ILogger<HabitService> _logger;

    public HabitService(
        CalmCadenceDbContext dbContext,
        ILogger<HabitService> logger)
    {
        _dbContext = dbContext;
        _logger = logger;
    }

    #region Habit CRUD Operations

    public async Task<Habit> CreateHabitAsync(Habit habit)
    {
        try
        {
            // Validate habit
            if (string.IsNullOrWhiteSpace(habit.Name))
                throw new ArgumentException("Habit name is required");

            if (habit.Type == HabitType.Binary && habit.TargetValue.HasValue)
                throw new ArgumentException("Binary habits cannot have target values");

            if (habit.Type == HabitType.Scalar && !habit.TargetValue.HasValue)
                throw new ArgumentException("Scalar habits must have a target value");

            habit.CreatedAt = DateTimeOffset.UtcNow;
            _dbContext.Habits.Add(habit);
            await _dbContext.SaveChangesAsync();

            _logger.LogInformation("Created habit {HabitId}: {HabitName}", habit.Id, habit.Name);
            return habit;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to create habit {HabitName}", habit.Name);
            throw;
        }
    }

    public async Task<Habit?> GetHabitAsync(Guid habitId)
    {
        return await _dbContext.Habits
            .Include(h => h.Logs.OrderByDescending(l => l.Date))
            .FirstOrDefaultAsync(h => h.Id == habitId);
    }

    public async Task<IEnumerable<Habit>> GetAllHabitsAsync(bool includeArchived = false)
    {
        var query = _dbContext.Habits.AsQueryable();

        if (!includeArchived)
            query = query.Where(h => !h.IsArchived);

        return await query
            .OrderBy(h => h.Name)
            .ToListAsync();
    }

    public async Task<Habit> UpdateHabitAsync(Habit habit)
    {
        try
        {
            var existingHabit = await _dbContext.Habits.FindAsync(habit.Id);
            if (existingHabit == null)
                throw new KeyNotFoundException($"Habit {habit.Id} not found");

            // Validate updates
            if (string.IsNullOrWhiteSpace(habit.Name))
                throw new ArgumentException("Habit name is required");

            if (habit.Type == HabitType.Binary && habit.TargetValue.HasValue)
                throw new ArgumentException("Binary habits cannot have target values");

            if (habit.Type == HabitType.Scalar && !habit.TargetValue.HasValue)
                throw new ArgumentException("Scalar habits must have a target value");

            // Update properties
            existingHabit.Name = habit.Name;
            existingHabit.Description = habit.Description;
            existingHabit.Type = habit.Type;
            existingHabit.TargetValue = habit.TargetValue;
            existingHabit.Unit = habit.Unit;
            existingHabit.ScheduleJson = habit.ScheduleJson;
            existingHabit.ColorHex = habit.ColorHex;

            await _dbContext.SaveChangesAsync();

            _logger.LogInformation("Updated habit {HabitId}: {HabitName}", habit.Id, habit.Name);
            return existingHabit;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to update habit {HabitId}", habit.Id);
            throw;
        }
    }

    public async Task<bool> DeleteHabitAsync(Guid habitId)
    {
        try
        {
            var habit = await _dbContext.Habits.FindAsync(habitId);
            if (habit == null)
                return false;

            _dbContext.Habits.Remove(habit);
            await _dbContext.SaveChangesAsync();

            _logger.LogInformation("Deleted habit {HabitId}: {HabitName}", habitId, habit.Name);
            return true;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to delete habit {HabitId}", habitId);
            throw;
        }
    }

    public async Task<bool> ArchiveHabitAsync(Guid habitId)
    {
        try
        {
            var habit = await _dbContext.Habits.FindAsync(habitId);
            if (habit == null)
                return false;

            habit.IsArchived = true;
            await _dbContext.SaveChangesAsync();

            _logger.LogInformation("Archived habit {HabitId}: {HabitName}", habitId, habit.Name);
            return true;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to archive habit {HabitId}", habitId);
            throw;
        }
    }

    #endregion

    #region Habit Logging Operations

    public async Task<HabitLog> LogHabitAsync(Guid habitId, DateOnly date, double? value = null, string? note = null)
    {
        try
        {
            var habit = await _dbContext.Habits.FindAsync(habitId);
            if (habit == null)
                throw new KeyNotFoundException($"Habit {habitId} not found");

            // Validate value based on habit type
            if (habit.Type == HabitType.Binary)
            {
                if (value.HasValue && value != 1)
                    throw new ArgumentException("Binary habits can only be logged as complete (value=1) or incomplete (value=null)");
                value = 1; // Binary habits are always 1 when logged
            }
            else if (habit.Type == HabitType.Scalar)
            {
                if (!value.HasValue)
                    throw new ArgumentException("Scalar habits must have a value");
                if (value < 0)
                    throw new ArgumentException("Scalar habit values cannot be negative");
            }

            // Check if log already exists for this date
            var existingLog = await _dbContext.HabitLogs
                .FirstOrDefaultAsync(l => l.HabitId == habitId && l.Date == date);

            if (existingLog != null)
            {
                // Update existing log
                existingLog.Value = value;
                existingLog.Note = note;
                existingLog.CreatedAt = DateTimeOffset.UtcNow;
                await _dbContext.SaveChangesAsync();
                return existingLog;
            }
            else
            {
                // Create new log
                var log = new HabitLog
                {
                    HabitId = habitId,
                    Date = date,
                    Value = value,
                    Note = note,
                    CreatedAt = DateTimeOffset.UtcNow
                };

                _dbContext.HabitLogs.Add(log);
                await _dbContext.SaveChangesAsync();

                _logger.LogInformation("Logged habit {HabitId} for date {Date}", habitId, date);
                return log;
            }
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to log habit {HabitId} for date {Date}", habitId, date);
            throw;
        }
    }

    public async Task<bool> UpdateHabitLogAsync(Guid logId, double? value = null, string? note = null)
    {
        try
        {
            var log = await _dbContext.HabitLogs.FindAsync(logId);
            if (log == null)
                return false;

            // Get habit to validate
            var habit = await _dbContext.Habits.FindAsync(log.HabitId);
            if (habit == null)
                throw new InvalidOperationException("Associated habit not found");

            // Validate value based on habit type
            if (habit.Type == HabitType.Binary && value.HasValue && value != 1)
                throw new ArgumentException("Binary habits can only be logged as complete (value=1) or incomplete (value=null)");

            if (habit.Type == HabitType.Scalar && value.HasValue && value < 0)
                throw new ArgumentException("Scalar habit values cannot be negative");

            log.Value = value;
            log.Note = note;
            log.CreatedAt = DateTimeOffset.UtcNow;

            await _dbContext.SaveChangesAsync();

            _logger.LogInformation("Updated habit log {LogId}", logId);
            return true;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to update habit log {LogId}", logId);
            throw;
        }
    }

    public async Task<bool> DeleteHabitLogAsync(Guid logId)
    {
        try
        {
            var log = await _dbContext.HabitLogs.FindAsync(logId);
            if (log == null)
                return false;

            _dbContext.HabitLogs.Remove(log);
            await _dbContext.SaveChangesAsync();

            _logger.LogInformation("Deleted habit log {LogId}", logId);
            return true;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to delete habit log {LogId}", logId);
            throw;
        }
    }

    public async Task<HabitLog?> GetHabitLogAsync(Guid habitId, DateOnly date)
    {
        return await _dbContext.HabitLogs
            .FirstOrDefaultAsync(l => l.HabitId == habitId && l.Date == date);
    }

    public async Task<IEnumerable<HabitLog>> GetHabitLogsAsync(Guid habitId, DateOnly? startDate = null, DateOnly? endDate = null)
    {
        var query = _dbContext.HabitLogs
            .Where(l => l.HabitId == habitId);

        if (startDate.HasValue)
            query = query.Where(l => l.Date >= startDate.Value);

        if (endDate.HasValue)
            query = query.Where(l => l.Date <= endDate.Value);

        return await query
            .OrderByDescending(l => l.Date)
            .ToListAsync();
    }

    #endregion

    #region Status and Analytics

    public async Task<HabitStatusDetail> GetHabitStatusAsync(Guid habitId, DateOnly date)
    {
        var habit = await _dbContext.Habits.FindAsync(habitId);
        if (habit == null)
            throw new KeyNotFoundException($"Habit {habitId} not found");

        var log = await GetHabitLogAsync(habitId, date);
        var currentStreak = await GetCurrentStreakAsync(habitId, date);

        return new HabitStatusDetail
        {
            HabitId = habitId,
            HabitName = habit.Name,
            IsCompleted = log?.Value.HasValue == true,
            Value = log?.Value,
            Note = log?.Note,
            CompletedAt = log?.CreatedAt,
            CurrentStreak = currentStreak
        };
    }

    public async Task<IEnumerable<HabitStatusDetail>> GetDailyHabitStatusesAsync(DateOnly date)
    {
        var habits = await GetAllHabitsAsync(includeArchived: false);
        var statuses = new List<HabitStatusDetail>();

        foreach (var habit in habits)
        {
            var status = await GetHabitStatusAsync(habit.Id, date);
            statuses.Add(status);
        }

        return statuses;
    }

    public async Task<int> GetCurrentStreakAsync(Guid habitId, DateOnly asOfDate)
    {
        var habit = await _dbContext.Habits.FindAsync(habitId);
        if (habit == null)
            return 0;

        // Get logs for the last 100 days to calculate streak
        var startDate = asOfDate.AddDays(-100);
        var logs = await GetHabitLogsAsync(habitId, startDate, asOfDate);

        var logDates = logs
            .Where(l => l.Value.HasValue)
            .Select(l => l.Date)
            .OrderByDescending(d => d)
            .ToList();

        if (!logDates.Any())
            return 0;

        // Check if today/yesterday is completed
        var streak = 0;
        var currentDate = asOfDate;

        while (logDates.Contains(currentDate))
        {
            streak++;
            currentDate = currentDate.AddDays(-1);
        }

        return streak;
    }

    public async Task<HabitAnalytics> GetHabitAnalyticsAsync(Guid habitId, DateOnly startDate, DateOnly endDate)
    {
        var habit = await _dbContext.Habits.FindAsync(habitId);
        if (habit == null)
            throw new KeyNotFoundException($"Habit {habitId} not found");

        var logs = await GetHabitLogsAsync(habitId, startDate, endDate);
        var logsList = logs.ToList();

        var totalLogs = logsList.Count;
        var completedLogs = logsList.Count(l => l.Value.HasValue);
        var completionRate = totalLogs > 0 ? (double)completedLogs / totalLogs : 0;

        var currentStreak = await GetCurrentStreakAsync(habitId, endDate);

        // Calculate longest streak
        var longestStreak = 0;
        var currentStreakCount = 0;
        var previousDate = startDate.AddDays(-1);

        foreach (var log in logsList.Where(l => l.Value.HasValue).OrderBy(l => l.Date))
        {
            if (log.Date == previousDate.AddDays(1))
            {
                currentStreakCount++;
            }
            else
            {
                longestStreak = Math.Max(longestStreak, currentStreakCount);
                currentStreakCount = 1;
            }
            previousDate = log.Date;
        }
        longestStreak = Math.Max(longestStreak, currentStreakCount);

        // Group by month
        var logsByMonth = logsList
            .GroupBy(l => $"{l.Date.Year}-{l.Date.Month:00}")
            .ToDictionary(g => g.Key, g => g.Count());

        var lastCompletedDate = logsList
            .Where(l => l.Value.HasValue)
            .OrderByDescending(l => l.Date)
            .Select(l => (DateOnly?)l.Date)
            .FirstOrDefault();

        return new HabitAnalytics
        {
            HabitId = habitId,
            TotalLogs = totalLogs,
            CompletedCount = completedLogs,
            CompletionRate = completionRate,
            LongestStreak = longestStreak,
            CurrentStreak = currentStreak,
            LastCompletedDate = lastCompletedDate,
            LogsByMonth = logsByMonth
        };
    }

    #endregion
}
