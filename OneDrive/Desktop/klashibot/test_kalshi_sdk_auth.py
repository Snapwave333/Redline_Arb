#!/usr/bin/env python3
"""
Test Kalshi SDK Authentication

This script tests the Kalshi SDK authentication methods to identify
the correct way to authenticate with the API.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path so we can import our modules
sys.path.append('src')

try:
    from kalshi_python import KalshiClient, Configuration, PortfolioApi, MarketsApi
    from kalshi_python.api_client import ApiClient
    from config import config
    
    print("="*70)
    print("KALSHI SDK AUTHENTICATION TEST")
    print("="*70)
    
    # Test 1: Check configuration
    print("\n1. CONFIGURATION CHECK:")
    print(f"   API Key: {config.api.kalshi_api_key[:10]}..." if config.api.kalshi_api_key else "   API Key: NOT SET")
    print(f"   Private Key: {config.api.kalshi_private_key[:50]}..." if config.api.kalshi_private_key else "   Private Key: NOT SET")
    print(f"   Base URL: {config.api.kalshi_base_url}")
    
    # Test 2: Try SDK authentication
    print("\n2. SDK AUTHENTICATION TEST:")
    try:
        # Initialize SDK client
        sdk_config = Configuration(host=config.api.kalshi_base_url)
        api_client = ApiClient(sdk_config)
        
        # Set authentication
        api_client.set_kalshi_auth(config.api.kalshi_api_key, config.api.kalshi_private_key)
        
        # Initialize API clients
        portfolio_api = PortfolioApi(api_client)
        markets_api = MarketsApi(api_client)
        
        print("   SUCCESS: SDK client initialized successfully")
        
        # Test 3: Try portfolio API calls
        print("\n3. PORTFOLIO API TEST:")
        try:
            # Test get_balance
            balance_response = portfolio_api.get_balance()
            print(f"   SUCCESS: get_balance() SUCCESS: {balance_response}")
        except Exception as e:
            print(f"   FAILED: get_balance() FAILED: {e}")
        
        try:
            # Test get_positions
            positions_response = portfolio_api.get_positions()
            print(f"   SUCCESS: get_positions() SUCCESS: {positions_response}")
        except Exception as e:
            print(f"   FAILED: get_positions() FAILED: {e}")
        
        # Test 4: Try markets API (should work)
        print("\n4. MARKETS API TEST:")
        try:
            markets_response = markets_api.get_markets(limit=5)
            print(f"   SUCCESS: get_markets() SUCCESS: Found {len(markets_response.markets) if markets_response.markets else 0} markets")
        except Exception as e:
            print(f"   FAILED: get_markets() FAILED: {e}")
            
    except Exception as e:
        print(f"   FAILED: SDK initialization FAILED: {e}")
    
    print("\n" + "="*70)
    print("TEST COMPLETE")
    print("="*70)
    
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure kalshi-python is installed: pip install kalshi-python")
except Exception as e:
    print(f"Unexpected error: {e}")

