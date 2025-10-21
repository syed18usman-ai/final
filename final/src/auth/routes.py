from fastapi import APIRouter, HTTPException, Depends, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from typing import Optional
import secrets
import logging

from .auth_service import AuthService
from .google_oauth import GoogleOAuth

logger = logging.getLogger(__name__)

# Initialize auth service
auth_service = AuthService()

# Google OAuth configuration
import os
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "your-google-client-id")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "your-google-client-secret")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8002/auth/google/callback")

google_oauth = GoogleOAuth(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI)

router = APIRouter(prefix="/auth", tags=["authentication"])

def get_current_user(request: Request) -> Optional[dict]:
    """Get current user from request headers"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    
    token = auth_header.split(" ")[1]
    payload = auth_service.verify_token(token)
    
    if not payload or payload.get("type") != "access":
        return None
    
    return payload

@router.post("/register")
async def register(
    email: str = Form(...),
    password: str = Form(...),
    user_type: str = Form("student"),
    name: str = Form(""),
    college: str = Form(""),
    year: int = Form(1),
    semester: int = Form(1),
    branch: str = Form("")
):
    """Register a new user"""
    try:
        profile_data = {
            "name": name,
            "college": college,
            "year": year,
            "semester": semester,
            "branch": branch
        }
        
        user_data = auth_service.register_user(email, password, user_type, profile_data)
        tokens = auth_service.generate_tokens(user_data)
        
        return {
            "message": "User registered successfully",
            "user": user_data,
            "tokens": tokens
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")

@router.post("/login")
async def login(
    email: str = Form(...),
    password: str = Form(...)
):
    """Login user"""
    user_data = auth_service.authenticate_user(email, password)
    
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    tokens = auth_service.generate_tokens(user_data)
    
    return {
        "message": "Login successful",
        "user": user_data,
        "tokens": tokens
    }

@router.get("/google")
async def google_login():
    """Initiate Google OAuth login"""
    state = secrets.token_urlsafe(32)
    auth_url = google_oauth.get_authorization_url(state)
    return RedirectResponse(url=auth_url)

@router.get("/google/callback")
async def google_callback(code: str, state: str = None):
    """Handle Google OAuth callback"""
    try:
        google_user = await google_oauth.authenticate_user(code)
        user_data = auth_service.create_google_user(google_user)
        tokens = auth_service.generate_tokens(user_data)
        
        # In a real app, you'd redirect to a frontend page with tokens
        return {
            "message": "Google login successful",
            "user": user_data,
            "tokens": tokens
        }
    except Exception as e:
        logger.error(f"Google OAuth error: {e}")
        raise HTTPException(status_code=400, detail="Google authentication failed")

@router.get("/profile")
async def get_profile(current_user: dict = Depends(get_current_user)):
    """Get current user profile"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user = auth_service.get_user_by_email(current_user["email"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "user_id": user["user_id"],
        "email": user["email"],
        "user_type": user["user_type"],
        "profile": user["profile"]
    }

@router.put("/profile")
async def update_profile(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Update user profile"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        profile_data = await request.json()
        success = auth_service.update_user_profile(current_user["email"], profile_data)
        
        if not success:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {"message": "Profile updated successfully"}
    except Exception as e:
        logger.error(f"Profile update error: {e}")
        raise HTTPException(status_code=500, detail="Profile update failed")

@router.post("/refresh")
async def refresh_token(refresh_token: str = Form(...)):
    """Refresh access token"""
    payload = auth_service.verify_token(refresh_token)
    
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    
    user = auth_service.get_user_by_email(payload["email"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user_data = {
        "user_id": user["user_id"],
        "email": user["email"],
        "user_type": user["user_type"]
    }
    
    tokens = auth_service.generate_tokens(user_data)
    return tokens

@router.post("/logout")
async def logout():
    """Logout user (client should discard tokens)"""
    return {"message": "Logged out successfully"}

@router.get("/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    return current_user
