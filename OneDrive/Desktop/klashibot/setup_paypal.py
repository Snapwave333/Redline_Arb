#!/usr/bin/env python3
"""
PayPal Setup Script for Kalshi Trading Bot

This script helps you configure PayPal API credentials for automatic $400 daily transfers.
"""

import os
import sys
from pathlib import Path

def setup_paypal_credentials():
    """Setup PayPal API credentials for automatic transfers"""
    
    print("=" * 60)
    print("PAYPAL SETUP FOR AUTOMATIC $400 DAILY TRANSFERS")
    print("=" * 60)
    print()
    print("This script will help you configure PayPal API credentials")
    print("for automatic daily transfers of $400 to your PayPal account.")
    print()
    
    # Check if .env file exists
    env_file = Path(".env")
    if not env_file.exists():
        print("ERROR: .env file not found!")
        print("Please run 'python setup.py' first to create the .env file.")
        return False
    
    print("Step 1: PayPal Developer Account Setup")
    print("-" * 40)
    print("1. Go to https://developer.paypal.com/")
    print("2. Sign in with your PayPal account")
    print("3. Create a new application:")
    print("   - Click 'Create App'")
    print("   - Choose 'Default Application'")
    print("   - Select 'Sandbox' for testing (or 'Live' for production)")
    print("4. Copy your Client ID and Client Secret")
    print()
    
    # Get PayPal credentials
    paypal_client_id = input("Enter your PayPal Client ID: ").strip()
    if not paypal_client_id:
        print("ERROR: PayPal Client ID is required!")
        return False
    
    paypal_client_secret = input("Enter your PayPal Client Secret: ").strip()
    if not paypal_client_secret:
        print("ERROR: PayPal Client Secret is required!")
        return False
    
    print()
    print("Step 2: PayPal Account Configuration")
    print("-" * 40)
    print("Enter the PayPal email address where you want to receive")
    print("the daily $400 transfers (this should be your PayPal account).")
    print()
    
    recipient_email = input("Enter your PayPal email address: ").strip()
    if not recipient_email or "@" not in recipient_email:
        print("ERROR: Valid PayPal email address is required!")
        return False
    
    print()
    print("Step 3: Transfer Configuration")
    print("-" * 40)
    print("Configure the automatic transfer settings:")
    print()
    
    # Transfer time
    transfer_time = input("Enter transfer time (HH:MM format, default 18:00): ").strip()
    if not transfer_time:
        transfer_time = "18:00"
    
    # Validate time format
    try:
        hour, minute = map(int, transfer_time.split(':'))
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError
    except ValueError:
        print("ERROR: Invalid time format! Using default 18:00")
        transfer_time = "18:00"
    
    # Mode selection
    print()
    print("Select PayPal mode:")
    print("1. Sandbox (for testing - recommended)")
    print("2. Live (for production - real money)")
    
    mode_choice = input("Enter choice (1 or 2, default 1): ").strip()
    paypal_mode = "sandbox" if mode_choice != "2" else "live"
    
    print()
    print("Step 4: Updating Configuration")
    print("-" * 40)
    
    # Read current .env file
    try:
        with open(".env", "r") as f:
            lines = f.readlines()
    except Exception as e:
        print(f"ERROR: Could not read .env file: {e}")
        return False
    
    # Update PayPal settings
    paypal_settings = {
        "PAYPAL_ENABLED": "true",
        "PAYPAL_CLIENT_ID": paypal_client_id,
        "PAYPAL_CLIENT_SECRET": paypal_client_secret,
        "PAYPAL_MODE": paypal_mode,
        "PAYPAL_RECIPIENT_EMAIL": recipient_email,
        "DAILY_TRANSFER_ENABLED": "true",
        "DAILY_TRANSFER_AMOUNT": "400.0",
        "MIN_TRANSFER_AMOUNT": "400.0",
        "MAX_TRANSFER_AMOUNT": "400.0",
        "TRANSFER_FREQUENCY": "daily",
        "TRANSFER_TIME": transfer_time,
        "AUTO_TRANSFER_ENABLED": "true"
    }
    
    # Update or add PayPal settings
    updated_lines = []
    paypal_keys_found = set()
    
    for line in lines:
        line = line.strip()
        if "=" in line:
            key = line.split("=")[0].strip()
            if key.startswith("PAYPAL_") or key in ["DAILY_TRANSFER_", "MIN_TRANSFER_", "MAX_TRANSFER_", "TRANSFER_", "AUTO_TRANSFER_"]:
                paypal_keys_found.add(key)
                continue  # Skip old PayPal settings
        
        if line and not line.startswith("#"):
            updated_lines.append(line + "\n")
    
    # Add new PayPal settings
    updated_lines.append("\n# PayPal Integration Settings - $400 Daily Transfer\n")
    for key, value in paypal_settings.items():
        updated_lines.append(f"{key}={value}\n")
    
    # Write updated .env file
    try:
        with open(".env", "w") as f:
            f.writelines(updated_lines)
    except Exception as e:
        print(f"ERROR: Could not write .env file: {e}")
        return False
    
    print("PayPal configuration updated successfully!")
    print()
    
    print("Step 5: Configuration Summary")
    print("-" * 40)
    print(f"PayPal Mode: {paypal_mode}")
    print(f"Recipient Email: {recipient_email}")
    print(f"Daily Transfer Amount: $400.00")
    print(f"Transfer Time: {transfer_time}")
    print(f"Auto Transfer: Enabled")
    print()
    
    print("Step 6: Testing Setup")
    print("-" * 40)
    print("To test your PayPal integration:")
    print("1. Run: python cli.py status")
    print("2. Check the 'paypal_transfer_summary' section")
    print("3. Verify your credentials are loaded correctly")
    print()
    
    if paypal_mode == "sandbox":
        print("IMPORTANT: You're using SANDBOX mode!")
        print("- This is for testing only - no real money will be transferred")
        print("- To switch to live mode, update PAYPAL_MODE=live in .env")
        print("- Make sure you have sufficient funds in your sandbox account")
    else:
        print("IMPORTANT: You're using LIVE mode!")
        print("- Real money will be transferred to your PayPal account")
        print("- Make sure you have sufficient funds in your trading account")
        print("- Test thoroughly in sandbox mode first!")
    
    print()
    print("Step 7: Next Steps")
    print("-" * 40)
    print("1. Install PayPal SDK: pip install paypalrestsdk")
    print("2. Start trading: python cli.py trade --tickers TRUMP2024 ELECTION2024")
    print("3. Monitor transfers: python cli.py status")
    print("4. Check PayPal account for daily $400 transfers")
    print()
    
    print("=" * 60)
    print("PAYPAL SETUP COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print()
    print("Your bot will now automatically transfer $400 daily to your PayPal account!")
    print("Make sure to monitor the bot's performance and transfer status.")
    
    return True

def main():
    """Main function"""
    try:
        success = setup_paypal_credentials()
        if success:
            print("\nSetup completed successfully!")
            sys.exit(0)
        else:
            print("\nSetup failed!")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
