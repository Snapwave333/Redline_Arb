# 🔑 Adding Your Kalshi Account - Manual Setup

## Option 1: Automated Setup (Recommended)

Run the credential setup script:
```bash
python setup_credentials.py
```

This will securely prompt you for your credentials and update the `.env` file.

## Option 2: Manual Setup

### Step 1: Get Your Kalshi API Credentials

1. **Log into Kalshi**: Go to [kalshi.com](https://kalshi.com) and log in
2. **Navigate to API Settings**: Dashboard → Settings → API Keys
3. **Generate API Key**: Create a new API key if you don't have one
4. **Copy Credentials**: You'll need both:
   - **API Key** (public key)
   - **Private Key** (secret key)

### Step 2: Edit the .env File

Open the `.env` file in your editor and replace the placeholder values:

```env
# API Configuration
KALSHI_API_KEY=your_actual_api_key_here
KALSHI_PRIVATE_KEY=your_actual_private_key_here
KALSHI_BASE_URL=https://trading-api.kalshi.co/trade-api/v2
KALSHI_WS_URL=wss://trading-api.kalshi.co/trade-api/v2/ws

# Bot Configuration
BOT_NAME=kalshi_trading_bot
ENVIRONMENT=sandbox  # Change to 'production' for live trading
LOG_LEVEL=INFO

# Trading Parameters
DEFAULT_KELLY_FRACTION=0.1
MIN_PROBABILITY_DELTA=0.05
MAX_POSITION_SIZE=1000
MIN_LIQUIDITY_THRESHOLD=1000

# Risk Management
MAX_DAILY_LOSS=500
MAX_PORTFOLIO_RISK=0.02
POSITION_TIMEOUT_HOURS=24

# Data Collection
MARKET_DATA_INTERVAL=60
HISTORICAL_DATA_DAYS=30

# Model Configuration
MODEL_RETRAIN_INTERVAL=3600
FEATURE_WINDOW_HOURS=24
```

### Step 3: Validate Configuration

Test your configuration:
```bash
python cli.py config --validate
```

## 🔒 Security Notes

- **Never share your private key** - it's used to sign API requests
- **Start with sandbox** - test with fake money first
- **Keep credentials secure** - don't commit `.env` to version control
- **Use environment variables** in production deployments

## 🌍 Environment Settings

- **`ENVIRONMENT=sandbox`** - Testing environment (recommended to start)
- **`ENVIRONMENT=production`** - Live trading environment

## ⚠️ Important Warnings

1. **Start Small**: Begin with small position sizes
2. **Test First**: Always test in sandbox before live trading
3. **Monitor Closely**: Watch logs and performance metrics
4. **Risk Management**: Configure appropriate risk limits

## 🚀 Next Steps After Setup

1. **Validate**: `python cli.py config --validate`
2. **Train Models**: `python cli.py train TRUMP2024 ELECTION2024`
3. **Start Trading**: `python cli.py trade --tickers TRUMP2024 ELECTION2024`

## 🆘 Troubleshooting

### Common Issues:

- **"Configuration validation failed"**: Check API key format
- **"API request failed"**: Verify credentials and network connection
- **"Rate limit exceeded"**: Reduce trading frequency or increase intervals

### Getting Help:

- Check logs in `logs/` directory
- Run `python cli.py status` for current status
- Review error messages in console output
