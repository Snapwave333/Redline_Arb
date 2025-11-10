import React, { useState, useEffect, useCallback } from 'react';
import { initializeApp } from 'firebase/app';
import { getFirestore, onSnapshot, runTransaction, doc } from 'firebase/firestore';
import { getAuth, signInAnonymously } from 'firebase/auth';

// Firebase configuration - using backend service account
const firebaseConfig = {
  apiKey: "AIzaSyDemoKey",
  authDomain: "kalshi-trading.firebaseapp.com",
  projectId: "kalshi-trading",
  storageBucket: "kalshi-trading.appspot.com",
  messagingSenderId: "123456789",
  appId: "kalshi-trading-bot"
};

// Initialize Firebase - Disabled for now
let app, db, auth;

// Disable Firebase completely until credentials are configured
db = null;
auth = null;

// Global variables (as per requirements)
const __app_id = "kalshi-trading-bot";
const __firebase_config = firebaseConfig;
const __initial_auth_token = null; // Will be set after authentication

// Custom Toast Component
const Toast = ({ message, type = 'info', onClose }) => {
  const bgColor = {
    success: 'bg-green-600',
    error: 'bg-red-600',
    warning: 'bg-yellow-600',
    info: 'bg-blue-600'
  }[type];

  return (
    <div className={`fixed top-4 right-4 ${bgColor} text-white px-6 py-3 rounded-lg shadow-lg z-50 flex items-center space-x-2`}>
      <span>{message}</span>
      <button onClick={onClose} className="text-white hover:text-gray-200">
        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
        </svg>
      </button>
    </div>
  );
};

