// PDFs Page JavaScript Module
window.PDFsPage = class PDFsPage {
    constructor() {
        this.init();
    }

    init() {
        this.setupEventListeners();
    }

    setupEventListeners() {
        // PDF download button events are handled by event delegation in main.js
    }

    async loadPDFs() {
        console.log('PDFPage: Loading PDFs...');
        const grid = document.getElementById('pdf-grid');
        if (!grid) {
            console.error('PDFPage: pdf-grid element not found!');
            return;
        }
        
        // Show loading state
        grid.innerHTML = `
            <div style="grid-column: 1 / -1; text-align: center; padding: 2rem;">
                <i class="fas fa-spinner fa-spin" style="font-size: 3rem; margin-bottom: 1rem;"></i>
                <h4>Loading PDFs...</h4>
            </div>
        `;
        
        try {
            console.log('PDFPage: Fetching from /api/pdfs...');
            const response = await fetch('/api/pdfs');
            console.log('PDFPage: Response received:', response.status);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            console.log('PDFPage: Data received:', data);
            
            if (data.success && data.pdfs && (Array.isArray(data.pdfs) || typeof data.pdfs === 'object')) {
                const pdfs = Array.isArray(data.pdfs) ? data.pdfs : Object.values(data.pdfs);
                console.log('PDFPage: Processing', pdfs.length, 'PDFs');
                
                if (pdfs.length > 0) {
                    grid.innerHTML = `
                        <div class="pdf-grid-header">
                            <h3>Found ${pdfs.length} PDFs</h3>
                        </div>
                    `;
                    pdfs.forEach(pdf => {
                        const card = this.createPDFCard(pdf);
                        grid.appendChild(card);
                    });
                } else {
                    this.showNoPDFsMessage();
                }
            } else {
                console.log('PDFPage: No PDFs found, showing message');
                this.showNoPDFsMessage();
            }
        } catch (error) {
            console.error('PDFPage: Error loading PDFs:', error);
            this.showErrorMessage();
        }
    }

    createPDFCard(pdf) {
        console.log('Creating PDF card for:', pdf);
        const card = document.createElement('div');
        card.className = 'pdf-card';
        
        card.innerHTML = `
            <h4>${pdf.book_title}</h4>
            <div class="file-info">
                <div><strong>Subject:</strong> ${pdf.subject}</div>
                <div><strong>Semester:</strong> ${pdf.semester}</div>
                <div><strong>Size:</strong> ${pdf.file_size}</div>
            </div>
            <button class="download-btn" data-file-path="${pdf.file_path}" data-filename="${pdf.filename}">
                <i class="fas fa-download"></i> Download
            </button>
        `;
        
        return card;
    }

    showNoPDFsMessage() {
        const grid = document.getElementById('pdf-grid');
        if (grid) {
            grid.innerHTML = `
                <div style="grid-column: 1 / -1; text-align: center; padding: 2rem; color: var(--text-secondary);">
                    <i class="fas fa-file-pdf" style="font-size: 3rem; margin-bottom: 1rem; opacity: 0.5;"></i>
                    <h4>No PDFs Available</h4>
                    <p>No PDF files have been uploaded yet.</p>
                </div>
            `;
        }
    }

    showErrorMessage() {
        const grid = document.getElementById('pdf-grid');
        if (grid) {
            grid.innerHTML = `
                <div style="grid-column: 1 / -1; text-align: center; padding: 2rem; color: #ef4444;">
                    <i class="fas fa-exclamation-triangle" style="font-size: 3rem; margin-bottom: 1rem;"></i>
                    <h4>Error Loading PDFs</h4>
                    <p>Failed to load PDF files. Please try again later.</p>
                </div>
            `;
        }
    }

    downloadPDF(filePath, filename) {
        try {
            // Extract path components from the file path
            const pathParts = filePath.split(/[\/\\]/);
            const semester = pathParts[pathParts.length - 4]; // data/raw/semester/subject/book/filename
            const subject = pathParts[pathParts.length - 3];
            const bookTitle = pathParts[pathParts.length - 2];
            
            // Create download URL using our API endpoint
            const downloadUrl = `/api/pdfs/${semester}/${subject}/${bookTitle}/${filename}`;
            
            console.log('Downloading from:', downloadUrl);
            
            // Create a temporary link to download the file
            const link = document.createElement('a');
            link.href = downloadUrl;
            link.download = filename;
            link.target = '_blank';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        } catch (error) {
            console.error('Error downloading PDF:', error);
            alert('Error downloading PDF: ' + error.message);
        }
    }

    // Filter PDFs by semester and subject
    async filterPDFs(semester = null, subject = null) {
        try {
            let url = '/api/pdfs';
            if (semester && subject) {
                url = `/api/pdfs/${semester}/${subject}`;
            } else if (semester) {
                url = `/api/pdfs/${semester}`;
            }
            
            const response = await fetch(url);
            const data = await response.json();
            
            if (data.success) {
                const grid = document.getElementById('pdf-grid');
                if (grid) {
                    grid.innerHTML = '';
                    
                    data.pdfs.forEach(pdf => {
                        const card = this.createPDFCard(pdf);
                        grid.appendChild(card);
                    });
                }
            }
        } catch (error) {
            console.error('Error filtering PDFs:', error);
        }
    }

    // Search PDFs by title or subject
    searchPDFs(query) {
        const cards = document.querySelectorAll('.pdf-card');
        const searchTerm = query.toLowerCase();
        
        cards.forEach(card => {
            const title = card.querySelector('h4').textContent.toLowerCase();
            const subject = card.querySelector('.file-info').textContent.toLowerCase();
            
            if (title.includes(searchTerm) || subject.includes(searchTerm)) {
                card.style.display = 'block';
            } else {
                card.style.display = 'none';
            }
        });
    }
}

// Export for use in main.js
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PDFsPage;
}
