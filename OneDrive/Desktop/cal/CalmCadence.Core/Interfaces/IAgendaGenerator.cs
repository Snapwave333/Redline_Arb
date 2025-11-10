using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using CalmCadence.Core.Models;

namespace CalmCadence.Core.Interfaces;

public interface IAgendaGenerator
{
    Task<IReadOnlyList<AgendaEntry>> GenerateAsync(DateOnly date);
}