// Performance Chart Component
const PerformanceChart = ({ data }) => {
  if (!data || data.length === 0) {
    return (
      <div className="h-64 flex items-center justify-center text-gray-400">
        No performance data available
      </div>
    );
  }

  const maxPnl = Math.max(...data.map(d => Math.abs(d.dailyPnl || 0)));
  const minPnl = Math.min(...data.map(d => d.dailyPnl || 0));
  const range = maxPnl - minPnl || 1;
  
  const width = 400;
  const height = 200;
  const padding = 40;
  const chartWidth = width - 2 * padding;
  const chartHeight = height - 2 * padding;

  const points = data.map((item, index) => {
    const x = padding + (index / (data.length - 1)) * chartWidth;
    const y = padding + chartHeight - ((item.dailyPnl - minPnl) / range) * chartHeight;
    return `${x},${y}`;
  }).join(' ');

  return (
    <div className="w-full">
      <svg width={width} height={height} className="w-full h-64">
        {/* Grid lines */}
        <defs>
          <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
            <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#374151" strokeWidth="1" opacity="0.3"/>
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#grid)" />
        
        {/* Zero line */}
        <line
          x1={padding}
          y1={padding + chartHeight - ((0 - minPnl) / range) * chartHeight}
          x2={width - padding}
          y2={padding + chartHeight - ((0 - minPnl) / range) * chartHeight}
          stroke="#6B7280"
          strokeWidth="2"
          strokeDasharray="5,5"
        />
        
        {/* Chart line */}
        <polyline
          fill="none"
          stroke={data[data.length - 1]?.dailyPnl >= 0 ? "#10B981" : "#EF4444"}
          strokeWidth="3"
          points={points}
        />
        
        {/* Data points */}
        {data.map((item, index) => {
          const x = padding + (index / (data.length - 1)) * chartWidth;
          const y = padding + chartHeight - ((item.dailyPnl - minPnl) / range) * chartHeight;
          return (
            <circle
              key={index}
              cx={x}
              cy={y}
              r="4"
              fill={item.dailyPnl >= 0 ? "#10B981" : "#EF4444"}
              stroke="#1F2937"
              strokeWidth="2"
            />
          );
        })}
        
        {/* Labels */}
        {data.map((item, index) => {
          const x = padding + (index / (data.length - 1)) * chartWidth;
          return (
            <text
              key={index}
              x={x}
              y={height - 10}
              textAnchor="middle"
              className="text-xs fill-gray-400"
            >
              {new Date(item.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
            </text>
          );
        })}
      </svg>
    </div>
  );
};

// Configuration Modal Component
const ConfigModal = ({ isOpen, onClose, currentConfig, onUpdate }) => {
  const [maxDailyLoss, setMaxDailyLoss] = useState(currentConfig?.maxDailyLoss || 0);
  const [maxPortfolioRisk, setMaxPortfolioRisk] = useState(currentConfig?.maxPortfolioRisk || 0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (currentConfig) {
      setMaxDailyLoss(currentConfig.maxDailyLoss || 0);
      setMaxPortfolioRisk(currentConfig.maxPortfolioRisk || 0);
    }
  }, [currentConfig]);

  const handleSubmit = useCallback(async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    // Client-side validation
    if (maxDailyLoss <= 0) {
      setError('Max Daily Loss must be greater than 0');
      setIsLoading(false);
      return;
    }
    if (maxPortfolioRisk <= 0 || maxPortfolioRisk > 1) {
      setError('Max Portfolio Risk must be between 0 and 1');
      setIsLoading(false);
      return;
    }

    try {
      const docRef = doc(db, 'artifacts', __app_id, 'users', 'user-123', 'bot_status', 'main_state');
      
      await runTransaction(db, async (transaction) => {
        const doc = await transaction.get(docRef);
        if (doc.exists()) {
          transaction.update(docRef, {
            maxDailyLoss: maxDailyLoss,
            maxPortfolioRisk: maxPortfolioRisk,
            lastUpdated: new Date()
          });
        }
      });

      onUpdate({ maxDailyLoss, maxPortfolioRisk });
      onClose();
    } catch (err) {
      setError('Failed to update configuration: ' + err.message);
    } finally {
      setIsLoading(false);
    }
  }, [maxDailyLoss, maxPortfolioRisk, onUpdate, onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-gray-800 rounded-lg p-6 w-full max-w-md mx-4">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold text-white">Manage Risk Settings</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Max Daily Loss ($)
            </label>
            <input
              type="number"
              step="0.01"
              min="0"
              value={maxDailyLoss}
              onChange={(e) => setMaxDailyLoss(parseFloat(e.target.value) || 0)}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Max Portfolio Risk (0-1)
            </label>
            <input
              type="number"
              step="0.01"
              min="0"
              max="1"
              value={maxPortfolioRisk}
              onChange={(e) => setMaxPortfolioRisk(parseFloat(e.target.value) || 0)}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>

          {error && (
            <div className="text-red-400 text-sm">{error}</div>
          )}

          <div className="flex space-x-3 pt-4">
            <button
              type="submit"
              disabled={isLoading}
              className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white font-medium py-2 px-4 rounded-md transition-colors"
            >
              {isLoading ? 'Updating...' : 'Update Settings'}
            </button>
            <button
              type="button"
              onClick={onClose}
              className="flex-1 bg-gray-600 hover:bg-gray-700 text-white font-medium py-2 px-4 rounded-md transition-colors"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Welcome Screen Component with Plaid/Dwolla Setup
const WelcomeScreen = ({ onComplete }) => {
  const [plaidLinkReady, setPlaidLinkReady] = useState(false);
  const [isConnectingPlaid, setIsConnectingPlaid] = useState(false);
  const [isConnectingDwolla, setIsConnectingDwolla] = useState(false);
  const [linkToken, setLinkToken] = useState(null);
  const [toast, setToast] = useState(null);
  const ACH_SERVICE_URL = process.env.REACT_APP_ACH_SERVICE_URL || 'http://localhost:3000';

  useEffect(() => {
    // Create Plaid link token on mount
    const createLinkToken = async () => {
      try {
        const response = await fetch(`${ACH_SERVICE_URL}/plaid/create_link_token`, {
          method: 'POST',
        });
        const data = await response.json();
        if (data.success) {
          setLinkToken(data.link_token);
          setPlaidLinkReady(true);
        }
      } catch (error) {
        setToast({ message: 'Failed to initialize bank linking', type: 'error' });
      }
    };
    createLinkToken();
  }, []);

  const handleConnectPlaid = async () => {
    setIsConnectingPlaid(true);
    try {
      setToast({ message: 'Connecting to Plaid...', type: 'info' });
      
      // Fetch link token from ACH service
      const response = await fetch(`${ACH_SERVICE_URL}/plaid/create_link_token`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.success && data.link_token) {
          setToast({ 
            message: 'Plaid Link ready! (Demo: No credentials configured)', 
            type: 'info' 
          });
          
          // In production, you would:
          // 1. Initialize Plaid Link with link_token
          // 2. Open the Plaid Link modal
          // 3. User selects bank and connects
          // 4. Handle public_token on success
          // 5. Exchange for processor token
          
          // For demo: simulate success after a delay
          setTimeout(() => {
            setToast({ 
              message: 'Bank connection ready. Configure Plaid credentials to use live connection.', 
              type: 'success' 
            });
            setIsConnectingPlaid(false);
          }, 2000);
        } else {
          throw new Error('Failed to get link token');
        }
      } else {
        throw new Error('ACH service not available');
      }
    } catch (error) {
      setToast({ 
        message: 'Plaid integration requires ACH service and credentials to be configured. This is a demo interface.', 
        type: 'warning' 
      });
      setIsConnectingPlaid(false);
    }
  };

  const handleConnectDwolla = async () => {
    setIsConnectingDwolla(true);
    try {
      setToast({ message: 'Configuring Dwolla...', type: 'info' });
      
      // Create Dwolla customer and funding source
      const response = await fetch(`${ACH_SERVICE_URL}/dwolla/customer`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          first_name: 'User',
          last_name: 'Account',
          email: 'user@example.com',
          type: 'personal'
        }),
      });
      
      const data = await response.json();
      if (data.success) {
        setToast({ 
          message: 'Dwolla configured. Configure credentials for live transfers.', 
          type: 'success' 
        });
        setIsConnectingDwolla(false);
      } else {
        throw new Error(data.error || 'Failed to configure Dwolla');
      }
    } catch (error) {
      setToast({ 
        message: 'Dwolla configuration requires ACH service and credentials. This is a demo interface.', 
        type: 'warning' 
      });
      setIsConnectingDwolla(false);
    }
  };

  const closeToast = () => setToast(null);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900 flex items-center justify-center p-4">
      {/* Background Pattern */}
      <div className="absolute inset-0 opacity-10">
        <div className="absolute inset-0" style={{
          backgroundImage: 'radial-gradient(circle at 2px 2px, white 1px, transparent 0)',
          backgroundSize: '40px 40px'
        }} />
      </div>

      {/* Welcome Card */}
      <div className="relative bg-gray-800 rounded-2xl shadow-2xl p-8 md:p-12 max-w-2xl w-full border border-gray-700">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-600 rounded-full mb-4">
            <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
            </svg>
          </div>
          <h1 className="text-3xl md:text-4xl font-bold text-white mb-2">
            Welcome to ACH Transfers
          </h1>
          <p className="text-gray-400 text-lg">
            Connect your bank account for secure, automated transfers
          </p>
        </div>

        {/* Connection Steps */}
        <div className="space-y-4 mb-8">
          {/* Plaid Connection */}
          <div className="bg-gray-700 rounded-lg p-6 border border-gray-600">
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center space-x-3">
                <div className="flex-shrink-0 w-10 h-10 bg-purple-600 rounded-lg flex items-center justify-center">
                  <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm0 2c5.514 0 10 4.486 10 10s-4.486 10-10 10S2 17.514 2 12 6.486 2 12 2z" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-white">Connect Your Bank</h3>
                  <p className="text-sm text-gray-400">Link your bank account via Plaid</p>
                </div>
              </div>
              <button
                onClick={handleConnectPlaid}
                disabled={!plaidLinkReady || isConnectingPlaid}
                className={`px-6 py-2 rounded-lg font-medium transition-colors ${
                  plaidLinkReady && !isConnectingPlaid
                    ? 'bg-purple-600 hover:bg-purple-700 text-white'
                    : 'bg-gray-600 text-gray-400 cursor-not-allowed'
                }`}
              >
                {isConnectingPlaid ? 'Connecting...' : 'Connect'}
              </button>
            </div>
            <div className="flex items-center space-x-2 text-xs text-gray-500">
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd" />
              </svg>
              <span>Bank-level security with Plaid</span>
            </div>
          </div>

          {/* Dwolla Configuration */}
          <div className="bg-gray-700 rounded-lg p-6 border border-gray-600">
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center space-x-3">
                <div className="flex-shrink-0 w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
                  <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-white">Set Up ACH Transfers</h3>
                  <p className="text-sm text-gray-400">Configure Dwolla for automated deposits</p>
                </div>
              </div>
              <button
                onClick={handleConnectDwolla}
                disabled={isConnectingDwolla}
                className={`px-6 py-2 rounded-lg font-medium transition-colors ${
                  isConnectingDwolla
                    ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                    : 'bg-blue-600 hover:bg-blue-700 text-white'
                }`}
              >
                {isConnectingDwolla ? 'Configuring...' : 'Configure'}
              </button>
            </div>
            <div className="flex items-center space-x-2 text-xs text-gray-500">
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd" />
              </svg>
              <span>Instant setup, secure transfers</span>
            </div>
          </div>
        </div>

        {/* Skip Button */}
        <div className="text-center">
          <button
            onClick={onComplete}
            className="text-gray-400 hover:text-white transition-colors"
          >
            Skip for now →
          </button>
        </div>
      </div>

      {/* Toast */}
      {toast && (
        <div className={`fixed top-4 right-4 ${
          toast.type === 'success' ? 'bg-green-600' :
          toast.type === 'error' ? 'bg-red-600' :
          'bg-blue-600'
        } text-white px-6 py-3 rounded-lg shadow-lg z-50 flex items-center space-x-2 max-w-md`}>
          <span>{toast.message}</span>
          <button onClick={closeToast} className="text-white hover:text-gray-200 ml-4">
            ×
          </button>
        </div>
      )}
    </div>
  );
};

