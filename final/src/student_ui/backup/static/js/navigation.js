// Navigation JavaScript Module
window.Navigation = class Navigation {
    constructor() {
        this.currentPage = 'home';
        this.init();
    }

    init() {
        this.setupNavigationListeners();
        this.setupGlobalEventListeners();
    }

    setupNavigationListeners() {
        // Navigation menu event listeners - handle at container level to prevent double triggers
        const navContainer = document.querySelector('.nav-menu');
        if (!navContainer) {
            console.error('Navigation: nav-menu container not found!');
            return;
        }

        navContainer.addEventListener('click', (e) => {
            const navItem = e.target.closest('.nav-item');
            if (!navItem) return;
            
            e.preventDefault();
            const targetPage = navItem.dataset.page;
            console.log('Navigation item clicked:', targetPage);
            this.navigateToPage(targetPage);
        });
    }

    setupGlobalEventListeners() {
        // Listen for custom navigation events from other modules
        document.addEventListener('navigateToHome', () => {
            this.navigateToPage('home');
        });

        document.addEventListener('navigateToChat', (e) => {
            this.navigateToPage('chat');
        });

        document.addEventListener('navigateToPDFs', () => {
            this.navigateToPage('pdfs');
        });
    }

    navigateToPage(targetPage) {
        try {
            // Prevent navigating to the current page
            if (targetPage === this.currentPage) {
                console.log(`Already on ${targetPage} page`);
                return;
            }

            console.log(`Navigating to: ${targetPage}`);
            
            // Hide all pages
            this.hideAllPages();
            
            // Show target page
            this.showPage(targetPage);
            
            // Update navigation state
            this.updateNavigationState(targetPage);
            
            // Update page indicator
            this.updatePageIndicator(targetPage);
            
            // Initialize page content
            this.initializePageContent(targetPage);
            
            console.log(`Navigation to ${targetPage} completed successfully`);
            
        } catch (error) {
            console.error(`Error navigating to ${targetPage}:`, error);
            console.error(error.stack);
            alert(`Error navigating to ${targetPage}. Check console for details.`);
        }
    }

    initializePageContent(pageName) {
        console.log(`Initializing content for ${pageName}`);
        try {
            if (pageName === 'pdfs' && window.pdfsPage) {
                console.log('Loading PDFs content...');
                window.pdfsPage.loadPDFs();
            } else if (pageName === 'chat' && window.chatPage) {
                console.log('Initializing chat content...');
                window.chatPage.showWelcomeMessage();
            }
        } catch (error) {
            console.error(`Error initializing ${pageName} content:`, error);
        }
    }

    hideAllPages() {
        const pages = ['home-page', 'chat-page', 'pdfs-page'];
        pages.forEach(pageId => {
            const page = document.getElementById(pageId);
            if (page) {
                page.hidden = true;
            } else {
                console.error(`Navigation: Page element ${pageId} not found!`);
            }
        });
    }

    showPage(pageName) {
        console.log(`Navigation: Showing page ${pageName}`);
        const pageId = this.getPageId(pageName);
        const page = document.getElementById(pageId);
        
        if (!page) {
            console.error(`Navigation: Page element ${pageId} not found!`);
            return;
        }
        
        // Show the page
        page.hidden = false;
        console.log(`Navigation: Made ${pageId} visible`);
    }

    getPageId(pageName) {
        const pageMap = {
            'home': 'home-page',
            'chat': 'chat-page',
            'pdfs': 'pdfs-page'
        };
        return pageMap[pageName] || 'home-page';
    }

    updateNavigationState(targetPage) {
        this.currentPage = targetPage;
        
        // Update navigation active states
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
        });
        
        const activeNav = document.querySelector(`.nav-item[data-page="${targetPage}"]`);
        if (activeNav) {
            activeNav.classList.add('active');
        }
    }

    updatePageIndicator(targetPage) {
        const indicator = document.getElementById('current-page-indicator');
        if (indicator) {
            const pageLabels = {
                'home': 'Home',
                'chat': 'Chat',
                'pdfs': 'PDFs'
            };
            indicator.textContent = pageLabels[targetPage] || 'Home';
        }
    }

    addVisualFeedback(targetPage) {
        // Add visual feedback based on the page
        let targetElement = null;
        
        switch (targetPage) {
            case 'home':
                targetElement = document.querySelector('.home-section h2');
                break;
            case 'chat':
                targetElement = document.querySelector('.chat-header h3');
                break;
            case 'pdfs':
                targetElement = document.querySelector('.pdf-section h3');
                break;
        }
        
        if (targetElement) {
            targetElement.style.color = '#22c55e';
            setTimeout(() => {
                targetElement.style.color = '';
            }, 1000);
        }
    }

    // Public methods for external use
    showHome() {
        this.navigateToPage('home');
    }

    showChat() {
        this.navigateToPage('chat');
    }

    showPDFs() {
        this.navigateToPage('pdfs');
    }

    // Get current page
    getCurrentPage() {
        return this.currentPage;
    }

    // Check if a specific page is active
    isPageActive(pageName) {
        return this.currentPage === pageName;
    }
}

// Export for use in main.js
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Navigation;
}
