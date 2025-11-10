/**
 * ACH Transfer Microservice
 * 
 * Standalone Node.js/Express service for ACH transfers using Plaid + Dwolla
 * Replaces legacy PayPal integration with secure bank linking
 */

const express = require('express');
const cors = require('cors');
const { PlaidApi, Products, CountryCode, Configuration, ProcessorTokenCreateRequest, ProcessorEnum } = require('plaid');
const fetch = require('node-fetch');
const { v4: uuidv4 } = require('uuid');
const admin = require('firebase-admin');
const path = require('path');
require('dotenv').config();

// Initialize Express app
const app = express();
const PORT = process.env.ACH_SERVICE_PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());

// Plaid Configuration
const PLAID_CONFIG = {
  clientId: process.env.PLAID_CLIENT_ID,
  secret: process.env.PLAID_SECRET,
  environment: process.env.PLAID_ENV || 'sandbox', // sandbox, development, or production
};

const plaidConfig = new Configuration({
  basePath: PLAID_CONFIG.environment === 'production' 
    ? 'https://production.plaid.com'
    : 'https://sandbox.plaid.com',
  baseOptions: {
    headers: {
      'PLAID-CLIENT-ID': PLAID_CONFIG.clientId,
      'PLAID-SECRET': PLAID_CONFIG.secret,
      'Plaid-Version': '2020-09-14',
    },
  },
});

const plaidClient = new PlaidApi(plaidConfig);

// Dwolla Configuration
const DWOLLA_CONFIG = {
  key: process.env.DWOLLA_KEY,
  secret: process.env.DWOLLA_SECRET,
  environment: process.env.DWOLLA_ENV || 'sandbox',
  webhookSecret: process.env.DWOLLA_WEBHOOK_SECRET,
};

// Firebase App IDs (from existing config)
const APP_ID = process.env.FIREBASE_APP_ID || 'kalshi-trading-bot';
const USER_ID = process.env.FIREBASE_USER_ID || 'user-123';

// Initialize Firebase Admin
let firestoreDb = null;

try {
  const serviceAccount = require(path.join(__dirname, '../config/firebase_service_account.json'));
  
  admin.initializeApp({
    credential: admin.credential.cert(serviceAccount),
  });
  
  firestoreDb = admin.firestore();
  console.log('Firebase initialized successfully');
} catch (error) {
  console.error('Firebase initialization failed:', error.message);
  console.error('Running in limited mode without Firebase');
}

// Helper Functions
const getFirebasePath = (resource) => {
  return `artifacts/${APP_ID}/users/${USER_ID}/${resource}`;
};

const createDwollaAuth = () => {
  const credentials = Buffer.from(`${DWOLLA_CONFIG.key}:${DWOLLA_CONFIG.secret}`).toString('base64');
  return {
    'Authorization': `Basic ${credentials}`,
    'Content-Type': 'application/vnd.dwolla.v1.hal+json',
    'Accept': 'application/vnd.dwolla.v1.hal+json',
  };
};

const getDwollaBaseUrl = () => {
  return DWOLLA_CONFIG.environment === 'production'
    ? 'https://api.dwolla.com'
    : 'https://api-sandbox.dwolla.com';
};

// ==========================================
// PLAID ENDPOINTS
// ==========================================

/**
 * POST /plaid/create_link_token
 * Create a link token for Plaid Link initialization
 */
app.post('/plaid/create_link_token', async (req, res) => {
  try {
    const request = {
      user: {
        client_user_id: USER_ID,
      },
      client_name: 'Kalshi Trading Bot',
      products: [Products.Auth, Products.Transactions],
      country_codes: [CountryCode.Us],
      language: 'en',
      processor: 'dwolla',
    };

    const response = await plaidClient.linkTokenCreate(request);
    
    res.json({
      success: true,
      link_token: response.data.link_token,
      expiration: response.data.expiration,
    });
  } catch (error) {
    console.error('Error creating link token:', error);
    res.status(500).json({
      success: false,
      error: error.response?.data?.error_message || error.message,
    });
  }
});

/**
 * POST /plaid/exchange_public_token
 * Exchange public token for access token and create processor token
 */
app.post('/plaid/exchange_public_token', async (req, res) => {
  try {
    const { public_token } = req.body;

    if (!public_token) {
      return res.status(400).json({
        success: false,
        error: 'public_token is required',
      });
    }

    // Exchange public token for access token
    const exchangeResponse = await plaidClient.itemPublicTokenExchange({
      public_token,
    });

    const accessToken = exchangeResponse.data.access_token;

    // Create processor token for Dwolla
    const processorRequest = {
      access_token: accessToken,
      account_id: exchangeResponse.data.item_id,
      processor: ProcessorEnum.Dwolla,
    };

    const processorResponse = await plaidClient.processorTokenCreate(processorRequest);
    const processorToken = processorResponse.data.processor_token;

    // Store access_token in Firebase
    if (firestoreDb) {
      await firestoreDb
        .doc(getFirebasePath('plaid/access_token'))
        .set({
          token: accessToken,
          created_at: admin.firestore.FieldValue.serverTimestamp(),
        });
    }

    res.json({
      success: true,
      processor_token: processorToken,
      access_token: accessToken, // Return for immediate use
    });
  } catch (error) {
    console.error('Error exchanging public token:', error);
    res.status(500).json({
      success: false,
      error: error.response?.data?.error_message || error.message,
    });
  }
});

