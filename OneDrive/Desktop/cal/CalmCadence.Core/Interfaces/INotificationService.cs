using System;
using System.Threading.Tasks;

namespace CalmCadence.Core.Interfaces;

public interface INotificationService
{
    Task ScheduleAsync(DateTimeOffset when, string title, string body);
    Task CancelAllAsync();
}
