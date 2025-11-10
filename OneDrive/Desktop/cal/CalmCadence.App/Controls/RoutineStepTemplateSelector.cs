using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using CalmCadence.Core.Models;
using CalmCadence.App.ViewModels;

namespace CalmCadence.App.Controls;

public class RoutineStepTemplateSelector : DataTemplateSelector
{
    public DataTemplate? ReviewAgendaTemplate { get; set; }
    public DataTemplate? MarkHabitCompleteTemplate { get; set; }
    public DataTemplate? ShowNotificationTemplate { get; set; }
    public DataTemplate? StartTimerTemplate { get; set; }
    public DataTemplate? DefaultTemplate { get; set; }

    protected override DataTemplate? SelectTemplateCore(object item)
    {
        if (item is RoutineStepViewModel step)
        {
            return step.StepType switch
            {
                RoutineStepType.ReviewAgenda => ReviewAgendaTemplate ?? DefaultTemplate,
                RoutineStepType.MarkHabitComplete => MarkHabitCompleteTemplate ?? DefaultTemplate,
                RoutineStepType.ShowNotification => ShowNotificationTemplate ?? DefaultTemplate,
                RoutineStepType.StartTimer => StartTimerTemplate ?? DefaultTemplate,
                _ => DefaultTemplate
            };
        }

        return DefaultTemplate;
    }
}
