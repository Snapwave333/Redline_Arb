using System;
using System.Threading.Tasks;
using CalmCadence.Core.Models;

namespace CalmCadence.Core.Interfaces;

public interface IDailyStudioService
{
    Task<DailyMedia?> GenerateDailyBriefAsync(DateTimeOffset date);
    Task<bool> IsBriefAvailableAsync(DateTimeOffset date);
    Task<DailyMedia?> GetDailyMediaAsync(DateTimeOffset date);
    Task CleanupExpiredMediaAsync();
    Task<bool> RegenerateBriefAsync(DateTimeOffset date);

    // Status APIs for UI panels
    Task<DailyBriefStatus> GetStatusAsync(DateOnly date);
    Task<DailyMedia?> GetLatestMediaAsync();
}

// Minimal-churn status model for interface exposure
public class DailyBriefStatus
{
    public bool IsGenerated { get; set; }
    public DateTimeOffset? LastRun { get; set; }
}
