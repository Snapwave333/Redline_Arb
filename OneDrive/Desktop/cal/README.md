![Header](https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=12&height=300&section=header&text=CalmCadence&fontSize=70&fontColor=ffffff&animation=twinkling&fontAlignY=38&desc=Your%20Daily%20Productivity%20Companion&descAlignY=55&descSize=20)

<p align="center">
  <img src="./CalmCadence.App/Assets/CalmCadence_HeroLogo.svg" alt="CalmCadence Hero Logo" width="320" />
  <br/>
  <em>Branded hero logo applied across app and packaging.</em>
  <br/>
</p>

<p align="center">
  <a href="https://github.com/Snapwave333/CalmCadence/actions/workflows/main.yml">
    <img src="https://github.com/Snapwave333/CalmCadence/actions/workflows/main.yml/badge.svg" alt="Build Status" />
  </a>
  <a href="https://github.com/Snapwave333/CalmCadence/releases">
    <img src="https://img.shields.io/github/v/release/Snapwave333/CalmCadence?include_prereleases&logo=github&logoColor=white" alt="Latest Release" />
  </a>
  <a href="https://github.com/Snapwave333/CalmCadence/actions/workflows/snake.yml">
    <img src="https://github.com/Snapwave333/CalmCadence/actions/workflows/snake.yml/badge.svg" alt="Snake SVG Workflow" />
  </a>
  <img src="https://img.shields.io/badge/.NET-9.0-512BD4?logo=dotnet&logoColor=white" alt=".NET 9" />
  <img src="https://img.shields.io/badge/WinUI-3-0078D4?logo=windows&logoColor=white" alt="WinUI 3" />
  <img src="https://img.shields.io/badge/Platform-Windows-00A4EF?logo=windows&logoColor=white" alt="Windows" />
  <img src="https://img.shields.io/github/license/Snapwave333/CalmCadence?color=blue&logo=opensourceinitiative&logoColor=white" alt="License" />
</p>

<p align="center">
  <a href="https://github.com/Snapwave333/CalmCadence/stargazers">
    <img src="https://img.shields.io/github/stars/Snapwave333/CalmCadence?style=social" alt="GitHub Stars" />
  </a>
  <a href="https://github.com/Snapwave333/CalmCadence/network/members">
    <img src="https://img.shields.io/github/forks/Snapwave333/CalmCadence?style=social" alt="GitHub Forks" />
  </a>
  <a href="https://github.com/Snapwave333/CalmCadence/watchers">
    <img src="https://img.shields.io/github/watchers/Snapwave333/CalmCadence?style=social" alt="GitHub Watchers" />
  </a>
</p>

# CalmCadence

```yaml
name: CalmCadence
description: Your Daily Productivity Companion
platform: Windows (WinUI 3)
purpose: Unifies tasks, calendar events, routines, and habits into a daily brief
features:
  - Daily brief generation (text, audio, video)
  - Local SQLite database with Entity Framework Core
  - ICS import/export for calendar integration
  - Google Calendar synchronization
  - Gemini AI integration for smart summaries
  - Background scheduling with quiet-hours awareness
  - Multi-tier audio generation (NotebookLM + Gemini TTS)
  - FFmpeg video slideshow generation
architecture: Multi-project .NET solution
target_audience: Productivity enthusiasts and busy professionals
```

> **CalmCadence** transforms your scattered productivity data into a cohesive daily experience. Whether you prefer reading, listening, or watching your daily brief, CalmCadence adapts to your workflow while respecting your focus time and sensory preferences.

## Table of Contents
- Overview
- Features
- Screenshots & Media
- Quick Start
- Configuration
- Architecture
- Video & Audio Pipeline
- Google Integration
- Cutting a Release
- Contributing
- Roadmap

## Overview
This repository is organized as a multi-project .NET solution:
- CalmCadence.App — WinUI 3 desktop application (UI layer)
- CalmCadence.Core — Domain models, interfaces, and services (Gemini, QuickAdd, etc.)
- CalmCadence.Data — EF Core DbContext, model configurations, ICS service, data services
- CalmCadence.Tests — Unit tests for core logic and data

## 🛠️ Tech Stack

