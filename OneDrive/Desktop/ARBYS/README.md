<!-- hero -->

<div align="center">

  <picture>

    <source media="(prefers-color-scheme: dark)" srcset="./GitHub_README_Assets/logo_dark.svg" />

    <source media="(prefers-color-scheme: light)" srcset="./GitHub_README_Assets/logo_light.svg" />

    <img alt="Redline Arbitrage Logo" src="./GitHub_README_Assets/logo_light.svg" width="160" />

  </picture>

  <br/>

  <img src="./GitHub_README_Assets/readme_banner.png" alt="Redline Arbitrage Banner" width="100%" />

  <p>

    <a href="https://github.com/Snapwave333/Redline_Arb/actions/workflows/ci-windows.yml">

      <img alt="Build" src="https://img.shields.io/github/actions/workflow/status/Snapwave333/Redline_Arb/ci-windows.yml?label=CI&logo=githubactions&labelColor=%230D0D0F&color=%23FF0033" />

    </a>

    <img alt="Python" src="https://img.shields.io/badge/Python-3.10%2B-%23FF0033?logo=python&labelColor=%230D0D0F&color=%23FF0033" />

    <img alt="GUI" src="https://img.shields.io/badge/GUI-PyQt6-%23FF0033?logo=qt&labelColor=%230D0D0F&color=%23FF0033" />

    <img alt="License" src="https://img.shields.io/badge/License-MIT-%23FF0033?labelColor=%230D0D0F&color=%23FF0033" />

    <a href="https://github.com/Snapwave333/Redline_Arb/releases/tag/v1.2.1">

      <img alt="Release" src="https://img.shields.io/badge/Release-v1.2.1-%23FF0033?labelColor=%230D0D0F&logo=github" />

    </a>

  </p>

</div>

---

# 🏎️ Redline Arbitrage

**Precision sports-arbitrage engine with a modern PyQt6 interface.**  

Built for **fast market scanning**, **account-health monitoring**, and **one-click execution**—presented in the Redline palette (`#FF0033 / #0D0D0F / #FFFFFF`).

> **Scope & Compliance:** Sportsbooks only. **No DeFi/crypto/meme-coin content.** Windows 10/11 desktop focused.

---

## 🚀 Quick Links

- 📦 **Latest Release v1.2.1** → https://github.com/Snapwave333/Redline_Arb/releases/tag/v1.2.1  

- ⬇️ **Windows Portable ZIP (x64)** → `Redline_Arbitrage_1.2.1_Windows_x64.zip`  

- 📚 **Install Guide (Windows)** → [`docs/setup/INSTALL_DESKTOP_WINDOWS.md`](docs/setup/INSTALL_DESKTOP_WINDOWS.md)  

- 🔧 **Backend API (optional)** → [`apps/backend/api_server.py`](apps/backend/api_server.py)  

- 🧪 **Checksums** → `SHA256SUMS_v1.2.1.txt`  

---

## 🧭 Table of Contents

<details>

<summary>Expand</summary>

