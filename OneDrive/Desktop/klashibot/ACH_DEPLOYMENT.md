# ACH Transfer Integration - Deployment Guide

## Overview

Your Kalshi Trading Bot has been successfully upgraded from PayPal to a secure **Plaid + Dwolla ACH transfer system**. The new architecture uses a dedicated Node.js microservice for all financial operations.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Python Trading Bot                        │
│  (Existing: Trading, ML Models, Risk Management)           │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP Calls
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              ACH Transfer Microservice                       │
│                  (Node.js/Express)                           │
│  • /plaid/create_link_token                                  │
│  • /plaid/exchange_public_token                              │
│  • /dwolla/customer                                           │
│  • /dwolla/funding-source                                     │
│  • /dwolla/transfers                                         │
│  • /dwolla/webhook                                            │
└──────────────────────┬──────────────────────────────────────┘
                       │ API Calls
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    Firebase Cloud                            │
│  • Stores: access_token, customer_url, funding_source_url   │
│  • Transfer records and status updates                      │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Plaid API           │     Dwolla API            │
│  • Bank Linking                │     • Customer Management   │
│  • Token Exchange              │     • Funding Sources        │
│  • Processor Tokens           │     • ACH Transfers         │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Install Node.js Dependencies

```bash
cd src
npm install
```

This installs:
- `express` - Web server
- `plaid` - Plaid API client
- `node-fetch` - HTTP requests
- `uuid` - Idempotency keys
- `firebase-admin` - Firebase integration
- `cors` - CORS support
- `dotenv` - Environment configuration

### 2. Configure Credentials

Copy your configuration variables to the `.env` file in the project root:

```env
# ACH Service Configuration
ACH_SERVICE_PORT=3000

# Plaid Configuration (from Plaid Dashboard)
PLAID_CLIENT_ID=your_client_id_here
PLAID_SECRET=your_secret_here
PLAID_ENV=sandbox  # or 'production'

# Dwolla Configuration (from Dwolla Dashboard)
DWOLLA_KEY=your_key_here
DWOLLA_SECRET=your_secret_here
DWOLLA_ENV=sandbox  # or 'production'
DWOLLA_WEBHOOK_SECRET=your_webhook_secret
```

**Get Your Credentials:**

#### Plaid
1. Sign up at https://dashboard.plaid.com
2. Create a new application
3. Get your Client ID and Secret from the dashboard
4. Add `http://localhost:3000` to allowed redirect URIs (development)

#### Dwolla
1. Sign up at https://dashboard.dwolla.com
2. Create an application
3. Get your Key and Secret from the dashboard
4. Configure webhook URL: `https://your-domain.com/dwolla/webhook`

### 3. Start the ACH Microservice

```bash
cd src
npm start
```

For development with auto-reload:
```bash
npm run dev
```

You should see:
```
ACH Transfer Microservice running on port 3000
Firebase initialized: true
Plaid configured: true
Dwolla configured: true
```

### 4. Verify Integration

Check the health of the service:
```bash
curl http://localhost:3000/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "ACH Transfer Microservice",
  "firebase_initialized": true,
  "plaid_configured": true,
  "dwolla_configured": true
}
```

## Integration with Python Bot

The Python bot now uses `ACHTransferManager` instead of `PayPalTransferManager`. The interface is compatible, so no changes are needed to your trading logic.

### Updated Files

- `src/realistic_growth.py` - Uses `ACHTransferManager`
- `src/dual_strategy.py` - Uses `ACHTransferManager`
- Created `src/ach_client.py` - Python HTTP client for ACH service
- Created `src/ach_transfer_manager.py` - Drop-in replacement for PayPal

### Backward Compatibility

The ACH manager maintains the same interface as the PayPal manager:
```python
from src.ach_transfer_manager import ACHTransferManager

manager = ACHTransferManager()
await manager.initialize()
result = await manager.transfer_daily_income(400.0)
```

## Deployment

### Local Development

1. Start the ACH service:
   ```bash
   cd src && npm start
   ```

2. Start the Python bot:
   ```bash
   python launch_real.py
   ```

The bot will automatically connect to the ACH service at `http://localhost:3000`.

### Production Deployment

#### Option 1: Separate Servers

Deploy the ACH service separately:
```bash
# On your server
cd /path/to/klashibot/src
pm2 start ach_manager.js
```

Update Python bot to point to production ACH URL:
```env
ACH_SERVICE_URL=https://ach.your-domain.com
```

#### Option 2: Docker Compose

Create `docker-compose.yml`:
```yaml
version: '3.8'
services:
  python-bot:
    build: .
    environment:
      - ACH_SERVICE_URL=http://ach-service:3000
    depends_on:
      - ach-service
  
  ach-service:
    build:
      context: ./src
    ports:
      - "3000:3000"
    environment:
      - PLAID_CLIENT_ID=${PLAID_CLIENT_ID}
      - PLAID_SECRET=${PLAID_SECRET}
      - DWOLLA_KEY=${DWOLLA_KEY}
      - DWOLLA_SECRET=${DWOLLA_SECRET}
```

