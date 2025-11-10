using System;
using System.Collections;
using System.IO;
using System.Threading.Tasks;
using UnityEngine;

#if ADDRESSABLES
using UnityEngine.AddressableAssets;
using UnityEngine.ResourceManagement.AsyncOperations;
#endif

/// <summary>
/// Lightweight loader that prefers Addressables if available, otherwise falls back to StreamingAssets.
/// </summary>
public static class AddressableLoader
{
    public static async Task<T> LoadAssetAsync<T>(string keyOrPath) where T : UnityEngine.Object
    {
#if ADDRESSABLES
        try
        {
            AsyncOperationHandle<T> handle = Addressables.LoadAssetAsync<T>(keyOrPath);
            return await handle.Task;
        }
        catch (Exception)
        {
            // fall through to fallback
        }
#endif
        // Fallback: simple StreamingAssets path for TextAsset/AudioClip via WWW
        return await LoadFromStreamingAssets<T>(keyOrPath);
    }

    public static async Task<bool> LoadSceneAsync(string keyOrPath)
    {
#if ADDRESSABLES
        try
        {
            var handle = UnityEngine.AddressableAssets.Addressables.LoadSceneAsync(keyOrPath);
            await handle.Task;
            return handle.Status == UnityEngine.ResourceManagement.AsyncOperations.AsyncOperationStatus.Succeeded;
        }
        catch (Exception)
        {
        }
#endif
        await Task.Yield();
        return false;
    }

    private static async Task<T> LoadFromStreamingAssets<T>(string relativePath) where T : UnityEngine.Object
    {
        var fullPath = Path.Combine(Application.streamingAssetsPath, relativePath);
        if (typeof(T) == typeof(AudioClip))
        {
            var req = UnityEngine.Networking.UnityWebRequestMultimedia.GetAudioClip("file://" + fullPath, AudioType.WAV);
            await req.SendWebRequest();
#if UNITY_2020_2_OR_NEWER
            if (req.result != UnityEngine.Networking.UnityWebRequest.Result.Success)
#else
            if (req.isNetworkError || req.isHttpError)
#endif
            {
                return null;
            }
            var clip = UnityEngine.Networking.DownloadHandlerAudioClip.GetContent(req);
            return clip as T;
        }
        if (typeof(T) == typeof(TextAsset))
        {
            var text = File.Exists(fullPath) ? File.ReadAllText(fullPath) : null;
            if (text == null) return null;
            var ta = new TextAsset(text);
            return ta as T;
        }
        return null;
    }
}


