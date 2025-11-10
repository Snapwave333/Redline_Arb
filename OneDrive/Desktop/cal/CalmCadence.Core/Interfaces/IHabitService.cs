using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using CalmCadence.Core.Models;

namespace CalmCadence.Core.Interfaces;

public interface IHabitService
{
    // Habit CRUD operations
    Task<Habit> CreateHabitAsync(Habit habit);
    Task<Habit?> GetHabitAsync(Guid habitId);
    Task<IEnumerable<Habit>> GetAllHabitsAsync(bool includeArchived = false);
    Task<Habit> UpdateHabitAsync(Habit habit);
    Task<bool> DeleteHabitAsync(Guid habitId);
    Task<bool> ArchiveHabitAsync(Guid habitId);

    // Habit logging operations
    Task<HabitLog> LogHabitAsync(Guid habitId, DateOnly date, double? value = null, string? note = null);
    Task<bool> UpdateHabitLogAsync(Guid logId, double? value = null, string? note = null);
    Task<bool> DeleteHabitLogAsync(Guid logId);
    Task<HabitLog?> GetHabitLogAsync(Guid habitId, DateOnly date);
    Task<IEnumerable<HabitLog>> GetHabitLogsAsync(Guid habitId, DateOnly? startDate = null, DateOnly? endDate = null);

    // Status and analytics
    Task<HabitStatusDetail> GetHabitStatusAsync(Guid habitId, DateOnly date);
    Task<IEnumerable<HabitStatusDetail>> GetDailyHabitStatusesAsync(DateOnly date);
    Task<int> GetCurrentStreakAsync(Guid habitId, DateOnly asOfDate);
    Task<HabitAnalytics> GetHabitAnalyticsAsync(Guid habitId, DateOnly startDate, DateOnly endDate);
}

// Status models for UI consumption
public class HabitStatusDetail
{
    public Guid HabitId { get; set; }
    public string HabitName { get; set; } = string.Empty;
    public bool IsCompleted { get; set; }
    public double? Value { get; set; }
    public string? Note { get; set; }
    public DateTimeOffset? CompletedAt { get; set; }
    public int CurrentStreak { get; set; }
}

public class HabitAnalytics
{
    public Guid HabitId { get; set; }
    public int TotalLogs { get; set; }
    public int CompletedCount { get; set; }
    public double CompletionRate { get; set; }
    public int LongestStreak { get; set; }
    public int CurrentStreak { get; set; }
    public DateOnly? LastCompletedDate { get; set; }
    public Dictionary<string, int> LogsByMonth { get; set; } = new();
}
