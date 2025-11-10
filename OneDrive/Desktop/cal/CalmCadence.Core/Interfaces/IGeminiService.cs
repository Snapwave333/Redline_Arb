using System.Threading.Tasks;
using CalmCadence.Core.Models;

namespace CalmCadence.Core.Interfaces;

public interface IGeminiService
{
    Task<BriefOutput?> GenerateBriefAsync(BriefInput input);
    Task<byte[]?> GenerateAudioAsync(string text, string voice = "en-US-Neural2-D");
    Task<string?> GenerateTextAsync(string prompt, double temperature = 0.2);
}
