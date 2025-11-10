#!/usr/bin/env python3
"""
Firebase Database Region Configuration Script
Configures Firebase Firestore database to use us-central1 region
"""

import webbrowser
import json
import os
import sys
from pathlib import Path

def configure_firebase_region():
    print("============================================================")
    print("FIREBASE DATABASE REGION CONFIGURATION")
    print("============================================================")
    print()
    
    # Load project ID from service account
    cred_path = "config/firebase_service_account.json"
    if not os.path.exists(cred_path):
        print("[ERROR] Firebase service account file not found!")
        print("Please ensure config/firebase_service_account.json exists")
        return False
    
    with open(cred_path, 'r') as f:
        cred_data = json.load(f)
    
    project_id = cred_data.get('project_id', 'Unknown')
    print(f"Project ID: {project_id}")
    print(f"Target Region: us-central1")
    print()
    
    print("STEP 1: Access Firebase Console")
    print("-------------------------------")
    print("1. Go to Firebase Console")
    print("2. Select your project")
    print("3. Navigate to Firestore Database")
    print()
    
    print("STEP 2: Check Current Database Status")
    print("------------------------------------")
    print("Look for one of these scenarios:")
    print("• Database exists in us-central1 (Already configured)")
    print("• Database exists in different region (Needs migration)")
    print("• No database exists (Needs creation)")
    print()
    
    print("STEP 3: Configure Database for us-central1")
    print("-----------------------------------------")
    print("If database exists in different region:")
    print("1. Click the gear icon (Settings) next to Firestore Database")
    print("2. Click 'Delete database' (WARNING: This will delete all data)")
    print("3. Confirm deletion")
    print("4. Click 'Create database'")
    print("5. Select 'Start in test mode'")
    print("6. Choose region: us-central1")
    print("7. Click 'Done'")
    print()
    print("If no database exists:")
    print("1. Click 'Create database'")
    print("2. Select 'Start in test mode'")
    print("3. Choose region: us-central1")
    print("4. Click 'Done'")
    print()
    
    print("STEP 4: Configure Security Rules (Optional)")
    print("--------------------------------------------")
    print("For development/testing, you can use these rules:")
    print("rules_version = '2';")
    print("service cloud.firestore {")
    print("  match /databases/{database}/documents {")
    print("    match /{document=**} {")
    print("      allow read, write: if true;")
    print("    }")
    print("  }")
    print("}")
    print()
    
    # Open Firebase console
    firebase_url = f"https://console.firebase.google.com/project/{project_id}/firestore"
    print(f"Opening Firebase Console: {firebase_url}")
    
    try:
        webbrowser.open(firebase_url)
        print("[SUCCESS] Firebase Console opened in browser")
    except:
        print("[INFO] Please manually open the Firebase Console")
    
    print()
    print("STEP 5: Test Configuration")
    print("------------------------")
    print("After configuring the database, run:")
    print("python test_firebase_region_connection.py")
    print()
    
    print("IMPORTANT NOTES:")
    print("• us-central1 is the default region and provides best compatibility")
    print("• Deleting existing database will remove all data permanently")
    print("• Make sure to backup important data before migration")
    print("• The bot will automatically connect to us-central1 once configured")
    
    return True

def create_region_specific_test():
    """Create a test script for region-specific Firebase connection"""
    test_script = '''#!/usr/bin/env python3
"""
Firebase Region Connection Test - us-central1
"""

import os
import json
import firebase_admin
from firebase_admin import credentials, firestore

def test_firebase_region_connection():
    print("Testing Firebase connection to us-central1 region...")
    
    # Load credentials
    cred_path = "config/firebase_service_account.json"
    if not os.path.exists(cred_path):
        print("[ERROR] Firebase service account file not found!")
        return False
    
    with open(cred_path, 'r') as f:
        cred_data = json.load(f)
    
    project_id = cred_data.get('project_id', 'Unknown')
    print(f"Project ID: {project_id}")
    
    try:
        # Clear any existing apps
        try:
            firebase_admin.delete_app(firebase_admin.get_app())
        except:
            pass
        
        # Initialize Firebase
        cred = credentials.Certificate(cred_path)
        app = firebase_admin.initialize_app(cred)
        print("[SUCCESS] Firebase Admin SDK initialized")
        
        # Create Firestore client
        db = firestore.client()
        print("[SUCCESS] Firestore client created")
        
        # Test write operation
        test_ref = db.collection('_region_test').document('us_central1_test')
        test_ref.set({
            'message': 'Firebase us-central1 region test',
            'timestamp': firestore.SERVER_TIMESTAMP,
            'project_id': project_id,
            'region': 'us-central1'
        })
        print("[SUCCESS] Test write to us-central1 successful!")
        
        # Test read operation
        doc = test_ref.get()
        if doc.exists:
            data = doc.to_dict()
            print(f"[SUCCESS] Test read successful: {data}")
        
        # Clean up test document
        test_ref.delete()
        print("[INFO] Test document cleaned up")
        
        print("\\n[SUCCESS] Firebase us-central1 region is fully operational!")
        print("Your Kalshi Trading Bot can now store and retrieve data.")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Firebase connection failed: {e}")
        print("\\nTroubleshooting:")
        print("1. Ensure database is created in us-central1 region")
        print("2. Check service account permissions")
        print("3. Verify network connectivity")
        return False

if __name__ == "__main__":
    test_firebase_region_connection()
'''
    
    with open('test_firebase_region_connection.py', 'w') as f:
        f.write(test_script)
    
    print("[SUCCESS] Created test_firebase_region_connection.py")

if __name__ == "__main__":
    success = configure_firebase_region()
    if success:
        create_region_specific_test()
        print("\n[COMPLETE] Firebase region configuration guide created!")
        print("Next steps:")
        print("1. Follow the configuration steps above")
        print("2. Run: python test_firebase_region_connection.py")
        print("3. Start your trading bot")
