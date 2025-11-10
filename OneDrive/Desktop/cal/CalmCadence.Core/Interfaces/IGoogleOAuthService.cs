using System.Threading.Tasks;
using Google.Apis.Auth.OAuth2;

namespace CalmCadence.Core.Interfaces;

public interface IGoogleOAuthService
{
    // Initiates OAuth flow (opens browser) and stores refresh token securely for reuse
    Task<bool> SignInAsync();

    // Clears stored tokens
    Task SignOutAsync();

    // Returns an authenticated credential, or null if not signed in
    Task<UserCredential?> GetCredentialAsync();
}