- [Why Redline](#-why-redline)

- [Key Features](#-key-features)

- [Screenshots](#-screenshots)

- [Install & Run (Windows)](#-install--run-windows)

- [Environment (.env)](#-environment-env)

- [Packaging (Windows)](#-packaging-windows)

- [Backend API Server (optional)](#-backend-api-server-optional)

- [Provider Configuration](#-provider-configuration)

- [Tech Stack](#-tech-stack)

- [Roadmap](#-roadmap)

- [Contributing](#-contributing)

- [Troubleshooting](#-troubleshooting)

- [License](#-license)

- [Contact](#-contact)

</details>

---

## 💡 Why Redline

Live sports-arbitrage tooling is often fragile, slow, and visually dated. **Redline Arbitrage** ships with a **performant orchestrator**, a **polished PyQt6 GUI**, and **production-minded packaging**—so you can research and act quickly with confidence.

---

## ✅ Key Features

- ⚡ **High-Performance Orchestrator** – multi-provider aggregation with async-ready variants  

- 📈 **Arbitrage Calc + Stake Distribution** – optimized stake suggestions  

- 🧬 **Account Health Scoring** – dashboard widgets to guide risk decisions  

- 🧩 **Modular Providers** – SofaScore (free), API-Sports, The Odds API, etc.  

- 💾 **Historical Storage Utilities** – keep a trail for analysis and validation  

- 🎛️ **Modern 2025 Design System** – Light/Dark themes with design tokens, Rajdhani/Orbitron typography, carbon-fiber UI accents  

- 🪪 **Onboarding & Setup Wizard** – first-run flow and splash  

- ♿ **Accessibility Features** – keyboard navigation, focus indicators, screen reader support  

- 🧪 **Comprehensive Tests** – unit, perf, integration  

- 📦 **Windows Builds** – portable ZIP + installer scripts  

- 🏷️ **Filters "Modified" Pill** – quick diff of current vs. saved sportsbook filters (hover tooltip)

---

## 🎬 Screenshots

<div align="center">

  <img src="./preview_ui.png" alt="UI Preview" />

  <br/><br/>

  <img src="./GitHub_README_Assets/social_preview.png" alt="Social Preview" />

</div>

Additional previews:

<div align="center">

  <table>

    <tr>

      <td><img src="./previews/main_window.png" alt="Main Window" width="420"/></td>

    </tr>

    <tr>

      <td><img src="./previews/firstday_slideshow.png" alt="First-Day Slideshow" width="420"/></td>

      <td><img src="./previews/tutorial_overlay.png" alt="Tutorial Overlay" width="420"/></td>

    </tr>

  </table>

  <br/>

  <sub>Generated via <code>scripts/gui_preview_capture.py</code></sub>

</div>

---

## 📥 Install & Run (Windows)

### Option A — Quick Start (2 minutes)

- **Portable ZIP** (v1.2.1): Download, extract, run the EXE inside  

- **Guide:** [`docs/setup/INSTALL_DESKTOP_WINDOWS.md`](docs/setup/INSTALL_DESKTOP_WINDOWS.md)  

- **Checksums:** `SHA256SUMS_v1.2.1.txt`

### Option B — From Source

```powershell
git clone https://github.com/Snapwave333/Redline_Arb.git
cd Redline_Arb
python -m venv .venv310
.venv310\Scripts\activate
pip install -r requirements.txt
python apps\desktop\main.py
```

> **Tip:** "Production Skip Mode" (suppresses onboarding)
>
> ```powershell
> $env:ARBYS_SUPPRESS_WIZARD="1"; python apps\desktop\main.py
> ```

---

## 🔧 Environment (.env)

Both Desktop and Backend auto-load **`.env`** (via `python-dotenv`).

* Copy `env.example` → `.env` (if available)

* Set optional keys for paid providers:

```powershell
$env:API_SPORTS_KEY   = "<your api-sports key>"
$env:THE_ODDS_API_KEY = "<your the-odds-api key>"
$env:ARBYS_BACKEND_URL = "http://localhost:5000"
```

Key entries:

* `ARBYS_BACKEND_URL` – backend health & opportunities endpoint

* `API_SPORTS_KEY` / `THE_ODDS_API_KEY` – unlock broader coverage

* `SOFASCORE_ENABLED` – `1` (default) for the free scraper

* `ARBYS_THEME` – `light`, `dark`, or `system` (default: `system`)

---

## 📦 Packaging (Windows)

Build with PyInstaller using PowerShell:

```powershell
# From project root
.venv310\Scripts\activate
pwsh -File scripts\windows\build.ps1
```

Output: `dist\Redline_Arbitrage_1.2.1_Windows_x64\`

If `dist/` is empty, Windows Defender likely blocked resource injection—add a temporary exclusion and re-run.

---

## 🌐 Backend API Server (optional)

Run the Flask REST API for enhanced aggregation:

```powershell
python apps\backend\api_server.py
# http://127.0.0.1:5000
```

Endpoints:

* `GET /api/health`

* `GET /api/opportunities?sport=soccer&min_profit_pct=1.0&limit=100&include_raw=false`

Providers:

* SofaScore (free, enabled by default)

* API-Sports (key)

* TheOddsAPI (key)

---

## 🔌 Provider Configuration

**In-App (recommended):** Settings → API Providers → Add key(s) → Enable → Restart

**CLI helper:**

```powershell
python scripts/configure_api_sports.py --api-key YOUR_APISPORTS_KEY
```

Keeps SofaScore as free fallback, mirrors key to `.env`.

---

## 🧱 Tech Stack

* **Python 3.10+**, **PyQt6** (GUI)

* **AioHTTP / Requests**, **NumPy**, **BeautifulSoup4**

* **PyInstaller**, **Inno Setup**

* **GitHub Actions CI** (Windows)

* **Design Tokens** (JSON-based theming system)

---

## 🗺️ Roadmap

* Multi-API expansion & failover improvements

* Performance benchmarks & profiling

* Structured error/state management (datatable/struct-driven)

* UI lighting/theme presets

* Additional scrapers & providers

(See [`docs/features/MULTI_API_ENHANCEMENT.md`](docs/features/MULTI_API_ENHANCEMENT.md), [`docs/features/PERFORMANCE_OPTIMIZATION.md`](docs/features/PERFORMANCE_OPTIMIZATION.md), [`docs/archive/PHASE2_STATUS.md`](docs/archive/PHASE2_STATUS.md).)

---

## 🤝 Contributing

```powershell
python -m pip install nox
nox  # run linting, tests, quality checks
```

* **Formatting:** Black + isort

* **Linting:** Ruff

* **Types:** MyPy (strict)

* **Tests:** PyTest (unit/perf/integration)

See [`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md) for detailed guidelines.

---

## 🛠 Troubleshooting

* **Empty dashboard after skipping onboarding**

  Ensure `ARBYS_SUPPRESS_WIZARD=1`. Use "Refresh Now." Free SofaScore can rate-limit—add a paid provider.

* **Empty `dist/` after build**

  Likely Windows Defender blocked resource injection—add a temporary folder exclusion and rebuild.

* **Backend health warnings**

  Expected in offline/dev environments; they don't block the GUI.

* **`ModuleNotFoundError: No module named 'json'`**

  Ensure `config/__init__.py` exists and rebuild. The `.spec` file should include standard library modules in `hiddenimports`.

---

## ✅ License

MIT License — see `LICENSE` file for details.

---

## 📬 Contact

Open a GitHub issue for support/requests.

Security concerns → private issue.

---

<div align="center">

  <picture>

    <source media="(prefers-color-scheme: dark)" srcset="./GitHub_README_Assets/logo_dark.svg" />

    <source media="(prefers-color-scheme: light)" srcset="./GitHub_README_Assets/logo_light.svg" />

    <img alt="Redline Arbitrage Logo" src="./GitHub_README_Assets/logo_light.svg" width="120" />

  </picture>

  <br/>

  <sub>Built with ❤️ — Snapwave333F</sub>

</div>
