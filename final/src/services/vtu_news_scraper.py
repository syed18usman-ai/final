import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
from typing import List, Dict, Any
import logging
from urllib.parse import urljoin, urlparse
import time

logger = logging.getLogger(__name__)

class VTUNewsScraper:
    """Scraper for VTU official website news and announcements"""
    
    def __init__(self):
        self.base_url = "https://vtu.ac.in"
        self.news_urls = [
            "https://vtu.ac.in/announcements/",
            "https://vtu.ac.in/examination/",
            "https://vtu.ac.in/results/",
            "https://vtu.ac.in/academic-calendar/",
            # VTU Administration circulars/notifications listing (English site)
            "https://vtu.ac.in/en/category/administration/"
        ]
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def scrape_news(self) -> List[Dict[str, Any]]:
        """Scrape news from all VTU URLs"""
        all_news = []
        
        for url in self.news_urls:
            try:
                logger.info(f"Scraping news from: {url}")
                news_items = self._scrape_url(url)
                all_news.extend(news_items)
                time.sleep(1)  # Be respectful to the server
            except Exception as e:
                logger.error(f"Error scraping {url}: {e}")
                continue
        
        # Remove duplicates and sort by date
        unique_news = self._remove_duplicates(all_news)
        return sorted(unique_news, key=lambda x: x['published_date'], reverse=True)
    
    def _scrape_url(self, url: str) -> List[Dict[str, Any]]:
        """Scrape news from a specific URL"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            news_items = []
            
            # Specialized handling for VTU WordPress category archives (e.g., Administration)
            if "/en/category/administration/" in url:
                # Typical WP archive markup: articles with entry-title and posted-on/meta date
                for art in soup.select("article"):  # broader capture
                    # prefer h2.entry-title a
                    a = art.select_one("h2.entry-title a") or art.find("a")
                    if not a:
                        continue
                    title = a.get_text(strip=True)
                    link = a.get("href", "")
                    # date may be in time tag or within meta
                    time_tag = art.find("time")
                    date_text = time_tag.get_text(strip=True) if time_tag else self._extract_date(art)
                    published_date = self._parse_date(date_text)
                    news_items.append({
                        'id': f"vtu_admin_{hash(title + link)}",
                        'title': title,
                        'content': title,
                        'url': link,
                        'published_date': published_date,
                        'category': 'notification',
                        'relevance_semesters': list(range(1, 9)),
                        'relevance_subjects': []
                    })
            else:
                # Look for common news item patterns across other sections
                news_selectors = [
                    '.news-item',
                    '.announcement',
                    '.post',
                    '.article',
                    'li a',
                    '.list-group-item'
                ]
                
                for selector in news_selectors:
                    items = soup.select(selector)
                    for item in items:
                        news_item = self._extract_news_item(item, url)
                        if news_item:
                            news_items.append(news_item)
            
            return news_items
            
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return []
    
    def _extract_news_item(self, element, base_url: str) -> Dict[str, Any]:
        """Extract news item from HTML element"""
        try:
            # Extract title and link
            title_elem = element.find('a') or element
            title = title_elem.get_text(strip=True)
            link = title_elem.get('href', '')
            
            if not title or len(title) < 10:  # Skip very short titles
                return None
            
            # Make URL absolute
            if link and not link.startswith('http'):
                link = urljoin(base_url, link)
            
            # Extract date (look for various date patterns)
            date_text = self._extract_date(element)
            published_date = self._parse_date(date_text)
            
            # Determine category based on URL
            category = self._determine_category(base_url)
            
            # Determine relevance
            relevance_semesters, relevance_subjects = self._determine_relevance(title, element)
            
            return {
                'id': f"vtu_{hash(title + link)}",
                'title': title,
                'content': title,  # For now, use title as content
                'url': link,
                'published_date': published_date,
                'category': category,
                'relevance_semesters': relevance_semesters,
                'relevance_subjects': relevance_subjects
            }
            
        except Exception as e:
            logger.error(f"Error extracting news item: {e}")
            return None
    
    def _extract_date(self, element) -> str:
        """Extract date text from element"""
        # Look for date in various places
        date_patterns = [
            r'\d{1,2}[/-]\d{1,2}[/-]\d{4}',
            r'\d{4}[/-]\d{1,2}[/-]\d{1,2}',
            r'\d{1,2}\s+\w+\s+\d{4}',
            r'\w+\s+\d{1,2},?\s+\d{4}'
        ]
        
        text = element.get_text()
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group()
        
        return ""
    
    def _parse_date(self, date_text: str) -> datetime:
        """Parse date text to datetime object"""
        if not date_text:
            return datetime.now()
        
        # Try various date formats
        date_formats = [
            '%d/%m/%Y',
            '%d-%m-%Y',
            '%Y-%m-%d',
            '%Y/%m/%d',
            '%d %B %Y',
            '%B %d, %Y',
            '%d %b %Y',
            '%b %d, %Y'
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_text, fmt)
            except ValueError:
                continue
        
        return datetime.now()
    
    def _determine_category(self, url: str) -> str:
        """Determine news category based on URL"""
        if 'examination' in url or 'exam' in url:
            return 'exam'
        elif 'result' in url:
            return 'result'
        elif 'academic' in url or 'calendar' in url:
            return 'academic'
        elif 'announcement' in url:
            return 'notification'
        else:
            return 'general'
    
    def _determine_relevance(self, title: str, element) -> tuple[List[int], List[str]]:
        """Determine which semesters and subjects this news is relevant for"""
        title_lower = title.lower()
        text_lower = element.get_text().lower()
        combined_text = f"{title_lower} {text_lower}"
        
        # Semester relevance
        relevance_semesters = []
        for i in range(1, 9):  # VTU typically has 8 semesters
            if f"semester {i}" in combined_text or f"sem {i}" in combined_text:
                relevance_semesters.append(i)
        
        # If no specific semester mentioned, assume all
        if not relevance_semesters:
            relevance_semesters = list(range(1, 9))
        
        # Subject relevance
        relevance_subjects = []
        subject_keywords = {
            'ml': ['machine learning', 'ml'],
            'dl': ['deep learning', 'dl'],
            'crytography': ['cryptography', 'crypto'],
            'ADA': ['algorithm', 'ada', 'design analysis'],
            'BDA': ['big data', 'bda', 'analytics'],
            'physics': ['physics'],
            'WebProgramming': ['web programming', 'html', 'css', 'javascript']
        }
        
        for subject, keywords in subject_keywords.items():
            if any(keyword in combined_text for keyword in keywords):
                relevance_subjects.append(subject)
        
        return relevance_semesters, relevance_subjects
    
    def _remove_duplicates(self, news_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate news items"""
        seen = set()
        unique_items = []
        
        for item in news_items:
            item_id = item['id']
            if item_id not in seen:
                seen.add(item_id)
                unique_items.append(item)
        
        return unique_items

