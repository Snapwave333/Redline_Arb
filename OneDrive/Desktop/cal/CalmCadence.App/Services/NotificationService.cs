using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Threading.Tasks;
using CalmCadence.Core.Interfaces;
using CalmCadence.Data.Context;
using Microsoft.EntityFrameworkCore;
using Microsoft.Windows.AppNotifications;
using Microsoft.Windows.AppNotifications.Builder;

namespace CalmCadence.App.Services;

public class NotificationService : INotificationService
{
    private readonly CalmCadenceDbContext _db;

    private readonly List<(DateTimeOffset when, string title, string body)> _scheduled = new();

    public NotificationService(CalmCadenceDbContext db)
    {
        _db = db;
    }

    public async Task ScheduleAsync(DateTimeOffset when, string title, string body)
    {
        // Respect Quiet Hours and runtime flags from Settings
        var settings = await _db.Settings.AsNoTracking().FirstOrDefaultAsync();
        if (settings != null)
        {
            var start = settings.QuietHoursStart;
            var end = settings.QuietHoursEnd;
            var t = when.TimeOfDay;
            var inQuietHours = start <= end ? (t >= start && t <= end) : (t >= start || t <= end);
            if (settings.LowSensoryModeEnabled && inQuietHours)
            {
                // Skip notification in quiet hours when low sensory mode is enabled
                Debug.WriteLine($"[NotificationService] Skipped due to Quiet Hours: {title}");
                return;
            }

            if (!settings.ToastsEnabled)
            {
                Debug.WriteLine($"[NotificationService] Toasts disabled, storing scheduled entry only: {title}");
                _scheduled.Add((when, title, body));
                return;
            }
        }

        // Attempt to show toast immediately; keep scheduled list for future background scheduling
        try
        {
            var builder = new AppNotificationBuilder()
                .AddText(title)
                .AddText(body);

            var notification = builder.BuildNotification();
            AppNotificationManager.Default.Show(notification);

            _scheduled.Add((when, title, body));
            Debug.WriteLine($"[NotificationService] Toast shown & scheduled: {title} at {when}");
        }
        catch (Exception ex)
        {
            // Graceful fallback for non-packaged builds or when AppNotifications are unavailable
            Debug.WriteLine($"[NotificationService] AppNotification unavailable: {ex.Message}. Stored only.");
            _scheduled.Add((when, title, body));
        }
    }

    public Task CancelAllAsync()
    {
        _scheduled.Clear();
        Debug.WriteLine("[NotificationService] Cancelled all notifications");
        return Task.CompletedTask;
    }
}
