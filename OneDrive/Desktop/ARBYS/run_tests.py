#!/usr/bin/env python3
"""Run tests and capture output."""
import os
import subprocess
import sys

# Set environment variables
os.environ["TEST_MODE"] = "1"
os.environ["ODDS_API_KEY"] = "TEST_KEY"
os.environ["ARBYS_SUPPRESS_WIZARD"] = "1"

# Run pytest
result = subprocess.run(
    [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        "--maxfail=10",
        "-m",
        "not slow",
        "--cov=src",
        "--cov=gui",
        "--cov-report=term-missing",
    ],
    capture_output=True,
    text=True,
)

print(result.stdout)
print(result.stderr, file=sys.stderr)
sys.exit(result.returncode)
