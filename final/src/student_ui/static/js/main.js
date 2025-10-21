class VTUStudyAssistant {
    constructor() {
        this.modules = {};
        this.currentUser = null;
        this.init();
    }

    init() {
        // Check authentication first
        this.checkAuthentication();
        
        this.modules.navigation = new Navigation();
        this.modules.homePage = new HomePage();
        this.modules.chatPage = new ChatPage();
        this.modules.pdfPage = new PDFPage();

        // Inject navigation reference
        this.modules.homePage.navigation = this.modules.navigation;
        this.modules.chatPage.navigation = this.modules.navigation;
        this.modules.pdfPage.navigation = this.modules.navigation;

        // Expose for debugging
        window.app = this;
        window.navigation = this.modules.navigation;
        window.homePage = this.modules.homePage;
        window.chatPage = this.modules.chatPage;
        window.pdfPage = this.modules.pdfPage;

        // Basic smoke test log
        console.log('VTU Study Assistant initialized');
    }

    checkAuthentication() {
        // Check if user is authenticated
        const tokens = this.getStoredTokens();
        const user = this.getStoredUser();
        
        if (!tokens || !user) {
            // Redirect to auth page
            window.location.href = '/auth.html';
            return;
        }
        
        this.currentUser = user;
        this.setupUserInterface();
    }

    getStoredTokens() {
        try {
            const tokens = localStorage.getItem('vtu_tokens');
            return tokens ? JSON.parse(tokens) : null;
        } catch {
            return null;
        }
    }

    getStoredUser() {
        try {
            const user = localStorage.getItem('vtu_user');
            return user ? JSON.parse(user) : null;
        } catch {
            return null;
        }
    }

    setupUserInterface() {
        // Add user info to header if needed
        const header = document.querySelector('.app-header');
        if (header && this.currentUser) {
            const userInfo = document.createElement('div');
            userInfo.className = 'user-info';
            userInfo.innerHTML = `
                <span>Welcome, ${this.currentUser.profile?.name || this.currentUser.email}</span>
                <a href="/profile.html" class="btn btn-sm">Profile</a>
                <button onclick="VTUStudyAssistant.logout()" class="btn btn-sm btn-secondary">Logout</button>
            `;
            header.appendChild(userInfo);
        }
    }

    static logout() {
        localStorage.removeItem('vtu_tokens');
        localStorage.removeItem('vtu_user');
        window.location.href = '/auth.html';
    }
}

// Start app once DOM is ready
(function startWhenReady() {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => new VTUStudyAssistant());
    } else {
        new VTUStudyAssistant();
    }
})();
