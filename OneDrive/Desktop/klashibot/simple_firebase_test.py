#!/usr/bin/env python3
"""
Simple Firebase Test
"""

import os
import sys
import json
from pathlib import Path

try:
    import firebase_admin
    from firebase_admin import credentials, firestore
    
    print("Testing Firebase connection...")
    
    # Check credentials file
    cred_path = "config/firebase_service_account.json"
    if not os.path.exists(cred_path):
        print("[ERROR] Credentials file not found")
        sys.exit(1)
    
    # Load credentials
    with open(cred_path, 'r') as f:
        cred_data = json.load(f)
    
    project_id = cred_data.get('project_id', 'Unknown')
    print(f"Project ID: {project_id}")
    
    # Initialize Firebase
    try:
        # Clear any existing apps
        try:
            firebase_admin.delete_app(firebase_admin.get_app())
        except:
            pass
        
        # Initialize with credentials
        cred = credentials.Certificate(cred_path)
        app = firebase_admin.initialize_app(cred)
        print("[SUCCESS] Firebase Admin SDK initialized")
        
        # Get Firestore client
        db = firestore.client()
        print("[SUCCESS] Firestore client created")
        
        # Test a simple read operation
        test_ref = db.collection('test').document('connection_test')
        test_ref.set({
            'message': 'Hello from Kalshi Trading Bot!',
            'timestamp': firestore.SERVER_TIMESTAMP
        })
        print("[SUCCESS] Test write successful!")
        
        # Test read
        doc = test_ref.get()
        if doc.exists:
            print(f"[SUCCESS] Test read successful: {doc.to_dict()}")
        
        print("\n[SUCCESS] Firebase is fully operational!")
        print("Your bot can now store and retrieve data from Firestore.")
        
    except Exception as e:
        print(f"[ERROR] Firebase operation failed: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure the Firestore database is created in the Firebase console")
        print("2. Check that the database is in the correct region")
        print("3. Verify the service account has Firestore permissions")
        
except ImportError as e:
    print(f"[ERROR] Firebase import failed: {e}")
    print("Make sure firebase-admin is installed: pip install firebase-admin")
