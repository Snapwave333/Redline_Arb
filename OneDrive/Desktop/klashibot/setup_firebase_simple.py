#!/usr/bin/env python3
"""
Simple Firebase Setup Script for Kalshi Trading Bot
"""

import os
import json
from pathlib import Path

def setup_firebase():
    print("============================================================")
    print("FIREBASE SETUP FOR KALSHI TRADING BOT")
    print("============================================================")
    print()
    print("STEP 1: Create Firebase Project")
    print("------------------------------")
    print("1. Go to https://console.firebase.google.com/")
    print("2. Click 'Create a project' or 'Add project'")
    print("3. Enter project name: 'kalshi-trading-bot' (or your preferred name)")
    print("4. Enable Google Analytics (optional)")
    print("5. Click 'Create project'")
    print()
    print("STEP 2: Set up Firestore Database")
    print("--------------------------------")
    print("1. Click 'Firestore Database' in the left sidebar")
    print("2. Click 'Create database'")
    print("3. Select 'Start in test mode'")
    print("4. Choose a region close to you")
    print("5. Click 'Done'")
    print()
    print("STEP 3: Generate Service Account Key")
    print("------------------------------------")
    print("1. Go to Project Settings (gear icon)")
    print("2. Click 'Service accounts' tab")
    print("3. Click 'Generate new private key'")
    print("4. Click 'Generate key' in confirmation dialog")
    print("5. Download the JSON file")
    print()
    
    # Create config directory if it doesn't exist
    config_dir = Path("config")
    config_dir.mkdir(exist_ok=True)
    
    print("STEP 4: Configure Credentials")
    print("-----------------------------")
    print("Please paste the contents of your downloaded JSON file below.")
    print("(Copy the entire contents and paste, then press Ctrl+Z on Windows or Ctrl+D on Mac/Linux)")
    print()
    
    try:
        # Read the JSON content from stdin
        json_content = input("Paste your Firebase service account JSON here: ")
        
        # Parse and validate JSON
        try:
            service_account_data = json.loads(json_content)
            
            # Save to file
            service_account_file = config_dir / "firebase_service_account.json"
            with open(service_account_file, 'w') as f:
                json.dump(service_account_data, f, indent=2)
            
            print(f"\n[OK] Service account credentials saved to: {service_account_file}")
            
            # Update .env file
            env_file = Path(".env")
            if env_file.exists():
                with open(env_file, 'r') as f:
                    env_content = f.read()
                
                # Add Firebase project ID to .env
                project_id = service_account_data.get('project_id', '')
                if project_id and 'FIREBASE_PROJECT_ID=' not in env_content:
                    with open(env_file, 'a') as f:
                        f.write(f"\nFIREBASE_PROJECT_ID={project_id}\n")
                    print(f"[OK] Added FIREBASE_PROJECT_ID={project_id} to .env")
            
            print("\n[SUCCESS] Firebase setup completed!")
            print("Your bot can now connect to Firebase Firestore.")
            
        except json.JSONDecodeError as e:
            print(f"[ERROR] Invalid JSON format: {e}")
            return False
            
    except KeyboardInterrupt:
        print("\n[INFO] Setup cancelled by user")
        return False
    except Exception as e:
        print(f"[ERROR] Setup failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    setup_firebase()
