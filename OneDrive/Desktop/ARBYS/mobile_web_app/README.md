# Redline Arbitrage - Mobile Web App

> Maintenance Notice: Mobile/Web build, test, and production pipelines are temporarily paused to prioritize the Desktop Client and Backend API delivery. This document is retained for reference; please use the desktop installation guides for current releases. The last published mobile/web build is available under v1.1.6 releases.

Note: The backend API server now lives at `backend/api_server.py`. If you need live opportunities during development, start the backend from the project root:

```bash
python backend/api_server.py
# Server: http://127.0.0.1:5000
```

 A mobile browser-based version of the Redline Arbitrage sports betting application that runs entirely offline in your browser, with optional Live Data fetching and data usage warnings.

## Features

- **Offline-First**: All data stored locally in your browser using IndexedDB
- **Mobile-Optimized**: Responsive design that works perfectly on phones and tablets
- **Arbitrage Detection**: Real-time scanning for guaranteed profit opportunities
- **Stake Calculator**: Optimal bet distribution across multiple bookmakers
- **Account Health Tracking**: Monitor bookmaker account status and stealth scores
- **PWA Ready**: Installable as a Progressive Web App for native app experience
- **Live Data Mode**: Optional internet data fetching with daily usage tracking and cellular warning
 - **Sport Selector**: Compact dropdown to filter opportunities by sport (All, Soccer, Basketball, Baseball, Hockey, Tennis). Selection persists across reloads via localStorage.

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Modern web browser (Chrome, Firefox, Safari, Edge)

### Installation

1. Clone the repository and navigate to the mobile app:
```bash
cd mobile_web_app
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server (backend optional for offline mode):
```bash
npm run dev
```

4. Open [http://localhost:3000](http://localhost:3000) in your browser

### Building for Production

```bash
npm run build
```

The built files will be in the `dist/` directory, ready for deployment to any static hosting service.

### Running Standalone (No Installation Required)

For a completely standalone version that runs locally:

```bash
# Build the app
npm run build

# Serve locally (includes auto-open in browser)
python serve.py
```

This starts a local web server at `http://localhost:8000` that serves the complete application. The app works entirely offline after the initial load - no internet connection needed for calculations. For live odds data and real arbitrage opportunities, start the backend server at `backend/api_server.py`.

**Perfect for:**
- Running on any computer without installation
- Sharing with others via local network
- Mobile testing on actual devices
- Offline arbitrage analysis

### Live Data & Data Usage Warning

The app can run fully offline, but if you enable Live Data it will fetch event data from the internet and generate odds locally.

- Enable Live Data: Settings → "Enable live data fetching"
- Data Usage Banner: When Live Data is on, a banner shows daily usage and warns on cellular connections
- Threshold: Adjust the daily usage warning threshold (default 25 MB) in Settings
- Disable Anytime: Use the banner "Disable Live" button or toggle in Settings

Note: We only fetch lightweight event listings from TheSportsDB and compute odds locally to minimize bandwidth.

## Architecture

### Core Components

- **ArbitrageDetector**: Core algorithm for finding arbitrage opportunities
- **StakeCalculator**: Calculates optimal bet distributions
- **StorageService**: IndexedDB-based offline data persistence
- **Mobile UI**: Material-UI based responsive interface

### Data Storage

All data is stored locally in your browser:
- Arbitrage opportunities and calculations
- Account health data
- User preferences and settings
- API response caching

### Offline Functionality

The app works completely offline:
- No internet connection required for calculations
- Data persists between sessions
- Background sync when online (future feature)

## Usage

### Dashboard
- View recent arbitrage opportunities
- Refresh data from configured APIs
- Tap opportunities to calculate stakes
 - Filter by sport using the dropdown in the controls bar. Selection is remembered across sessions.

### Calculator
- Input total stake amount
- View optimal bet distribution
- See guaranteed profit calculations

### Accounts
- Monitor bookmaker account health
- Track stealth scores and bet history
- View profit/loss analytics

### Settings
- Enable/Disable Live Data mode
- Set daily data usage warning threshold
- View local storage stats
- Clear all local data (opportunities, calculations, cache, settings)

## Browser Compatibility

- **Chrome/Edge**: Full support including PWA installation
- **Firefox**: Full support
- **Safari**: Full support (iOS 11.3+)
- **Mobile Browsers**: Optimized for iOS Safari and Android Chrome

## Security & Privacy

- All data stored locally in your browser
- No data sent to external servers
- API keys stored securely in browser storage
- No tracking or analytics

## Development

### Project Structure

```
src/
├── components/     # Reusable UI components
├── pages/         # Main application pages
├── services/      # Business logic and data services
├── types/         # TypeScript type definitions
├── hooks/         # Custom React hooks
└── stores/        # State management
```

### Key Technologies

- **React 18**: Modern React with hooks
- **TypeScript**: Type-safe development
- **Material-UI**: Mobile-first component library
- **IndexedDB**: Client-side database
- **Vite**: Fast build tool and dev server
- **PWA**: Progressive Web App capabilities

## Testing & QA

The mobile web app includes a full test and benchmarking suite.

### Install test tooling

```bash
npm install
npx playwright install
```

### Run unit and component tests (Vitest)

```bash
npm run test
```

- Generates coverage at `mobile_web_app/coverage/` (open `index.html`).
- Vitest uses `jsdom` and a test setup that polyfills IndexedDB.

### Build and start preview server

```bash
npm run build
npm run preview
# Opens http://localhost:4173/
```

### Run E2E tests (Playwright)

```bash
npm run test:e2e
```

- Validates homepage rendering, PWA service worker registration, and SPA routing.
- HTML report available; open with:

```bash
npx playwright show-report
```

### Run performance benchmarks

```bash
npm run test:perf
```

- Collects basic timing metrics (`elapsed`, `domContentLoaded`, `loadTime`) against the preview build.
- Thresholds are set for local runs and can be tuned per environment.

### Troubleshooting

- If Vitest requests installing `jsdom`, re-run `npm run test` after it installs.
- Ensure the preview server is running at `http://localhost:4173/` before running Playwright tests.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly on mobile devices
5. Submit a pull request

## License

MIT License - see the main project LICENSE file.

## Related Projects

- [Redline Arbitrage Desktop](https://github.com/Snapwave333/Redline_Arb) - Original desktop application
