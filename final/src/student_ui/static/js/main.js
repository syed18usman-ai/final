class VTUStudyAssistant {
    constructor() {
        this.modules = {};
        this.init();
    }

    init() {
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
}

// Start app once DOM is ready
(function startWhenReady() {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => new VTUStudyAssistant());
    } else {
        new VTUStudyAssistant();
    }
})();