<p align="center">
  <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/dotnetcore/dotnetcore-original.svg" alt=".NET" width="60" height="60"/>
  <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/csharp/csharp-original.svg" alt="C#" width="60" height="60"/>
  <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/windows8/windows8-original.svg" alt="WinUI 3" width="60" height="60"/>
  <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/sqlite/sqlite-original.svg" alt="SQLite" width="60" height="60"/>
  <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/google/google-original.svg" alt="Google APIs" width="60" height="60"/>
  <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/git/git-original.svg" alt="Git" width="60" height="60"/>
  <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/github/github-original.svg" alt="GitHub" width="60" height="60"/>
  <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/visualstudio/visualstudio-plain.svg" alt="Visual Studio" width="60" height="60"/>
</p>

<div align="center">

| Framework | Database | Integration | Tools |
|-----------|----------|-------------|-------|
| .NET 9 | Entity Framework Core | Google Calendar API | FFMpegCore |
| WinUI 3 | SQLite | Ical.Net (ICS) | System.Speech |
| CommunityToolkit.Mvvm | - | Gemini AI | Microsoft.Extensions.Hosting |

</div>

## Features
- Daily Brief generation: summary, agenda, top tasks, habit status
- Multi-tier audio brief generation: NotebookLM (primary) with Gemini TTS fallback; offline fallback when APIs are unavailable
- Agenda generation from Tasks, Events, Routines, Habits
- ICS import/export (SimpleIcsService)
- Notification scheduling respecting Quiet Hours and Low Sensory mode
- Local SQLite storage in %LocalAppData%/CalmCadence/calmcadence.db
- Optional slideshow video generation (FFmpeg) with audio mux

## Screenshots & Media
- Branding: see CalmCadence_Branding_Pack for icons and hero artwork.
- Daily Studio playback uses MediaPlayerElement to play the generated video (preferred) or audio-only brief.

## Quick Start
Prerequisites:
- Windows 10 (build 19041) or later
- .NET SDK 9.0
- Visual Studio 2022 (17.10+) with .NET Desktop workload
- Windows App SDK and WebView2 runtime
- PowerShell 7+
- Optional: FFmpeg on PATH (for video generation), Google OAuth credentials

Build & Test:
```powershell
# From repository root

# Restore & build entire solution
dotnet restore
dotnet build CalmCadence.sln -c Release

# Run tests
dotnet test CalmCadence.Tests/CalmCadence.Tests.csproj -c Release
```

Run (IDE):
- Open CalmCadence.sln in Visual Studio and press F5.

## Configuration
- Database path: %LocalAppData%/CalmCadence/calmcadence.db
- Settings are stored in the database (Quiet Hours, Low Sensory mode, Daily Studio options)
- Gemini and Google APIs are optional; configure via your own credentials and secure storage

### EF Core
CalmCadence.Data uses EF Core (SQLite). If you need migrations, ensure the dotnet-ef tool is installed:
```powershell
# Install EF Core tooling
dotnet tool install --global dotnet-ef

# Create migration (example)
dotnet ef migrations add InitialCreate --project CalmCadence.Data

# Update database
dotnet ef database update --project CalmCadence.Data
```

## Architecture
- CalmCadence.App
  - App startup and DI
  - Views (DailyStudioPage, MainPage, GoogleIntegrationPage, Routine pages)
  - Services (DailyStudioService, AgendaGenerator, NotificationService)
- CalmCadence.Core
  - Interfaces (IDailyStudioService, IAgendaGenerator, INotificationService, IGeminiService, ICalendarService, etc.)
  - Models (TaskItem, EventItem, Habit, HabitLog, DailyMedia, Settings, BriefInput/Output)
  - Services (GeminiService, QuickAddParser, GoogleApiService)
- CalmCadence.Data
  - EF Core DbContext and configurations
  - Services (DailyStudioService for data-backed brief, SimpleIcsService)
- CalmCadence.Tests
  - Unit tests for core/data services

## Video & Audio Pipeline
- Slideshow video (1920×1080) from the brief (Summary, Agenda, Top Tasks, Habits, Notes)
- Slides rendered with System.Drawing, assembled with FFmpeg into MP4 (H.264, yuv420p, ~6s/slide @ 30fps)
- If an audio brief exists for the date, it is muxed into the video (AAC)
- Output path: `%LocalAppData%/CalmCadence/DailyMedia/daily-brief-YYYY-MM-DD.mp4`
- Slides staged under: `%LocalAppData%/CalmCadence/DailyMedia/YYYY-MM-DD/slides/`
- Requirement: FFmpeg on PATH (`ffmpeg`). If FFmpeg is not found or fails, the app gracefully skips video creation and keeps the audio-only brief.

