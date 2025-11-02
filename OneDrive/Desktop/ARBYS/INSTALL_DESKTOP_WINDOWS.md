# Install ARBYS Desktop (Windows)

This guide shows how to install and run the ARBYS desktop app on Windows 10/11 using the packaged onedir build.

System requirements
- Windows 10 or 11 (x64)
- ~500 MB free disk space
- Internet connection for first run (providers/config)
- Microsoft Visual C++ runtime (most systems already have it)

Download
- From the latest GitHub Release, download:
  - `Redline_Arbitrage.zip` (onedir package built with Python 3.10)
  - Optional: `CHECKSUMS.txt` to verify integrity

Verify (optional but recommended)
1) Open PowerShell in the download folder
2) Run: `Get-FileHash .\Redline_Arbitrage.zip -Algorithm SHA256`
3) Confirm the hash matches the entry for the zip in `CHECKSUMS.txt`

Install and first run
1) Right-click `Redline_Arbitrage.zip` → “Extract All…”
2) Open the extracted folder and double-click `Redline_Arbitrage.exe`
3) If Windows SmartScreen warns, click “More info” → “Run anyway” (publisher certificate may be absent in this build)
4) The app is portable; no MSI installer is required. All runtime files (including python310.dll) are bundled in the folder.
5) On first run, follow the onboarding/setup wizard. Configuration is stored in `config/bot_config.json`.

Troubleshooting
- App doesn’t start: Try “Run as Administrator” or move the folder to a writable location (e.g., `C:\Users\<you>\Downloads`)
- Missing web engine features: Optional PyQt6-WebEngine components are not required for core functionality
- Antivirus blocks the app: Add an exception for the downloaded .exe
- Reinstall: Simply delete the old .exe and replace it with the new version

Common error fixes
- “Failed to load Python DLL '..._internal\\python313.dll'”: Download the new onedir build (`Redline_Arbitrage.zip`) which is aligned to Python 3.10 and fully bundles the required runtime.
- Install the Microsoft Visual C++ Redistributable (x64) from Microsoft if missing: https://learn.microsoft.com/windows/win32/api/_coreu/windows-installer-requirements
- Always extract the zip fully before running (do not launch from inside a compressed folder).

Uninstall
- Delete the extracted app folder and the `config` folder if you want to remove local settings

Privacy & data
- No background network access beyond configured providers
- Local cache/storage lives under the app directory (portable)

Support
- See `QUICKSTART.md` and `TESTING_GUIDE.md`
- Open an issue on GitHub if you encounter problems