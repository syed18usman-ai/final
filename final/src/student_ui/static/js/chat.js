class ChatPage {
    constructor() {
        this.messagesEl = document.getElementById('chat-messages');
        this.inputEl = document.getElementById('chat-input');
        this.sendBtn = document.getElementById('send-button');
        this.currentContext = { semester: '7', subject: 'ml' }; // Use actual subject code
        this.navigation = null; // injected by main
        this.setupEventListeners();
    }

    setupEventListeners() {
        if (this.sendBtn) {
            this.sendBtn.addEventListener('click', () => this.sendChatMessage());
        }
        if (this.inputEl) {
            this.inputEl.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendChatMessage();
                }
            });
        }

        window.addEventListener('start-chat', (e) => {
            const { semester, subject } = e.detail;
            this.currentContext = { semester, subject };
            if (this.navigation) this.navigation.showChat();
            this.addSystemMessage(`Chat started for Semester ${semester} - ${subject}`);
        });
    }

    addMessage(content, role = 'bot') {
        const div = document.createElement('div');
        div.className = `message ${role}`;
        div.innerHTML = this.formatContent(content);
        this.messagesEl.appendChild(div);
        this.messagesEl.scrollTop = this.messagesEl.scrollHeight;
    }

    addSystemMessage(text) { this.addMessage(`<strong>${text}</strong>`, 'bot'); }

    formatContent(text) {
        return text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\n/g, '<br>');
    }

    renderImages(images) {
        if (!images || !images.length) return;
        const wrap = document.createElement('div');
        wrap.className = 'message bot';
        const grid = document.createElement('div');
        grid.className = 'grid';
        images.forEach(im => {
            const card = document.createElement('div');
            card.className = 'card';
            const rel = this.toProcessedRelPath(im.image_path);
            const url = `/processed/${rel}`;
            card.innerHTML = `
                <img src="${url}" alt="${im.book_title || 'diagram'}" style="max-width:100%; height:auto;" />
                <div><strong>${im.book_title || ''}</strong> — Page ${im.page ?? ''}</div>
                <a href="${url}" target="_blank">Open</a>
            `;
            grid.appendChild(card);
        });
        wrap.appendChild(grid);
        this.messagesEl.appendChild(wrap);
        this.messagesEl.scrollTop = this.messagesEl.scrollHeight;
    }

    toProcessedRelPath(absOrRel) {
        // Expect image_path like data/processed/<subject>/<semester>/<book_title>/images/...
        // Strip leading data/processed/ if present
        let p = absOrRel.replace(/\\/g, '/');
        const idx = p.indexOf('data/processed/');
        if (idx >= 0) p = p.slice(idx + 'data/processed/'.length);
        return p;
    }

    async sendChatMessage() {
        const text = this.inputEl.value.trim();
        if (!text) return;
        this.addMessage(text, 'user');
        this.inputEl.value = '';

        try {
            const res = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    question: text,
                    include_images: true,
                    semester: this.currentContext.semester,
                    subject: this.currentContext.subject
                })
            });
            if (!res.ok) throw new Error('Request failed');
            const data = await res.json();
            console.log('Chat response:', data); // Debug log
            const answer = data.answer || data.message || JSON.stringify(data);
            this.addMessage(answer, 'bot');
            if (data.sources && data.sources.length) {
                const lines = data.sources.map(s => {
                    if (s.type === 'image' && s.image_path) {
                        const rel = this.toProcessedRelPath(s.image_path);
                        const url = `/processed/${rel}`;
                        return `• [Image] ${s.book_title || ''} — Page ${s.page ?? ''} — <a href="${url}" target="_blank">open</a>`;
                    }
                    return `• [Text] ${s.book_title || ''} — Page ${s.page ?? ''}`;
                }).join('<br>');
                this.addMessage(`<strong>Sources</strong><br>${lines}`, 'bot');
            }
            this.renderImages(data.images);
        } catch (err) {
            this.addMessage('Error fetching response. Please try again.', 'bot');
            console.error(err);
        }
    }
}

window.ChatPage = ChatPage;
