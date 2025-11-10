# Quick Start Guide - Kalshi Trading Bot

## 🚀 Getting Started

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Setup Environment
```bash
python setup.py
```

### 3. Configure API Credentials
Edit the `.env` file with your Kalshi API credentials:
```env
KALSHI_API_KEY=your_actual_api_key
KALSHI_PRIVATE_KEY=your_actual_private_key
KALSHI_BASE_URL=https://trading-api.kalshi.co/trade-api/v2
ENVIRONMENT=sandbox  # Start with sandbox!
```

### 4. Train Models (Optional but Recommended)
```bash
python cli.py train TRUMP2024 ELECTION2024
```

### 5. Start Trading
```bash
python cli.py trade --tickers TRUMP2024 ELECTION2024 --train
```

## 📊 Key Features

- **Machine Learning**: Ensemble models (Logistic Regression, Random Forest, Gradient Boosting)
- **Kelly Criterion**: Mathematically optimal position sizing
- **Risk Management**: Multi-layer risk controls and monitoring
- **Real-time Data**: WebSocket integration for live market data
- **Smart Execution**: Limit orders with optimal pricing

## ⚠️ Important Notes

1. **Start with Sandbox**: Always test in sandbox environment first
2. **Small Positions**: Begin with small position sizes
3. **Monitor Closely**: Watch the logs and monitoring dashboard
4. **Risk Limits**: Configure appropriate risk limits in `.env`

## 🔧 Configuration

Key settings in `.env`:
- `DEFAULT_KELLY_FRACTION=0.1` - Conservative Kelly multiplier
- `MIN_PROBABILITY_DELTA=0.05` - Minimum edge required for trades
- `MAX_POSITION_SIZE=1000` - Maximum position size
- `MAX_DAILY_LOSS=500` - Daily loss limit

## 📈 Monitoring

- **Logs**: Check `logs/` directory for detailed logs
- **Status**: Run `python cli.py status` for current status
- **Alerts**: Monitor console output for important alerts

## 🆘 Troubleshooting

- **API Errors**: Check API credentials and rate limits
- **Model Errors**: Ensure sufficient historical data for training
- **Risk Violations**: Adjust risk parameters if too restrictive

## 📚 Documentation

- `README.md` - Full documentation
- `IMPLEMENTATION_SUMMARY.md` - Technical details
- `tests/test_bot.py` - Unit tests

## 🎯 Next Steps

1. Test with small amounts in sandbox
2. Analyze performance metrics
3. Adjust strategy parameters
4. Scale up gradually

Happy trading! 🎉
