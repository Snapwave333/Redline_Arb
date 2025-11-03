# ARBYS Backend Flask API Server (Windows x86)

Real-data backend for serving arbitrage opportunities to the Desktop client and the Mobile Web App. This server enforces the REAL_DATA_ONLY policy: no prefabs, no placeholders, no mock or synthetic data — all opportunities are computed from real provider odds.

## Prerequisites

- Windows x86 (64-bit) with Python 3.10+ installed and on PATH
- pip and a working internet connection
- Optional: API keys for paid providers

## Installation

1) Create and activate a virtual environment (recommended):

```powershell
# From project root
python -m venv .venv_backend
.venv_backend\Scripts\activate
```

2) Install dependencies:

```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

Flask and CORS are included in the requirements; if you need to ensure they’re present:

```powershell
pip install Flask Flask-Cors
```

## Provider Configuration (Real Data)

The backend uses real providers via the MultiAPIOrchestrator:

- SofaScoreScraperProvider (free; enabled by default)
- APISportsProvider (requires API key; optional)
- TheOddsAPIProvider (requires API key; optional)

Set environment variables to enable paid providers:

```powershell
$env:API_SPORTS_KEY = "<your api-sports key>"
$env:THE_ODDS_API_KEY = "<your the-odds-api key>"
```

SofaScore is enabled by default. To disable it:

```powershell
$env:SOFASCORE_ENABLED = "0"
```

## Run the Server

Start the backend Flask server:

```powershell
python backend\api_server.py
# Server runs at http://127.0.0.1:5000
```

Alternatively, use the helper script which sets up a venv and launches the server in a separate console window:

```powershell
scripts\backend_install.bat
```

## Endpoints

- GET `/api/health`
  - Returns server status, version, and per-provider health metrics.

- GET `/api/opportunities`
  - Query parameters:
    - `sport` (string; default `soccer`). Other sports require paid providers configured.
    - `min_profit_pct` (float; default `1.0`). Minimum arbitrage profit percentage to include.
    - `limit` (int; default `100`, max `500`). Max number of opportunities to return.
    - `include_raw` (bool; default `false`). Include normalized per-provider raw data.
  - Returns JSON with keys: `count`, `sport`, `min_profit_pct`, `latency`, `errors`, `opportunities`.

## Quick Test

Test the health endpoint:

```powershell
curl http://127.0.0.1:5000/api/health
```

Test opportunities for soccer (free provider):

```powershell
curl "http://127.0.0.1:5000/api/opportunities?sport=soccer&min_profit_pct=1.0&limit=50"
```

If you set API keys for paid providers, repeat the test for other sports:

```powershell
curl "http://127.0.0.1:5000/api/opportunities?sport=basketball&min_profit_pct=1.0&limit=50"
```

## Notes

- REAL_DATA_ONLY: The server never generates synthetic or placeholder data. All opportunities are derived from real provider odds.
- CORS is enabled for browser-based clients.
- If no API keys are provided, only SofaScoreScraperProvider will be active; some sports may return zero opportunities depending on market conditions.
- Logs print provider enablement and error messages to the console.

