#!/usr/bin/env python3
"""
Firebase Database Region Checker
"""

import webbrowser
import json
import os

def check_firebase_region():
    print("============================================================")
    print("FIREBASE DATABASE REGION CHECKER")
    print("============================================================")
    print()
    
    # Load project ID
    cred_path = "config/firebase_service_account.json"
    if os.path.exists(cred_path):
        with open(cred_path, 'r') as f:
            cred_data = json.load(f)
        project_id = cred_data.get('project_id', 'your-project-id')
    else:
        project_id = 'your-project-id'
    
    print(f"Project ID: {project_id}")
    print()
    print("STEP 1: Check Database Region")
    print("----------------------------")
    print("1. Go to Firebase Console: https://console.firebase.google.com/")
    print(f"2. Select project: {project_id}")
    print("3. Click 'Firestore Database'")
    print("4. Look at the top of the page for the region (e.g., 'us-central1')")
    print("5. Note down the region")
    print()
    
    print("STEP 2: Verify Database Type")
    print("---------------------------")
    print("Make sure you see 'Cloud Firestore' not 'Cloud Datastore'")
    print("If you see 'Cloud Datastore', you need to create a Firestore database")
    print()
    
    print("STEP 3: If Database Doesn't Work")
    print("-------------------------------")
    print("1. Delete the existing database (if any)")
    print("2. Create a new Firestore database")
    print("3. Select 'Start in test mode'")
    print("4. Choose region: us-central1 (recommended)")
    print("5. Click 'Done'")
    print()
    
    # Open Firebase console
    firebase_url = f"https://console.firebase.google.com/project/{project_id}/firestore"
    print(f"Opening Firebase Console: {firebase_url}")
    
    try:
        webbrowser.open(firebase_url)
        print("[SUCCESS] Firebase Console opened")
    except:
        print("[INFO] Please manually open the Firebase Console")
    
    print()
    print("After checking/creating the database, run:")
    print("python simple_firebase_test.py")

if __name__ == "__main__":
    check_firebase_region()