// ==========================================
// DWOLLA ENDPOINTS
// ==========================================

/**
 * POST /dwolla/customer
 * Create or retrieve Dwolla customer
 */
app.post('/dwolla/customer', async (req, res) => {
  try {
    const { first_name, last_name, email, type = 'personal' } = req.body;

    if (!first_name || !last_name || !email) {
      return res.status(400).json({
        success: false,
        error: 'first_name, last_name, and email are required',
      });
    }

    let customerUrl = null;

    // Check Firebase for existing customer
    if (firestoreDb) {
      const customerDoc = await firestoreDb
        .doc(getFirebasePath('dwolla/customer_url'))
        .get();

      if (customerDoc.exists) {
        customerUrl = customerDoc.data().url;
        return res.json({
          success: true,
          customer_url: customerUrl,
          message: 'Retrieved existing customer',
        });
      }
    }

    // Create new Dwolla customer
    const customerData = {
      firstName: first_name,
      lastName: last_name,
      email,
      type,
      ipAddress: req.ip || '0.0.0.0',
    };

    const response = await fetch(`${getDwollaBaseUrl()}/customers`, {
      method: 'POST',
      headers: createDwollaAuth(),
      body: JSON.stringify(customerData),
    });

    const responseData = await response.json();

    if (!response.ok) {
      throw new Error(responseData.message || 'Failed to create customer');
    }

    customerUrl = responseData._links.self.href;

    // Store customer URL in Firebase
    if (firestoreDb) {
      await firestoreDb
        .doc(getFirebasePath('dwolla/customer_url'))
        .set({
          url: customerUrl,
          created_at: admin.firestore.FieldValue.serverTimestamp(),
        });
    }

    res.json({
      success: true,
      customer_url: customerUrl,
      message: 'Customer created successfully',
    });
  } catch (error) {
    console.error('Error creating Dwolla customer:', error);
    res.status(500).json({
      success: false,
      error: error.message,
    });
  }
});

/**
 * POST /dwolla/funding-source
 * Create funding source from Plaid processor token
 */
app.post('/dwolla/funding-source', async (req, res) => {
  try {
    const { processor_token } = req.body;

    if (!processor_token) {
      return res.status(400).json({
        success: false,
        error: 'processor_token is required',
      });
    }

    // Get customer URL from Firebase
    if (!firestoreDb) {
      return res.status(500).json({
        success: false,
        error: 'Firebase not initialized',
      });
    }

    const customerDoc = await firestoreDb
      .doc(getFirebasePath('dwolla/customer_url'))
      .get();

    if (!customerDoc.exists) {
      return res.status(400).json({
        success: false,
        error: 'Dwolla customer must be created first',
      });
    }

    const customerUrl = customerDoc.data().url;

    // Create funding source
    const fundingSourceData = {
      plaidToken: processor_token,
    };

    const response = await fetch(`${customerUrl}/funding-sources`, {
      method: 'POST',
      headers: createDwollaAuth(),
      body: JSON.stringify(fundingSourceData),
    });

    const responseData = await response.json();

    if (!response.ok) {
      throw new Error(responseData.message || 'Failed to create funding source');
    }

    const fundingSourceUrl = responseData._links.self.href;

    // Store funding source URL in Firebase
    await firestoreDb
      .doc(getFirebasePath('dwolla/funding_source_url'))
      .set({
        url: fundingSourceUrl,
        created_at: admin.firestore.FieldValue.serverTimestamp(),
      });

    res.json({
      success: true,
      funding_source_url: fundingSourceUrl,
      message: 'Funding source created successfully',
    });
  } catch (error) {
    console.error('Error creating funding source:', error);
    res.status(500).json({
      success: false,
      error: error.message,
    });
  }
});

/**
 * POST /dwolla/transfers
 * Initiate ACH transfer
 */
