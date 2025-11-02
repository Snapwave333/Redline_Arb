# Install ARBYS Desktop (Windows)

This guide shows how to install and run the ARBYS desktop app on Windows 10/11 using the packaged .exe.

System requirements
- Windows 10 or 11 (x64)
- ~500 MB free disk space
- Internet connection for first run (providers/config)
- Microsoft Visual C++ runtime (most systems already have it)

Download
- From the GitHub Release v1.0.0, download:
  - `Redline_Arb_Windows_v1.0.0.exe`
  - Optional: `CHECKSUMS.txt` to verify integrity

Verify (optional but recommended)
1) Open PowerShell in the download folder
2) Run: `Get-FileHash .\Redline_Arb_Windows_v1.0.0.exe -Algorithm SHA256`
3) Confirm the hash matches the entry for the .exe in `CHECKSUMS.txt`

Install and first run
1) Double-click `Redline_Arb_Windows_v1.0.0.exe`
2) If Windows SmartScreen warns, click “More info” → “Run anyway” (publisher certificate may be absent in this build)
3) The app is portable; no MSI installer is required. It will extract and run directly.
4) On first run, follow the onboarding/setup wizard. Configuration is stored in `config/bot_config.json`.

Troubleshooting
- App doesn’t start: Try “Run as Administrator” or move the .exe to a writable location (e.g., `C:\Users\<you>\Downloads`)
- Missing web engine features: Optional PyQt6-WebEngine components are not required for core functionality
- Antivirus blocks the app: Add an exception for the downloaded .exe
- Reinstall: Simply delete the old .exe and replace it with the new version

Uninstall
- Delete the .exe and the `config` folder if you want to remove local settings

Privacy & data
- No background network access beyond configured providers
- Local cache/storage lives under the app directory (portable)

Support
- See `QUICKSTART.md` and `TESTING_GUIDE.md`
- Open an issue on GitHub if you encounter problems