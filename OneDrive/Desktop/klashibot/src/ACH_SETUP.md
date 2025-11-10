# ACH Transfer Microservice Setup

## Overview

The ACH Transfer Microservice is a standalone Node.js/Express service that handles secure bank linking via Plaid and ACH transfers via Dwolla. It runs alongside the Python trading bot on port 3000.

## Quick Start

### 1. Install Dependencies

```bash
cd src
npm install
```

### 2. Configure Environment

Add the following to your `.env` file:

```env
# ACH Service Configuration
ACH_SERVICE_PORT=3000

# Plaid Configuration
PLAID_CLIENT_ID=your_plaid_client_id_here
PLAID_SECRET=your_plaid_secret_here
PLAID_ENV=sandbox  # or 'development' or 'production'

# Dwolla Configuration
DWOLLA_KEY=your_dwolla_key_here
DWOLLA_SECRET=your_dwolla_secret_here
DWOLLA_ENV=sandbox  # or 'production'
DWOLLA_WEBHOOK_SECRET=your_webhook_secret_here
```

### 3. Start the Service

```bash
# Production mode
npm start

# Development mode (with auto-reload)
npm run dev
```

## API Endpoints

### Health Check

**GET** `/health`

Returns service status and configuration.

**Response:**
```json
{
  "status": "healthy",
  "service": "ACH Transfer Microservice",
  "firebase_initialized": true,
  "plaid_configured": true,
  "dwolla_configured": true
}
```

---

### Plaid Endpoints

#### Create Link Token

**POST** `/plaid/create_link_token`

Creates a Plaid Link token for client-side bank linking.

**Response:**
```json
{
  "success": true,
  "link_token": "link-sandbox-...",
  "expiration": "2024-01-01T00:00:00Z"
}
```

#### Exchange Public Token

**POST** `/plaid/exchange_public_token`

Exchanges Plaid public token for access token and processor token.

**Request Body:**
```json
{
  "public_token": "public-sandbox-..."
}
```

**Response:**
```json
{
  "success": true,
  "processor_token": "processor-sandbox-...",
  "access_token": "access-sandbox-..."
}
```

---

### Dwolla Endpoints

#### Create Customer

**POST** `/dwolla/customer`

Creates or retrieves a Dwolla customer.

**Request Body:**
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "email": "john@example.com",
  "type": "personal"
}
```

**Response:**
```json
{
  "success": true,
  "customer_url": "https://api-sandbox.dwolla.com/customers/...",
  "message": "Customer created successfully"
}
```

#### Create Funding Source

**POST** `/dwolla/funding-source`

Attaches a bank account using Plaid processor token.

**Request Body:**
```json
{
  "processor_token": "processor-sandbox-..."
}
```

**Response:**
```json
{
  "success": true,
  "funding_source_url": "https://api-sandbox.dwolla.com/funding-sources/...",
  "message": "Funding source created successfully"
}
```

#### Initiate Transfer

**POST** `/dwolla/transfers`

Initiates an ACH transfer with idempotency.

**Request Body:**
```json
{
  "amount": 400.00,
  "metadata": {
    "description": "Daily trading income"
  }
}
```

**Response:**
```json
{
  "success": true,
  "transfer_id": "...",
  "transfer_url": "https://api-sandbox.dwolla.com/transfers/...",
  "amount": 400.00,
  "status": "pending",
  "idempotency_key": "uuid-here",
  "message": "Transfer initiated successfully"
}
```

---

### Webhook Endpoint

#### Dwolla Webhook

**POST** `/dwolla/webhook`

Receives Dwolla webhook events for transfer status updates.

**Headers:**
- `x-request-signature-sha-256`: Webhook signature
- `dwolla-topic`: Event type

**Events Handled:**
- `transfer_completed`
- `transfer_failed`
- `bank_transfer_returned`

---

## Integration Flow

### 1. Initial Setup

```javascript
// 1. Create Plaid link token
const response = await fetch('http://localhost:3000/plaid/create_link_token', {
  method: 'POST'
});
const { link_token } = await response.json();

// 2. Use link_token in Plaid Link component (frontend)
// User completes bank linking
// Frontend receives public_token

// 3. Exchange public token
await fetch('http://localhost:3000/plaid/exchange_public_token', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ public_token })
});

// 4. Create Dwolla customer
await fetch('http://localhost:3000/dwolla/customer', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    first_name: 'John',
    last_name: 'Doe',
    email: 'john@example.com'
  })
});

// 5. Create funding source
await fetch('http://localhost:3000/dwolla/funding-source', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ processor_token })
});
```

### 2. Daily Transfers

```javascript
// Initiate daily transfer
await fetch('http://localhost:3000/dwolla/transfers', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    amount: 400.00,
    metadata: { description: 'Daily trading income' }
  })
});
```

### 3. Webhook Updates

Dwolla will send webhook events to `/dwolla/webhook` for:
- Transfer completion
- Transfer failures
- Bank returns

The service automatically updates Firebase with transfer status.

---

## Security Best Practices

1. **Never Store Sensitive Data**: Only store access tokens, customer URLs, and funding source URLs in Firebase
2. **HTTPS in Production**: Always use HTTPS for all endpoints
3. **Webhook Verification**: Verify Dwolla webhook signatures
4. **Idempotency Keys**: All transfers use UUID-based idempotency keys
5. **Environment Separation**: Use sandbox for testing, production for live

---

## Testing

### Test Plaid Integration

```bash
# Start the service
npm start

# In another terminal, test link token creation
curl -X POST http://localhost:3000/plaid/create_link_token

# Check health
curl http://localhost:3000/health
```

### Test Dwolla Integration

Use the Dwolla sandbox environment for testing. All test credentials are available in your Dwolla dashboard.

---

## Troubleshooting

### Firebase Not Initialized

Ensure `config/firebase_service_account.json` exists and is valid.

### Plaid Connection Errors

Check that `PLAID_CLIENT_ID` and `PLAID_SECRET` are correct for your environment.

### Dwolla Connection Errors

Verify `DWOLLA_KEY` and `DWOLLA_SECRET` match your environment (sandbox vs production).

### Webhook Not Receiving Events

Configure your Dwolla webhook URL in the Dwolla dashboard to point to your deployed service endpoint.

---

## Production Deployment

1. Set `PLAID_ENV=production` and `DWOLLA_ENV=production`
2. Use production credentials for Plaid and Dwolla
3. Configure webhook URL in Dwolla dashboard
4. Enable HTTPS (required by Plaid and Dwolla)
5. Deploy with process manager (PM2, Docker, etc.)

---

## Architecture

```
┌─────────────────┐
│  Python Bot     │
│  (Trading)      │
└────────┬────────┘
         │ HTTP calls
         ▼
┌─────────────────┐
│  ACH Service     │◄───┐
│  (Node.js)      │    │
├─────────────────┤    │
│  /plaid/*       │    │
│  /dwolla/*      │    │
│  /dwolla/webhook│    │
└────────┬────────┘    │
         │             │ Webhook Events
         ▼             │
┌─────────────────┐   │
│  Firebase        │◄──┘
│  (Storage)       │
└─────────────────┘
         │
         ▼
┌─────────────────┐
│  Plaid API      │
│  Dwolla API     │
└─────────────────┘
```

---

## Support

For issues or questions:
1. Check logs: `src/ach_manager.js` logs to console
2. Verify configuration in `.env`
3. Test endpoints with curl or Postman
4. Check Dwolla/Plaid dashboards for API status
