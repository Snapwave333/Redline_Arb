using System.Threading.Tasks;

namespace CalmCadence.Core.Interfaces;

public interface IGoogleApiService
{
    Task<string?> CreateOrUpdateNotebookAsync(string projectId, string location, string notebookId, string content);
    Task<string?> GenerateAudioOverviewAsync(string projectId, string location, string notebookId, string episodeFocus, string[]? sourceIds = null);
    Task<bool> DeleteAudioOverviewAsync(string projectId, string location, string notebookId);
    Task<bool> IsAuthenticatedAsync();
    Task AuthenticateAsync();
}
