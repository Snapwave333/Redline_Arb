#!/usr/bin/env python3
"""
Firebase Setup Script for Kalshi Trading Bot

This script guides the user through setting up Firebase for the trading bot dashboard.
"""

import os
import json
from pathlib import Path

def setup_firebase():
    """Guide user through Firebase setup"""
    print("=" * 60)
    print("FIREBASE SETUP FOR KALSHI TRADING BOT")
    print("=" * 60)
    print()
    print("This script will help you set up Firebase for the trading bot dashboard.")
    print("You'll need a Firebase project with Firestore enabled.")
    print()
    
    # Check if credentials already exist
    credentials_path = "firebase-credentials.json"
    if os.path.exists(credentials_path):
        print(f"[INFO] Firebase credentials already exist at {credentials_path}")
        response = input("Do you want to use existing credentials? (y/n): ").lower().strip()
        if response == 'y':
            print("[OK] Using existing Firebase credentials")
            return True
    
    print()
    print("STEP 1: Create Firebase Project")
    print("-" * 30)
    print("1. Go to https://console.firebase.google.com/")
    print("2. Click 'Create a project' or 'Add project'")
    print("3. Enter project name: 'kalshi-trading-bot' (or your preferred name)")
    print("4. Enable Google Analytics (optional)")
    print("5. Click 'Create project'")
    print()
    
    input("Press Enter when you've created the Firebase project...")
    
    print()
    print("STEP 2: Enable Firestore Database")
    print("-" * 30)
    print("1. In your Firebase project, go to 'Firestore Database'")
    print("2. Click 'Create database'")
    print("3. Choose 'Start in test mode' (for development)")
    print("4. Select a location (choose closest to you)")
    print("5. Click 'Done'")
    print()
    
    input("Press Enter when Firestore is enabled...")
    
    print()
    print("STEP 3: Generate Service Account Key")
    print("-" * 30)
    print("1. Go to Project Settings (gear icon)")
    print("2. Click on 'Service accounts' tab")
    print("3. Click 'Generate new private key'")
    print("4. Download the JSON file")
    print("5. Save it as 'firebase-credentials.json' in the project root")
    print()
    
    input("Press Enter when you've downloaded the service account key...")
    
    # Check if credentials file exists
    if not os.path.exists(credentials_path):
        print(f"[ERROR] {credentials_path} not found!")
        print("Please download the service account key and save it as 'firebase-credentials.json'")
        return False
    
    # Validate credentials file
    try:
        with open(credentials_path, 'r') as f:
            creds = json.load(f)
        
        required_fields = ['type', 'project_id', 'private_key', 'client_email']
        missing_fields = [field for field in required_fields if field not in creds]
        
        if missing_fields:
            print(f"[ERROR] Invalid credentials file. Missing fields: {missing_fields}")
            return False
        
        print(f"[OK] Firebase credentials validated")
        print(f"Project ID: {creds['project_id']}")
        print(f"Client Email: {creds['client_email']}")
        
    except json.JSONDecodeError:
        print("[ERROR] Invalid JSON in credentials file")
        return False
    except Exception as e:
        print(f"[ERROR] Failed to validate credentials: {e}")
        return False
    
    print()
    print("STEP 4: Configure Firestore Security Rules")
    print("-" * 30)
    print("For development, you can use these rules:")
    print()
    print("rules_version = '2';")
    print("service cloud.firestore {")
    print("  match /databases/{database}/documents {")
    print("    match /artifacts/{appId}/users/{userId}/{document=**} {")
    print("      allow read, write: if request.auth != null;")
    print("    }")
    print("  }")
    print("}")
    print()
    print("1. Go to Firestore Database > Rules")
    print("2. Replace the default rules with the above")
    print("3. Click 'Publish'")
    print()
    
    input("Press Enter when security rules are configured...")
    
    print()
    print("STEP 5: Test Firebase Connection")
    print("-" * 30)
    
    try:
        from src.firebase_manager import FirebaseManager
        
        # Initialize Firebase manager
        firebase_manager = FirebaseManager()
        firebase_manager.initialize()
        
        # Test connection
        print("Testing Firebase connection...")
        firebase_manager.update_bot_state({
            'test': True,
            'timestamp': 'test'
        })
        
        print("[OK] Firebase connection successful!")
        
        # Create sample data for testing
        response = input("Create sample data for testing the dashboard? (y/n): ").lower().strip()
        if response == 'y':
            firebase_manager.create_sample_data()
            print("[OK] Sample data created")
        
        print()
        print("=" * 60)
        print("FIREBASE SETUP COMPLETE!")
        print("=" * 60)
        print()
        print("Next steps:")
        print("1. Start the Python bot: python launch_real.py")
        print("2. Start the React dashboard: cd frontend && npm start")
        print("3. Open http://localhost:3000 to view the dashboard")
        print()
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Firebase test failed: {e}")
        print()
        print("Troubleshooting:")
        print("1. Check that firebase-credentials.json is in the project root")
        print("2. Verify the service account has Firestore permissions")
        print("3. Ensure Firestore is enabled in your Firebase project")
        return False

def main():
    """Main function"""
    try:
        success = setup_firebase()
        if success:
            print("[SUCCESS] Firebase setup completed successfully!")
        else:
            print("[ERROR] Firebase setup failed. Please check the errors above.")
            return 1
    except KeyboardInterrupt:
        print("\n[INFO] Setup cancelled by user")
        return 1
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
