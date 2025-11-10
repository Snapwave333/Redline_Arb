#!/usr/bin/env python3
"""
Kalshi API Endpoint Diagnostic Tool

This standalone script tests various Kalshi API endpoints to identify
which ones are working and diagnose the 404 errors occurring in the bot.
"""

import os
import requests
import json
import logging
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ----------------------------------------------------------------------
# 1. SETUP: Configuration and Logging
# ----------------------------------------------------------------------

# Set up basic logging for clean console output
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def load_config() -> Dict[str, str]:
    """
    Loads necessary configuration from environment variables.
    """
    config = {
        "base_url": os.getenv("KALSHI_BASE_URL", "https://trading-api.kalshi.com/trade-api/v2"),
        "api_key": os.getenv("KALSHI_API_KEY"),
        "private_key": os.getenv("KALSHI_PRIVATE_KEY"),
    }
    
    if not config["api_key"]:
        logger.error("KALSHI_API_KEY not found in environment. Authentication will fail.")
    
    logger.info(f"Configuration loaded. Base URL: {config['base_url']}")
    return config

# ----------------------------------------------------------------------
# 2. DIAGNOSTIC REQUEST HANDLER
# ----------------------------------------------------------------------

def run_diagnostic_test(config: Dict[str, str], endpoint: str, method: str = "GET") -> Dict[str, Any]:
    """
    Executes a raw HTTP request against a specified endpoint and returns detailed results.
    """
    url = f"{config['base_url']}{endpoint}"
    
    if not config.get('api_key'):
        return {"STATUS": "FAILURE", "ERROR": "Missing API Key", "URL": url}

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        # Use the API Key as a Bearer token for standard REST API auth
        "Authorization": f"Bearer {config['api_key']}"
    }

    logger.info(f"Testing {method} {endpoint}")
    
    response = None
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        elif method == "POST":
            response = requests.post(url, headers=headers, json={}, timeout=10)
        
        # Check for non-2xx status codes
        if response.status_code >= 400:
            status = f"FAILURE (HTTP {response.status_code})"
            error = f"HTTP Error {response.status_code}"
            
            # Try to decode the body, if possible
            try:
                response_text = response.json()
            except json.JSONDecodeError:
                response_text = response.text
                
            return {
                "STATUS": status, 
                "ERROR": error, 
                "URL": url, 
                "RESPONSE_CODE": response.status_code, 
                "RESPONSE_BODY": response_text[:500] if isinstance(response_text, str) else response_text
            }

        # Success (2xx status code)
        try:
            data = response.json()
        except json.JSONDecodeError:
            data = {"raw_text": response.text[:200]}
            
        return {
            "STATUS": f"SUCCESS ({response.status_code})",
            "URL": url,
            "RESPONSE_CODE": response.status_code,
            "DATA": data
        }

    except requests.exceptions.RequestException as e:
        # Catch network errors, timeouts, etc.
        return {"STATUS": "FAILURE (Network Error)", "ERROR": f"{type(e).__name__}: {e}", "URL": url}
    except Exception as e:
        return {"STATUS": "FAILURE (Generic Error)", "ERROR": f"{type(e).__name__}: {e}", "URL": url}

# ----------------------------------------------------------------------
# 3. RESULT FORMATTING
# ----------------------------------------------------------------------

def print_result(name: str, result: Dict[str, Any]):
    """Formats and prints the result of a single diagnostic test."""
    
    print(f"\n{'='*70}")
    print(f"TEST: {name}")
    print(f"{'='*70}")
    print(f"STATUS: {result.get('STATUS', 'UNKNOWN')}")
    print(f"URL: {result['URL']}")

    if result['STATUS'].startswith("SUCCESS"):
        data = result.get('DATA', {})
        print(f"RESPONSE CODE: {result['RESPONSE_CODE']}")
        
        if isinstance(data, dict):
            keys = list(data.keys())
            if keys:
                print(f"RESPONSE KEYS: {keys}")
                # Show first few items
                snippet = {k: data[k] for k in keys[:3]}
                print(f"DATA SNIPPET: {json.dumps(snippet, indent=2, default=str)}")
            else:
                print("RESPONSE: Empty JSON object")
        else:
            print(f"RESPONSE: {data}")
        
    elif result['STATUS'].startswith("FAILURE"):
        print(f"ERROR: {result.get('ERROR', 'Unknown error')}")
        if 'RESPONSE_CODE' in result:
             print(f"RESPONSE CODE: {result['RESPONSE_CODE']}")
             
        # Print the problematic response body (the 404 message)
        body = result.get('RESPONSE_BODY', 'N/A')
        print(f"RESPONSE BODY: {body}")

# ----------------------------------------------------------------------
# 4. MAIN EXECUTION
# ----------------------------------------------------------------------

def main():
    """Runs the full diagnostic test suite."""
    print("\n" + "="*70)
    print("KALSHI API ENDPOINT DIAGNOSTIC TOOL")
    print("="*70)
    
    config = load_config()

    if not config['api_key']:
        print("\n\nCRITICAL FAILURE: Please set KALSHI_API_KEY in your .env file and try again.")
        return

    print(f"\nBASE URL: {config['base_url']}")
    print(f"API KEY: {config['api_key'][:10]}..." if config['api_key'] else "API KEY: Not set")
    
    # Endpoints to test based on the 404 issue and common alternatives
    endpoints_to_test = [
        # Original problematic endpoints
        ("Original /portfolio", "/portfolio", "GET"),
        ("Original /positions", "/positions", "GET"),
        
        # Alternative endpoint structures
        ("Alternative /exchange/balance", "/exchange/balance", "GET"),
        ("Alternative /exchange/positions", "/exchange/positions", "GET"),
        
        # Try with /portfolio prefix
        ("Portfolio Balance", "/portfolio/balance", "GET"),
        ("Portfolio Positions", "/portfolio/positions", "GET"),
        
        # Try with /exchange prefix
        ("Exchange Balance", "/exchange/balance", "GET"),
        ("Exchange Fills", "/exchange/fills", "GET"),
        
        # User/account endpoints
        ("User Info", "/users/me", "GET"),
        ("Account Balance", "/balance", "GET"),
        
        # Markets endpoint (should work if API is accessible)
        ("Markets List", "/markets", "GET"),
    ]
    
    results = {}
    for name, endpoint_path, method in endpoints_to_test:
        result = run_diagnostic_test(config, endpoint_path, method)
        results[name] = result
        print_result(name, result)
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    successes = [name for name, result in results.items() if result['STATUS'].startswith("SUCCESS")]
    failures = [name for name, result in results.items() if not result['STATUS'].startswith("SUCCESS")]
    
    print(f"\nSUCCESSFUL ENDPOINTS ({len(successes)}):")
    for name in successes:
        print(f"   - {name}")
    
    print(f"\nFAILED ENDPOINTS ({len(failures)}):")
    for name in failures:
        result = results[name]
        print(f"   - {name}: {result.get('ERROR', 'Unknown')}")
    
    print("\n" + "="*70)
    print("NEXT STEPS:")
    if successes:
        print("SUCCESS: Some endpoints are working! Update src/kalshi_client.py to use the working endpoints.")
    else:
        print("FAILURE: No endpoints working. Check:")
        print("   1. API key is valid and active")
        print("   2. Base URL is correct")
        print("   3. Account has proper permissions")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()

