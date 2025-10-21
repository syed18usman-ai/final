from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class UserProfile(BaseModel):
    """User profile model for VTU students"""
    user_id: str
    name: Optional[str] = None
    email: Optional[str] = None
    current_year: Optional[int] = None
    current_semester: Optional[int] = None
    branch: Optional[str] = None
    subjects: List[str] = []
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ProfileUpdate(BaseModel):
    """Model for updating user profile"""
    name: Optional[str] = None
    current_year: Optional[int] = None
    current_semester: Optional[int] = None
    branch: Optional[str] = None
    subjects: Optional[List[str]] = None

class NewsItem(BaseModel):
    """VTU news item model"""
    id: str
    title: str
    content: str
    url: str
    published_date: datetime
    category: str  # exam, result, notification, academic, etc.
    relevance_semesters: List[int] = []  # Which semesters this news is relevant for
    relevance_subjects: List[str] = []  # Which subjects this news is relevant for
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
