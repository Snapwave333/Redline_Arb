using System;
using System.Threading.Tasks;

namespace CalmCadence.Core.Interfaces;

public interface IGoogleCalendarSyncService
{
    // Performs bi-directional sync for the given date range
    Task<int> SyncAsync(DateOnly start, DateOnly end);
}