#!/usr/bin/env python3
"""
Setup script for Kalshi Trading Bot

This script helps set up the bot environment and validate configuration.
"""

import os
import sys
from pathlib import Path


def create_directories():
    """Create necessary directories"""
    directories = ['data', 'models', 'logs', 'tests']
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"[OK] Created directory: {directory}")


def create_env_file():
    """Create .env file from template"""
    env_file = Path('.env')
    template_file = Path('config.env.example')
    
    if not env_file.exists() and template_file.exists():
        env_file.write_text(template_file.read_text())
        print("[OK] Created .env file from template")
        print("  Please edit .env with your Kalshi API credentials")
    elif env_file.exists():
        print("[OK] .env file already exists")
    else:
        print("[ERROR] config.env.example not found")


def validate_python_version():
    """Validate Python version"""
    if sys.version_info < (3, 8):
        print("[ERROR] Python 3.8 or higher is required")
        return False
    
    print(f"[OK] Python version: {sys.version}")
    return True


def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = [
        'pandas', 'numpy', 'sklearn', 'aiohttp', 'websockets',
        'structlog', 'pydantic', 'dotenv'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"[OK] {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"[MISSING] {package}")
    
    if missing_packages:
        print(f"\nMissing packages: {', '.join(missing_packages)}")
        print("Install them with: pip install -r requirements.txt")
        return False
    
    return True


def validate_config():
    """Validate configuration"""
    try:
        from src.config import config
        
        if config.validate_config():
            print("[OK] Configuration is valid")
            return True
        else:
            print("[ERROR] Configuration validation failed")
            print("  Please check your .env file")
            return False
            
    except Exception as e:
        print(f"[ERROR] Configuration error: {e}")
        return False


def main():
    """Main setup function"""
    print("Kalshi Trading Bot Setup")
    print("=" * 30)
    
    # Validate Python version
    if not validate_python_version():
        sys.exit(1)
    
    print("\nCreating directories...")
    create_directories()
    
    print("\nCreating configuration...")
    create_env_file()
    
    print("\nChecking dependencies...")
    if not check_dependencies():
        print("\nPlease install missing dependencies and run setup again")
        sys.exit(1)
    
    print("\nValidating configuration...")
    if not validate_config():
        print("\nPlease fix configuration issues and run setup again")
        sys.exit(1)
    
    print("\n" + "=" * 30)
    print("[SUCCESS] Setup completed successfully!")
    print("\nNext steps:")
    print("1. Edit .env file with your Kalshi API credentials")
    print("2. Run: python cli.py train --tickers TRUMP2024 ELECTION2024")
    print("3. Run: python cli.py trade --tickers TRUMP2024 ELECTION2024")


if __name__ == "__main__":
    main()