## Google Integration (OAuth + Sync)
CalmCadence supports Google Calendar OAuth sign-in and bi-directional sync.
A dedicated UI page is available: Main Page → Google Integration.

Setup:
- Create OAuth 2.0 Client credentials (Desktop app) in Google Cloud Console.
- Set environment variables for the app to locate client secrets:
  - `CALMCADENCE_GOOGLE_CLIENT_ID`
  - `CALMCADENCE_GOOGLE_CLIENT_SECRET`
- Optional: Instead of env vars, place a JSON file at:
  - `%LocalAppData%/CalmCadence/google_client_secrets.json`
  - Use the standard "installed" client format with client_id and client_secret.

Using the Google Integration page:
- Sign in with Google: launches browser-based OAuth and stores an encrypted refresh token.
- Sign out: removes the stored token.
- Sync Now: executes a sync for the last 7 days and the next 7 days.
- Status text indicates whether a user is signed in.

Notes:
- Tokens are encrypted per-user using Windows DPAPI and stored under:
  - `%LocalAppData%/CalmCadence/google_oauth_tokens.json.enc`
- The provider uses your primary calendar by default.
- Headless sync is supported via command-line: `CalmCadence.App.exe --run-google-sync`

## Cutting a Release
CalmCadence uses Git tags to produce versioned, signed MSIX bundles and a GitHub Release automatically.

Prerequisites:
- GitHub Secrets in the repository settings:
  - `BASE64_ENCODED_PFX` (required to sign) — your code-signing certificate as base64-encoded `.pfx`
  - `PFX_PASSWORD` (optional) — password for the `.pfx`, if applicable
- Optional: ensure FFmpeg is available on development machines for local video generation (not required for CI).

Tag formats:
- Stable release: `vMAJOR.MINOR.PATCH` (e.g., `v1.0.0`)
- Pre-release: `vMAJOR.MINOR.PATCH-rc.N` or `vMAJOR.MINOR.PATCH-beta.N` (e.g., `v1.0.0-rc.1`)

Steps to cut a release:
```powershell
# From repository root

# Create and push a stable tag
git tag v1.0.0
git push origin v1.0.0

# Or create and push a pre-release tag
git tag v1.0.0-rc.1
git push origin v1.0.0-rc.1
```

What the pipeline does on tag builds:
- Stamps assemblies with `Version = X.Y.Z` and `AssemblyInformationalVersion = X.Y.Z+<commit SHA>`
- Produces MSIX packages with 4-part version: `X.Y.Z.<run_number>` (required by MSIX)
- Signs MSIX artifacts if `BASE64_ENCODED_PFX` is present (uses `PFX_PASSWORD` if provided)
- Computes SHA256 checksums for each package
- Publishes a GitHub Release attached to the tag, including:
  - `CalmCadence-x64-MSIX` and `CalmCadence-ARM64-MSIX` artifacts
  - `.sha256` checksum files for integrity verification
- Marks the release as a pre-release if the tag contains a hyphen (e.g., `-rc.1`)

Verification:
- Download artifacts from the GitHub Release page and install `.msix`
- In Windows Settings → Apps → CalmCadence, confirm the version shows `X.Y.Z.<run_number>`
- Launch the app and verify Daily Studio playback and OAuth flows in the packaged environment

Notes:
- Local/dev builds use defaults defined in `Directory.Build.props` (e.g., `0.1.0-dev`) unless overridden
- If no signing certificate is provided, MSIX artifacts are unsigned but still published
- Ensure the Windows SDK is available on the CI runner for SignTool; this is provided by `windows-latest`

## Contributing
- Submit PRs with tests where appropriate.
- Follow .NET coding guidelines and keep domain logic in Core, data access in Data, and UI in App.
- Keep changes small and focused; prefer minimal diffs and add validation steps.

## Roadmap (Planned / In Progress)
- Video generation: FFmpeg slideshow pipeline
- Live on-screen notifications: Windows App SDK AppNotification (toasts)
- Background scheduling: automatic daily brief generation at a configured time

---

## Deployment & GitHub Integration

### Contribution Snake (SVG)
The repository auto-generates contribution snake SVGs and publishes them to the `output` branch.

- SVG URLs used in README:
  - Light: `https://raw.githubusercontent.com/Snapwave333/CalmCadence/output/github-contribution-grid-snake.svg`
  - Dark: `https://raw.githubusercontent.com/Snapwave333/CalmCadence/output/github-contribution-grid-snake-dark.svg`

