import json
import os
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path
import logging

from ..models.user_profile import UserProfile, ProfileUpdate, NewsItem

logger = logging.getLogger(__name__)

class ProfileService:
    """Service for managing user profiles and news"""
    
    def __init__(self, data_dir: str = "data/profiles"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.profiles_file = self.data_dir / "profiles.json"
        self.news_file = self.data_dir / "news.json"
        self._load_data()
    
    def _load_data(self):
        """Load profiles and news from files"""
        # Load profiles
        if self.profiles_file.exists():
            try:
                with open(self.profiles_file, 'r') as f:
                    self.profiles = json.load(f)
            except Exception as e:
                logger.error(f"Error loading profiles: {e}")
                self.profiles = {}
        else:
            self.profiles = {}
        
        # Load news
        if self.news_file.exists():
            try:
                with open(self.news_file, 'r') as f:
                    self.news = json.load(f)
            except Exception as e:
                logger.error(f"Error loading news: {e}")
                self.news = []
        else:
            self.news = []
    
    def _save_data(self):
        """Save profiles and news to files"""
        try:
            # Save profiles
            with open(self.profiles_file, 'w') as f:
                json.dump(self.profiles, f, indent=2, default=str)
            
            # Save news
            with open(self.news_file, 'w') as f:
                json.dump(self.news, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving data: {e}")
    
    def create_profile(self, user_id: str, profile_data: Dict[str, Any]) -> UserProfile:
        """Create a new user profile"""
        profile = UserProfile(
            user_id=user_id,
            name=profile_data.get('name'),
            current_year=profile_data.get('current_year'),
            current_semester=profile_data.get('current_semester'),
            branch=profile_data.get('branch'),
            subjects=profile_data.get('subjects', [])
        )
        
        self.profiles[user_id] = profile.dict()
        self._save_data()
        
        logger.info(f"Created profile for user: {user_id}")
        return profile
    
    def get_profile(self, user_id: str) -> Optional[UserProfile]:
        """Get user profile by ID"""
        if user_id in self.profiles:
            return UserProfile(**self.profiles[user_id])
        return None
    
    def update_profile(self, user_id: str, update_data: ProfileUpdate) -> Optional[UserProfile]:
        """Update user profile"""
        if user_id not in self.profiles:
            return None
        
        profile_data = self.profiles[user_id]
        
        # Update fields
        for field, value in update_data.dict(exclude_unset=True).items():
            profile_data[field] = value
        
        profile_data['updated_at'] = datetime.now().isoformat()
        
        self.profiles[user_id] = profile_data
        self._save_data()
        
        logger.info(f"Updated profile for user: {user_id}")
        return UserProfile(**profile_data)
    
    def get_all_profiles(self) -> List[UserProfile]:
        """Get all user profiles"""
        return [UserProfile(**profile_data) for profile_data in self.profiles.values()]
    
    def add_news_item(self, news_item: NewsItem | Dict[str, Any]):
        """Add a news item"""
        # Coerce dicts into NewsItem
        if isinstance(news_item, dict):
            try:
                news_item = NewsItem(**news_item)
            except Exception as e:
                logger.error(f"Invalid news item payload, skipping: {e}")
                return
        # Check if news item already exists
        existing_ids = [item.get('id') for item in self.news]
        if news_item.id not in existing_ids:
            self.news.append(news_item.dict())
            self._save_data()
            logger.info(f"Added news item: {news_item.title}")
    
    def add_news_items(self, news_items: List[NewsItem] | List[Dict[str, Any]]):
        """Add multiple news items"""
        for news_item in news_items:
            self.add_news_item(news_item)

    def get_top_notifications(self, limit: int = 10) -> List[NewsItem]:
        """Get top N notification category items sorted by date desc"""
        items = [NewsItem(**n) for n in self.news if n.get('category') == 'notification']
        items.sort(key=lambda x: x.published_date, reverse=True)
        return items[:limit]
    
    def get_news_for_profile(self, user_id: str, limit: int = 10) -> List[NewsItem]:
        """Get news relevant to user's profile"""
        profile = self.get_profile(user_id)
        if not profile:
            return []
        
        relevant_news = []
        
        for news_data in self.news:
            news_item = NewsItem(**news_data)
            
            # Check if news is relevant to user's semester
            if (profile.current_semester and 
                profile.current_semester in news_item.relevance_semesters):
                relevant_news.append(news_item)
            elif not news_item.relevance_semesters:  # If no specific semester, include all
                relevant_news.append(news_item)
            
            # Check if news is relevant to user's subjects
            if (profile.subjects and 
                any(subject in news_item.relevance_subjects for subject in profile.subjects)):
                if news_item not in relevant_news:
                    relevant_news.append(news_item)
        
        # Sort by date and limit
        relevant_news.sort(key=lambda x: x.published_date, reverse=True)
        return relevant_news[:limit]
    
    def get_all_news(self, limit: int = 20) -> List[NewsItem]:
        """Get all news items"""
        news_items = [NewsItem(**news_data) for news_data in self.news]
        news_items.sort(key=lambda x: x.published_date, reverse=True)
        return news_items[:limit]
    
    def get_news_by_category(self, category: str, limit: int = 10) -> List[NewsItem]:
        """Get news by category"""
        news_items = [NewsItem(**news_data) for news_data in self.news 
                     if news_data.get('category') == category]
        news_items.sort(key=lambda x: x.published_date, reverse=True)
        return news_items[:limit]
    
    def search_news(self, query: str, limit: int = 10) -> List[NewsItem]:
        """Search news by title or content"""
        query_lower = query.lower()
        news_items = []
        
        for news_data in self.news:
            if (query_lower in news_data.get('title', '').lower() or 
                query_lower in news_data.get('content', '').lower()):
                news_items.append(NewsItem(**news_data))
        
        news_items.sort(key=lambda x: x.published_date, reverse=True)
        return news_items[:limit]
    
    def clear_old_news(self, days: int = 30):
        """Clear news older than specified days"""
        cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)
        
        original_count = len(self.news)
        self.news = [
            news_data for news_data in self.news
            if datetime.fromisoformat(news_data['published_date']).timestamp() > cutoff_date
        ]
        
        removed_count = original_count - len(self.news)
        if removed_count > 0:
            self._save_data()
            logger.info(f"Removed {removed_count} old news items")
