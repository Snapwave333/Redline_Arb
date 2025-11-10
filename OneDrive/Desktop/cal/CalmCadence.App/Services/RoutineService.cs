using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Text.Json;
using System.Threading.Tasks;
using CalmCadence.Core.Interfaces;
using CalmCadence.Core.Models;
using CalmCadence.Data.Context;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;

namespace CalmCadence.App.Services;

public class RoutineService : IRoutineService
{
    private readonly CalmCadenceDbContext _dbContext;
    private readonly IHabitService _habitService;
    private readonly IAgendaGenerator _agendaGenerator;
    private readonly INotificationService _notificationService;
    private readonly ILogger<RoutineService> _logger;

    public RoutineService(
        CalmCadenceDbContext dbContext,
        IHabitService habitService,
        IAgendaGenerator agendaGenerator,
        INotificationService notificationService,
        ILogger<RoutineService> logger)
    {
        _dbContext = dbContext;
        _habitService = habitService;
        _agendaGenerator = agendaGenerator;
        _notificationService = notificationService;
        _logger = logger;
    }

    #region Routine CRUD Operations

    public async Task<Routine> CreateRoutineAsync(Routine routine)
    {
        try
        {
            if (string.IsNullOrWhiteSpace(routine.Name))
                throw new ArgumentException("Routine name is required");

            routine.CreatedAt = DateTimeOffset.UtcNow;
            _dbContext.Routines.Add(routine);
            await _dbContext.SaveChangesAsync();

            _logger.LogInformation("Created routine {RoutineId}: {RoutineName}", routine.Id, routine.Name);
            return routine;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to create routine {RoutineName}", routine.Name);
            throw;
        }
    }

    public async Task<Routine?> GetRoutineAsync(Guid routineId)
    {
        return await _dbContext.Routines
            .FirstOrDefaultAsync(r => r.Id == routineId);
    }

    public async Task<IEnumerable<Routine>> GetAllRoutinesAsync(bool includeInactive = false)
    {
        var query = _dbContext.Routines.AsQueryable();

        if (!includeInactive)
            query = query.Where(r => r.Enabled);

        return await query
            .OrderBy(r => r.SortOrder)
            .ThenBy(r => r.Name)
            .ToListAsync();
    }

    public async Task<Routine> UpdateRoutineAsync(Routine routine)
    {
        try
        {
            var existingRoutine = await _dbContext.Routines.FindAsync(routine.Id);
            if (existingRoutine == null)
                throw new KeyNotFoundException($"Routine {routine.Id} not found");

            if (string.IsNullOrWhiteSpace(routine.Name))
                throw new ArgumentException("Routine name is required");

            // Update properties
            existingRoutine.Name = routine.Name;
            existingRoutine.Description = routine.Description;
            existingRoutine.StepsJson = routine.StepsJson;
            existingRoutine.Enabled = routine.Enabled;
            existingRoutine.ColorHex = routine.ColorHex;
            existingRoutine.SortOrder = routine.SortOrder;
            existingRoutine.UpdatedAt = DateTimeOffset.UtcNow;

            await _dbContext.SaveChangesAsync();

            _logger.LogInformation("Updated routine {RoutineId}: {RoutineName}", routine.Id, routine.Name);
            return existingRoutine;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to update routine {RoutineId}", routine.Id);
            throw;
        }
    }

    public async Task<bool> DeleteRoutineAsync(Guid routineId)
    {
        try
        {
            var routine = await _dbContext.Routines.FindAsync(routineId);
            if (routine == null)
                return false;

            _dbContext.Routines.Remove(routine);
            await _dbContext.SaveChangesAsync();

            _logger.LogInformation("Deleted routine {RoutineId}: {RoutineName}", routineId, routine.Name);
            return true;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to delete routine {RoutineId}", routineId);
            throw;
        }
    }

    public async Task<bool> SetRoutineEnabledAsync(Guid routineId, bool enabled)
    {
        try
        {
            var routine = await _dbContext.Routines.FindAsync(routineId);
            if (routine == null)
                return false;

            routine.Enabled = enabled;
            routine.UpdatedAt = DateTimeOffset.UtcNow;
            await _dbContext.SaveChangesAsync();

            _logger.LogInformation("Set routine {RoutineId} enabled to {Enabled}", routineId, enabled);
            return true;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to set routine {RoutineId} enabled status", routineId);
            throw;
        }
    }

    #endregion

    #region Routine Execution

    public async Task<RoutineExecutionResult> ExecuteRoutineAsync(Guid routineId)
    {
        var routine = await GetRoutineAsync(routineId);
        if (routine == null)
            throw new KeyNotFoundException($"Routine {routineId} not found");

        return await ExecuteRoutineAsync(routine);
    }

