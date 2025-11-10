#!/usr/bin/env python3
"""
Debug Firebase Initialization
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    import firebase_admin
    from firebase_admin import credentials, firestore
    import json
    
    print("Testing Firebase initialization...")
    
    # Check if file exists
    cred_path = "config/firebase_service_account.json"
    print(f"Credentials path: {cred_path}")
    print(f"File exists: {os.path.exists(cred_path)}")
    
    if os.path.exists(cred_path):
        # Try to load the credentials
        try:
            with open(cred_path, 'r') as f:
                cred_data = json.load(f)
            print(f"Credentials loaded successfully. Project ID: {cred_data.get('project_id', 'Unknown')}")
            
            # Try to initialize Firebase
            try:
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
                db = firestore.client()
                print("[SUCCESS] Firebase initialized successfully!")
                
                # Test a simple write
                doc_ref = db.collection('test').document('test_doc')
                doc_ref.set({'test': 'data', 'timestamp': firestore.SERVER_TIMESTAMP})
                print("[SUCCESS] Test write successful!")
                
            except Exception as e:
                print(f"[ERROR] Firebase initialization failed: {e}")
                
        except Exception as e:
            print(f"[ERROR] Failed to load credentials: {e}")
    else:
        print("[ERROR] Credentials file not found")
        
except Exception as e:
    print(f"[ERROR] Import failed: {e}")
