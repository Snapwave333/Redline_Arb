# Install ARBYS as a PWA (Android and iOS)

This guide shows you how to install the mobile web app as a Progressive Web App (PWA) on Android (Chrome) and iOS (Safari). The PWA runs fully offline once installed, with data stored in your browser.

Prerequisites:
- A running build (production) hosted from `mobile_web_app/dist` or the preview server started by `npm run preview`.
- Recommended preview URL for local testing: `http://localhost:4173/`

Important behaviors:
- Offline: A service worker precaches core assets; first visit must be online to install.
- Updates: The app downloads updates in the background; relaunch to apply.
- Storage: All data is stored locally (IndexedDB). Clearing site storage resets local data.

Android (Google Chrome):
1) Open Chrome and navigate to your hosted app URL (e.g., `http://localhost:4173/`).
2) Wait for the site to fully load. Ensure you can see the main app view.
3) Tap the browser menu (⋮).
4) Tap “Add to Home screen”.
5) Confirm the app name and tap “Add”.
6) Chrome will place a launcher icon on your home screen. Launch it to open in standalone mode.

Tips:
- If “Add to Home screen” doesn’t appear, verify `manifest.webmanifest` and the service worker are being served over HTTP/HTTPS from your host.
- Ensure the manifest includes `display: "standalone"` and a valid 192x192 icon.

iOS (Safari on iPhone/iPad):
1) Open Safari and navigate to the hosted app URL (e.g., `http://localhost:4173/`).
2) Wait for the site to load completely.
3) Tap the Share icon (square with up arrow).
4) Scroll and select “Add to Home Screen”.
5) Confirm the app name and tap “Add”.
6) A home screen icon is created; launch it to open the app in standalone mode.

Notes for iOS:
- iOS requires the site to be served over HTTP/HTTPS; localhost works during development.
- Safari may cache aggressively. Pull-to-refresh inside the PWA may not update the service worker; close and relaunch to apply updates.
- Notifications are limited; the app relies on in-app UI for alerts.

Hosting the production build:
1) Build the app: `cd mobile_web_app && npm run build` (dist folder generated).
2) Serve locally for testing: `npm run preview` and open the printed URL.
3) For a static host, upload `mobile_web_app/dist` contents.
4) For Windows sharing, you can use `python -m http.server 4173` from `dist` and visit `http://localhost:4173/`.

Troubleshooting:
- If install prompts don’t appear, verify:
  - `manifest.webmanifest` is accessible (check devtools Application -> Manifest).
  - A service worker is active (Application -> Service Workers).
  - Icons are valid sizes and mime types in the manifest.
  - HTTPS hosting for production; localhost is fine for dev.