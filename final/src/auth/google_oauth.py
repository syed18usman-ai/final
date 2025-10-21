import httpx
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class GoogleOAuth:
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.authorization_url = "https://accounts.google.com/o/oauth2/v2/auth"
        self.token_url = "https://oauth2.googleapis.com/token"
        self.user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"
    
    def get_authorization_url(self, state: str = None) -> str:
        """Generate Google OAuth authorization URL"""
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": "openid email profile",
            "response_type": "code",
            "access_type": "offline",
            "prompt": "consent"
        }
        
        if state:
            params["state"] = state
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{self.authorization_url}?{query_string}"
    
    async def exchange_code_for_tokens(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for access token"""
        async with httpx.AsyncClient() as client:
            data = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": self.redirect_uri
            }
            
            try:
                response = await client.post(self.token_url, data=data)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error(f"Error exchanging code for tokens: {e}")
                raise Exception("Failed to exchange authorization code")
    
    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get user information from Google"""
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {access_token}"}
            
            try:
                response = await client.get(self.user_info_url, headers=headers)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error(f"Error getting user info: {e}")
                raise Exception("Failed to get user information")
    
    async def authenticate_user(self, code: str) -> Dict[str, Any]:
        """Complete OAuth flow and return user data"""
        # Exchange code for tokens
        token_data = await self.exchange_code_for_tokens(code)
        access_token = token_data.get("access_token")
        
        if not access_token:
            raise Exception("No access token received")
        
        # Get user info
        user_info = await self.get_user_info(access_token)
        
        return {
            "sub": user_info.get("id"),
            "email": user_info.get("email"),
            "name": user_info.get("name"),
            "picture": user_info.get("picture"),
            "verified_email": user_info.get("verified_email", False)
        }
