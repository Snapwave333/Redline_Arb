using System;
using System.ComponentModel;
using System.Runtime.CompilerServices;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using CalmCadence.Core.Interfaces;

namespace CalmCadence.App.ViewModels;

public class MainPageViewModel : INotifyPropertyChanged
{
    private readonly IDailyStudioService _dailyStudioService;

    private DailyBriefStatus? _dailyBriefStatus;
    private bool _isLoading;
    private string _statusMessage = "Loading status...";

    public MainPageViewModel()
    {
        _dailyStudioService = App.AppHost?.Services.GetRequiredService<IDailyStudioService>()
            ?? throw new InvalidOperationException("IDailyStudioService not available");
    }

    public DailyBriefStatus? DailyBriefStatus
    {
        get => _dailyBriefStatus;
        set
        {
            _dailyBriefStatus = value;
            OnPropertyChanged();
            UpdateStatusMessage();
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

    public async Task LoadStatusAsync()
    {
        IsLoading = true;
        StatusMessage = "Checking Daily Brief status...";

        try
        {
            var today = DateOnly.FromDateTime(DateTime.Today);
            DailyBriefStatus = await _dailyStudioService.GetStatusAsync(today);
        }
        catch (Exception ex)
        {
            StatusMessage = $"Error loading status: {ex.Message}";
            DailyBriefStatus = null;
        }
        finally
        {
            IsLoading = false;
        }
    }

    private void UpdateStatusMessage()
    {
        if (DailyBriefStatus == null)
        {
            StatusMessage = "Unable to load Daily Brief status";
            return;
        }

        if (DailyBriefStatus.IsGenerated)
        {
            var lastRunText = DailyBriefStatus.LastRun.HasValue
                ? $" (last generated: {DailyBriefStatus.LastRun.Value:g})"
                : "";
            StatusMessage = $"Daily Brief: Ready{lastRunText}";
        }
        else
        {
            StatusMessage = "Daily Brief: Not Generated";
        }
    }

    public event PropertyChangedEventHandler? PropertyChanged;

    protected virtual void OnPropertyChanged([CallerMemberName] string? propertyName = null)
    {
        PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
    }
}
