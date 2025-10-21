import jwt
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from passlib.context import CryptContext
import json
import os

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    def __init__(self, secret_key: str = None):
        self.secret_key = secret_key or os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 30
        self.refresh_token_expire_days = 7
        
        # User storage (in production, use a database)
        self.users_file = "data/users.json"
        self._ensure_users_file()
    
    def _ensure_users_file(self):
        """Ensure users file exists"""
        os.makedirs(os.path.dirname(self.users_file), exist_ok=True)
        if not os.path.exists(self.users_file):
            with open(self.users_file, 'w') as f:
                json.dump({}, f)
    
    def _load_users(self) -> Dict[str, Any]:
        """Load users from file"""
        try:
            with open(self.users_file, 'r') as f:
                return json.load(f)
        except:
            return {}
    
    def _save_users(self, users: Dict[str, Any]):
        """Save users to file"""
        with open(self.users_file, 'w') as f:
            json.dump(users, f, indent=2)
    
    def hash_password(self, password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.JWTError:
            return None
    
    def register_user(self, email: str, password: str, user_type: str = "student", 
                     profile_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Register a new user"""
        users = self._load_users()
        
        if email in users:
            raise ValueError("User already exists")
        
        user_id = secrets.token_urlsafe(16)
        hashed_password = self.hash_password(password)
        
        user_data = {
            "user_id": user_id,
            "email": email,
            "password_hash": hashed_password,
            "user_type": user_type,  # "student" or "admin"
            "profile": profile_data or {},
            "created_at": datetime.utcnow().isoformat(),
            "is_active": True
        }
        
        users[email] = user_data
        self._save_users(users)
        
        return {
            "user_id": user_id,
            "email": email,
            "user_type": user_type,
            "profile": profile_data or {}
        }
    
    def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user with email and password"""
        users = self._load_users()
        
        if email not in users:
            return None
        
        user = users[email]
        if not self.verify_password(password, user["password_hash"]):
            return None
        
        if not user.get("is_active", True):
            return None
        
        return {
            "user_id": user["user_id"],
            "email": user["email"],
            "user_type": user["user_type"],
            "profile": user.get("profile", {})
        }
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        users = self._load_users()
        return users.get(email)
    
    def update_user_profile(self, email: str, profile_data: Dict[str, Any]) -> bool:
        """Update user profile"""
        users = self._load_users()
        
        if email not in users:
            return False
        
        users[email]["profile"].update(profile_data)
        users[email]["updated_at"] = datetime.utcnow().isoformat()
        self._save_users(users)
        return True
    
    def create_google_user(self, google_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create or update user from Google OAuth data"""
        users = self._load_users()
        email = google_data["email"]
        
        if email in users:
            # Update existing user
            users[email]["profile"].update({
                "name": google_data.get("name", ""),
                "picture": google_data.get("picture", ""),
                "google_id": google_data.get("sub", ""),
                "last_login": datetime.utcnow().isoformat()
            })
            users[email]["updated_at"] = datetime.utcnow().isoformat()
        else:
            # Create new user
            user_id = secrets.token_urlsafe(16)
            users[email] = {
                "user_id": user_id,
                "email": email,
                "password_hash": "",  # No password for Google users
                "user_type": "student",  # Default to student
                "profile": {
                    "name": google_data.get("name", ""),
                    "picture": google_data.get("picture", ""),
                    "google_id": google_data.get("sub", ""),
                    "last_login": datetime.utcnow().isoformat()
                },
                "created_at": datetime.utcnow().isoformat(),
                "is_active": True
            }
        
        self._save_users(users)
        
        return {
            "user_id": users[email]["user_id"],
            "email": email,
            "user_type": users[email]["user_type"],
            "profile": users[email]["profile"]
        }
    
    def generate_tokens(self, user_data: Dict[str, Any]) -> Dict[str, str]:
        """Generate access and refresh tokens for user"""
        access_token = self.create_access_token({
            "sub": user_data["user_id"],
            "email": user_data["email"],
            "user_type": user_data["user_type"]
        })
        
        refresh_token = self.create_refresh_token({
            "sub": user_data["user_id"],
            "email": user_data["email"]
        })
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