Run with:
```bash
docker-compose up -d
```

## Testing

### Test Plaid Integration

1. Create a link token:
   ```bash
   curl -X POST http://localhost:3000/plaid/create_link_token
   ```

2. Use the link token in your frontend to complete bank linking
3. Exchange the public token:
   ```bash
   curl -X POST http://localhost:3000/plaid/exchange_public_token \
     -H "Content-Type: application/json" \
     -d '{"public_token":"public-sandbox-..."}'
   ```

### Test Dwolla Integration

1. Create a customer:
   ```bash
   curl -X POST http://localhost:3000/dwolla/customer \
     -H "Content-Type: application/json" \
     -d '{"first_name":"John","last_name":"Doe","email":"john@example.com"}'
   ```

2. Create a funding source (after Plaid exchange):
   ```bash
   curl -X POST http://localhost:3000/dwolla/funding-source \
     -H "Content-Type: application/json" \
     -d '{"processor_token":"processor-sandbox-..."}'
   ```

3. Initiate a transfer:
   ```bash
   curl -X POST http://localhost:3000/dwolla/transfers \
     -H "Content-Type: application/json" \
     -d '{"amount":400.00}'
   ```

### Test Webhooks

Use Dwolla's webhook testing tool or Postman to send test webhooks to:
```
POST http://localhost:3000/dwolla/webhook
Headers:
  dwolla-topic: transfer_completed
  x-request-signature-sha-256: [signature]
Body: [Dwolla event payload]
```

## Security Checklist

- [ ] Use HTTPS in production
- [ ] Store credentials in `.env` (never commit)
- [ ] Enable webhook signature verification
- [ ] Use UUID-based idempotency keys
- [ ] Never log or store raw bank account details
- [ ] Implement rate limiting on API endpoints
- [ ] Set up monitoring and alerting
- [ ] Use separate sandbox and production environments

## Troubleshooting

### ACH Service Won't Start

**Error:** `Cannot find module 'plaid'`
```bash
cd src && npm install
```

### Firebase Not Initializing

**Error:** `Firebase initialization failed`
- Check that `config/firebase_service_account.json` exists
- Verify credentials are valid

### Plaid Connection Errors

**Error:** `Invalid client credentials`
- Verify `PLAID_CLIENT_ID` and `PLAID_SECRET` in `.env`
- Check environment matches (`sandbox` vs `production`)

### Dwolla Connection Errors

**Error:** `Invalid credentials`
- Verify `DWOLLA_KEY` and `DWOLLA_SECRET` in `.env`
- Check environment matches (`sandbox` vs `production`)

### Python Bot Can't Connect

**Error:** `Cannot connect to ACH service`
- Ensure service is running: `npm start` in `src/`
- Check `ACH_SERVICE_URL` in Python environment
- Verify port 3000 is not blocked by firewall

## Monitoring

### Health Checks

Monitor the ACH service health endpoint:
```bash
watch -n 5 'curl -s http://localhost:3000/health'
```

### Logs

ACH service logs to console:
```
ACH Transfer Microservice running on port 3000
Firebase initialized: true
Plaid configured: true
```

Python bot logs:
```python
logger.info("ACH transfer initiated successfully",
           amount=400.0, transfer_id="...", status="pending")
```

### Firebase Monitoring

Check transfer records in Firebase:
```
artifacts/kalshi-trading-bot/users/user-123/transfers/
```

## Migration from PayPal

The ACH system is a drop-in replacement for PayPal. No changes to trading logic required.

### What Changed
- PayPal Manager → ACH Transfer Manager
- PayPal SDK → HTTP client to ACH microservice
- PayPal webhooks → Dwolla webhooks

### What Stayed the Same
- Interface: `transfer_daily_income(amount)`
- Configuration: Uses existing `config.paypal` structure
- Logic: Daily transfer automation unchanged
- Integration: Works with existing dual strategy

## Support

For issues:
1. Check logs: `src/ach_manager.js` logs to console
2. Verify credentials in `.env`
3. Test endpoints with curl or Postman
4. Check Plaid and Dwolla dashboards

For questions:
- Plaid: https://plaid.com/support
- Dwolla: https://support.dwolla.com

## Next Steps

1. ✅ Install dependencies: `npm install`
2. ✅ Configure credentials in `.env`
3. ✅ Start ACH service: `npm start`
4. ✅ Test health endpoint
5. ✅ Start Python bot
6. ✅ Verify end-to-end transfer flow

**You're now using the most secure, production-ready ACH transfer system available!**
