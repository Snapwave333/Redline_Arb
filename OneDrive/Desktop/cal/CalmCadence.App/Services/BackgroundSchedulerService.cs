using System;
using System.Diagnostics;
using System.IO;
using System.Threading.Tasks;
using CalmCadence.Data.Context;
using Microsoft.EntityFrameworkCore;
using Microsoft.Windows.AppNotifications;
using Windows.ApplicationModel;

namespace CalmCadence.App.Services
{
    public class BackgroundSchedulerService
    {
        private const string DailyStudioTaskName = "CalmCadence_DailyStudio";
        private const string GoogleSyncTaskName = "CalmCadence_GoogleSync";
        private readonly CalmCadenceDbContext _db;

        public BackgroundSchedulerService(CalmCadenceDbContext db)
        {
            _db = db;
        }

        public async Task EnsureScheduledTaskAsync()
        {
            var settings = await _db.Settings.AsNoTracking().FirstOrDefaultAsync();
            if (settings == null)
            {
                Debug.WriteLine("[Scheduler] No settings found; skipping task scheduling.");
                return;
            }

            // Ensure both tasks are properly configured
            await EnsureDailyStudioTaskAsync(settings);
            await EnsureGoogleSyncTaskAsync(settings);
        }

        private async Task EnsureDailyStudioTaskAsync(CalmCadence.Core.Models.Settings settings)
        {
            if (!settings.DailyStudioEnabled)
            {
                RemoveScheduledTask(DailyStudioTaskName);
                return;
            }

            var time = settings.DailyStudioTime;

            // Determine packaged vs. unpackaged to compose command
            var hasIdentity = SafeHasIdentity();
            string exeCommand;
            if (hasIdentity)
            {
                // AppExecutionAlias: available when packaged
                exeCommand = "\"CalmCadence.exe\" --run-daily-studio";
            }
            else
            {
                // Unpackaged path
                var exePath = Path.Combine(AppContext.BaseDirectory, "CalmCadence.App.exe");
                exeCommand = $"\"{exePath}\" --run-daily-studio";
            }

            var st = $"{time.Hours:D2}:{time.Minutes:D2}";
            var args = $"/Create /TN \"{DailyStudioTaskName}\" /SC DAILY /ST {st} /F /RL LIMITED /TR {exeCommand}";
            RunSchtasks(args);
            Debug.WriteLine($"[Scheduler] Ensured Daily Studio task '{DailyStudioTaskName}' at {st} with command: {exeCommand}");
        }

        private async Task EnsureGoogleSyncTaskAsync(CalmCadence.Core.Models.Settings settings)
        {
            if (!settings.GoogleSyncEnabled)
            {
                RemoveScheduledTask(GoogleSyncTaskName);
                return;
            }

            // Determine packaged vs. unpackaged to compose command
            var hasIdentity = SafeHasIdentity();
            string exeCommand;
            if (hasIdentity)
            {
                // AppExecutionAlias: available when packaged
                exeCommand = "\"CalmCadence.exe\" --run-google-sync";
            }
            else
            {
                // Unpackaged path
                var exePath = Path.Combine(AppContext.BaseDirectory, "CalmCadence.App.exe");
                exeCommand = $"\"{exePath}\" --run-google-sync";
            }

            // Schedule Google sync every 6 hours
            var args = $"/Create /TN \"{GoogleSyncTaskName}\" /SC HOURLY /MO 6 /F /RL LIMITED /TR {exeCommand}";
            RunSchtasks(args);
            Debug.WriteLine($"[Scheduler] Ensured Google Sync task '{GoogleSyncTaskName}' every 6 hours with command: {exeCommand}");
        }

        public Task RemoveScheduledTaskAsync()
        {
            RemoveScheduledTask(DailyStudioTaskName);
            RemoveScheduledTask(GoogleSyncTaskName);
            return Task.CompletedTask;
        }

        private void RemoveScheduledTask(string taskName)
        {
            RunSchtasks($"/Delete /TN \"{taskName}\" /F");
            Debug.WriteLine($"[Scheduler] Removed task '{taskName}'");
        }

        private static void RunSchtasks(string arguments)
        {
            try
            {
                var psi = new ProcessStartInfo("schtasks.exe", arguments)
                {
                    UseShellExecute = false,
                    CreateNoWindow = true,
                };
                using var p = Process.Start(psi);
                p?.WaitForExit(5000);
            }
            catch (Exception ex)
            {
                Debug.WriteLine($"[Scheduler] schtasks failed: {ex.Message}");
            }
        }

        private static bool SafeHasIdentity()
        {
            try
            {
                // If the app is packaged, Package.Current will be accessible.
                var pkg = Package.Current;
                return pkg != null;
            }
            catch
            {
                return false;
            }
        }
    }
}
