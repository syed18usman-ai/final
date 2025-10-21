# Google OAuth Setup Guide

## Step 1: Get Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Google+ API and Google OAuth2 API
4. Go to "APIs & Services" → "Credentials"
5. Create OAuth 2.0 Client ID
6. Add redirect URI: `http://localhost:8002/auth/google/callback`

## Step 2: Configure Environment Variables

Create a `.env` file in the project root with:

```env
# Google OAuth Configuration
GOOGLE_CLIENT_ID=your-google-client-id-here
GOOGLE_CLIENT_SECRET=your-google-client-secret-here
GOOGLE_REDIRECT_URI=http://localhost:8002/auth/google/callback

# JWT Secret Key (change this in production)
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production
```

## Step 3: Install python-dotenv

```bash
pip install python-dotenv
```

## Step 4: Update the Application

The application will automatically load these environment variables.

## Step 5: Test Google OAuth

1. Start the server
2. Go to `http://localhost:8002/auth.html`
3. Click "Continue with Google"
4. Complete the OAuth flow

## Production Setup

For production, update the redirect URI to your domain:
```
GOOGLE_REDIRECT_URI=https://yourdomain.com/auth/google/callback
```
