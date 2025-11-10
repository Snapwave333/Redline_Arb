#!/usr/bin/env python3
"""Setup real Kalshi account credentials"""

print("Setting up your real Kalshi account...")

# Your real credentials
KALSHI_API_KEY = "8fe1b2e5-e094-4c1c-900f-27a02248c21a"
KALSHI_PRIVATE_KEY_PATH = "config/kalshi_private_key.pem"

# Write to .env file
with open('.env', 'w') as f:
    f.write(f"KALSHI_API_KEY={KALSHI_API_KEY}\n")
    f.write(f"KALSHI_PRIVATE_KEY={KALSHI_PRIVATE_KEY_PATH}\n")
    f.write("KALSHI_BASE_URL=https://api.elections.kalshi.com/trade-api/v2\n")

print("✅ Credentials saved to .env file")
print("Now the bot can connect to your real account!")

