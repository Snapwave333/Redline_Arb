using System;
using System.IO;
using System.Security.Cryptography;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using CalmCadence.Core.Interfaces;
using Google.Apis.Auth.OAuth2;
using Google.Apis.Auth.OAuth2.Flows;
using Google.Apis.Calendar.v3;
using Google.Apis.Services;
using Google.Apis.Auth.OAuth2.Responses;
using Google.Apis.Util.Store;
using Microsoft.Extensions.Logging;

namespace CalmCadence.Core.Services;

public class GoogleOAuthService : IGoogleOAuthService
{
    private readonly ILogger<GoogleOAuthService> _logger;
    private const string AppFolderName = "CalmCadence";
    private const string TokensFileName = "google_oauth_tokens.json.enc";
    private const string ClientSecretsFileName = "google_client_secrets.json"; // Optional local file

    private static readonly string[] Scopes =
    {
        CalendarService.Scope.Calendar,
        CalendarService.Scope.CalendarEvents
    };

    public GoogleOAuthService(ILogger<GoogleOAuthService> logger)
    {
        _logger = logger;
    }

    public async Task<bool> SignInAsync()
    {
        try
        {
            var secrets = await LoadClientSecretsAsync();
            if (secrets == null)
            {
                _logger.LogWarning("Google OAuth: Client secrets not found. Set env vars CALMCADENCE_GOOGLE_CLIENT_ID and CALMCADENCE_GOOGLE_CLIENT_SECRET, or place {ClientSecretsFileName} in %LocalAppData%/{AppFolderName}.", ClientSecretsFileName, AppFolderName);
                return false;
            }

            // Use LocalServerCodeReceiver to handle browser-based OAuth
            var initializer = new GoogleAuthorizationCodeFlow.Initializer
            {
                ClientSecrets = secrets,
                Scopes = Scopes,
                DataStore = new FileDataStore(Path.Combine(GetAppFolder(), "GoogleOAuth"), true)
            };
            var flow = new GoogleAuthorizationCodeFlow(initializer);

            var codeReceiver = new LocalServerCodeReceiver();
            var credential = await GoogleWebAuthorizationBroker.AuthorizeAsync(
                secrets,
                Scopes,
                "CalmCadenceUser",
                CancellationToken.None,
                initializer.DataStore,
                codeReceiver);

            if (credential?.Token?.RefreshToken is not null)
            {
                await SaveEncryptedTokensAsync(credential.Token);
                _logger.LogInformation("Google OAuth: Sign-in successful; refresh token stored.");
                return true;
            }

            _logger.LogWarning("Google OAuth: Sign-in did not yield a refresh token.");
            return false;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Google OAuth SignIn failed");
            return false;
        }
    }

    public Task SignOutAsync()
    {
        try
        {
            var path = GetTokensPath();
            if (File.Exists(path))
            {
                File.Delete(path);
            }
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Google OAuth SignOut failed");
        }
        return Task.CompletedTask;
    }

    public async Task<UserCredential?> GetCredentialAsync()
    {
        try
        {
            var secrets = await LoadClientSecretsAsync();
            if (secrets == null)
                return null;

            var initializer = new GoogleAuthorizationCodeFlow.Initializer
            {
                ClientSecrets = secrets,
                Scopes = Scopes,
                DataStore = new FileDataStore(Path.Combine(GetAppFolder(), "GoogleOAuth"), true)
            };
            var flow = new GoogleAuthorizationCodeFlow(initializer);

            // Attempt to load existing token from encrypted file
            var token = await TryLoadEncryptedTokensAsync();
            if (token != null)
            {
                var credential = new UserCredential(flow, "CalmCadenceUser", token);
                // Refresh if access token expired
                if (await credential.RefreshTokenAsync(CancellationToken.None))
                {
                    await SaveEncryptedTokensAsync(credential.Token);
                }
                return credential;
            }

            // Fallback: trigger sign-in
            var codeReceiver = new LocalServerCodeReceiver();
            var credentialNew = await GoogleWebAuthorizationBroker.AuthorizeAsync(
                secrets,
                Scopes,
                "CalmCadenceUser",
                CancellationToken.None,
                initializer.DataStore,
                codeReceiver);

            if (credentialNew?.Token != null)
            {
                await SaveEncryptedTokensAsync(credentialNew.Token);
            }
            return credentialNew;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "GetCredentialAsync failed");
            return null;
        }
    }

    private static string GetAppFolder()
    {
        var appData = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), AppFolderName);
        Directory.CreateDirectory(appData);
        return appData;
    }

    private static string GetTokensPath() => Path.Combine(GetAppFolder(), TokensFileName);
    private static string GetClientSecretsPath() => Path.Combine(GetAppFolder(), ClientSecretsFileName);

    private async Task<ClientSecrets?> LoadClientSecretsAsync()
    {
        // Try env vars first
        var clientId = Environment.GetEnvironmentVariable("CALMCADENCE_GOOGLE_CLIENT_ID");
        var clientSecret = Environment.GetEnvironmentVariable("CALMCADENCE_GOOGLE_CLIENT_SECRET");
        if (!string.IsNullOrWhiteSpace(clientId) && !string.IsNullOrWhiteSpace(clientSecret))
        {
            return new ClientSecrets { ClientId = clientId, ClientSecret = clientSecret };
        }

        // Fallback to LocalAppData file
        var path = GetClientSecretsPath();
        if (File.Exists(path))
        {
            using var fs = File.OpenRead(path);
            var doc = await JsonDocument.ParseAsync(fs);
            if (doc.RootElement.TryGetProperty("installed", out var installed))
            {
                var id = installed.GetProperty("client_id").GetString();
                var secret = installed.GetProperty("client_secret").GetString();
                if (!string.IsNullOrWhiteSpace(id) && !string.IsNullOrWhiteSpace(secret))
                    return new ClientSecrets { ClientId = id, ClientSecret = secret };
            }
        }
        return null;
    }

    private static async Task SaveEncryptedTokensAsync(TokenResponse token)
    {
        var json = JsonSerializer.Serialize(token);
        var bytes = System.Text.Encoding.UTF8.GetBytes(json);
        var enc = ProtectedData.Protect(bytes, null, DataProtectionScope.CurrentUser);
        await File.WriteAllBytesAsync(GetTokensPath(), enc);
    }

    private static async Task<TokenResponse?> TryLoadEncryptedTokensAsync()
    {
        var path = GetTokensPath();
        if (!File.Exists(path)) return null;
        try
        {
            var enc = await File.ReadAllBytesAsync(path);
            var dec = ProtectedData.Unprotect(enc, null, DataProtectionScope.CurrentUser);
            var json = System.Text.Encoding.UTF8.GetString(dec);
            var token = JsonSerializer.Deserialize<TokenResponse>(json);
            return token;
        }
        catch
        {
            return null;
        }
    }
}