using Microsoft.UI.Xaml.Navigation;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.EntityFrameworkCore;
using Microsoft.Windows.AppNotifications;
using Microsoft.Windows.AppNotifications.Builder;
using CalmCadence.Data.Context;
using CalmCadence.Core.Interfaces;
using CalmCadence.App.Services;
using System;
using System.IO;
using System.Linq;

namespace CalmCadence.App
{
    /// <summary>
    /// Provides application-specific behavior to supplement the default Application class.
    /// </summary>
    public partial class App : Application
    {
        private Window window = Window.Current;

        public static IHost? AppHost { get; private set; }

        /// <summary>
        /// Initializes the singleton application object.  This is the first line of authored code
        /// executed, and as such is the logical equivalent of main() or WinMain().
        /// </summary>
        public App()
        {
            this.InitializeComponent();

            AppHost = Host.CreateDefaultBuilder()
                .ConfigureServices((context, services) =>
                {
                    var appData = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "CalmCadence");
                    Directory.CreateDirectory(appData);
                    var dbPath = Path.Combine(appData, "calmcadence.db");

                    services.AddDbContext<CalmCadenceDbContext>(options =>
                        options.UseSqlite($"Data Source={dbPath}"));

                    // Domain services
                    services.AddSingleton<CalmCadence.Core.Interfaces.IQuickAddParser, CalmCadence.Core.Services.QuickAddParser>();
                    services.AddSingleton<CalmCadence.Core.Interfaces.INotificationService, CalmCadence.App.Services.NotificationService>();
                    services.AddSingleton<CalmCadence.Core.Interfaces.IAgendaGenerator, CalmCadence.App.Services.AgendaGenerator>();
                    services.AddSingleton<CalmCadence.Core.Interfaces.ICalendarService, CalmCadence.Data.Services.SimpleIcsService>();
                    services.AddSingleton<CalmCadence.Core.Interfaces.IHabitService, CalmCadence.Data.Services.HabitService>();
                    services.AddSingleton<CalmCadence.Core.Interfaces.IRoutineService, CalmCadence.App.Services.RoutineService>();

                    // Daily Studio services
                    services.AddSingleton<CalmCadence.Core.Interfaces.IDailyStudioService, CalmCadence.App.Services.DailyStudioService>();
                    services.AddSingleton<CalmCadence.Core.Interfaces.IGeminiService, CalmCadence.Core.Services.GeminiService>();
                    services.AddSingleton<CalmCadence.Core.Interfaces.IGoogleApiService>(
                        sp => new CalmCadence.Core.Services.GoogleApiService(
                            sp.GetRequiredService<HttpClient>(),
                            sp.GetRequiredService<ILogger<CalmCadence.Core.Services.GoogleApiService>>()));

                    // Google OAuth + Calendar provider (for live sync)
                    services.AddSingleton<CalmCadence.Core.Interfaces.IGoogleOAuthService, CalmCadence.Core.Services.GoogleOAuthService>();
                    services.AddSingleton<CalmCadence.Core.Interfaces.ICalendarProvider, CalmCadence.Core.Services.GoogleCalendarProvider>();
                    services.AddSingleton<CalmCadence.Core.Interfaces.IGoogleCalendarSyncService, CalmCadence.Data.Services.GoogleCalendarSyncService>();

                    // HttpClient for API calls
                    services.AddHttpClient();
                })
                .Build();
        }

