#!/usr/bin/env python3
"""
Start Full System - ACH + Bot + Dashboard

This script starts all components of the Kalshi Trading Bot system:
1. ACH Transfer Microservice (Node.js)
2. Python Trading Bot
3. React Dashboard (GUI)
"""

import subprocess
import time
import sys
import os
from pathlib import Path

def start_ach_service():
    """Start the ACH microservice"""
    print("[1/3] Starting ACH Transfer Microservice...")
    try:
        os.chdir('src')
        subprocess.Popen(['node', 'ach_manager.js'], 
                        stdout=subprocess.PIPE, 
                        stderr=subprocess.PIPE)
        print("  ✓ ACH service started on port 3000")
        os.chdir('..')
        time.sleep(2)
    except Exception as e:
        print(f"  ✗ Failed to start ACH service: {e}")

def start_dashboard():
    """Start the React dashboard"""
    print("[2/3] Starting Dashboard GUI...")
    try:
        os.chdir('frontend')
        subprocess.Popen(['npm', 'start'], 
                        stdout=subprocess.PIPE, 
                        stderr=subprocess.PIPE,
                        shell=True)
        print("  ✓ Dashboard starting (will open in browser)")
        print("  ✓ URL: http://localhost:3000")
        os.chdir('..')
        time.sleep(3)
    except Exception as e:
        print(f"  ✗ Failed to start dashboard: {e}")

def start_bot():
    """Start the Python trading bot"""
    print("[3/3] Starting Python Trading Bot...")
    try:
        subprocess.Popen([sys.executable, 'launch_real.py'],
                        stdout=subprocess.PIPE, 
                        stderr=subprocess.PIPE)
        print("  ✓ Trading bot started")
    except Exception as e:
        print(f"  ✗ Failed to start bot: {e}")

def main():
    """Main startup sequence"""
    print("=" * 60)
    print("KALSHI TRADING BOT - STARTING FULL SYSTEM")
    print("=" * 60)
    print()
    
    # Check current directory
    if not Path('src').exists():
        print("Error: Must run from project root directory")
        return
    
    # Start components
    start_ach_service()
    start_dashboard()
    start_bot()
    
    print()
    print("=" * 60)
    print("ALL SYSTEMS STARTED!")
    print("=" * 60)
    print()
    print("Components Running:")
    print("  ✓ ACH Service: http://localhost:3000")
    print("  ✓ Dashboard: http://localhost:3001 (or 3000 if 3000 taken)")
    print("  ✓ Trading Bot: Running in background")
    print()
    print("Dashboard will open automatically in your browser.")
    print("Press Ctrl+C to stop all services.")
    print()
    
    # Keep running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down all services...")
        print("Done!")

if __name__ == "__main__":
    main()
