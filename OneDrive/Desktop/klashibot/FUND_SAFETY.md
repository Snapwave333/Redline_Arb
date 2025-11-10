# 🔒 Fund Safety & Cash Management

## Overview

The Kalshi Trading Bot is designed with **multiple layers of fund safety** to ensure it **only uses available deposited funds** and **never attempts to pull funds from external sources**. This is a critical safety feature that protects your account from unexpected withdrawals or overdrafts.

## 🛡️ Safety Features Implemented

### 1. **Cash Balance Monitoring**
- **Real-time Updates**: Bot continuously monitors your Kalshi account cash balance
- **API Integration**: Uses Kalshi's official API to get accurate, up-to-date balance information
- **No External Access**: Bot has **no access** to external bank accounts or payment methods

### 2. **Multiple Cash Safety Checks**

#### **Check 1: Basic Availability**
```python
if required_cash > available_cash:
    # Trade rejected - insufficient funds
```

#### **Check 2: Minimum Reserve**
```python
min_reserve = 10.0  # Always keep $10 minimum
usable_cash = available_cash - min_reserve
if required_cash > usable_cash:
    # Trade rejected - would exceed safe limit
```

#### **Check 3: Maximum Usage Percentage**
```python
max_usage_pct = 0.95  # Use max 95% of available cash
max_safe_amount = available_cash * max_usage_pct
if required_cash > max_safe_amount:
    # Trade rejected - exceeds safe usage limit
```

#### **Check 4: Pending Orders**
```python
pending_value = sum(order.quantity * order.price for order in pending_orders)
net_available = available_cash - pending_value - min_reserve
if required_cash > net_available:
    # Trade rejected - insufficient considering pending orders
```

### 3. **Position Size Limits**
- **Kelly Criterion**: Mathematically optimal position sizing
- **Cash-Based Limits**: Position size automatically adjusted based on available cash
- **Conservative Approach**: Uses only a fraction of calculated optimal size

### 4. **Real-Time Monitoring**
- **Continuous Updates**: Cash balance checked every 30 seconds
- **Pending Order Tracking**: Monitors all pending orders to calculate true available cash
- **Safety Alerts**: Immediate warnings when cash levels get low

## ⚙️ Configuration Settings

### Cash Safety Parameters (in `.env` file):

```env
# Cash Safety Settings
MIN_CASH_RESERVE=10.0          # Always keep $10 minimum
MAX_CASH_USAGE_PCT=0.95        # Use max 95% of available cash
CASH_UPDATE_INTERVAL=30        # Update balance every 30 seconds
```

### Risk Management Parameters:

```env
# Risk Management
MAX_DAILY_LOSS=500             # Stop trading after $500 daily loss
MAX_PORTFOLIO_RISK=0.02        # Max 2% of portfolio at risk
POSITION_TIMEOUT_HOURS=24      # Cancel orders after 24 hours
```

## 🔍 How It Works

### 1. **Before Every Trade**
```
1. Update cash balance from Kalshi API
2. Check pending orders
3. Calculate net available cash
4. Apply safety limits
5. Only proceed if all checks pass
```

### 2. **Position Sizing Process**
```
1. Calculate Kelly-optimal position size
2. Check against available cash
3. Apply maximum usage percentage
4. Reserve minimum cash amount
5. Adjust position size if needed
```

### 3. **Continuous Monitoring**
```
1. Update cash balance every 30 seconds
2. Monitor pending orders
3. Check for low cash warnings
4. Log all cash-related activities
```

## 🚨 Safety Guarantees

### ✅ **What the Bot WILL Do:**
- Only use funds already deposited in your Kalshi account
- Respect all cash safety limits
- Monitor cash balance continuously
- Reject trades that would exceed safe limits
- Log all cash-related decisions

### ❌ **What the Bot WILL NOT Do:**
- Access external bank accounts
- Initiate fund transfers
- Overdraw your account
- Exceed configured safety limits
- Place trades without sufficient cash

## 📊 Cash Safety Dashboard

The bot provides real-time cash safety information:

```bash
python cli.py status
```

**Example Output:**
```
Cash Summary:
  Total Cash: $1,000.00
  Available Cash: $950.00
  Pending Orders Value: $0.00
  Reserved Cash: $10.00
  Last Updated: 2024-01-15 10:30:00

Safety Features:
  Min Cash Reserve: $10.00
  Max Cash Usage: 95%
  Balance Update Interval: 30 seconds
```

## 🔧 Troubleshooting

### **Common Issues:**

#### **"Insufficient cash" Error**
- **Cause**: Not enough funds in Kalshi account
- **Solution**: Deposit more funds or reduce position sizes

#### **"Would exceed safe cash limit" Error**
- **Cause**: Trade would use too much of available cash
- **Solution**: Reduce position size or increase cash reserve

#### **"Exceeds maximum safe cash usage" Error**
- **Cause**: Trade exceeds 95% cash usage limit
- **Solution**: Adjust `MAX_CASH_USAGE_PCT` or reduce position size

### **Monitoring Commands:**

```bash
# Check current status
python cli.py status

# Validate configuration
python cli.py config --validate

# View detailed logs
tail -f logs/kalshi_bot_*.log
```

## ⚠️ Important Warnings

1. **Start Small**: Begin with small amounts to test the system
2. **Monitor Closely**: Watch cash levels and safety warnings
3. **Test First**: Always test in sandbox environment
4. **Regular Checks**: Monitor your Kalshi account balance regularly
5. **Emergency Stop**: Bot will automatically stop if cash gets too low

## 🆘 Emergency Procedures

### **If Cash Gets Too Low:**
1. Bot will automatically reject new trades
2. Existing orders will be monitored
3. Low cash warnings will be logged
4. Manual intervention may be required

### **Manual Emergency Stop:**
```bash
# Stop all trading
python cli.py trade --stop

# Cancel all pending orders
python -c "
import asyncio
from src.main import KalshiTradingBot

async def emergency_stop():
    bot = KalshiTradingBot()
    await bot.initialize()
    await bot.execution_manager.cancel_all_orders()
    await bot.cleanup()

asyncio.run(emergency_stop())
"
```

## 📈 Best Practices

1. **Conservative Settings**: Start with conservative cash safety settings
2. **Regular Monitoring**: Check cash levels daily
3. **Gradual Scaling**: Increase position sizes gradually as you gain confidence
4. **Backup Plans**: Always have a plan for low cash situations
5. **Documentation**: Keep records of all cash-related decisions

## 🔒 Security Notes

- **API Keys**: Keep your Kalshi API credentials secure
- **Environment**: Use sandbox environment for testing
- **Logs**: Review logs regularly for any unusual activity
- **Updates**: Keep the bot updated with latest safety features

The bot is designed with **defense in depth** - multiple layers of protection ensure your funds are always safe and the bot never exceeds your available balance.
