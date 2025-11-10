#!/usr/bin/env python3
"""
Test Firebase Connection
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from firebase_manager import FirebaseManager
    print("Testing Firebase connection...")
    
    firebase_manager = FirebaseManager()
    firebase_manager.initialize()
    
    if firebase_manager.is_initialized:
        print("[SUCCESS] Firebase connected successfully!")
        print("Your bot can now store data persistently.")
    else:
        print("[WARNING] Firebase running in offline mode")
        print("Please complete the Firebase setup process.")
        
except Exception as e:
    print(f"[ERROR] Firebase test failed: {e}")
    print("Please ensure you have completed the Firebase setup.")
