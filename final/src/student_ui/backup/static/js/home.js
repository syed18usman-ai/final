// Home Page JavaScript Module
window.HomePage = class HomePage {
    constructor() {
        this.currentSemester = '';
        this.currentSubject = '';
        this.init();
    }

    init() {
        this.loadSemesters();
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Semester card click events - use event delegation
        document.addEventListener('click', (e) => {
            // Handle semester card clicks
            if (e.target.closest('.semester-card')) {
                const card = e.target.closest('.semester-card');
                const semester = card.querySelector('h3').textContent;
                console.log('Semester card clicked:', semester);
                this.loadSubjectsForSemester(semester, card);
            }
            
            // Handle subject list item clicks
            if (e.target.closest('.subject-list li')) {
                const subjectItem = e.target.closest('.subject-list li');
                const semester = subjectItem.closest('.semester-card').querySelector('h3').textContent;
                const subject = subjectItem.textContent;
                console.log('Subject clicked:', semester, subject);
                this.startChat(semester, subject);
            }
        });
    }

    async loadSemesters() {
        try {
            console.log('Loading semesters...');
            const response = await fetch('/api/semesters');
            const data = await response.json();
            const grid = document.getElementById('semester-grid');
            if (grid) grid.innerHTML = '';
            if (data.success && data.semesters && data.semesters.length > 0) {
                // ...existing code...
            } else if (grid) {
                grid.innerHTML = `<div style="text-align:center;padding:2rem;color:var(--text-secondary);">
                    <i class='fas fa-exclamation-circle' style='font-size:2rem;'></i><br>No semesters found. Please contact admin or try again later.
                </div>`;
            }
            
            if (data.success) {
                const grid = document.getElementById('semester-grid');
                if (grid) {
                    grid.innerHTML = '';
                    
                    data.semesters.forEach(semester => {
                        const card = this.createSemesterCard(semester);
                        grid.appendChild(card);
                        
                        // Load subjects for this semester
                        this.loadSubjectsForSemester(semester, card);
                    });
                }
            } else {
                console.log('No semesters data available');
                this.showFallbackSemesters();
            }
        } catch (error) {
            console.error('Error loading semesters:', error);
            this.showFallbackSemesters();
        }
    }

    createSemesterCard(semester) {
        const card = document.createElement('div');
        card.className = 'semester-card';
        
        card.innerHTML = `
            <h3>${semester}</h3>
            <ul class="subject-list">
                <li>Loading subjects...</li>
            </ul>
        `;
        
        return card;
    }

    showFallbackSemesters() {
        const grid = document.getElementById('semester-grid');
        if (grid) {
            grid.innerHTML = `
                <div class="semester-card">
                    <h3>7th Semester</h3>
                    <ul class="subject-list">
                        <li onclick="homePage.startChat('7th Semester', 'Machine Learning')">Machine Learning</li>
                        <li onclick="homePage.startChat('7th Semester', 'Deep Learning')">Deep Learning</li>
                        <li onclick="homePage.startChat('7th Semester', 'Cryptography')">Cryptography</li>
                    </ul>
                </div>
            `;
        }
    }

    async loadSubjectsForSemester(semester, cardElement = null) {
        try {
            const response = await fetch(`/api/subjects/${semester}`);
            const data = await response.json();
            
            if (data.success) {
                const card = cardElement;
                if (card) {
                    const subjectList = card.querySelector('.subject-list');
                    if (subjectList) {
                        subjectList.innerHTML = data.subjects.map(subject => 
                            `<li onclick="homePage.startChat('${semester}', '${subject}')">${subject}</li>`
                        ).join('');
                    }
                }
            }
        } catch (error) {
            console.error('Error loading subjects for semester:', error);
            this.showFallbackSubjects(semester, cardElement);
        }
    }

    showFallbackSubjects(semester, cardElement) {
        const card = cardElement;
        if (card) {
            const subjectList = card.querySelector('.subject-list');
            if (subjectList) {
                subjectList.innerHTML = `
                    <li onclick="homePage.startChat('${semester}', 'Machine Learning')">Machine Learning</li>
                    <li onclick="homePage.startChat('${semester}', 'Deep Learning')">Deep Learning</li>
                    <li onclick="homePage.startChat('${semester}', 'Cryptography')">Cryptography</li>
                `;
            }
        }
    }

    startChat(semester, subject) {
        this.currentSemester = semester;
        this.currentSubject = subject;
        
        // Emit custom event for navigation
        const event = new CustomEvent('navigateToChat', {
            detail: { semester, subject }
        });
        document.dispatchEvent(event);
    }

    // Test function for debugging
    testFunction() {
        alert('Home page JavaScript is working!');
    }
}

// Export for use in main.js
if (typeof module !== 'undefined' && module.exports) {
    module.exports = HomePage;
}
