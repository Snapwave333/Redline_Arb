#!/usr/bin/env python3
"""
Firebase Database Setup Helper
"""

import webbrowser
import json
import os

def setup_firestore_database():
    print("============================================================")
    print("FIREBASE FIRESTORE DATABASE SETUP")
    print("============================================================")
    print()
    
    # Load project ID from credentials
    cred_path = "config/firebase_service_account.json"
    if os.path.exists(cred_path):
        with open(cred_path, 'r') as f:
            cred_data = json.load(f)
        project_id = cred_data.get('project_id', 'your-project-id')
    else:
        project_id = 'your-project-id'
    
    print(f"Your Firebase Project ID: {project_id}")
    print()
    print("STEP 1: Create Firestore Database")
    print("--------------------------------")
    print("1. Go to Firebase Console: https://console.firebase.google.com/")
    print(f"2. Select your project: {project_id}")
    print("3. Click 'Firestore Database' in the left sidebar")
    print("4. Click 'Create database'")
    print("5. Select 'Start in test mode'")
    print("6. Choose a region (e.g., us-central1)")
    print("7. Click 'Done'")
    print()
    
    # Open the Firebase console
    firebase_url = f"https://console.firebase.google.com/project/{project_id}/firestore"
    print(f"Opening Firebase Console: {firebase_url}")
    
    try:
        webbrowser.open(firebase_url)
        print("[SUCCESS] Firebase Console opened in your browser")
    except:
        print("[INFO] Please manually open the Firebase Console")
    
    print()
    print("After creating the database, run: python test_firebase_connection.py")
    print("to verify the connection is working.")

if __name__ == "__main__":
    setup_firestore_database()