# Mock data for testing when scraping fails
MOCK_NEWS_DATA = [
    {
        'id': 'vtu_mock_1',
        'title': 'VTU Semester 7 Results Declared',
        'content': 'Results for Semester 7 examinations have been declared. Students can check their results on the official VTU website.',
        'url': 'https://vtu.ac.in/results/sem7',
        'published_date': datetime.now(),
        'category': 'result',
        'relevance_semesters': [7],
        'relevance_subjects': []
    },
    {
        'id': 'vtu_mock_2',
        'title': 'VTU Academic Calendar 2024-25 Released',
        'content': 'The academic calendar for the year 2024-25 has been released. Important dates for examinations and holidays are included.',
        'url': 'https://vtu.ac.in/academic-calendar/2024-25',
        'published_date': datetime.now(),
        'category': 'academic',
        'relevance_semesters': list(range(1, 9)),
        'relevance_subjects': []
    },
    {
        'id': 'vtu_mock_3',
        'title': 'Machine Learning Course Updates',
        'content': 'Updated syllabus and course materials for Machine Learning course are now available.',
        'url': 'https://vtu.ac.in/courses/ml-updates',
        'published_date': datetime.now(),
        'category': 'academic',
        'relevance_semesters': [7],
        'relevance_subjects': ['ml']
    }
]
