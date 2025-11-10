#!/usr/bin/env python3
"""
Secure credential setup for Kalshi Trading Bot

This script helps you securely add your Kalshi API credentials.
"""

import os
import getpass
from pathlib import Path


def setup_kalshi_credentials():
    """Setup Kalshi API credentials securely"""
    print("Kalshi API Credential Setup")
    print("=" * 40)
    
    # Check if .env exists
    env_file = Path('.env')
    if not env_file.exists():
        print("ERROR: .env file not found. Please run 'python setup.py' first.")
        return False
    
    print("\nYou'll need your Kalshi API credentials:")
    print("   1. API Key (public key)")
    print("   2. Private Key (secret key)")
    print("\nGet these from: Kalshi Dashboard -> Settings -> API Keys")
    
    # Get credentials securely
    print("\nEnter your credentials:")
    api_key = getpass.getpass("API Key: ").strip()
    private_key = getpass.getpass("Private Key: ").strip()
    
    if not api_key or not private_key:
        print("ERROR: Both API Key and Private Key are required.")
        return False
    
    # Ask for environment preference
    print("\nChoose environment:")
    print("   1. Sandbox (recommended for testing)")
    print("   2. Production (live trading)")
    
    while True:
        choice = input("Enter choice (1 or 2): ").strip()
        if choice == "1":
            environment = "sandbox"
            break
        elif choice == "2":
            environment = "production"
            break
        else:
            print("ERROR: Please enter 1 or 2")
    
    # Update .env file
    try:
        # Read current .env content
        env_content = env_file.read_text()
        
        # Replace placeholder values
        env_content = env_content.replace("your_api_key_here", api_key)
        env_content = env_content.replace("your_private_key_here", private_key)
        env_content = env_content.replace("ENVIRONMENT=sandbox", f"ENVIRONMENT={environment}")
        
        # Write updated content
        env_file.write_text(env_content)
        
        print(f"\nSUCCESS: Credentials saved successfully!")
        print(f"   Environment: {environment}")
        print(f"   API Key: {api_key[:8]}...{api_key[-4:]}")
        
        # Validate configuration
        print("\nValidating configuration...")
        try:
            from src.config import config
            if config.validate_config():
                print("SUCCESS: Configuration is valid!")
                return True
            else:
                print("ERROR: Configuration validation failed.")
                return False
        except Exception as e:
            print(f"ERROR: Error validating config: {e}")
            return False
            
    except Exception as e:
        print(f"ERROR: Error saving credentials: {e}")
        return False


def show_next_steps():
    """Show next steps after credential setup"""
    print("\nNext Steps:")
    print("   1. Test connection: python cli.py config --validate")
    print("   2. Train models: python cli.py train TRUMP2024 ELECTION2024")
    print("   3. Start trading: python cli.py trade --tickers TRUMP2024 ELECTION2024")
    print("\nImportant:")
    print("   - Start with small amounts")
    print("   - Monitor logs closely")
    print("   - Use sandbox environment first")


if __name__ == "__main__":
    if setup_kalshi_credentials():
        show_next_steps()
    else:
        print("\nERROR: Setup failed. Please try again.")
        exit(1)
