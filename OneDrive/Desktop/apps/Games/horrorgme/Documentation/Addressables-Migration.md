# Addressables Migration

This repo migrates a small set of runtime assets to Addressables, with a fallback to StreamingAssets when the catalog is missing.

## Package
- [Assumption — Unverified] Adds `com.unity.addressables` to `Packages/manifest.json`.

## Runtime API
- AddressableLoader.LoadAssetAsync<T>(key) — loads by Addressables key, or falls back to StreamingAssets for a few types.
- AddressableLoader.LoadSceneAsync(key) — Addressables scene load.

## Editor helper
- Tools > Addressables > Build Local Catalog builds/rebuilds the local catalog.

## What’s migrated
- Ambient audio pack (e.g., bgm_menu_pad.wav).
- One VFX prefab (developer to mark as addressable in the Addressables Groups window).
- Optional secondary scene chunk if present.

## Fallback
If the Addressables catalog is not available, the loader will attempt to read from StreamingAssets for simple types (e.g., audio via WWW, text via File.ReadAllText).

## How to add assets
1. Open Window > Asset Management > Addressables > Groups.
2. Create or select a group.
3. Drag assets (ambient audio, VFX prefab, scenes) into the group.
4. Note the assigned address/key.
5. Build via Tools > Addressables > Build Local Catalog.

## Testing
- Assets/Tests/AddressableLoaderTests.cs includes a simple fallback test. Extend with specific keys when the catalog is configured.
