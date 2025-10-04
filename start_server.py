#!/usr/bin/env python3
"""
Simple startup script for Smart Agriculture Dashboard with Real LLM
"""

import os
import sys

# Set environment variables for Real LLM BEFORE any imports
os.environ['OPENAI_API_KEY'] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySUQiOiI2ODQ1NzQzNDdkOTQ0NDlhMzc2NDFhNzgiLCJ0eXBlIjoiYXV0aCIsImlhdCI6MTc1ODEzNDY2N30.BdDAu4IF_y2oVZPUyZH41Ap_PZpfjZwRJoR3V8CCsGk'
os.environ['OPENAI_API_BASE'] = 'https://ai.liara.ir/api/v1/688a24a93d0c49e74e362a7f'
os.environ['OPENAI_MODEL_NAME'] = 'openai/gpt-4o-mini'

print("Smart Agriculture Dashboard - Real LLM Ready!")
print("=" * 50)
print("Configuration:")
print(f"   API Key: {'SET' if os.getenv('OPENAI_API_KEY') else 'NOT SET'}")
print(f"   Base URL: {os.getenv('OPENAI_API_BASE')}")
print(f"   Model: {os.getenv('OPENAI_MODEL_NAME')}")
print("=" * 50)

# Now import uvicorn after setting environment variables
import uvicorn

if __name__ == "__main__":
    try:
        # Get port and host from environment variables (for Liara)
        port_str = os.getenv("PORT", "8000")
        port = int(port_str) if port_str else 8000
        host = os.getenv("HOST", "0.0.0.0")
        
        print(f"Environment variables:")
        print(f"  PORT: '{os.getenv('PORT', 'NOT SET')}'")
        print(f"  HOST: '{os.getenv('HOST', 'NOT SET')}'")
        print(f"  PORT_STR: '{port_str}'")
        print(f"  Final PORT: {port}")
        print(f"Starting server on {host}:{port}")
        
        uvicorn.run(
            "app.main:app",
            host=host,
            port=port,
            reload=False,  # Disable reload in production
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Server error: {e}")
