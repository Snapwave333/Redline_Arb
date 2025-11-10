using System;
using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading.Tasks;
using CalmCadence.Core.Interfaces;
using CalmCadence.Core.Models;
using Microsoft.Extensions.DependencyInjection;

namespace CalmCadence.App.ViewModels;

public class RoutineListViewModel : INotifyPropertyChanged
{
    private readonly IRoutineService _routineService;
    private readonly INotificationService _notificationService;

    private ObservableCollection<RoutineListItemViewModel> _routines = new();
    private bool _isLoading;
    private string _errorMessage = string.Empty;

    public RoutineListViewModel()
    {
        _routineService = App.AppHost?.Services.GetRequiredService<IRoutineService>()
            ?? throw new InvalidOperationException("IRoutineService not available");
        _notificationService = App.AppHost?.Services.GetRequiredService<INotificationService>()
            ?? throw new InvalidOperationException("INotificationService not available");
    }

    public ObservableCollection<RoutineListItemViewModel> Routines
    {
        get => _routines;
        set
        {
            _routines = value;
            OnPropertyChanged();
            OnPropertyChanged(nameof(HasRoutines));
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

    public string ErrorMessage
    {
        get => _errorMessage;
        set
        {
            _errorMessage = value;
            OnPropertyChanged();
        }
    }

    public bool HasRoutines => Routines.Any();

    public async Task LoadRoutinesAsync()
    {
        IsLoading = true;
        ErrorMessage = string.Empty;

        try
        {
            var routines = await _routineService.GetAllRoutinesAsync();
            var routineItems = routines.Select(r => new RoutineListItemViewModel(r)).ToList();
            Routines = new ObservableCollection<RoutineListItemViewModel>(routineItems);
        }
        catch (Exception ex)
        {
            ErrorMessage = $"Failed to load routines: {ex.Message}";
            await _notificationService.ScheduleAsync(DateTimeOffset.Now, "Error", ErrorMessage);
        }
        finally
        {
            IsLoading = false;
        }
    }

    public async Task RunRoutineAsync(Guid routineId)
    {
        try
        {
            var result = await _routineService.ExecuteRoutineAsync(routineId);

            if (result.Success)
            {
                var message = $"✅ Routine '{result.RoutineName}' completed successfully in {result.TotalDuration.TotalSeconds:F1}s";
                await _notificationService.ScheduleAsync(DateTimeOffset.Now, "Routine Completed", message);
            }
            else
            {
                var message = $"❌ Routine '{result.RoutineName}' failed: {result.ErrorMessage}";
                await _notificationService.ScheduleAsync(DateTimeOffset.Now, "Routine Failed", message);
            }
        }
        catch (Exception ex)
        {
            var message = $"❌ Failed to run routine: {ex.Message}";
            await _notificationService.ScheduleAsync(DateTimeOffset.Now, "Error", message);
        }
    }

    public async Task DuplicateRoutineAsync(Guid routineId)
    {
        try
        {
            var originalRoutine = await _routineService.GetRoutineAsync(routineId);
            if (originalRoutine == null) return;

            var duplicatedRoutine = new Routine
            {
                Name = $"{originalRoutine.Name} (Copy)",
                Description = originalRoutine.Description,
                StepsJson = originalRoutine.StepsJson,
                Enabled = false, // Start disabled
                ColorHex = originalRoutine.ColorHex,
                SortOrder = originalRoutine.SortOrder
            };

            await _routineService.CreateRoutineAsync(duplicatedRoutine);
            await LoadRoutinesAsync(); // Refresh the list

            await _notificationService.ScheduleAsync(DateTimeOffset.Now, "Success", "Routine duplicated successfully");
        }
        catch (Exception ex)
        {
            var message = $"Failed to duplicate routine: {ex.Message}";
            ErrorMessage = message;
            await _notificationService.ScheduleAsync(DateTimeOffset.Now, "Error", message);
        }
    }

    public async Task DeleteRoutineAsync(Guid routineId)
    {
        try
        {
            var success = await _routineService.DeleteRoutineAsync(routineId);
            if (success)
            {
                await LoadRoutinesAsync(); // Refresh the list
                await _notificationService.ScheduleAsync(DateTimeOffset.Now, "Success", "Routine deleted successfully");
            }
        }
        catch (Exception ex)
        {
            var message = $"Failed to delete routine: {ex.Message}";
            ErrorMessage = message;
            await _notificationService.ScheduleAsync(DateTimeOffset.Now, "Error", message);
        }
    }

    public event PropertyChangedEventHandler? PropertyChanged;

    protected virtual void OnPropertyChanged([CallerMemberName] string? propertyName = null)
    {
        PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
    }
}

public class RoutineListItemViewModel : INotifyPropertyChanged
{
    private readonly Routine _routine;

    public RoutineListItemViewModel(Routine routine)
    {
        _routine = routine;
    }

    public Guid Id => _routine.Id;
    public string Name => _routine.Name;
    public string? Description => _routine.Description;
    public DateTimeOffset CreatedAt => _routine.CreatedAt;

    public int StepsCount
    {
        get
        {
            try
            {
                // Quick count of steps in JSON - this is approximate
                var json = _routine.StepsJson;
                if (string.IsNullOrWhiteSpace(json) || json == "[]") return 0;

                // Count occurrences of "id" field as rough step count
                var count = json.Split(new[] { "\"id\":" }, StringSplitOptions.None).Length - 1;
                return count;
            }
            catch
            {
                return 0;
            }
        }
    }

    public event PropertyChangedEventHandler? PropertyChanged;

    protected virtual void OnPropertyChanged([CallerMemberName] string? propertyName = null)
    {
        PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
    }
}
