using CalmCadence.Core.Models;

namespace CalmCadence.Core.Interfaces;

public interface IQuickAddParser
{
    TaskItem ParseTask(string input);
}
