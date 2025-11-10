#!/usr/bin/env python3
"""
Region-Aware Firebase Test
"""

import os
import sys
import json
from pathlib import Path

try:
    import firebase_admin
    from firebase_admin import credentials, firestore
    
    print("Testing Firebase with Region Detection...")
    
    # Load credentials
    cred_path = "config/firebase_service_account.json"
    with open(cred_path, 'r') as f:
        cred_data = json.load(f)
    
    project_id = cred_data.get('project_id', 'Unknown')
    print(f"Project ID: {project_id}")
    
    # Clear any existing apps
    try:
        firebase_admin.delete_app(firebase_admin.get_app())
    except:
        pass
    
    # Initialize Firebase
    cred = credentials.Certificate(cred_path)
    app = firebase_admin.initialize_app(cred)
    print("[SUCCESS] Firebase Admin SDK initialized")
    
    # Try different approaches to get Firestore client
    print("\nTrying different Firestore connection methods...")
    
    # Method 1: Default client
    try:
        db = firestore.client()
        print("[SUCCESS] Default Firestore client created")
        
        # Test with a simple collection that should work
        test_ref = db.collection('_test').document('connection_test')
        test_ref.set({
            'message': 'Hello from Kalshi Trading Bot!',
            'timestamp': firestore.SERVER_TIMESTAMP,
            'project_id': project_id
        })
        print("[SUCCESS] Test write to _test collection successful!")
        
        # Test read
        doc = test_ref.get()
        if doc.exists:
            data = doc.to_dict()
            print(f"[SUCCESS] Test read successful: {data}")
        
        print("\n[SUCCESS] Firebase is fully operational!")
        print("Your bot can now store and retrieve data from Firestore.")
        
        # Clean up test document
        test_ref.delete()
        print("[INFO] Test document cleaned up")
        
    except Exception as e:
        print(f"[ERROR] Firestore operation failed: {e}")
        
        # Method 2: Try with explicit project
        try:
            print("\nTrying with explicit project ID...")
            db = firestore.client(project=project_id)
            
            test_ref = db.collection('_test').document('connection_test')
            test_ref.set({
                'message': 'Hello from Kalshi Trading Bot!',
                'timestamp': firestore.SERVER_TIMESTAMP,
                'project_id': project_id
            })
            print("[SUCCESS] Test write with explicit project ID successful!")
            
        except Exception as e2:
            print(f"[ERROR] Explicit project method also failed: {e2}")
            
            print("\nTroubleshooting suggestions:")
            print("1. Check if the database region matches your Firebase console")
            print("2. Verify the service account has Firestore permissions")
            print("3. Try recreating the database in us-central1 region")
            print("4. Check if there are any firewall restrictions")
        
except ImportError as e:
    print(f"[ERROR] Firebase import failed: {e}")
    print("Make sure firebase-admin is installed: pip install firebase-admin")
except Exception as e:
    print(f"[ERROR] Unexpected error: {e}")
