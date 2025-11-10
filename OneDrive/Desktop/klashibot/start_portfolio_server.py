#!/usr/bin/env python3
"""Start portfolio server"""

import subprocess
import sys

print("Starting portfolio server on port 3002...")
subprocess.run([sys.executable, "src/portfolio_server.py"])