        /// <summary>
        /// Invoked when the application is launched normally by the end user.  Other entry points
        /// will be used such as when the application is launched to open a specific file.
        /// </summary>
        /// <param name="e">Details about the launch request and process.</param>
        protected override void OnLaunched(LaunchActivatedEventArgs e)
        {
            AppHost?.Start();

            // Register AppNotifications for packaged identity toasts
            AppNotificationManager.Default.NotificationInvoked += OnNotificationInvoked;
            AppNotificationManager.Default.Register();

            // Command-line activation: headless Daily Studio run
            var args = Environment.GetCommandLineArgs();
            if (args != null && Array.Exists(args, a => string.Equals(a, "--run-daily-studio", StringComparison.OrdinalIgnoreCase)))
            {
                try
                {
                    var scheduler = AppHost?.Services.GetService(typeof(IDailyStudioService)) as IDailyStudioService;
                    var notifier = AppHost?.Services.GetService(typeof(INotificationService)) as INotificationService;
                    var db = AppHost?.Services.GetService(typeof(CalmCadenceDbContext)) as CalmCadenceDbContext;
                    var settings = db?.Settings?.FirstOrDefault();

                    // Execute Daily Studio generation for today
                    scheduler?.GenerateDailyBriefAsync(DateTimeOffset.Now).GetAwaiter().GetResult();

                    // Notify completion if enabled
                    if (settings?.ToastsEnabled == true)
                    {
                        notifier?.ScheduleAsync(DateTimeOffset.Now, "Daily Studio", "Your Daily Brief has been generated.").GetAwaiter().GetResult();
                    }
                }
                catch (Exception ex)
                {
                    System.Diagnostics.Debug.WriteLine($"[App] --run-daily-studio failed: {ex.Message}");
                }

                // Exit without creating a window (headless run)
                Microsoft.UI.Dispatching.DispatcherQueue.GetForCurrentThread()?.TryEnqueue(() =>
                {
                    Application.Current?.Exit();
                });
                return;
            }

            // Command-line activation: headless Google Calendar sync
            if (args != null && Array.Exists(args, a => string.Equals(a, "--run-google-sync", StringComparison.OrdinalIgnoreCase)))
            {
                try
                {
                    var sync = AppHost?.Services.GetService(typeof(IGoogleCalendarSyncService)) as IGoogleCalendarSyncService;
                    // Default sync range: today +/- 7 days
                    var start = DateOnly.FromDateTime(DateTime.Today.AddDays(-7));
                    var end = DateOnly.FromDateTime(DateTime.Today.AddDays(7));
                    var changes = sync?.SyncAsync(start, end).GetAwaiter().GetResult() ?? 0;
                    System.Diagnostics.Debug.WriteLine($"[App] Google sync completed. Changes: {changes}");
                }
                catch (Exception ex)
                {
                    System.Diagnostics.Debug.WriteLine($"[App] --run-google-sync failed: {ex.Message}");
                }

                Microsoft.UI.Dispatching.DispatcherQueue.GetForCurrentThread()?.TryEnqueue(() =>
                {
                    Application.Current?.Exit();
                });
                return;
            }

            // Reconcile background scheduled task with current Settings
            try
            {
                var db = AppHost?.Services.GetService(typeof(CalmCadenceDbContext)) as CalmCadenceDbContext;
                var schedulerService = new BackgroundSchedulerService(db!);
                schedulerService.EnsureScheduledTaskAsync().GetAwaiter().GetResult();
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"[App] Background schedule reconcile failed: {ex.Message}");
            }

            window ??= new Window();

            if (window.Content is not Frame rootFrame)
            {
                rootFrame = new Frame();
                rootFrame.NavigationFailed += OnNavigationFailed;
                window.Content = rootFrame;
            }

            _ = rootFrame.Navigate(typeof(MainPage), e.Arguments);
            window.Activate();
        }

        /// <summary>
        /// Invoked when Navigation to a certain page fails
        /// </summary>
        /// <param name="sender">The Frame which failed navigation</param>
        /// <param name="e">Details about the navigation failure</param>
        void OnNavigationFailed(object sender, NavigationFailedEventArgs e)
        {
            throw new Exception("Failed to load Page " + e.SourcePageType.FullName);
        }

        // Minimal activation handler for toast clicks
        private void OnNotificationInvoked(AppNotificationManager sender, AppNotificationActivatedEventArgs args)
        {
            // Bring window to foreground; extend with payload routing as needed
            window?.Activate();
        }
    }
}
