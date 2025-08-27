class HomePage {
    constructor() {
        this.semesterGrid = document.getElementById('semester-grid');
        this.navigation = null; // will be injected by main
        this.subjectsData = {
            7: ['ml', 'dl', 'crytography']
        };
        // Mapping for display names
        this.subjectDisplayNames = {
            'ml': 'Machine Learning',
            'dl': 'Deep Learning', 
            'crytography': 'Cryptography'
        };
        this.renderSemesters();
        this.setupEventListeners();
    }

    renderSemesters() {
        this.semesterGrid.innerHTML = '';
        Object.keys(this.subjectsData).forEach(sem => {
            const card = document.createElement('div');
            card.className = 'card semester-card';
            card.innerHTML = `
                <h3>Semester ${sem}</h3>
                <ul class="subject-list">
                    ${this.subjectsData[sem].map(s => `<li data-subject="${s}">${this.subjectDisplayNames[s] || s}</li>`).join('')}
                </ul>
            `;
            this.semesterGrid.appendChild(card);
        });
    }

    setupEventListeners() {
        document.addEventListener('click', (e) => {
            if (e.target.closest('.subject-list li')) {
                const subjectItem = e.target.closest('.subject-list li');
                const semester = subjectItem.closest('.semester-card').querySelector('h3').textContent.replace('Semester ', '');
                const subject = subjectItem.dataset.subject; // Use the actual subject code from data attribute
                window.dispatchEvent(new CustomEvent('start-chat', { detail: { semester, subject } }));
                window.dispatchEvent(new CustomEvent('show-pdfs', { detail: { semester, subject } }));
            }
        });
    }
}

window.HomePage = HomePage;
