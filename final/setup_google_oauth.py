#!/usr/bin/env python3
"""
Google OAuth Setup Script for VTU Study Assistant
This script helps you configure Google OAuth credentials.
"""

import os
from pathlib import Path

def create_env_file():
    """Create .env file with Google OAuth configuration"""
    
    print("🔧 Google OAuth Setup for VTU Study Assistant")
    print("=" * 50)
    
    print("\n📋 Before we start, you need to:")
    print("1. Go to https://console.cloud.google.com/")
    print("2. Create a new project or select existing")
    print("3. Enable Google+ API and Google OAuth2 API")
    print("4. Create OAuth 2.0 Client ID")
    print("5. Add redirect URI: http://localhost:8002/auth/google/callback")
    print("6. Copy your Client ID and Client Secret")
    
    print("\n" + "=" * 50)
    
    # Get credentials from user
    client_id = input("\n🔑 Enter your Google Client ID: ").strip()
    client_secret = input("🔐 Enter your Google Client Secret: ").strip()
    
    if not client_id or not client_secret:
        print("❌ Error: Both Client ID and Client Secret are required!")
        return False
    
    # Create .env file
    env_content = f"""# Google OAuth Configuration
GOOGLE_CLIENT_ID={client_id}
GOOGLE_CLIENT_SECRET={client_secret}
GOOGLE_REDIRECT_URI=http://localhost:8002/auth/google/callback

# JWT Secret Key (change this in production)
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production-{os.urandom(16).hex()}

# OpenRouter API Key (for the chatbot)
OPENROUTER_API_KEY=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
"""
    
    env_file = Path(".env")
    with open(env_file, "w") as f:
        f.write(env_content)
    
    print(f"\n✅ Created .env file with your Google OAuth credentials!")
    print(f"📁 File location: {env_file.absolute()}")
    
    print("\n🚀 Next steps:")
    print("1. Start the server: python -m uvicorn src.student_ui.app:app --host 127.0.0.1 --port 8002 --reload")
    print("2. Go to http://localhost:8002/auth.html")
    print("3. Click 'Continue with Google' to test OAuth")
    
    return True

def check_existing_env():
    """Check if .env file already exists"""
    env_file = Path(".env")
    if env_file.exists():
        print("⚠️  .env file already exists!")
        response = input("Do you want to overwrite it? (y/N): ").strip().lower()
        if response != 'y':
            print("❌ Setup cancelled.")
            return False
    return True

if __name__ == "__main__":
    try:
        if check_existing_env():
            create_env_file()
    except KeyboardInterrupt:
        print("\n❌ Setup cancelled by user.")
    except Exception as e:
        print(f"❌ Error: {e}")
