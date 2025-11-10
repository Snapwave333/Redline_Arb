using UnityEditor;

public static class BuildAddressablesCatalog
{
#if ADDRESSABLES
    [MenuItem("Tools/Addressables/Build Local Catalog")]
    public static void BuildLocalCatalog()
    {
        UnityEditor.AddressableAssets.Settings.AddressableAssetSettings.BuildPlayerContent();
    }
#else
    [MenuItem("Tools/Addressables/Build Local Catalog")]
    public static void BuildLocalCatalog()
    {
        UnityEngine.Debug.LogWarning("[Assumption — Unverified] Addressables package not active. Install com.unity.addressables.");
    }
#endif
}


