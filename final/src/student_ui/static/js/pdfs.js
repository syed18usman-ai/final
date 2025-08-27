class PDFPage {
    constructor() {
        this.grid = document.getElementById('pdf-grid');
        this.subjectRow = document.getElementById('pdf-subjects');
        this.navigation = null; // injected by main
        this.currentContext = { semester: '7', subject: 'Machine Learning' };
        this.renderSubjectButtons();
        this.loadPDFs();
        this.setupEventListeners();
    }

    renderSubjectButtons() {
        const subjects = ['Machine Learning', 'Deep Learning', 'Cryptography'];
        this.subjectRow.innerHTML = subjects.map(s => `<button class="btn subject-btn" data-subject="${s}">${s}</button>`).join('');
    }

    setupEventListeners() {
        window.addEventListener('start-chat', (e) => {
            const { semester, subject } = e.detail;
            this.currentContext = { semester, subject };
            this.highlightActiveSubject();
            this.loadPDFs();
        });

        window.addEventListener('show-pdfs', (e) => {
            const { semester, subject } = e.detail;
            this.currentContext = { semester, subject };
            this.highlightActiveSubject();
            this.loadPDFs();
        });

        this.subjectRow.addEventListener('click', (e) => {
            const btn = e.target.closest('.subject-btn');
            if (!btn) return;
            const subject = btn.dataset.subject;
            const semester = this.currentContext.semester || '7';
            this.currentContext = { semester, subject };
            this.highlightActiveSubject();
            this.loadPDFs();
        });

        this.grid.addEventListener('click', async (e) => {
            if (e.target.closest('.download-btn')) {
                const btn = e.target.closest('.download-btn');
                const { semester, subject } = this.currentContext;
                const bookTitle = btn.dataset.bookTitle;
                const filename = btn.dataset.filename;
                const url = `/api/pdfs/${encodeURIComponent(semester)}/${encodeURIComponent(subject)}/${encodeURIComponent(bookTitle)}/${encodeURIComponent(filename)}`;
                console.log('Downloading PDF:', { semester, subject, bookTitle, filename, url });
                try {
                    const res = await fetch(url);
                    if (!res.ok) {
                        throw new Error(`${res.status} ${res.statusText}`);
                    }
                    const blob = await res.blob();
                    const link = document.createElement('a');
                    link.href = URL.createObjectURL(blob);
                    link.download = filename;
                    link.click();
                    URL.revokeObjectURL(link.href);
                } catch (err) {
                    console.error('Download failed', err);
                    alert(`Download failed: ${err.message}`);
                }
            }
        });
    }

    highlightActiveSubject() {
        const current = (this.currentContext.subject || '').toLowerCase();
        Array.from(this.subjectRow.querySelectorAll('.subject-btn')).forEach(b => {
            const isActive = b.dataset.subject.toLowerCase() === current;
            b.classList.toggle('active', isActive);
        });
    }

    async loadPDFs() {
        try {
            const { semester, subject } = this.currentContext;
            const url = `/api/pdfs/${encodeURIComponent(semester)}/${encodeURIComponent(subject)}`;
            console.log('Loading PDFs for:', { semester, subject, url });
            const res = await fetch(url);
            if (!res.ok) {
                throw new Error(`${res.status} ${res.statusText}`);
            }
            const data = await res.json();
            const items = data.pdfs || [];
            console.log('PDFs loaded:', { count: items.length, items });
            this.renderPDFs(items);
        } catch (err) {
            console.error('Failed to load PDFs', err);
            this.grid.innerHTML = '<div class="card">Failed to load PDFs</div>';
        }
    }

    renderPDFs(items) {
        const { semester, subject } = this.currentContext;
        this.grid.innerHTML = '';
        const heading = document.createElement('div');
        heading.className = 'card';
        heading.innerHTML = `<h3>Semester ${semester} — ${subject}</h3>`;
        this.grid.appendChild(heading);
        if (!items.length) {
            const empty = document.createElement('div');
            empty.className = 'card';
            empty.textContent = 'No PDFs found';
            this.grid.appendChild(empty);
            return;
        }
        items.forEach(pdf => {
            const card = document.createElement('div');
            card.className = 'card';
            const bookTitle = pdf.book_title || 'Unknown Book';
            const filename = pdf.filename || (pdf.file_path ? pdf.file_path.split('/').pop() : 'file.pdf');
            card.innerHTML = `
                <h3>${bookTitle}</h3>
                <p>${filename}</p>
                <button class="download-btn" data-book-title="${bookTitle}" data-filename="${filename}">Download</button>
            `;
            this.grid.appendChild(card);
        });
    }
}

window.PDFPage = PDFPage;
