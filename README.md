<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=0:6a11cb,100:2575fc&height=140&section=header&text=Oakhaven's%20Point&fontColor=ffffff&fontSize=36&animation=fadeIn" alt="Header" />
</p>

<div align="center">

[![Unity](https://img.shields.io/badge/Unity-6000.2.6f1-000000?logo=unity&logoColor=white)](https://unity.com/releases/editor/whats-new/6000.2)
[![Platforms](https://img.shields.io/badge/Platforms-Windows%20%7C%20Android-444)](https://unity.com)
[![CI](https://github.com/Snapwave333/OakhavensPoint/actions/workflows/unity-ci.yml/badge.svg)](https://github.com/Snapwave333/OakhavensPoint/actions)
[![License](https://img.shields.io/badge/License-Proprietary-red)](#license)

</div>

<div align="center">

Atmospheric horror narrative built with Unity 6. Fast iteration developer overlay, save/checkpoint system, addressables-ready runtime, and batteries‑included dev tooling.

</div>

<br/>

## ✨ Highlights
- Toggleable developer overlay and in‑game console (tilde) with attribute‑based commands
- JSON save/checkpoint system with migration, defaults, and pause save/load stub
- Addressables loader with StreamingAssets fallback and editor catalog build helper
- Editor tools: asset generators, crash/log uploader, screenshot tool, CI-ready tests

## 📸 Glimpse
<p align="center">
  <img src="Assets/Images/oakhaven_landscape.png" alt="Oakhaven Landscape" width="640"/>
</p>

## 🚀 Quick start
1. Install Unity 6 (Editor 6000.2.6f1)
2. Open the project with Unity Hub
3. Open `Assets/Scenes/Game.unity`
4. Press Play

## 🔧 Build
- Manual: `File > Build Settings… > Standalone Windows 64 > Build`
- One‑click: `Tools > Build > Create Scene and Build` (outputs `Builds/Windows/HorrorGame.exe`)

## 🧰 Developer tools
- Dev Overlay/Console: press `~` (see `Documentation/HowToUseDebugOverlay.md`)
- Asset Generators: `Tools > Assets > Asset Generator` (Python/Node)
- Crash/Log Uploader: opt‑in; run mock server `python tools/log_uploader_mock_server.py`
- Screenshots: press `F12` (saved under `Documentation/media/screenshots/`)
- Settings Menu: press `F9` (volume, subtitles, graphics presets)

## 🧱 Tech stack
<p>
  <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/unity/unity-original.svg" width="40" title="Unity"/>
  <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/csharp/csharp-original.svg" width="40" title="C#"/>
  <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/python/python-original.svg" width="40" title="Python"/>
  <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/nodejs/nodejs-original.svg" width="40" title="Node.js"/>
</p>

## 🗂️ Structure
```
Assets/
├─ Scenes/Game.unity
├─ Scripts/
│  ├─ Dev/…          # Overlay, console, screenshots
│  ├─ Save/…         # SaveManager, SaveData, defaults
│  ├─ Addressables/… # Loader (with fallback)
│  ├─ Interactions/… # IInteractable + base
│  ├─ Choice/…       # ChoiceManager
│  ├─ UI/…           # Settings
│  └─ Telemetry/…    # Logs, analytics
├─ Editor/…          # Build helpers, generators, addressables
└─ StreamingAssets/… # Runtime packs
Documentation/…      # How‑tos, CI, media, etc.
```

## 📚 Documentation
- Debug overlay: `Documentation/HowToUseDebugOverlay.md`
- Save system: `Documentation/SaveSystem.md`
- Addressables: `Documentation/Addressables-Migration.md`
- Asset generators: `Documentation/AssetGenerator.md`
- Crash reporting: `Documentation/CrashReporting.md`
- Interactions: `Documentation/Interactions.md`
- Accessibility/UX: `Documentation/Accessibility.md`
- Media capture: `Documentation/Media.md`
- CI: `Documentation/CI.md`
- Contributors quickstart: `Documentation/Contributors-Quickstart.md`

## 🙌 Contributing
PRs welcome. Please keep changes minimal and backwards‑compatible; add tests and docs for new public APIs. See `Documentation/Contributors-Quickstart.md`.

## 📝 License
Proprietary — all rights reserved.

<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=0:2575fc,100:6a11cb&height=100&section=footer&animation=fadeIn" alt="Footer" />
</p>

---

Inspiration: Profile‑style README layout and visuals adapted from design ideas in “How to Design an Attractive GitHub Profile Readme…” by Piyush Malhotra. See the article for styling concepts and resources: [medium.com/design-bootcamp/how-to-design-an-attractive-github-profile-readme-3618d6c53783](https://medium.com/design-bootcamp/how-to-design-an-attractive-github-profile-readme-3618d6c53783)