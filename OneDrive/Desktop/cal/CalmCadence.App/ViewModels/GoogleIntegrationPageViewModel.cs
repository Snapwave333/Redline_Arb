using System;
using System.ComponentModel;
using System.Runtime.CompilerServices;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using CalmCadence.Core.Interfaces;
using CalmCadence.Data.Context;
using Microsoft.EntityFrameworkCore;
using CalmCadence.App.Services;

namespace CalmCadence.App.ViewModels;

public class GoogleIntegrationPageViewModel : INotifyPropertyChanged
{
    private readonly IGoogleOAuthService _authService;
    private readonly IGoogleCalendarSyncService _syncService;
    private readonly CalmCadenceDbContext _db;
    private readonly BackgroundSchedulerService _scheduler;

    private bool _googleSyncEnabled;
    private bool _isLoading;
    private string _statusMessage = "Loading...";
    private string _lastSyncText = "Last Sync: Never";

    public GoogleIntegrationPageViewModel()
    {
        _authService = App.AppHost?.Services.GetRequiredService<IGoogleOAuthService>()
            ?? throw new InvalidOperationException("IGoogleOAuthService not available");
        _syncService = App.AppHost?.Services.GetRequiredService<IGoogleCalendarSyncService>()
            ?? throw new InvalidOperationException("IGoogleCalendarSyncService not available");
        _db = App.AppHost?.Services.GetRequiredService<CalmCadenceDbContext>()
            ?? throw new InvalidOperationException("CalmCadenceDbContext not available");
        _scheduler = new BackgroundSchedulerService(_db);
    }

    public bool GoogleSyncEnabled
    {
        get => _googleSyncEnabled;
        set
        {
            if (_googleSyncEnabled != value)
            {
                _googleSyncEnabled = value;
                OnPropertyChanged();
                _ = ToggleGoogleSyncAsync();
            }
        }
    }

    public bool IsLoading
    {
        get => _isLoading;
        set
        {
            _isLoading = value;
            OnPropertyChanged();
        }
    }

    public string StatusMessage
    {
        get => _statusMessage;
        set
        {
            _statusMessage = value;
            OnPropertyChanged();
        }
    }

    public string LastSyncText
    {
        get => _lastSyncText;
        set
        {
            _lastSyncText = value;
            OnPropertyChanged();
        }
    }

    public async Task LoadSettingsAsync()
    {
        IsLoading = true;
        StatusMessage = "Checking credentials...";

        try
        {
            var settings = await _db.Settings.FirstOrDefaultAsync();
            if (settings != null)
            {
                GoogleSyncEnabled = settings.GoogleSyncEnabled;
            }

            await UpdateStatusAsync();
        }
        catch (Exception ex)
        {
            StatusMessage = $"Error loading settings: {ex.Message}";
        }
        finally
        {
            IsLoading = false;
        }
    }

    private async Task UpdateStatusAsync()
    {
        try
        {
            var credential = await _authService.GetCredentialAsync();

            if (credential?.Token?.AccessToken != null)
            {
                var expires = credential.Token.ExpiresInSeconds;
                StatusMessage = expires.HasValue
                    ? $"Signed In. Token valid for ~{expires.Value}s."
                    : "Signed In.";

                var settings = await _db.Settings.FirstOrDefaultAsync();
                var lastSync = settings?.GoogleLastSync;
                LastSyncText = lastSync.HasValue
                    ? $"Last successful sync: {lastSync.Value:g}"
                    : "Last successful sync: Never";
            }
            else
            {
                StatusMessage = "Signed Out. Please sign in to enable live calendar sync.";
                LastSyncText = "Last Sync: N/A";
            }
        }
        catch (Exception ex)
        {
            StatusMessage = $"Error checking status: {ex.Message}";
        }
    }

    public async Task SignInAsync()
    {
        IsLoading = true;
        StatusMessage = "Signing in... Check your browser for the Google authentication page.";

        try
        {
            await _authService.SignInAsync();
            await UpdateStatusAsync();
        }
        catch (Exception ex)
        {
            StatusMessage = $"Sign In Failed: {ex.Message}";
        }
        finally
        {
            IsLoading = false;
        }
    }

    public async Task SignOutAsync()
    {
        IsLoading = true;
        StatusMessage = "Signing out...";

        try
        {
            await _authService.SignOutAsync();
            await UpdateStatusAsync();
        }
        catch (Exception ex)
        {
            StatusMessage = $"Sign Out Failed: {ex.Message}";
        }
        finally
        {
            IsLoading = false;
        }
    }

    public async Task SyncNowAsync()
    {
        IsLoading = true;
        StatusMessage = "Syncing calendar events... This may take a moment.";

        try
        {
            var today = DateOnly.FromDateTime(DateTime.Now);
            int changes = await _syncService.SyncAsync(today.AddDays(-7), today.AddDays(7));

            await UpdateStatusAsync();
            StatusMessage = $"Sync Successful. {changes} changes processed.";
        }
        catch (Exception ex)
        {
            StatusMessage = $"Sync Failed: {ex.Message}";
        }
        finally
        {
            IsLoading = false;
        }
    }

    private async Task ToggleGoogleSyncAsync()
    {
        try
        {
            var settings = await _db.Settings.FirstOrDefaultAsync();
            if (settings != null)
            {
                settings.GoogleSyncEnabled = GoogleSyncEnabled;
                settings.UpdatedAt = DateTimeOffset.UtcNow;
                await _db.SaveChangesAsync();

                // Update scheduled tasks immediately
                await _scheduler.EnsureScheduledTaskAsync();
            }
        }
        catch (Exception ex)
        {
            // Revert the UI change on error
            GoogleSyncEnabled = !GoogleSyncEnabled;
            StatusMessage = $"Failed to update sync setting: {ex.Message}";
        }
    }

    public event PropertyChangedEventHandler? PropertyChanged;

    protected virtual void OnPropertyChanged([CallerMemberName] string? propertyName = null)
    {
        PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
    }
}
