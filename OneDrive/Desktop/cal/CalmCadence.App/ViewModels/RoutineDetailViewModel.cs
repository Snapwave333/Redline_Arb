using System;
using System.Collections.ObjectModel;
using System.Collections.Generic;
using System.ComponentModel;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading.Tasks;
using System.Text.Json;
using System.Windows.Input;
using CalmCadence.Core.Interfaces;
using CalmCadence.Core.Models;
using CalmCadence.Core.Enums;
using CalmCadence.App.Helpers;
using Microsoft.Extensions.DependencyInjection;

namespace CalmCadence.App.ViewModels;

public class RoutineDetailViewModel : INotifyPropertyChanged
{
    private readonly IRoutineService _routineService;
    private readonly INotificationService _notificationService;

    private Routine _routine = new();
    private bool _isLoading;
    private string _loadingMessage = "Loading...";
    private bool _hasUnsavedChanges;
    private RoutineColorViewModel? _selectedColor;

    public RoutineDetailViewModel()
    {
        _routineService = App.AppHost?.Services.GetRequiredService<IRoutineService>()
            ?? throw new InvalidOperationException("IRoutineService not available");
        _notificationService = App.AppHost?.Services.GetRequiredService<INotificationService>()
            ?? throw new InvalidOperationException("INotificationService not available");

        Steps = new ObservableCollection<RoutineStepViewModel>();
        AvailableStepTypes = Enum.GetValues<RoutineStepType>().ToList();
        AvailableColors = new List<RoutineColorViewModel>
        {
            new RoutineColorViewModel { Name = "Default", HexValue = "#0078D4" },
            new RoutineColorViewModel { Name = "Green", HexValue = "#107C10" },
            new RoutineColorViewModel { Name = "Orange", HexValue = "#FF8C00" },
            new RoutineColorViewModel { Name = "Red", HexValue = "#D13438" },
            new RoutineColorViewModel { Name = "Purple", HexValue = "#5C2D91" }
        };
    }

    public Routine Routine
    {
        get => _routine;
        set
        {
            _routine = value;
            OnPropertyChanged();
            OnPropertyChanged(nameof(PageTitle));
            OnPropertyChanged(nameof(PageSubtitle));
            OnPropertyChanged(nameof(CanSave));
        }
    }

    public ObservableCollection<RoutineStepViewModel> Steps { get; }

    public List<RoutineStepType> AvailableStepTypes { get; }

    public List<RoutineColorViewModel> AvailableColors { get; }

    public RoutineColorViewModel? SelectedColor
    {
        get => _selectedColor;
        set
        {
            _selectedColor = value;
            if (value != null)
            {
                Routine.ColorHex = value.HexValue;
            }
            OnPropertyChanged();
        }
    }

    public string PageTitle => string.IsNullOrWhiteSpace(Routine.Name) ? "New Routine" : $"Edit: {Routine.Name}";

    public string PageSubtitle => string.IsNullOrWhiteSpace(Routine.Name) ? "Create a new automated routine" : "Modify routine settings and steps";

    public bool IsLoading
    {
        get => _isLoading;
        set
        {
            _isLoading = value;
            OnPropertyChanged();
        }
    }

    public string LoadingMessage
    {
        get => _loadingMessage;
        set
        {
            _loadingMessage = value;
            OnPropertyChanged();
        }
    }

    public bool HasUnsavedChanges
    {
        get => _hasUnsavedChanges;
        set
        {
            _hasUnsavedChanges = value;
            OnPropertyChanged();
            OnPropertyChanged(nameof(CanSave));
        }
    }

    public bool CanSave => !string.IsNullOrWhiteSpace(Routine.Name) && !IsLoading;

    public void InitializeNewRoutine()
    {
        Routine = new Routine
        {
            Name = string.Empty,
            Description = string.Empty,
            StepsJson = "[]",
            Enabled = true,
            ColorHex = "#0078D4"
        };

        Steps.Clear();
        SelectedColor = AvailableColors.First();
        HasUnsavedChanges = false;
    }

