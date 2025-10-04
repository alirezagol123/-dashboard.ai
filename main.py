#!/usr/bin/env python3
"""
Main entry point for Liara deployment
This file calls start_server.py
"""

import subprocess
import sys
import os

if __name__ == "__main__":
    try:
        # Change to the app directory
        os.chdir('/usr/src/app')
        
        # Run start_server.py
        subprocess.run([sys.executable, 'start_server.py'], check=True)
    except Exception as e:
        print(f"Error running start_server.py: {e}")
        sys.exit(1)
