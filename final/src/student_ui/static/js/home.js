class HomePage {
    constructor() {
        this.newsFeed = document.getElementById('news-feed');
        this.refreshNewsBtn = document.getElementById('refresh-news');
        this.navigation = null; // will be injected by main
        this.loadNews();
        this.setupEventListeners();
    }

    setupEventListeners() {
        // News refresh button
        if (this.refreshNewsBtn) {
            this.refreshNewsBtn.addEventListener('click', () => {
                this.refreshNews();
            });
        }
    }

    async loadNews() {
        try {
            const response = await fetch('/api/news?limit=5');
            const newsItems = await response.json();
            this.renderNews(newsItems);
        } catch (error) {
            console.error('Error loading news:', error);
            if (this.newsFeed) {
                this.newsFeed.innerHTML = '<div class="news-empty">Unable to load news</div>';
            }
        }
    }

    async refreshNews() {
        try {
            if (this.refreshNewsBtn) {
                this.refreshNewsBtn.disabled = true;
                this.refreshNewsBtn.textContent = '🔄 Refreshing...';
            }
            
            const response = await fetch('/api/news/refresh', { method: 'POST' });
            const result = await response.json();
            
            // Reload news after refresh
            await this.loadNews();
            
            console.log('News refreshed:', result);
        } catch (error) {
            console.error('Error refreshing news:', error);
        } finally {
            if (this.refreshNewsBtn) {
                this.refreshNewsBtn.disabled = false;
                this.refreshNewsBtn.textContent = '🔄 Refresh';
            }
        }
    }

    renderNews(newsItems) {
        if (!this.newsFeed) return;
        
        if (!newsItems || newsItems.length === 0) {
            this.newsFeed.innerHTML = '<div class="news-empty">No news available</div>';
            return;
        }

        this.newsFeed.innerHTML = newsItems.map(newsItem => `
            <div class="news-item-compact">
                <div class="news-item-header">
                    <span class="news-category">${this.getCategoryIcon(newsItem.category)} ${this.getCategoryName(newsItem.category)}</span>
                    <span class="news-date">${new Date(newsItem.published_date).toLocaleDateString()}</span>
                </div>
                <h4 class="news-title">${newsItem.title}</h4>
                <p class="news-description">${newsItem.content.substring(0, 100)}...</p>
                <a href="${newsItem.url}" target="_blank" class="news-link">Read More →</a>
            </div>
        `).join('');
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
            'exam': 'Exam',
            'result': 'Result',
            'academic': 'Academic',
            'notification': 'Notification',
            'general': 'General'
        };
        return names[category] || 'General';
    }
}

window.HomePage = HomePage;