using UnityEditor;
using UnityEngine;
using UnityEngine.UI;

/// <summary>
/// Applies sprites from Assets/oakhaven_ui_spritepack/svgs to DevOverlay UI at runtime in Editor.
/// This is Editor-only and non-destructive to prefabs.
/// </summary>
[InitializeOnLoad]
public static class DevOverlaySkinner
{
    static DevOverlaySkinner()
    {
        EditorApplication.playModeStateChanged += OnPlayMode;
    }

    private static void OnPlayMode(PlayModeStateChange state)
    {
        if (state != PlayModeStateChange.EnteredPlayMode) return;
        ApplySkin();
    }

    public static void ApplySkin()
    {
        var dc = Object.FindFirstObjectByType<DevConsole>();
        if (dc == null) return;

        // Load SVGs as Sprites via Vector Graphics
        var panel = LoadSprite("Assets/oakhaven_ui_spritepack/svgs/menu_panel.svg");
        var btnPrimary = LoadSprite("Assets/oakhaven_ui_spritepack/svgs/btn_primary.svg");
        var btnSecondary = LoadSprite("Assets/oakhaven_ui_spritepack/svgs/btn_secondary.svg");
        var inputBg = LoadSprite("Assets/oakhaven_ui_spritepack/svgs/dialog_box.svg");

        if (dc.rootPanel != null)
        {
            var img = dc.rootPanel.GetComponent<Image>();
            if (img != null && panel != null) img.sprite = panel;
        }
        if (dc.toggleButton != null)
        {
            var img = dc.toggleButton.GetComponent<Image>();
            if (img != null && btnSecondary != null) img.sprite = btnSecondary;
        }
        if (dc.commandInput != null)
        {
            var img = dc.commandInput.GetComponent<Image>();
            if (img != null && inputBg != null) img.sprite = inputBg;
        }
        if (dc.commandFilterInput != null)
        {
            var img = dc.commandFilterInput.GetComponent<Image>();
            if (img != null && inputBg != null) img.sprite = inputBg;
        }
    }

    private static Sprite LoadSprite(string assetPath)
    {
        // Load directly as Sprite (requires SVG importer from Vector Graphics package)
        var s = AssetDatabase.LoadAssetAtPath<Sprite>(assetPath);
        return s;
    }
}


