# Install Guide: Backend Flask API (Windows x86)

This guide installs and runs the ARBYS Backend Flask API on Windows. The backend provides real arbitrage opportunities to the desktop client and mobile web app. It strictly uses real provider data (no synthetic/mock).

## Requirements

- Windows 10/11 x86_64
- Python 3.10+ on PATH
- pip
- Optional: provider API keys

## Steps

1) Clone or download the ARBYS project and open PowerShell in the project root.

2) Create and activate a virtual environment:

```powershell
python -m venv .venv_backend
.venv_backend\Scripts\activate
```

3) Install dependencies:

```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

4) (Optional) Configure provider API keys for paid sources:

```powershell
$env:API_SPORTS_KEY = "<your api-sports key>"
$env:THE_ODDS_API_KEY = "<your the-odds-api key>"
```

5) Start the backend server:

```powershell
python backend\api_server.py
# Server runs at http://127.0.0.1:5000
```

Alternatively, use the helper installer that sets up a venv and launches the server in a separate console:

```powershell
scripts\backend_install.bat
```

## Verify

Open a browser or PowerShell:

```powershell
# Health check
curl http://127.0.0.1:5000/api/health

# Opportunities (soccer)
curl "http://127.0.0.1:5000/api/opportunities?sport=soccer&min_profit_pct=1.0&limit=50"
```

## Notes

- REAL_DATA_ONLY policy: strictly no prefabs/placeholders/mocks.
- CORS is enabled for browser clients.
- Without API keys, only the free SofaScore provider is active; other sports may return zero opportunities depending on availability.

