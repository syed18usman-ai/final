class PDFPage {
    constructor() {
        console.log('=== PDFPage constructor called ===');
        
        this.grid = document.getElementById('pdf-grid');
        this.subjectRow = document.getElementById('pdf-subjects');
        
        console.log('Grid element found:', this.grid);
        console.log('Subject row element found:', this.subjectRow);
        
        if (!this.grid) {
            console.error('CRITICAL: pdf-grid element not found!');
        }
        if (!this.subjectRow) {
            console.error('CRITICAL: pdf-subjects element not found!');
        }
        
        this.navigation = null; // injected by main
        this.allResources = [];
        this.filteredResources = [];
        this.currentFilters = {
            semester: 'all',
            subject: 'all',
            search: ''
        };
        
        console.log('Setting up UI...');
        this.setupUI();
        
        console.log('Setting up event listeners...');
        this.setupEventListeners();
        
        // Delay loading resources to ensure page is ready
        console.log('Scheduling resource loading...');
        setTimeout(() => {
            console.log('Loading all resources (delayed)...');
            this.loadAllResources();
        }, 100);
        
        console.log('=== PDFPage constructor completed ===');
    }

    // Method to refresh resources when page becomes visible
    refreshResources() {
        console.log('=== refreshResources called ===');
        if (this.allResources.length === 0) {
            console.log('No resources loaded yet, loading now...');
            this.loadAllResources();
        } else {
            console.log('Resources already loaded, re-rendering...');
            this.applyFilters();
        }
    }

    setupUI() {
        // Create comprehensive filter UI
        this.subjectRow.innerHTML = `
            <div class="filter-section">
                <div class="filter-group">
                    <label for="semester-filter">Semester:</label>
                    <select id="semester-filter">
                        <option value="all">All Semesters</option>
                    </select>
                </div>
                <div class="filter-group">
                    <label for="subject-filter">Subject:</label>
                    <select id="subject-filter">
                        <option value="all">All Subjects</option>
                    </select>
                </div>
                <div class="filter-group">
                    <label for="search-input">Search:</label>
                    <input type="text" id="search-input" placeholder="Search resources...">
                </div>
                <div class="filter-group">
                    <button id="clear-filters" class="btn btn-secondary">Clear Filters</button>
                </div>
            </div>
        `;
    }

    async loadAllResources() {
        try {
            console.log('=== PDFPage: Starting to load all resources ===');
            console.log('Grid element:', this.grid);
            console.log('Subject row element:', this.subjectRow);
            
            // Show loading state
            this.grid.innerHTML = '<div class="card"><p>Loading resources...</p></div>';
            
            // Load all semesters
            console.log('Fetching semesters from /api/semesters...');
            const semestersResponse = await fetch('/api/semesters');
            console.log('Semesters response status:', semestersResponse.status);
            
            if (!semestersResponse.ok) {
                throw new Error(`Failed to fetch semesters: ${semestersResponse.status} ${semestersResponse.statusText}`);
            }
            
            const semesters = await semestersResponse.json();
            console.log('Available semesters:', semesters);
            
            if (!semesters || semesters.length === 0) {
                throw new Error('No semesters found');
            }
            
            // Populate semester filter
            const semesterFilter = document.getElementById('semester-filter');
            console.log('Semester filter element:', semesterFilter);
            
            if (semesterFilter) {
                semesters.forEach(semester => {
                    const option = document.createElement('option');
                    option.value = semester;
                    option.textContent = `Semester ${semester}`;
                    semesterFilter.appendChild(option);
                });
                console.log('Populated semester filter with', semesters.length, 'options');
            } else {
                console.error('Semester filter element not found!');
            }

            // Load all resources
            this.allResources = [];
            console.log('Starting to load resources for each semester...');
            
            for (const semester of semesters) {
                console.log(`\n--- Loading semester ${semester} ---`);
                
                const subjectsResponse = await fetch(`/api/subjects/${semester}`);
                console.log(`Subjects response status for ${semester}:`, subjectsResponse.status);
                
                if (!subjectsResponse.ok) {
                    console.error(`Failed to fetch subjects for semester ${semester}:`, subjectsResponse.status);
                    continue;
                }
                
                const subjects = await subjectsResponse.json();
                console.log(`  Subjects for semester ${semester}:`, subjects);
                
                if (!subjects || subjects.length === 0) {
                    console.log(`  No subjects found for semester ${semester}`);
                    continue;
                }
                
                for (const subject of subjects) {
                    console.log(`  \n  Loading PDFs for ${semester}/${subject}...`);
                    
                    const pdfsResponse = await fetch(`/api/pdfs/${semester}/${subject}`);
                    console.log(`  PDFs response status for ${semester}/${subject}:`, pdfsResponse.status);
                    
                    if (!pdfsResponse.ok) {
                        console.error(`  Failed to fetch PDFs for ${semester}/${subject}:`, pdfsResponse.status);
                        continue;
                    }
                    
                    const pdfsData = await pdfsResponse.json();
                    console.log(`    PDFs data structure:`, pdfsData);
                    
                    // Handle the API response format: {pdfs: Array}
                    const pdfs = pdfsData.pdfs || pdfsData;
                    console.log(`    Found ${pdfs.length} PDFs for ${semester}/${subject}`);
                    console.log(`    PDFs array:`, pdfs);
                    
                    if (pdfs && pdfs.length > 0) {
                        pdfs.forEach((pdf, index) => {
                            const resource = {
                                ...pdf,
                                semester,
                                subject,
                                displayName: this.getSubjectDisplayName(subject)
                            };
                            console.log(`    Adding resource ${index + 1}:`, resource);
                            this.allResources.push(resource);
                        });
                    } else {
                        console.log(`    No PDFs found for ${semester}/${subject}`);
                    }
                }
            }

            console.log(`\n=== Total resources loaded: ${this.allResources.length} ===`);
            console.log('All resources:', this.allResources);

            // Populate subject filter
            const subjectFilter = document.getElementById('subject-filter');
            console.log('Subject filter element:', subjectFilter);
            
            if (subjectFilter && this.allResources.length > 0) {
                const uniqueSubjects = [...new Set(this.allResources.map(r => r.subject))];
                console.log('Unique subjects found:', uniqueSubjects);
                
                uniqueSubjects.forEach(subject => {
                    const option = document.createElement('option');
                    option.value = subject;
                    option.textContent = this.getSubjectDisplayName(subject);
                    subjectFilter.appendChild(option);
                });
                console.log('Populated subject filter with', uniqueSubjects.length, 'options');
            } else {
                console.error('Subject filter element not found or no resources loaded!');
            }

            console.log('Calling applyFilters...');
            this.applyFilters();
            console.log('=== PDFPage: Finished loading resources ===');
            
        } catch (error) {
            console.error('=== ERROR in loadAllResources ===');
            console.error('Error details:', error);
            console.error('Error stack:', error.stack);
            this.grid.innerHTML = `<div class="card"><p>Error loading resources: ${error.message}</p></div>`;
        }
    }

    getSubjectDisplayName(subject) {
        const displayNames = {
            'ml': 'Machine Learning',
            'dl': 'Deep Learning',
            'crytography': 'Cryptography',
            'ADA': 'Algorithm Design & Analysis',
            'BDA': 'Big Data Analytics',
            'physics': 'Physics',
            'WebProgramming': 'Web Programming'
        };
        return displayNames[subject] || subject;
    }

    setupEventListeners() {
        // Filter event listeners
        document.getElementById('semester-filter').addEventListener('change', (e) => {
            this.currentFilters.semester = e.target.value;
            this.applyFilters();
        });

        document.getElementById('subject-filter').addEventListener('change', (e) => {
            this.currentFilters.subject = e.target.value;
            this.applyFilters();
        });

        document.getElementById('search-input').addEventListener('input', (e) => {
            this.currentFilters.search = e.target.value.toLowerCase();
            this.applyFilters();
        });

        document.getElementById('clear-filters').addEventListener('click', () => {
            this.currentFilters = { semester: 'all', subject: 'all', search: '' };
            document.getElementById('semester-filter').value = 'all';
            document.getElementById('subject-filter').value = 'all';
            document.getElementById('search-input').value = '';
            this.applyFilters();
        });

        // Download button clicks
        this.grid.addEventListener('click', async (e) => {
            if (e.target.closest('.download-btn')) {
                const btn = e.target.closest('.download-btn');
                const semester = btn.dataset.semester;
                const subject = btn.dataset.subject;
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

    applyFilters() {
        console.log('=== applyFilters called ===');
        console.log('Current filters:', this.currentFilters);
        console.log('All resources count:', this.allResources.length);
        console.log('All resources:', this.allResources);
        
        this.filteredResources = this.allResources.filter(resource => {
            // Semester filter
            if (this.currentFilters.semester !== 'all' && resource.semester !== this.currentFilters.semester) {
                return false;
            }
            
            // Subject filter
            if (this.currentFilters.subject !== 'all' && resource.subject !== this.currentFilters.subject) {
                return false;
            }
            
            // Search filter
            if (this.currentFilters.search) {
                const searchTerm = this.currentFilters.search.toLowerCase();
                const searchableText = [
                    resource.filename,
                    resource.book_title,
                    resource.subject,
                    resource.displayName,
                    resource.semester
                ].join(' ').toLowerCase();
                
                if (!searchableText.includes(searchTerm)) {
                    return false;
                }
            }
            
            return true;
        });
        
        console.log(`Filtered resources: ${this.filteredResources.length} out of ${this.allResources.length}`);
        console.log('Filtered resources:', this.filteredResources);
        this.renderResources();
    }

    renderResources() {
        console.log('=== renderResources called ===');
        console.log('Grid element:', this.grid);
        console.log('Filtered resources count:', this.filteredResources.length);
        console.log('Filtered resources:', this.filteredResources);
        
        if (!this.grid) {
            console.error('Grid element is null! Cannot render resources.');
            return;
        }
        
        this.grid.innerHTML = '';
        
        if (this.filteredResources.length === 0) {
            console.log('No filtered resources, showing empty message');
            this.grid.innerHTML = '<div class="card"><p>No resources found matching your filters.</p></div>';
            return;
        }
        
        console.log('Rendering resources...');
        
        // Add summary
        const summary = document.createElement('div');
        summary.className = 'card resource-summary';
        summary.innerHTML = `
            <h3>📚 VTU Resource Library</h3>
            <p>Found ${this.filteredResources.length} resources</p>
        `;
        this.grid.appendChild(summary);
        console.log('Added summary card');
        
        // Group resources by semester and subject
        const grouped = this.groupResourcesBySemesterSubject(this.filteredResources);
        console.log('Grouped resources:', grouped);
        
        Object.keys(grouped).forEach(semester => {
            console.log(`Rendering semester ${semester} with ${Object.keys(grouped[semester]).length} subjects`);
            
            const semesterDiv = document.createElement('div');
            semesterDiv.className = 'semester-group';
            semesterDiv.innerHTML = `<h4>Semester ${semester}</h4>`;
            
            Object.keys(grouped[semester]).forEach(subject => {
                console.log(`  Rendering subject ${subject} with ${grouped[semester][subject].length} resources`);
                
                const subjectDiv = document.createElement('div');
                subjectDiv.className = 'subject-group';
                subjectDiv.innerHTML = `<h5>${this.getSubjectDisplayName(subject)}</h5>`;
                
                const resourcesGrid = document.createElement('div');
                resourcesGrid.className = 'resources-grid';
                
                grouped[semester][subject].forEach((resource, index) => {
                    console.log(`    Creating card ${index + 1} for resource:`, resource);
                    const card = this.createResourceCard(resource);
                    resourcesGrid.appendChild(card);
                });
                
                subjectDiv.appendChild(resourcesGrid);
                semesterDiv.appendChild(subjectDiv);
            });
            
            this.grid.appendChild(semesterDiv);
        });
        
        console.log('=== renderResources completed ===');
    }

    groupResourcesBySemesterSubject(resources) {
        const grouped = {};
        resources.forEach(resource => {
            if (!grouped[resource.semester]) {
                grouped[resource.semester] = {};
            }
            if (!grouped[resource.semester][resource.subject]) {
                grouped[resource.semester][resource.subject] = [];
            }
            grouped[resource.semester][resource.subject].push(resource);
        });
        return grouped;
    }

    createResourceCard(resource) {
            const card = document.createElement('div');
        card.className = 'resource-card';
            card.innerHTML = `
            <div class="resource-header">
                <h6>${resource.filename}</h6>
                <span class="resource-type">PDF</span>
            </div>
            <div class="resource-meta">
                <span class="book-title">${resource.book_title}</span>
                <span class="semester-badge">Sem ${resource.semester}</span>
            </div>
            <div class="resource-actions">
                <button class="download-btn btn" 
                        data-semester="${resource.semester}"
                        data-subject="${resource.subject}"
                        data-book-title="${resource.book_title}"
                        data-filename="${resource.filename}">
                    📥 Download
                </button>
                <button class="preview-btn btn btn-secondary" 
                        data-semester="${resource.semester}"
                        data-subject="${resource.subject}"
                        data-book-title="${resource.book_title}"
                        data-filename="${resource.filename}">
                    👁️ Preview
                </button>
            </div>
        `;
        return card;
    }
}

window.PDFPage = PDFPage;
