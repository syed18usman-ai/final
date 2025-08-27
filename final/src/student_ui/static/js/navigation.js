class Navigation {
    constructor() {
        this.currentPage = 'home';
        this.menuItems = document.querySelectorAll('.nav-item');
        this.pages = {
            home: document.getElementById('home-page'),
            chat: document.getElementById('chat-page'),
            pdfs: document.getElementById('pdf-page')
        };
        this.indicator = document.getElementById('current-page-indicator');
        this.setupNavigationListeners();
        this.navigateToPage('home');
    }

    setupNavigationListeners() {
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const targetPage = item.dataset.page;
                this.navigateToPage(targetPage);
            });
        });
    }

    navigateToPage(page) {
        Object.values(this.pages).forEach(p => p.classList.remove('visible'));
        this.pages[page]?.classList.add('visible');

        this.menuItems.forEach(mi => mi.classList.remove('active'));
        const active = Array.from(this.menuItems).find(mi => mi.dataset.page === page);
        if (active) active.classList.add('active');

        if (this.indicator) this.indicator.textContent = page.charAt(0).toUpperCase() + page.slice(1);
        this.currentPage = page;
    }

    showHome() { this.navigateToPage('home'); }
    showChat() { this.navigateToPage('chat'); }
    showPDFs() { this.navigateToPage('pdfs'); }
}

window.Navigation = Navigation;
