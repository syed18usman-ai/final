class NewsPage {
    constructor() {
        this.newsFeed = document.getElementById('news-feed');
        this.refreshBtn = document.getElementById('refresh-news');
        this.categoryFilter = document.getElementById('news-category-filter');
        this.navigation = null; // will be injected by main
        this.currentUserId = this.getCurrentUserId();
        this.setupEventListeners();
        this.loadNews();
    }

    getCurrentUserId() {
        // For now, use a default user ID. In a real app, this would come from authentication
        return localStorage.getItem('vtu_user_id') || 'default_user';
    }

    setupEventListeners() {
        this.refreshBtn.addEventListener('click', () => this.refreshNews());
        this.categoryFilter.addEventListener('change', () => this.loadNews());
    }

    async loadNews() {
        try {
            this.showLoading();
            
            const category = this.categoryFilter.value;
            let newsItems;
            
            if (category === 'all') {
                // Load all news
                const response = await fetch('/api/news?limit=20');
                newsItems = await response.json();
            } else {
                // Load news by category
                const response = await fetch(`/api/news/category/${category}?limit=20`);
                newsItems = await response.json();
            }
            
            this.renderNews(newsItems);
        } catch (error) {
            console.error('Error loading news:', error);
            this.showError('Failed to load news. Please try again.');
        }
    }

    async refreshNews() {
        try {
            this.refreshBtn.disabled = true;
            this.refreshBtn.textContent = '🔄 Refreshing...';
            
            const response = await fetch('/api/news/refresh', { method: 'POST' });
            const result = await response.json();
            
            console.log('News refresh result:', result);
            
            // Reload news after refresh
            await this.loadNews();
            
            this.showMessage(`News refreshed! ${result.count} items updated.`);
        } catch (error) {
            console.error('Error refreshing news:', error);
            this.showError('Failed to refresh news. Please try again.');
        } finally {
            this.refreshBtn.disabled = false;
            this.refreshBtn.textContent = '🔄 Refresh News';
        }
    }

    renderNews(newsItems) {
        this.newsFeed.innerHTML = '';
        
        if (!newsItems || newsItems.length === 0) {
            this.newsFeed.innerHTML = '<div class="news-empty">No news items found.</div>';
            return;
        }

        newsItems.forEach(newsItem => {
            const newsCard = this.createNewsCard(newsItem);
            this.newsFeed.appendChild(newsCard);
        });
    }

    createNewsCard(newsItem) {
        const card = document.createElement('div');
        card.className = 'news-card';
        
        const publishedDate = new Date(newsItem.published_date).toLocaleDateString();
        const categoryIcon = this.getCategoryIcon(newsItem.category);
        
        card.innerHTML = `
            <div class="news-header">
                <div class="news-category">
                    <span class="category-icon">${categoryIcon}</span>
                    <span class="category-name">${this.getCategoryName(newsItem.category)}</span>
                </div>
                <div class="news-date">${publishedDate}</div>
            </div>
            <div class="news-content">
                <h3 class="news-title">${newsItem.title}</h3>
                <p class="news-description">${newsItem.content}</p>
                ${newsItem.relevance_semesters && newsItem.relevance_semesters.length > 0 ? 
                    `<div class="news-relevance">
                        <span class="relevance-label">Relevant for:</span>
                        <span class="relevance-semesters">Semesters ${newsItem.relevance_semesters.join(', ')}</span>
                    </div>` : ''
                }
            </div>
            <div class="news-actions">
                <a href="${newsItem.url}" target="_blank" class="btn btn-primary">
                    Read More
                </a>
            </div>
        `;
        
        return card;
    }

    getCategoryIcon(category) {
        const icons = {
            'exam': '📝',
            'result': '📊',
            'academic': '🎓',
            'notification': '📢',
            'general': '📰'
        };
        return icons[category] || '📰';
    }

    getCategoryName(category) {
        const names = {
            'exam': 'Examination',
            'result': 'Results',
            'academic': 'Academic',
            'notification': 'Notification',
            'general': 'General'
        };
        return names[category] || 'General';
    }

    showLoading() {
        this.newsFeed.innerHTML = '<div class="news-loading">Loading news...</div>';
    }

    showError(message) {
        this.newsFeed.innerHTML = `<div class="news-error">${message}</div>`;
    }

    showMessage(message) {
        // Create a temporary message
        const messageDiv = document.createElement('div');
        messageDiv.className = 'news-message';
        messageDiv.textContent = message;
        this.newsFeed.insertBefore(messageDiv, this.newsFeed.firstChild);
        
        // Remove message after 3 seconds
        setTimeout(() => {
            if (messageDiv.parentNode) {
                messageDiv.parentNode.removeChild(messageDiv);
            }
        }, 3000);
    }
}

window.NewsPage = NewsPage;