    public async Task<RoutineExecutionResult> ExecuteRoutineAsync(Routine routine)
    {
        var startedAt = DateTimeOffset.UtcNow;
        var stepResults = new List<RoutineStepResult>();
        var overallSuccess = true;

        _logger.LogInformation("Starting execution of routine {RoutineId}: {RoutineName}",
            routine.Id, routine.Name);

        try
        {
            // Deserialize steps from JSON
            var steps = DeserializeSteps(routine.StepsJson);

            // Execute each step
            foreach (var step in steps.Where(s => s.IsEnabled).OrderBy(s => s.Order))
            {
                var stepResult = await ExecuteStepAsync(step);
                stepResults.Add(stepResult);

                if (!stepResult.Success)
                {
                    overallSuccess = false;
                    _logger.LogWarning("Step {StepId} ({StepType}) failed: {Error}",
                        step.Id, step.Type, stepResult.ErrorMessage);
                }
                else
                {
                    _logger.LogInformation("Step {StepId} ({StepType}) completed successfully",
                        step.Id, step.Type);
                }
            }
        }
        catch (Exception ex)
        {
            overallSuccess = false;
            _logger.LogError(ex, "Routine execution failed for {RoutineId}", routine.Id);

            // Add a general error step result
            stepResults.Add(new RoutineStepResult
            {
                StepId = Guid.Empty,
                StepType = RoutineStepType.CustomAction,
                StepDescription = "Routine execution error",
                Success = false,
                Duration = TimeSpan.Zero,
                ErrorMessage = ex.Message,
                ExecutedAt = DateTimeOffset.UtcNow
            });
        }

        var completedAt = DateTimeOffset.UtcNow;
        var totalDuration = completedAt - startedAt;

        var result = new RoutineExecutionResult
        {
            RoutineId = routine.Id,
            RoutineName = routine.Name,
            Success = overallSuccess,
            StepResults = stepResults,
            TotalDuration = totalDuration,
            StartedAt = startedAt,
            CompletedAt = completedAt,
            ErrorMessage = overallSuccess ? null : "One or more steps failed"
        };

        _logger.LogInformation("Completed execution of routine {RoutineId} in {Duration}ms. Success: {Success}",
            routine.Id, totalDuration.TotalMilliseconds, overallSuccess);

        return result;
    }

    private async Task<RoutineStepResult> ExecuteStepAsync(RoutineStep step)
    {
        var executedAt = DateTimeOffset.UtcNow;
        var stopwatch = Stopwatch.StartNew();

        try
        {
            string? resultMessage = null;
            string? errorMessage = null;
            var success = true;

            switch (step.Type)
            {
                case RoutineStepType.ReviewAgenda:
                    (success, resultMessage, errorMessage) = await ExecuteReviewAgendaStepAsync(step);
                    break;

                case RoutineStepType.MarkHabitComplete:
                    (success, resultMessage, errorMessage) = await ExecuteMarkHabitCompleteStepAsync(step);
                    break;

                case RoutineStepType.StartTimer:
                    (success, resultMessage, errorMessage) = await ExecuteStartTimerStepAsync(step);
                    break;

                case RoutineStepType.ShowNotification:
                    (success, resultMessage, errorMessage) = await ExecuteShowNotificationStepAsync(step);
                    break;

                default:
                    success = false;
                    errorMessage = $"Unsupported step type: {step.Type}";
                    break;
            }

            stopwatch.Stop();

            return new RoutineStepResult
            {
                StepId = step.Id,
                StepType = step.Type,
                StepDescription = step.Description,
                Success = success,
                Duration = stopwatch.Elapsed,
                ResultMessage = resultMessage,
                ErrorMessage = errorMessage,
                ExecutedAt = executedAt
            };
        }
        catch (Exception ex)
        {
            stopwatch.Stop();

            return new RoutineStepResult
            {
                StepId = step.Id,
                StepType = step.Type,
                StepDescription = step.Description,
                Success = false,
                Duration = stopwatch.Elapsed,
                ErrorMessage = ex.Message,
                ExecutedAt = executedAt
            };
        }
    }

