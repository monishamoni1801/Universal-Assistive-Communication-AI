#!/usr/bin/env python3
"""
Run script for Universal Assistive Communication System
"""

import os
import sys
import logging

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, socketio

if __name__ == '__main__':
    print("="*60)
    print("🚀 UNIVERSAL ASSISTIVE COMMUNICATION SYSTEM")
    print("="*60)
    print("\n📱 DEEP LEARNING MODELS:")
    print("   1. Speech-to-Text (for Deaf users)")
    print("   2. Text-to-Sign (for Mute/Deaf users)")
    print("   3. Text-to-Speech (for Mute/Blind users)")
    print("   4. Sign-to-Text (for Mute users)")
    print("\n🔌 Starting Flask server...")
    print("   Connect your React Native app to this server")
    print("="*60)
    
    # Get local IP
    import socket
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    
    print(f"\n🌐 Server will be available at:")
    print(f"   ➜ Local:   http://localhost:5000")
    print(f"   ➜ Network: http://{local_ip}:5000")
    print(f"\n📱 Update your React Native api.js with:")
    print(f"   const BASE_URL = 'http://{local_ip}:5000';")
    print("="*60)
    
    # Run server
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)