Workflow details:
- File: `.github/workflows/snake.yml`
- Triggers: daily schedule, manual dispatch, and pushes to `main`
- Permissions: explicitly grants `contents: write` and validates `GITHUB_TOKEN`

To test end-to-end:
1) Manually run the workflow from the Actions tab (Generate Contribution Snake).
2) Confirm the `output` branch updated with `dist/` SVG assets.
3) Verify README images render correctly.

### Release Pipeline & Environment Variables
The main CI workflow builds, tests, packages MSIX, and publishes GitHub Releases on tags.

- File: `.github/workflows/main.yml`
- Permissions: `contents: write` for release publishing.
- Required secrets (Repository Settings → Secrets and variables → Actions):
  - `BASE64_ENCODED_PFX` (optional for signing)
  - `PFX_PASSWORD` (optional)

Error handling:
- Release job validates `GITHUB_TOKEN` presence and provides a clear failure message if missing.
- MSIX signing steps are conditional; builds succeed even without signing secrets.

### Branding Application of Icons & Color Scheme
- Branded icons copied into app assets:
  - `CalmCadence.App/Assets/CalmCadence_Icon.png`
  - `CalmCadence.App/Assets/CalmCadence_Icon.ico`
  - `CalmCadence.App/Assets/CalmCadence_HeroLogo.svg`
- Packaging manifest updated to use branded icon paths for StoreLogo, tiles, and splash screen.
- Brand resource dictionary: `CalmCadence.App/Styles/Brand.xaml`
  - Tokens: `BrandPrimary`, `BrandSecondary`, `BrandAccent`, `BrandForeground`, `BrandBackground`
  - Brushes and base styles applied via `App.xaml` merged dictionaries.

Verification steps:
1) Build the app in Release mode.
2) Confirm Start menu tile, app list icon, and splash use the CalmCadence icon.
3) Inspect UI buttons and headers to ensure brand colors render consistently.

### Notes on package.json
This repository is a .NET WinUI solution; it does not use `package.json`. The contribution snake is driven entirely by a GitHub Actions workflow and does not require Node dependencies.
- Calendar sync: additional providers beyond ICS, e.g., Google Calendar
- Audio pipeline: Multi-tier approach (NotebookLM primary, Gemini TTS fallback; offline fallback)

---

## 📊 Repository Insights

<div align="center">
  <table>
    <tr>
      <td>
        <img src="https://github-readme-stats.vercel.app/api?username=Snapwave333&show_icons=true&theme=catppuccin_mocha&hide_border=true&count_private=true" alt="GitHub Stats" />
      </td>
      <td>
        <img src="https://github-readme-stats.vercel.app/api/top-langs/?username=Snapwave333&layout=compact&theme=catppuccin_mocha&hide_border=true&langs_count=8" alt="Top Languages" />
      </td>
    </tr>
  </table>

  <img src="https://github-readme-streak-stats.herokuapp.com/?user=Snapwave333&theme=catppuccin&hide_border=true" alt="GitHub Streak" />
</div>

---

### Contribution Grid Snake

<div align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/Snapwave333/CalmCadence/output/github-contribution-grid-snake-dark.svg">
    <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/Snapwave333/CalmCadence/output/github-contribution-grid-snake.svg">
    <img alt="GitHub contribution grid snake animation" src="https://raw.githubusercontent.com/Snapwave333/CalmCadence/output/github-contribution-grid-snake.svg">
  </picture>
</div>

---

<div align="center">
  <img src="https://komarev.com/ghpvc/?username=Snapwave333&color=blueviolet&style=flat-square&label=Profile+Views" alt="Profile Views" />
</div>

<div align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/Snapwave333/Snapwave333/output/github-contribution-grid-snake-dark.svg">
    <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/Snapwave333/Snapwave333/output/github-contribution-grid-snake.svg">
    <img alt="github contribution grid snake animation" src="https://raw.githubusercontent.com/Snapwave333/Snapwave333/output/github-contribution-grid-snake.svg">
  </picture>
</div>

## CI
GitHub Actions workflow is defined at `.github/workflows/main.yml` and runs build + tests.

---

Run & Verify
```powershell
# Build & test
dotnet restore
dotnet build CalmCadence.sln -c Release
dotnet test CalmCadence.Tests/CalmCadence.Tests.csproj -c Release

# Launch the WinUI app via IDE (Visual Studio) and open the Daily Studio page.
```