    public async Task LoadRoutineAsync(Guid routineId)
    {
        IsLoading = true;
        LoadingMessage = "Loading routine...";

        try
        {
            var routine = await _routineService.GetRoutineAsync(routineId);
            if (routine == null)
            {
                await _notificationService.ScheduleAsync(DateTimeOffset.Now, "Error", "Routine not found");
                return;
            }

            Routine = routine;
            SelectedColor = AvailableColors.FirstOrDefault(c => c.HexValue == routine.ColorHex) ?? AvailableColors.First();

            // Load steps from JSON
            Steps.Clear();
            var steps = DeserializeSteps(routine.StepsJson);
            foreach (var step in steps)
            {
                Steps.Add(step);
            }

            HasUnsavedChanges = false;
        }
        catch (Exception ex)
        {
            await _notificationService.ScheduleAsync(DateTimeOffset.Now, "Error", $"Failed to load routine: {ex.Message}");
        }
        finally
        {
            IsLoading = false;
        }
    }

    public async Task<bool> SaveRoutineAsync()
    {
        if (!CanSave) return false;

        IsLoading = true;
        LoadingMessage = "Saving routine...";

        try
        {
            // Serialize steps to JSON
            Routine.StepsJson = SerializeSteps(Steps.ToList());

            Routine updatedRoutine;
            if (Routine.Id == Guid.Empty)
            {
                // Create new
                updatedRoutine = await _routineService.CreateRoutineAsync(Routine);
            }
            else
            {
                // Update existing
                var success = await _routineService.UpdateRoutineAsync(Routine);
                if (!success)
                {
                    await _notificationService.ScheduleAsync(DateTimeOffset.Now, "Error", "Failed to update routine");
                    return false;
                }
                updatedRoutine = Routine;
            }

            Routine = updatedRoutine;
            HasUnsavedChanges = false;

            await _notificationService.ScheduleAsync(DateTimeOffset.Now, "Success", "Routine saved successfully");
            return true;
        }
        catch (Exception ex)
        {
            await _notificationService.ScheduleAsync(DateTimeOffset.Now, "Error", $"Failed to save routine: {ex.Message}");
            return false;
        }
        finally
        {
            IsLoading = false;
        }
    }

    public void AddNewStep()
    {
        var newStep = new RoutineStepViewModel
        {
            Id = Guid.NewGuid(),
            StepType = RoutineStepType.ReviewAgenda,
            Description = "New step",
            ConfigJson = "{}",
            Order = Steps.Count
        };

        Steps.Add(newStep);
        HasUnsavedChanges = true;
    }

    public void RemoveStep(int index)
    {
        if (index >= 0 && index < Steps.Count)
        {
            Steps.RemoveAt(index);
            // Reorder remaining steps
            for (int i = 0; i < Steps.Count; i++)
            {
                Steps[i].Order = i;
            }
            HasUnsavedChanges = true;
        }
    }

    public void MoveStepUp(int index)
    {
        if (index > 0 && index < Steps.Count)
        {
            var step = Steps[index];
            Steps.RemoveAt(index);
            Steps.Insert(index - 1, step);

            // Update order
            for (int i = 0; i < Steps.Count; i++)
            {
                Steps[i].Order = i;
            }
            HasUnsavedChanges = true;
        }
    }

    public void MoveStepDown(int index)
    {
        if (index >= 0 && index < Steps.Count - 1)
        {
            var step = Steps[index];
            Steps.RemoveAt(index);
            Steps.Insert(index + 1, step);

            // Update order
            for (int i = 0; i < Steps.Count; i++)
            {
                Steps[i].Order = i;
            }
            HasUnsavedChanges = true;
        }
    }

