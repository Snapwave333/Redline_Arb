# Install Guide: Desktop Client (Windows x86)

This guide installs and runs the Redline Arbitrage Desktop Client on Windows. The desktop client uses real data only and integrates with the Backend Flask API for live opportunities.

## Requirements

- Windows 10/11 x86_64
- Python 3.10+ on PATH
- pip
- Optional: provider API keys for backend

## Option A: Run from Source

1) Open PowerShell in the project root.

2) Create and activate a virtual environment:

```powershell
python -m venv .venv310
.venv310\Scripts\activate
```

3) Install dependencies:

```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

4) Start the Backend Server (recommended for live data):

```powershell
# In a separate PowerShell window
python backend\api_server.py
```

5) Launch the Desktop Client:

```powershell
python main.py
```

## Option B: Run the Packaged EXE

If you have the packaged build (e.g., `dist/Redline_Arbitrage.exe`):

```powershell
# Double-click the EXE
# Or run from PowerShell:
& "dist/Redline_Arbitrage.exe"
```

## Provider Configuration

- Configure providers via the Desktop UI: Settings → API Providers.
- For backend providers, set environment variables before launching the backend:

```powershell
$env:API_SPORTS_KEY = "<your api-sports key>"
$env:THE_ODDS_API_KEY = "<your the-odds-api key>"
```

## Tips

- First run flags: `config/first_run_flags.json`
- Settings: `config/settings.py`
- The GUI polls backend health at `/api/health` when configured.

## Notes

- REAL_DATA_ONLY: The application and backend never use synthetic or placeholder data.
- For mobile/web instructions, refer to `mobile_web_app/README.md` (currently under maintenance pause).

