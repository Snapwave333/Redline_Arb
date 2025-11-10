# ACH Transfer Integration - Quick Start

## 🚀 Get Started in 60 Seconds

### 1. Start the ACH Microservice

From the `src` directory:
```bash
node ach_manager.js
```

Or from the project root:
```bash
cd src
node ach_manager.js
```

You should see:
```
ACH Transfer Microservice running on port 3000
Firebase initialized: true
Plaid configured: true
Dwolla configured: true
```

### 2. Verify It's Working

In another terminal:
```bash
curl http://localhost:3000/health
```

Or visit in browser: http://localhost:3000/health

### 3. Start Your Python Bot

```bash
python launch_real.py
```

The bot will automatically use ACH transfers instead of PayPal!

## 📋 Required Configuration

Before running, add these to your `.env` file:

```env
# ACH Service
ACH_SERVICE_PORT=3000

# Plaid (get from https://dashboard.plaid.com)
PLAID_CLIENT_ID=your_plaid_client_id
PLAID_SECRET=your_plaid_secret
PLAID_ENV=sandbox

# Dwolla (get from https://dashboard.dwolla.com)
DWOLLA_KEY=your_dwolla_key
DWOLLA_SECRET=your_dwolla_secret
DWOLLA_ENV=sandbox
DWOLLA_WEBHOOK_SECRET=your_webhook_secret
```

## ✅ What Was Integrated

**Files Created:**
- `src/ach_manager.js` - Node.js microservice
- `src/ach_client.py` - Python client
- `src/ach_transfer_manager.py` - Drop-in PayPal replacement
- `src/package.json` - Dependencies
- `src/ACH_SETUP.md` - Full API documentation
- `ACH_DEPLOYMENT.md` - Deployment guide

**Files Updated:**
- `src/realistic_growth.py` - Now uses ACH
- `src/dual_strategy.py` - Now uses ACH
- `config.env.example` - Added ACH config

## 🔄 What Changed

**Before (PayPal):**
```python
from src.paypal_manager import PayPalTransferManager
manager = PayPalTransferManager()
```

**After (ACH):**
```python
from src.ach_transfer_manager import ACHTransferManager
manager = ACHTransferManager()
```

Same interface! Your code doesn't need any changes.

## 🎯 Key Features

✅ **Secure**: Tokenized bank connections via Plaid  
✅ **Compliant**: Never stores raw bank details  
✅ **Idempotent**: UUID-based duplicate prevention  
✅ **Reliable**: Webhook reconciliation for status updates  
✅ **Fast**: Low-latency transfers for trading  

## 🧪 Test the Integration

1. **Health Check:**
   ```bash
   curl http://localhost:3000/health
   ```

2. **Start Python Bot:**
   ```bash
   python launch_real.py
   ```

3. **Check Logs:**
   The bot will log ACH transfer initiation automatically.

## 📞 Troubleshooting

**Service won't start:**
```bash
cd src
npm install
node ach_manager.js
```

**Can't connect:**
- Ensure service is running: `curl http://localhost:3000/health`
- Check `.env` has correct credentials

**Firebase errors:**
- Verify `config/firebase_service_account.json` exists
- Check Firebase credentials

**Plaid/Dwolla errors:**
- Verify credentials in `.env` file
- Use sandbox for testing

## 📚 Documentation

- **Full API Docs:** `src/ACH_SETUP.md`
- **Deployment Guide:** `ACH_DEPLOYMENT.md`
- **Configuration:** `config.env.example`

## 🎉 You're Ready!

Your trading bot now uses secure ACH transfers via Plaid + Dwolla!

Start the service, then start your bot - it's that simple. 🚀
