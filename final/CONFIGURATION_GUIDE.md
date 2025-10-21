# VTU Study Assistant - Configuration Guide

## 🔧 Google OAuth Setup

### Quick Setup (Recommended)

1. **Run the setup script:**
   ```bash
   python setup_google_oauth.py
   ```

2. **Follow the prompts to enter your Google OAuth credentials**

### Manual Setup

1. **Create a `.env` file in the project root:**
   ```env
   # Google OAuth Configuration
   GOOGLE_CLIENT_ID=your-google-client-id-here
   GOOGLE_CLIENT_SECRET=your-google-client-secret-here
   GOOGLE_REDIRECT_URI=http://localhost:8002/auth/google/callback
   
   # JWT Secret Key (change this in production)
   JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production
   
   # OpenRouter API Key (for the chatbot)
   OPENROUTER_API_KEY=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
   ```

2. **Get Google OAuth Credentials:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing
   - Enable Google+ API and Google OAuth2 API
   - Go to "APIs & Services" → "Credentials"
   - Create OAuth 2.0 Client ID
   - Add redirect URI: `http://localhost:8002/auth/google/callback`
   - Copy Client ID and Client Secret

## 🚀 Starting the Application

1. **Activate virtual environment:**
   ```bash
   .\.venv\Scripts\Activate.ps1
   ```

2. **Start the server:**
   ```bash
   python -m uvicorn src.student_ui.app:app --host 127.0.0.1 --port 8002 --reload
   ```

3. **Access the application:**
   - Main App: http://localhost:8002/
   - Login/Register: http://localhost:8002/auth.html
   - Profile: http://localhost:8002/profile.html

## 🧪 Testing Google OAuth

1. Go to http://localhost:8002/auth.html
2. Click "Continue with Google"
3. Complete the OAuth flow
4. You should be redirected back to the main app

## 🔒 Security Notes

- Change the JWT_SECRET_KEY in production
- Use HTTPS in production
- Update GOOGLE_REDIRECT_URI for your production domain
- Keep your Google OAuth credentials secure

## 🐛 Troubleshooting

- **"Invalid client" error:** Check your Google OAuth credentials
- **"Redirect URI mismatch" error:** Ensure the redirect URI matches exactly
- **"Access denied" error:** Check OAuth consent screen configuration
