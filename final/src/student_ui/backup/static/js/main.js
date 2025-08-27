// Main Application JavaScript
window.VTUStudyAssistant = class VTUStudyAssistant {
    constructor() {
        this.modules = {};
        this.init();
    }

    init() {
        console.log('VTU Study Assistant initializing...');
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.onDOMReady());
        } else {
            this.onDOMReady();
        }
    }

    onDOMReady() {
        try {
            this.setupModules();
        } catch (err) {
            console.error('Error during setupModules:', err);
            alert('Critical error: ' + err.message);
        }
    }

    setupModules() {
        try {
            console.log('Setting up modules...');
            // Only check for containers that exist at page load
            const requiredElements = [
                'home-page',
                'chat-page',
                'pdfs-page'
            ];
            for (const elementId of requiredElements) {
                const element = document.getElementById(elementId);
                if (!element) {
                    throw new Error(`Required element not found: ${elementId}`);
                }
                console.log(`Found element: ${elementId}`);
            }
            
            // Check if all required classes are available
            if (typeof Navigation === 'undefined') {
                throw new Error('Navigation class not found');
            }
            if (typeof HomePage === 'undefined') {
                throw new Error('HomePage class not found');
            }
            if (typeof ChatPage === 'undefined') {
                throw new Error('ChatPage class not found');
            }
            if (typeof PDFsPage === 'undefined') {
                throw new Error('PDFsPage class not found');
            }
            
            // Initialize navigation first
            window.navigation = new Navigation();
            console.log('Navigation module initialized');
            
            // Initialize other modules
            window.homePage = new HomePage();
            window.chatPage = new ChatPage();
            window.pdfsPage = new PDFsPage();

            // Store modules locally
            this.modules = {
                navigation: window.navigation,
                homePage: window.homePage,
                chatPage: window.chatPage,
                pdfsPage: window.pdfsPage
            };
            window.navigation = this.modules.navigation;
            window.homePage = this.modules.homePage;
            window.chatPage = this.modules.chatPage;
            window.pdfPage = this.modules.pdfPage;

            // Show home page by default
            if (this.modules.navigation && typeof this.modules.navigation.navigateToPage === 'function') {
                this.modules.navigation.navigateToPage('home');
            } else {
                document.getElementById('home-page').hidden = false;
                document.getElementById('chat-page').hidden = true;
                document.getElementById('pdf-page').hidden = true;
            }
        } catch (error) {
            console.error('Error setting up modules:', error);
            alert('Error initializing application: ' + error.message);
        }
        this.setupGlobalEventListeners();
        // Setup PDF download event delegation
        this.setupPDFDownloadEvents();
        console.log('All modules initialized successfully');
    }

    setupGlobalEventListeners() {
        // Global click event delegation for dynamic elements
        document.addEventListener('click', (e) => {
            this.handleGlobalClick(e);
        });

        // Global error handling
        window.addEventListener('error', (e) => {
            console.error('Global error:', e.error);
        });

        // Global unhandled promise rejection handling
        window.addEventListener('unhandledrejection', (e) => {
            console.error('Unhandled promise rejection:', e.reason);
        });
    }

    handleGlobalClick(e) {
        // Handle PDF download button clicks
        if (e.target.closest('.download-btn')) {
            const button = e.target.closest('.download-btn');
            const filePath = button.dataset.filePath;
            const filename = button.dataset.filename;
            
            console.log('PDF download clicked:', filePath, filename);
            
            if (filePath && filename) {
                this.modules.pdfPage.downloadPDF(filePath, filename);
            }
        }

        // Handle test button clicks
        if (e.target.matches('[onclick*="testFunction"]')) {
            e.preventDefault();
            console.log('Test function clicked');
            this.modules.homePage.testFunction();
        }

        if (e.target.matches('[onclick*="showChat"]')) {
            e.preventDefault();
            console.log('Show chat clicked');
            this.modules.navigation.showChat();
        }

        if (e.target.matches('[onclick*="showPDFs"]')) {
            e.preventDefault();
            console.log('Show PDFs clicked');
            this.modules.navigation.showPDFs();
        }

        if (e.target.matches('[onclick*="showHome"]')) {
            e.preventDefault();
            console.log('Show home clicked');
            this.modules.navigation.showHome();
        }
    }

    setupPDFDownloadEvents() {
        // Event delegation for PDF downloads
        document.addEventListener('click', (e) => {
            if (e.target.closest('.download-btn')) {
                const button = e.target.closest('.download-btn');
                const filePath = button.dataset.filePath;
                const filename = button.dataset.filename;
                
                if (filePath && filename) {
                    this.modules.pdfPage.downloadPDF(filePath, filename);
                }
            }
        });
    }

    // Public methods for external use
    getModule(moduleName) {
        return this.modules[moduleName];
    }

    // Test function for debugging
    testAllModules() {
        console.log('Testing all modules...');
        
        try {
            // Test navigation
            console.log('Navigation module:', this.modules.navigation);
            console.log('Current page:', this.modules.navigation.getCurrentPage());
            
            // Test home page
            console.log('Home page module:', this.modules.homePage);
            
            // Test chat page
            console.log('Chat page module:', this.modules.chatPage);
            
            // Test PDF page
            console.log('PDF page module:', this.modules.pdfPage);
            
            console.log('All modules are working!');
            return true;
            
        } catch (error) {
            console.error('Module test failed:', error);
            return false;
        }
    }

    // Utility methods
    showNotification(message, type = 'info') {
        // Create a simple notification
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 1rem 1.5rem;
            background: ${type === 'error' ? '#ef4444' : type === 'success' ? '#22c55e' : '#3b82f6'};
            color: white;
            border-radius: 8px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            z-index: 1000;
            font-weight: 500;
        `;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        // Remove after 3 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 3000);
    }
}

// Initialize the application when the script loads
let app;

// Wait for all modules to be loaded
function initializeApp() {
    console.log('Checking for required modules...');
    
    if (typeof Navigation !== 'undefined' && 
        typeof HomePage !== 'undefined' && 
        typeof ChatPage !== 'undefined' && 
        typeof PDFPage !== 'undefined') {
        
        console.log('All modules found, creating app...');
        app = new VTUStudyAssistant();
        console.log('VTU Study Assistant application started successfully!');
        
        // Make app globally accessible for debugging
        window.app = app;
        
        // Test all modules
        setTimeout(() => {
            try {
                app.testAllModules();
            } catch (error) {
                console.error('Module test failed:', error);
            }
        }, 1000);
        
    } else {
        console.log('Some modules not ready, retrying...');
        // Retry after a short delay
        setTimeout(initializeApp, 100);
    }
}

// Start initialization
console.log('Starting VTU Study Assistant initialization...');
initializeApp();
