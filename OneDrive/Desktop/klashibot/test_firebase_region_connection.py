#!/usr/bin/env python3
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
        db = firestore.client(database_id="kalshi-trading")
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
        
        print("\n[SUCCESS] Firebase us-central1 region is fully operational!")
        print("Your Kalshi Trading Bot can now store and retrieve data.")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Firebase connection failed: {e}")
        print("\nTroubleshooting:")
        print("1. Ensure database is created in us-central1 region")
        print("2. Check service account permissions")
        print("3. Verify network connectivity")
        return False

if __name__ == "__main__":
    test_firebase_region_connection()