    private List<RoutineStepViewModel> DeserializeSteps(string json)
    {
        if (string.IsNullOrWhiteSpace(json) || json == "[]")
            return new List<RoutineStepViewModel>();

        try
        {
            var stepDtos = JsonSerializer.Deserialize<List<RoutineStepDto>>(json);
            return stepDtos?.Select(dto => new RoutineStepViewModel
            {
                Id = dto.Id,
                StepType = dto.Type,
                Description = dto.Description,
                ConfigJson = dto.ConfigJson,
                Order = dto.Order,
                IsEnabled = dto.IsEnabled
            }).ToList() ?? new List<RoutineStepViewModel>();
        }
        catch
        {
            return new List<RoutineStepViewModel>();
        }
    }

    private string SerializeSteps(List<RoutineStepViewModel> steps)
    {
        var dtos = steps.Select(step => new RoutineStepDto
        {
            Id = step.Id,
            Type = step.StepType ?? RoutineStepType.ReviewAgenda,
            Description = step.Description,
            ConfigJson = step.ConfigJson,
            Order = step.Order,
            IsEnabled = step.IsEnabled
        }).ToList();

        return JsonSerializer.Serialize(dtos);
    }

    // Commands
    public ICommand MoveStepUpCommand => new RelayCommand<RoutineStepViewModel>(step =>
    {
        if (step != null)
        {
            var index = Steps.IndexOf(step);
            MoveStepUp(index);
        }
    });

    public ICommand MoveStepDownCommand => new RelayCommand<RoutineStepViewModel>(step =>
    {
        if (step != null)
        {
            var index = Steps.IndexOf(step);
            MoveStepDown(index);
        }
    });

    public ICommand RemoveStepCommand => new RelayCommand<RoutineStepViewModel>(async step =>
    {
        if (step != null)
        {
            var index = Steps.IndexOf(step);
            var dialog = new ContentDialog
            {
                Title = "Delete Step",
                Content = "Are you sure you want to delete this step?",
                PrimaryButtonText = "Delete",
                CloseButtonText = "Cancel"
            };

            // Note: Dialog would need to be shown from the view
            // For now, just remove the step
            RemoveStep(index);
        }
    });

    public event PropertyChangedEventHandler? PropertyChanged;

    protected virtual void OnPropertyChanged([CallerMemberName] string? propertyName = null)
    {
        PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
    }
}

public class RoutineStepViewModel : INotifyPropertyChanged
{
    private Guid _id;
    private RoutineStepType? _stepType;
    private string _description = string.Empty;
    private string _configJson = "{}";
    private int _order;
    private bool _isEnabled = true;

    public Guid Id
    {
        get => _id;
        set
        {
            _id = value;
            OnPropertyChanged();
        }
    }

    public RoutineStepType? StepType
    {
        get => _stepType;
        set
        {
            _stepType = value;
            OnPropertyChanged();
        }
    }

    public string Description
    {
        get => _description;
        set
        {
            _description = value;
            OnPropertyChanged();
        }
    }

    public string ConfigJson
    {
        get => _configJson;
        set
        {
            _configJson = value;
            OnPropertyChanged();
        }
    }

    public int Order
    {
        get => _order;
        set
        {
            _order = value;
            OnPropertyChanged();
        }
    }

    public bool IsEnabled
    {
        get => _isEnabled;
        set
        {
            _isEnabled = value;
            OnPropertyChanged();
        }
    }

    public event PropertyChangedEventHandler? PropertyChanged;

    protected virtual void OnPropertyChanged([CallerMemberName] string? propertyName = null)
    {
        PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
    }
}

public class RoutineColorViewModel
{
    public string Name { get; set; } = string.Empty;
    public string HexValue { get; set; } = string.Empty;
}

internal class RoutineStepDto
{
    public Guid Id { get; set; }
    public RoutineStepType Type { get; set; }
    public string Description { get; set; } = string.Empty;
    public string ConfigJson { get; set; } = "{}";
    public int Order { get; set; }
    public bool IsEnabled { get; set; } = true;
}
