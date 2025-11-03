# Redline Arbitrage v1.2.1

Release date: (YYYY-MM-DD)

## Highlights

- Desktop GUI: Backend health indicator wired by default
  - Provider panel footer shows backend health on startup and updates every 60 seconds
  - Tooltip displays backend version and last update time (e.g., "Updated 3m ago")

- Backend Flask API: .env auto-loading
  - `python-dotenv` loads `.env` automatically for easier Windows setup
  - Works alongside PowerShell `$env:` variables

- Windows-friendly `.env` example and documentation improvements
  - Added Environment (.env) setup section in `README.md` with PowerShell tips
  - `backend/README.md` now references `env.example` and `.env` usage

- Source ZIPs rebuilt
  - `release_assets/backend_source_windows_x86.zip`
  - `release_assets/desktop_source_windows_x86.zip`

## How to Run (from source)

### Backend (Flask API)

```powershell
.\.venv310\Scripts\activate
python backend\api_server.py
# Visit http://127.0.0.1:5000/api/health
```

Configure providers via `.env` (recommended) or PowerShell session variables:

```powershell
# .env entries (copy env.example to .env and set values)
ARBYS_BACKEND_URL=http://localhost:5000
API_SPORTS_KEY=<your api-sports key>
THE_ODDS_API_KEY=<your the-odds-api key>
SOFASCORE_ENABLED=1

# Or PowerShell session variables
$env:API_SPORTS_KEY   = "<your api-sports key>"
$env:THE_ODDS_API_KEY = "<your the-odds-api key>"
$env:ARBYS_BACKEND_URL = "http://localhost:5000"
```

### Desktop GUI

```powershell
.\.venv310\Scripts\activate
python main.py
```

Ensure the backend is running (above) for live health and opportunities.

## Notes

- REAL_DATA_ONLY: No mock/synthetic data anywhere. Opportunities are computed from real providers.
- Mobile/web pipelines are paused; focus is on desktop and backend for this release.

## Changes Summary

- GUI: `create_provider_status_panel` includes backend label; `update_backend_health` uses `ARBYS_BACKEND_URL` env and runs on startup + timer
- Backend: loads `.env` at import via `python-dotenv`
- Docs: README adds Environment (.env) section; backend README references env.example
- Version: bumped to `v1.2.1`