    private async Task<(bool success, string? resultMessage, string? errorMessage)> ExecuteReviewAgendaStepAsync(RoutineStep step)
    {
        try
        {
            var today = DateOnly.FromDateTime(DateTime.Today);
            var agendaEntries = await _agendaGenerator.GenerateAsync(today);

            if (!agendaEntries.Any())
            {
                var message = "Your agenda for today is clear! 🎉";
                await _notificationService.ScheduleAsync(DateTimeOffset.Now, "Daily Agenda", message);
                return (true, message, null);
            }

            // Group entries by type for better formatting
            var tasks = agendaEntries.Where(e => e.Type == AgendaItemType.Task).ToList();
            var events = agendaEntries.Where(e => e.Type == AgendaItemType.Event).ToList();
            var habits = agendaEntries.Where(e => e.Type == AgendaItemType.Habit).ToList();
            var routines = agendaEntries.Where(e => e.Type == AgendaItemType.Routine).ToList();

            var messageBuilder = new System.Text.StringBuilder();
            messageBuilder.AppendLine("📅 Your Daily Agenda:");

            if (tasks.Any())
            {
                messageBuilder.AppendLine($"\n📝 Tasks ({tasks.Count}):");
                foreach (var task in tasks.Take(3))
                    messageBuilder.AppendLine($"  • {task.Title}");
                if (tasks.Count > 3) messageBuilder.AppendLine($"  ... and {tasks.Count - 3} more");
            }

            if (events.Any())
            {
                messageBuilder.AppendLine($"\n📅 Events ({events.Count}):");
                foreach (var evt in events.Take(3))
                    messageBuilder.AppendLine($"  • {evt.Title}");
                if (events.Count > 3) messageBuilder.AppendLine($"  ... and {events.Count - 3} more");
            }

            if (habits.Any())
            {
                messageBuilder.AppendLine($"\n🎯 Habits ({habits.Count}):");
                foreach (var habit in habits.Take(3))
                    messageBuilder.AppendLine($"  • {habit.Title}");
            }

            if (routines.Any())
            {
                messageBuilder.AppendLine($"\n🔄 Routines ({routines.Count}):");
                foreach (var routine in routines.Take(2))
                    messageBuilder.AppendLine($"  • {routine.Title}");
            }

            var agendaMessage = messageBuilder.ToString();
            await _notificationService.ScheduleAsync(DateTimeOffset.Now, "Daily Agenda", agendaMessage);

            return (true, $"Reviewed {agendaEntries.Count} agenda items", null);
        }
        catch (Exception ex)
        {
            return (false, null, $"Failed to review agenda: {ex.Message}");
        }
    }

    private async Task<(bool success, string? resultMessage, string? errorMessage)> ExecuteMarkHabitCompleteStepAsync(RoutineStep step)
    {
        try
        {
            // Parse configuration for habit ID
            var config = JsonSerializer.Deserialize<Dictionary<string, JsonElement>>(step.ConfigJson);
            if (config == null || !config.TryGetValue("habitId", out var habitIdElement))
                return (false, null, "Missing habitId in step configuration");

            if (!Guid.TryParse(habitIdElement.GetString(), out var habitId))
                return (false, null, "Invalid habitId format in step configuration");

            // Get habit to verify it exists and get name
            var habit = await _habitService.GetHabitAsync(habitId);
            if (habit == null)
                return (false, null, $"Habit {habitId} not found");

            // Log the habit as complete for today
            var today = DateOnly.FromDateTime(DateTime.Today);
            var log = await _habitService.LogHabitAsync(habitId, today);

            var message = $"✅ Marked '{habit.Name}' as complete!";
            await _notificationService.ScheduleAsync(DateTimeOffset.Now, "Habit Completed", message);

            return (true, $"Completed habit: {habit.Name}", null);
        }
        catch (Exception ex)
        {
            return (false, null, $"Failed to mark habit complete: {ex.Message}");
        }
    }

    private async Task<(bool success, string? resultMessage, string? errorMessage)> ExecuteStartTimerStepAsync(RoutineStep step)
    {
        try
        {
            // Parse configuration for duration
            var config = JsonSerializer.Deserialize<Dictionary<string, JsonElement>>(step.ConfigJson);
            var durationMinutes = step.DurationMinutes ?? 15; // Default to 15 minutes

            if (config != null && config.TryGetValue("durationMinutes", out var durationElement))
            {
                if (durationElement.TryGetInt32(out var parsedDuration))
                    durationMinutes = parsedDuration;
            }

            // For now, just show a notification - timer implementation would be more complex
            var message = $"⏰ Starting {durationMinutes}-minute timer: {step.Description}";
            await _notificationService.ScheduleAsync(DateTimeOffset.Now, "Timer Started", message);

            return (true, $"Started {durationMinutes}-minute timer", null);
        }
        catch (Exception ex)
        {
            return (false, null, $"Failed to start timer: {ex.Message}");
        }
    }

    private async Task<(bool success, string? resultMessage, string? errorMessage)> ExecuteShowNotificationStepAsync(RoutineStep step)
    {
        try
        {
            // Parse configuration for title and message
            var config = JsonSerializer.Deserialize<Dictionary<string, JsonElement>>(step.ConfigJson);
            var title = "Routine Notification";
            var notificationMessage = step.Description;

            if (config != null)
            {
                if (config.TryGetValue("title", out var titleElement))
                    title = titleElement.GetString() ?? title;

                if (config.TryGetValue("message", out var msgElement))
                    notificationMessage = msgElement.GetString() ?? notificationMessage;
            }

            await _notificationService.ScheduleAsync(DateTimeOffset.Now, title, notificationMessage);

            return (true, $"Sent notification: {title}", null);
        }
        catch (Exception ex)
        {
            return (false, null, $"Failed to show notification: {ex.Message}");
        }
    }

