#!/usr/bin/env python3
"""
Firebase Database Region Solution
"""

import webbrowser
import json
import os

def solve_firebase_region():
    print("============================================================")
    print("FIREBASE DATABASE REGION SOLUTION")
    print("============================================================")
    print()
    
    # Load project ID
    cred_path = "config/firebase_service_account.json"
    with open(cred_path, 'r') as f:
        cred_data = json.load(f)
    project_id = cred_data.get('project_id', 'your-project-id')
    
    print(f"Project ID: {project_id}")
    print()
    print("ISSUE IDENTIFIED:")
    print("Your Firestore database exists but is in a different region")
    print("than what the Firebase Admin SDK expects.")
    print()
    
    print("SOLUTION OPTIONS:")
    print("================")
    print()
    print("OPTION 1: Find Current Database Region")
    print("--------------------------------------")
    print("1. Go to Firebase Console")
    print("2. Click 'Firestore Database'")
    print("3. Look for region info (e.g., 'europe-west1', 'asia-southeast1')")
    print("4. Note down the region")
    print()
    
    print("OPTION 2: Create New Database in us-central1 (Recommended)")
    print("--------------------------------------------------------")
    print("1. Go to Firebase Console")
    print("2. Click 'Firestore Database'")
    print("3. Click the gear icon (Settings)")
    print("4. Click 'Delete database' (if you want to start fresh)")
    print("5. Click 'Create database'")
    print("6. Select 'Start in test mode'")
    print("7. Choose region: us-central1")
    print("8. Click 'Done'")
    print()
    
    print("OPTION 3: Keep Current Database (If Region is Known)")
    print("---------------------------------------------------")
    print("If you know the region, we can configure the SDK to use it.")
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
    print("RECOMMENDATION:")
    print("Create a new database in us-central1 region for best compatibility.")
    print("After creating the new database, run: python region_aware_firebase_test.py")

if __name__ == "__main__":
    solve_firebase_region()
