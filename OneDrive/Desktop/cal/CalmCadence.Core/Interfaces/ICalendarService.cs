using System;
using System.Threading.Tasks;

namespace CalmCadence.Core.Interfaces;

public interface ICalendarService
{
    Task ExportEventsAsync(DateOnly start, DateOnly end, string filePath);
    Task<int> ImportEventsAsync(string filePath);
}