    private List<RoutineStep> DeserializeSteps(string stepsJson)
    {
        if (string.IsNullOrWhiteSpace(stepsJson) || stepsJson == "[]")
            return new List<RoutineStep>();

        try
        {
            return JsonSerializer.Deserialize<List<RoutineStep>>(stepsJson) ?? new List<RoutineStep>();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to deserialize routine steps JSON");
            return new List<RoutineStep>();
        }
    }

    #endregion

    #region Routine Step Management

    public async Task<Routine> AddStepToRoutineAsync(Guid routineId, RoutineStep step)
    {
        var routine = await GetRoutineAsync(routineId);
        if (routine == null)
            throw new KeyNotFoundException($"Routine {routineId} not found");

        var steps = DeserializeSteps(routine.StepsJson);
        step.Id = Guid.NewGuid();
        step.Order = steps.Any() ? steps.Max(s => s.Order) + 1 : 1;
        steps.Add(step);

        routine.StepsJson = JsonSerializer.Serialize(steps);
        routine.UpdatedAt = DateTimeOffset.UtcNow;

        await _dbContext.SaveChangesAsync();

        _logger.LogInformation("Added step {StepId} to routine {RoutineId}", step.Id, routineId);
        return routine;
    }

    public async Task<Routine> UpdateRoutineStepAsync(Guid routineId, RoutineStep step)
    {
        var routine = await GetRoutineAsync(routineId);
        if (routine == null)
            throw new KeyNotFoundException($"Routine {routineId} not found");

        var steps = DeserializeSteps(routine.StepsJson);
        var existingStep = steps.FirstOrDefault(s => s.Id == step.Id);
        if (existingStep == null)
            throw new KeyNotFoundException($"Step {step.Id} not found in routine {routineId}");

        // Update step properties
        existingStep.Type = step.Type;
        existingStep.Description = step.Description;
        existingStep.ConfigJson = step.ConfigJson;
        existingStep.Order = step.Order;
        existingStep.DurationMinutes = step.DurationMinutes;
        existingStep.IsEnabled = step.IsEnabled;

        routine.StepsJson = JsonSerializer.Serialize(steps);
        routine.UpdatedAt = DateTimeOffset.UtcNow;

        await _dbContext.SaveChangesAsync();

        _logger.LogInformation("Updated step {StepId} in routine {RoutineId}", step.Id, routineId);
        return routine;
    }

    public async Task<Routine> RemoveStepFromRoutineAsync(Guid routineId, Guid stepId)
    {
        var routine = await GetRoutineAsync(routineId);
        if (routine == null)
            throw new KeyNotFoundException($"Routine {routineId} not found");

        var steps = DeserializeSteps(routine.StepsJson);
        var stepToRemove = steps.FirstOrDefault(s => s.Id == stepId);
        if (stepToRemove == null)
            return routine; // Step not found, return unchanged

        steps.Remove(stepToRemove);

        // Reorder remaining steps
        for (int i = 0; i < steps.Count; i++)
            steps[i].Order = i + 1;

        routine.StepsJson = JsonSerializer.Serialize(steps);
        routine.UpdatedAt = DateTimeOffset.UtcNow;

        await _dbContext.SaveChangesAsync();

        _logger.LogInformation("Removed step {StepId} from routine {RoutineId}", stepId, routineId);
        return routine;
    }

    public async Task<Routine> ReorderRoutineStepsAsync(Guid routineId, List<Guid> stepIdsInOrder)
    {
        var routine = await GetRoutineAsync(routineId);
        if (routine == null)
            throw new KeyNotFoundException($"Routine {routineId} not found");

        var steps = DeserializeSteps(routine.StepsJson);

        // Validate that all provided IDs exist
        var existingIds = steps.Select(s => s.Id).ToHashSet();
        if (!stepIdsInOrder.All(id => existingIds.Contains(id)))
            throw new ArgumentException("One or more step IDs not found in routine");

        // Reorder steps according to the provided order
        var reorderedSteps = new List<RoutineStep>();
        for (int i = 0; i < stepIdsInOrder.Count; i++)
        {
            var step = steps.First(s => s.Id == stepIdsInOrder[i]);
            step.Order = i + 1;
            reorderedSteps.Add(step);
        }

        routine.StepsJson = JsonSerializer.Serialize(reorderedSteps);
        routine.UpdatedAt = DateTimeOffset.UtcNow;

        await _dbContext.SaveChangesAsync();

        _logger.LogInformation("Reordered steps in routine {RoutineId}", routineId);
        return routine;
    }

    #endregion
}