// Live Trades Terminal Component
const LiveTradesTerminal = () => {
  const [trades, setTrades] = useState([]);
  const [latestTrade, setLatestTrade] = useState(null);

  useEffect(() => {
    const fetchLatestTrade = async () => {
      try {
        const response = await fetch('http://localhost:3002/trades/latest');
        const data = await response.json();
        if (data.success && data.trade) {
          setLatestTrade(data.trade);
          setTrades(prev => [data.trade, ...prev].slice(0, 500)); // Keep last 500 trades
        }
      } catch (error) {
        console.error('Failed to fetch trades:', error);
      }
    };

    // Fetch every 10ms for real-time updates
    const interval = setInterval(fetchLatestTrade, 10);
    
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="bg-black rounded-lg font-mono text-green-400 p-4 overflow-hidden">
      <div className="border-b border-gray-700 mb-2 pb-2">
        <span className="text-gray-500">Kalshi Bot &gt;</span>
        <span className="ml-2 text-green-400 animate-pulse">●</span>
        <span className="ml-2 text-gray-400">LIVE TRADING</span>
      </div>
      <div className="h-96 overflow-y-auto">
        {trades.map((trade, idx) => (
          <div key={idx} className="text-xs mb-1 hover:bg-gray-900 p-1 rounded transition-colors">
            <span className="text-gray-500">[{trade.timestamp}]</span>
            <span className="ml-2 text-cyan-400">{trade.order_id}</span>
            <span className={`ml-2 font-bold ${trade.direction === 'YES' ? 'text-green-400' : 'text-red-400'}`}>
              {trade.direction}
            </span>
            <span className="ml-2 text-yellow-400">{trade.ticker}</span>
            <span className="ml-2">{trade.shares} @ ${trade.price}</span>
            <span className={`ml-2 font-bold ${trade.pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              PnL: ${trade.pnl}
            </span>
            <span className="ml-2 text-green-500">{trade.status}</span>
          </div>
        ))}
        {trades.length === 0 && (
          <div className="text-gray-500 text-center mt-40">Waiting for trades...</div>
        )}
      </div>
      <div className="border-t border-gray-700 mt-2 pt-2 text-xs text-gray-500">
        <span>Total Trades: {trades.length}</span>
      </div>
    </div>
  );
};

// Main Dashboard Component
const BotDashboard = () => {
  const [botState, setBotState] = useState(null);
  const [positions, setPositions] = useState([]);
  const [performanceData, setPerformanceData] = useState([]);
  const [isConfigModalOpen, setIsConfigModalOpen] = useState(false);
  const [toast, setToast] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [showWelcome, setShowWelcome] = useState(false); // Start directly with dashboard
  const [botRunning, setBotRunning] = useState(false);

  // Initialize Firebase authentication
  useEffect(() => {
    const initAuth = async () => {
      try {
        if (auth) {
          await signInAnonymously(auth);
        }
        setIsAuthenticated(true);
      } catch (error) {
        console.log('Firebase auth skipped:', error.message);
        // Continue without Firebase auth
        setIsAuthenticated(true);
      }
    };
    initAuth();
  }, []);

  // New real-time state
  const [wsConnected, setWsConnected] = useState(false);
  const [usePolling, setUsePolling] = useState(true); // start with polling until WS connects
  const [positionsSource, setPositionsSource] = useState('combined'); // 'combined' | 'kalshi'

  // Initialize Firebase authentication
  useEffect(() => {
    const initAuth = async () => {
      try {
        if (auth) {
          await signInAnonymously(auth);
        }
        setIsAuthenticated(true);
      } catch (error) {
        console.log('Firebase auth skipped:', error.message);
        // Continue without Firebase auth
        setIsAuthenticated(true);
      }
    };
    initAuth();
  }, []);

  // WebSocket: real-time portfolio updates with fallback
  useEffect(() => {
    let ws;
    let reconnectTimer;

    const connectWs = () => {
      try {
        ws = new WebSocket('ws://localhost:3002/ws/portfolio');
        ws.onopen = () => {
          setWsConnected(true);
          setUsePolling(false);
          setToast({ message: '✅ Live portfolio connected', type: 'success' });
        };
        ws.onmessage = (evt) => {
          try {
            const msg = JSON.parse(evt.data);
            if (msg.success && msg.data) {
              const portfolio = msg.data;
              setBotState({
                portfolioValue: portfolio?.balance || 0,
                dailyPnl: portfolio?.daily_pnl || 0,
                currentExposure: portfolio?.exposure || 0,
                kellyFactor: 0.05,
              });
            }
          } catch (e) {
            console.warn('WS message parse error:', e);
          }
        };
        ws.onerror = () => {
          setWsConnected(false);
          setUsePolling(true);
        };
        ws.onclose = () => {
          setWsConnected(false);
          setUsePolling(true);
          reconnectTimer = setTimeout(connectWs, 2000);
        };
      } catch (e) {
        console.warn('WS connection error:', e);
        setUsePolling(true);
      }
    };

    connectWs();

    return () => {
      if (ws) {
        try { ws.close(); } catch {}
      }
      if (reconnectTimer) clearTimeout(reconnectTimer);
    };
  }, []);

  // Polling fallback for portfolio (runs only when usePolling=true)
  useEffect(() => {
    if (!usePolling) return;

    const fetchPortfolio = async () => {
      try {
        const portfolioResponse = await fetch('http://localhost:3002/portfolio');
        const portfolioData = await portfolioResponse.json();
        if (portfolioData.success) {
          const portfolio = portfolioData.data;
          setBotState({
            portfolioValue: portfolio ? portfolio.balance || 0 : 0,
            dailyPnl: portfolio ? portfolio.daily_pnl || 0 : 0,
            currentExposure: portfolio ? portfolio.exposure || 0 : 0,
            kellyFactor: 0.05,
          });
        }
      } catch (error) {
        console.log('Portfolio polling error:', error);
      }
    };

    fetchPortfolio();
    const interval = setInterval(fetchPortfolio, 1000);
    return () => clearInterval(interval);
  }, [usePolling]);

  // Positions fetching with source toggle
  useEffect(() => {
    const fetchPositions = async () => {
      try {
        const url = positionsSource === 'combined'
          ? 'http://localhost:3002/positions/combined'
          : 'http://localhost:3002/positions';
        const res = await fetch(url);
        const data = await res.json();
        if (positionsSource === 'combined' && data.success && data.merged) {
          setPositions(data.merged.map(p => ({
            marketId: p.ticker,
            status: 'Active',
            shares: p.quantity || 0,
            entryPrice: p.average_price || 0,
            currentPrice: p.average_price || 0,
            pnl: 0,
          })));
        } else if (positionsSource === 'kalshi' && data.success && data.data) {
          setPositions(data.data);
        }
      } catch (e) {
        console.log('Positions fetch error:', e);
      }
    };

    fetchPositions();
    const interval = setInterval(fetchPositions, 2000);
    return () => clearInterval(interval);
  }, [positionsSource]);

  const handleConfigUpdate = useCallback((newConfig) => {
    setBotState(prev => ({ ...prev, ...newConfig }));
    setToast({ message: 'Configuration updated successfully', type: 'success' });
  }, []);

  const closeToast = useCallback(() => {
    setToast(null);
  }, []);

  // Skip authentication check - go straight to welcome screen
  // Show welcome screen after splash
  if (showWelcome) {
    return <WelcomeScreen onComplete={() => setShowWelcome(false)} />;
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-3">
              <div>
                <h1 className="text-2xl font-bold">Kalshi Trading Bot</h1>
                <p className="text-gray-400">Real-time trading dashboard</p>
              </div>
              <span className={`ml-4 px-2 py-1 text-xs rounded-full ${wsConnected && !usePolling ? 'bg-green-700 text-green-200' : 'bg-yellow-700 text-yellow-200'}`}>
                {wsConnected && !usePolling ? 'LIVE' : 'POLLING'}
              </span>
            </div>
            <button
              onClick={() => setIsConfigModalOpen(true)}
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md flex items-center space-x-2 transition-colors"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              <span>Manage Risk Settings</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Metrics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-gray-800 rounded-lg p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <svg className="w-8 h-8 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-400">Portfolio Value</p>
                <p className="text-2xl font-semibold text-white">
                  ${botState?.portfolioValue?.toFixed(2) || '0.00'}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-gray-800 rounded-lg p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <svg className="w-8 h-8 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-400">Daily PnL</p>
                <p className={`text-2xl font-semibold ${(botState?.dailyPnl || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  ${botState?.dailyPnl?.toFixed(2) || '0.00'}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-gray-800 rounded-lg p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <svg className="w-8 h-8 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-400">Exposure</p>
                <p className="text-2xl font-semibold text-white">
                  ${botState?.currentExposure?.toFixed(2) || '0.00'}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-gray-800 rounded-lg p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <svg className="w-8 h-8 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-400">Kelly Factor</p>
                <p className="text-2xl font-semibold text-white">
                  {(botState?.kellyFactor || 0).toFixed(3)}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Performance Chart */}
        <div className="bg-gray-800 rounded-lg p-6 mb-8">
          <h2 className="text-xl font-semibold text-white mb-4">7-Day Performance</h2>
          <PerformanceChart data={performanceData} />
        </div>

        {/* Live Trades Terminal - COMMAND WINDOW STYLE */}
        <div className="bg-gray-800 rounded-lg p-6 mb-8">
          <h2 className="text-xl font-semibold text-white mb-4">📊 Live Trades Stream</h2>
          <LiveTradesTerminal />
        </div>

        {/* Positions Table */}
        <div className="bg-gray-800 rounded-lg p-6">
          <h2 className="text-xl font-semibold text-white mb-4">Positions</h2>
          {positions.length === 0 ? (
            <div className="text-gray-400 text-center py-8">No active positions</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-700">
                <thead>
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Market</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Status</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Shares</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Entry Price</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Current Price</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">PnL</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-700">
                  {positions.map((position, index) => (
                    <tr key={index}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-white">{position.marketId}</td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          position.status === 'Active' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                        }`}>
                          {position.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-white">{position.shares}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-white">${position.entryPrice?.toFixed(2)}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-white">${position.currentPrice?.toFixed(2)}</td>
                      <td className={`px-6 py-4 whitespace-nowrap text-sm font-medium ${
                        (position.pnl || 0) >= 0 ? 'text-green-400' : 'text-red-400'
                      }`}>
                        ${position.pnl?.toFixed(2) || '0.00'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </main>

      {/* Configuration Modal */}
      <ConfigModal
        isOpen={isConfigModalOpen}
        onClose={() => setIsConfigModalOpen(false)}
        currentConfig={botState}
        onUpdate={handleConfigUpdate}
      />

      {/* Toast Notifications */}
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={closeToast}
        />
      )}
    </div>
  );
};

export default BotDashboard;