app.post('/dwolla/transfers', async (req, res) => {
  try {
    const { amount, metadata } = req.body;

    if (!amount || amount <= 0) {
      return res.status(400).json({
        success: false,
        error: 'Valid amount is required',
      });
    }

    // Get funding source URL from Firebase
    if (!firestoreDb) {
      return res.status(500).json({
        success: false,
        error: 'Firebase not initialized',
      });
    }

    const fundingSourceDoc = await firestoreDb
      .doc(getFirebasePath('dwolla/funding_source_url'))
      .get();

    if (!fundingSourceDoc.exists) {
      return res.status(400).json({
        success: false,
        error: 'Funding source must be created first',
      });
    }

    const fundingSourceUrl = fundingSourceDoc.data().url;

    // Get customer URL for transfer source
    const customerDoc = await firestoreDb
      .doc(getFirebasePath('dwolla/customer_url'))
      .get();

    if (!customerDoc.exists) {
      return res.status(400).json({
        success: false,
        error: 'Dwolla customer must be created first',
      });
    }

    const customerUrl = customerDoc.data().url;

    // Create transfer with idempotency key
    const idempotencyKey = uuidv4();
    const transferData = {
      _links: {
        source: {
          href: customerUrl,
        },
        destination: {
          href: fundingSourceUrl,
        },
      },
      amount: {
        value: amount.toFixed(2),
        currency: 'USD',
      },
      metadata: metadata || {},
    };

    const response = await fetch(`${getDwollaBaseUrl()}/transfers`, {
      method: 'POST',
      headers: {
        ...createDwollaAuth(),
        'Idempotency-Key': idempotencyKey,
      },
      body: JSON.stringify(transferData),
    });

    const responseData = await response.json();

    if (!response.ok) {
      throw new Error(responseData.message || 'Failed to create transfer');
    }

    const transferId = responseData._links.self.href.split('/').pop();
    const transferUrl = responseData._links.self.href;

    // Store transfer record in Firebase
    await firestoreDb
      .collection('artifacts')
      .doc(APP_ID)
      .collection('users')
      .doc(USER_ID)
      .collection('transfers')
      .doc(transferId)
      .set({
        transfer_url: transferUrl,
        amount,
        idempotency_key: idempotencyKey,
        status: 'pending',
        created_at: admin.firestore.FieldValue.serverTimestamp(),
        metadata: metadata || {},
      });

    res.json({
      success: true,
      transfer_id: transferId,
      transfer_url: transferUrl,
      amount,
      status: 'pending',
      idempotency_key: idempotencyKey,
      message: 'Transfer initiated successfully',
    });
  } catch (error) {
    console.error('Error creating transfer:', error);
    res.status(500).json({
      success: false,
      error: error.message,
    });
  }
});

/**
 * POST /dwolla/webhook
 * Handle Dwolla webhook events for transfer updates
 */
app.post('/dwolla/webhook', async (req, res) => {
  try {
    const signature = req.headers['x-request-signature-sha-256'];

    // Verify webhook signature (simplified - should use proper HMAC verification)
    if (!signature) {
      console.warn('Missing webhook signature');
    }

    const { data } = req.body;

    if (!data || !data._links || !data._links.self) {
      return res.status(400).json({
        success: false,
        error: 'Invalid webhook payload',
      });
    }

    const topic = req.headers['dwolla-topic'] || 'unknown';
    const resourceId = data._links.self.href.split('/').pop();
    const resourceUrl = data._links.self.href;

    console.log(`Received Dwolla webhook: ${topic} for resource: ${resourceUrl}`);

    // Handle transfer status updates
    if (topic.includes('transfer')) {
      const status = data.status || 'unknown';
      
      if (firestoreDb) {
        await firestoreDb
          .collection('artifacts')
          .doc(APP_ID)
          .collection('users')
          .doc(USER_ID)
          .collection('transfers')
          .doc(resourceId)
          .update({
            status,
            updated_at: admin.firestore.FieldValue.serverTimestamp(),
            webhook_topic: topic,
          });
      }

      console.log(`Transfer ${resourceId} status updated to: ${status}`);
    }

    // Log reconciliation event
    console.log(`Reconciliation event: ${topic} - ${resourceUrl}`);

    res.status(200).json({
      success: true,
      message: 'Webhook received',
    });
  } catch (error) {
    console.error('Error processing webhook:', error);
    res.status(500).json({
      success: false,
      error: error.message,
    });
  }
});

// ==========================================
// HEALTH CHECK
// ==========================================

app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    service: 'ACH Transfer Microservice',
    firebase_initialized: firestoreDb !== null,
    plaid_configured: !!PLAID_CONFIG.clientId && !!PLAID_CONFIG.secret,
    dwolla_configured: !!DWOLLA_CONFIG.key && !!DWOLLA_CONFIG.secret,
  });
});

// ==========================================
// START SERVER
// ==========================================

app.listen(PORT, () => {
  console.log(`ACH Transfer Microservice running on port ${PORT}`);
  console.log(`Firebase initialized: ${firestoreDb !== null}`);
  console.log(`Plaid configured: ${!!PLAID_CONFIG.clientId}`);
  console.log(`Dwolla configured: ${!!DWOLLA_CONFIG.key}`);
});

module.exports = app;
