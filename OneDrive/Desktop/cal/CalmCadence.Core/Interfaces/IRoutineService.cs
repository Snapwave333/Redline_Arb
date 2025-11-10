using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using CalmCadence.Core.Models;

namespace CalmCadence.Core.Interfaces;

public interface IRoutineService
{
    // Routine CRUD operations
    Task<Routine> CreateRoutineAsync(Routine routine);
    Task<Routine?> GetRoutineAsync(Guid routineId);
    Task<IEnumerable<Routine>> GetAllRoutinesAsync(bool includeInactive = false);
    Task<Routine> UpdateRoutineAsync(Routine routine);
    Task<bool> DeleteRoutineAsync(Guid routineId);
    Task<bool> SetRoutineEnabledAsync(Guid routineId, bool enabled);

    // Routine execution
    Task<RoutineExecutionResult> ExecuteRoutineAsync(Guid routineId);
    Task<RoutineExecutionResult> ExecuteRoutineAsync(Routine routine);

    // Routine step management
    Task<Routine> AddStepToRoutineAsync(Guid routineId, RoutineStep step);
    Task<Routine> UpdateRoutineStepAsync(Guid routineId, RoutineStep step);
    Task<Routine> RemoveStepFromRoutineAsync(Guid routineId, Guid stepId);
    Task<Routine> ReorderRoutineStepsAsync(Guid routineId, List<Guid> stepIdsInOrder);
}

// Result model for routine execution
public class RoutineExecutionResult
{
    public Guid RoutineId { get; set; }
    public string RoutineName { get; set; } = string.Empty;
    public bool Success { get; set; }
    public List<RoutineStepResult> StepResults { get; set; } = new();
    public TimeSpan TotalDuration { get; set; }
    public DateTimeOffset StartedAt { get; set; }
    public DateTimeOffset CompletedAt { get; set; }
    public string? ErrorMessage { get; set; }
}

public class RoutineStepResult
{
    public Guid StepId { get; set; }
    public RoutineStepType StepType { get; set; }
    public string StepDescription { get; set; } = string.Empty;
    public bool Success { get; set; }
    public TimeSpan Duration { get; set; }
    public string? ResultMessage { get; set; }
    public string? ErrorMessage { get; set; }
    public DateTimeOffset ExecutedAt { get; set; }
}
