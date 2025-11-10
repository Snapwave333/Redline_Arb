# Kalshi Trading Bot - React Dashboard

A real-time React dashboard for monitoring and controlling the Kalshi Trading Bot with Firebase Firestore integration.

## Features

- **Real-time Monitoring**: Live updates of portfolio value, daily PnL, and active positions
- **Performance Charts**: 7-day performance visualization with custom SVG charts
- **Risk Management**: Configure max daily loss and portfolio risk limits
- **Position Tracking**: View all active and closed positions with detailed metrics
- **Responsive Design**: Mobile-first design with Tailwind CSS
- **Dark Theme**: Professional dark interface optimized for trading

## Quick Start

### Prerequisites

- Node.js 16+ and npm
- Firebase project with Firestore enabled
- Kalshi Trading Bot backend running

### Installation

1. Install dependencies:
```bash
npm install
```

2. Configure Firebase:
   - Update `public/index.html` with your Firebase configuration
   - Set `window.__firebase_config` with your project details
   - Set `window.__initial_auth_token` if using custom authentication

3. Start the development server:
```bash
npm start
```

The dashboard will be available at `http://localhost:3000`

## Configuration

### Firebase Setup

The dashboard requires the following Firestore collections:

**Bot State** (`/artifacts/{appId}/users/{userId}/bot_status/main_state`):
- `portfolioValue`: Current total capital
- `dailyPnl`: Today's profit/loss
- `isRunning`: Bot operational status
- `maxDailyLoss`: Maximum daily loss limit
- `maxPortfolioRisk`: Maximum portfolio risk percentage
- `kellyFactor`: Kelly criterion fraction
- `currentExposure`: Current capital at risk

**Positions** (`/artifacts/{appId}/users/{userId}/positions`):
- `marketId`: Market identifier
- `status`: Position status (Active/Closed)
- `shares`: Number of contracts
- `entryPrice`: Entry price per share
- `currentPrice`: Current market price
- `pnl`: Position profit/loss
- `entryTime`: Entry timestamp
- `closeTime`: Close timestamp (if closed)

**Performance History** (`/artifacts/{appId}/users/{userId}/performance_history`):
- `date`: Date string (YYYY-MM-DD)
- `cumulativePnl`: Total profit since inception
- `dailyPnl`: Daily profit/loss

### Global Variables

Set these in your deployment environment:

```javascript
window.__app_id = 'your-app-id';
window.__firebase_config = {
  apiKey: "your-api-key",
  authDomain: "your-project.firebaseapp.com",
  projectId: "your-project-id",
  storageBucket: "your-project.appspot.com",
  messagingSenderId: "123456789",
  appId: "your-app-id"
};
window.__initial_auth_token = 'your-custom-token';
```

## Architecture

### Single File Design

The entire dashboard is contained in `BotDashboard.jsx` (~1000 lines) to meet deployment constraints:

- **Firebase Integration**: Real-time listeners and transactions
- **Custom Hooks**: `useFirestore` and `useFirestoreCollection`
- **Inline Components**: All UI components defined within the file
- **SVG Icons**: Custom inline SVG icons (no external libraries)
- **Custom Charts**: SVG-based performance visualization

### Key Components

- **MetricCard**: Displays key performance indicators
- **PositionsTable**: Shows active and closed positions
- **PerformanceChart**: 7-day PnL visualization
- **ConfigModal**: Risk settings configuration
- **Toast**: Custom notification system

### Data Flow

1. **Authentication**: Firebase custom token authentication
2. **Real-time Listeners**: `onSnapshot` for instant updates
3. **User Actions**: `runTransaction` for atomic updates
4. **Error Handling**: Custom toast notifications

## Styling

### Tailwind CSS

The dashboard uses Tailwind CSS with a custom dark theme:

- **Background**: `bg-gray-900` (main), `bg-gray-800` (cards)
- **Text**: `text-gray-100` (primary), `text-gray-400` (secondary)
- **Accents**: `text-green-500` (profit), `text-red-500` (loss)
- **Interactive**: `bg-blue-600` (buttons), focus rings

### Responsive Design

- **Mobile-first**: Optimized for small screens
- **Grid Layouts**: Responsive grid with `grid-cols-1 md:grid-cols-2 lg:grid-cols-4`
- **Table Overflow**: Horizontal scroll on mobile
- **Modal**: Centered overlay with backdrop

## Development

### Available Scripts

- `npm start`: Start development server
- `npm build`: Build for production
- `npm test`: Run tests
- `npm eject`: Eject from Create React App

### Code Structure

```javascript
// Firebase initialization
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const db = getFirestore(app);

// Custom hooks
const useFirestore = (path, options) => { /* ... */ };
const useFirestoreCollection = (path, options) => { /* ... */ };

// Utility functions
const formatCurrency = (amount) => { /* ... */ };
const formatPercent = (value) => { /* ... */ };

// Components (all inline)
const MetricCard = ({ title, value, subtitle, color, icon }) => { /* ... */ };
const PositionsTable = ({ positions, loading }) => { /* ... */ };
const PerformanceChart = ({ data, loading }) => { /* ... */ };
const ConfigModal = ({ isOpen, onClose, botState, onSave }) => { /* ... */ };
const Toast = ({ message, type, onClose }) => { /* ... */ };

// Main component
const BotDashboard = () => { /* ... */ };
```

## Deployment

### Production Build

```bash
npm run build
```

This creates a `build` folder with optimized production files.

### Environment Variables

Set these in your deployment environment:

- `REACT_APP_FIREBASE_API_KEY`
- `REACT_APP_FIREBASE_AUTH_DOMAIN`
- `REACT_APP_FIREBASE_PROJECT_ID`
- `REACT_APP_FIREBASE_STORAGE_BUCKET`
- `REACT_APP_FIREBASE_MESSAGING_SENDER_ID`
- `REACT_APP_FIREBASE_APP_ID`

### Firebase Hosting

Deploy to Firebase Hosting:

```bash
npm install -g firebase-tools
firebase login
firebase init hosting
firebase deploy
```

## Security

- **Authentication**: Firebase custom token authentication
- **Data Validation**: Client-side input validation
- **Atomic Updates**: Firestore transactions prevent race conditions
- **Error Handling**: Secure error messages without sensitive data

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## License

MIT License - See LICENSE file for details.
