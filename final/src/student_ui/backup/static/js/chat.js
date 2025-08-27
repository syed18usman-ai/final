// Chat Page JavaScript Module
window.ChatPage = class ChatPage {
    constructor() {
        this.chatHistory = [];
        this.currentSemester = '';
        this.currentSubject = '';
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.listenForNavigationEvents();
        // Force show welcome message on init
        this.showWelcomeMessage();
    }

    showWelcomeMessage() {
        console.log('ChatPage: Showing welcome message');
        const chatMessages = document.getElementById('chat-messages');
        if (!chatMessages) {
            console.error('ChatPage: chat-messages container not found!');
            return;
        }

        chatMessages.innerHTML = `
            <div class="welcome-message">
                <i class="fas fa-lightbulb"></i>
                <h3>Welcome to VTU Study Assistant!</h3>
                <p>Ask me anything about your engineering subjects. I'll provide structured, well-cited answers with relevant images!</p>
            </div>
        `;
        console.log('ChatPage: Welcome message added to DOM');
    }

    showWelcomeIfEmpty() {
        const chatMessages = document.getElementById('chat-messages');
        if (!chatMessages) {
            console.error('ChatPage: chat-messages container not found!');
            return;
        }

        if (chatMessages.children.length === 0) {
            this.showWelcomeMessage();
        }
    }

    setupEventListeners() {
        // Chat input enter key
        const chatInput = document.getElementById('chat-input');
        if (chatInput) {
            chatInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendChatMessage();
                }
            });

            // Auto-resize textarea
            chatInput.addEventListener('input', (e) => {
                e.target.style.height = 'auto';
                e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px';
            });
        }

        // Send button click
        const sendButton = document.getElementById('send-button');
        if (sendButton) {
            sendButton.addEventListener('click', () => {
                this.sendChatMessage();
            });
        }

        // Back button
        const backButton = document.querySelector('.back-button');
        if (backButton) {
            backButton.addEventListener('click', () => {
                this.navigateToHome();
            });
        }
    }

    listenForNavigationEvents() {
        document.addEventListener('navigateToChat', (e) => {
            this.currentSemester = e.detail.semester;
            this.currentSubject = e.detail.subject;
            this.updateChatHeader();
        });
    }

    updateChatHeader() {
        const chatHeader = document.querySelector('.chat-header h3');
        if (chatHeader) {
            chatHeader.innerHTML = `
                <i class="fas fa-robot"></i> Chat - ${this.currentSemester} - ${this.currentSubject}
            `;
        }
    }

    async sendChatMessage() {
        try {
            const chatInput = document.getElementById('chat-input');
            const message = chatInput.value.trim();
            
            if (!message) return;
            
            // Add message to chat immediately
            this.addMessageToChat('user', message);
            
            // Show loading state
            const loadingMessage = this.addMessageToChat('assistant', 'Thinking...');
            
            // Create FormData properly
            const formData = new FormData();
            formData.append('message', message);
            formData.append('chat_history', JSON.stringify(this.chatHistory));
            formData.append('include_images', 'true');
            
            if (this.currentSemester) {
                formData.append('semester', this.currentSemester);
            }
            if (this.currentSubject) {
                formData.append('subject', this.currentSubject);
            }

            chatInput.value = '';

            // Debug log
            console.log('Sending chat request:', {
                message,
                semester: this.currentSemester,
                subject: this.currentSubject
            });

            // Send to backend
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Accept': 'application/json',
                },
                body: formData
            });

            // Debug log
            console.log('Response status:', response.status);
            console.log('Response headers:', Object.fromEntries(response.headers));

            // Handle different response statuses
            if (response.status === 405) {
                throw new Error('Method Not Allowed: The API endpoint does not accept POST requests');
            }

            if (!response.ok) {
                const errorText = await response.text();
                console.error('Error response:', errorText);
                throw new Error(`HTTP error! status: ${response.status}, details: ${errorText}`);
            }

            const data = await response.json();
            console.log('Response data:', data);  // Debug log
            
            // Remove loading message
            if (loadingMessage) {
                loadingMessage.remove();
            }

            if (data.success) {
                this.addStructuredMessageToChat(
                    'assistant',
                    data.response,
                    data.sources,
                    data.images,
                    data.summary
                );
                this.chatHistory = data.chat_history;
            } else {
                throw new Error(data.error || 'Failed to get response');
            }

        } catch (error) {
            console.error('Error in sendChatMessage:', error);
            this.addMessageToChat('assistant', 
                `Sorry, I encountered an error: ${error.message}. Please try again.`);
        }
    }

    addMessageToChat(role, content) {
        const messagesContainer = document.getElementById('chat-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        
        const avatar = role === 'user' ? '<i class="fas fa-user"></i>' : '<i class="fas fa-robot"></i>';
        
        messageDiv.innerHTML = `
            <div class="message-avatar">${avatar}</div>
            <div class="message-content">${content}</div>
        `;
        
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    addStructuredMessageToChat(role, content, sources, images, summary) {
        const messagesContainer = document.getElementById('chat-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        
        const avatar = role === 'user' ? '<i class="fas fa-user"></i>' : '<i class="fas fa-robot"></i>';
        
        // Format the content to preserve line breaks and formatting
        const formattedContent = this.formatResponseContent(content);
        
        let contentHtml = `<div class="structured-response">${formattedContent}</div>`;
        
        // Add sources if available
        if (sources && sources.length > 0) {
            contentHtml += `
                <div class="citations">
                    <h4><i class="fas fa-book"></i> Sources:</h4>
                    ${sources.map((source, index) => `
                        <div class="citation">
                            <span class="citation-number">[${index + 1}]</span>
                            <strong>${source.book}</strong> - Page ${source.page}
                            ${source.subject ? ` (${source.subject})` : ''}
                        </div>
                    `).join('')}
                </div>
            `;
        }
        
        // Add images if available
        if (images && images.length > 0) {
            contentHtml += `
                <div class="images-section">
                    <h4><i class="fas fa-image"></i> Relevant Images:</h4>
                    ${images.map(image => `
                        <div class="image-item">
                            <div class="image-info">
                                <i class="fas fa-image image-icon"></i>
                                <div class="image-details">
                                    <div class="image-title">${image.book}</div>
                                    <div class="image-source">Page ${image.page} - ${image.subject}</div>
                                </div>
                            </div>
                            <div class="image-description">${image.description}</div>
                        </div>
                    `).join('')}
                </div>
            `;
        }
        
        messageDiv.innerHTML = `
            <div class="message-avatar">${avatar}</div>
            <div class="message-content">${contentHtml}</div>
        `;
        
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    formatResponseContent(content) {
        if (!content) return '';
        
        // Convert line breaks to HTML
        let formatted = content
            .replace(/\n\n/g, '</p><p>')  // Double line breaks become paragraph breaks
            .replace(/\n/g, '<br>')        // Single line breaks become <br>
            .replace(/^\s*/, '')           // Remove leading whitespace
            .replace(/\s*$/, '');          // Remove trailing whitespace
        
        // Wrap in paragraph tags if not already wrapped
        if (!formatted.startsWith('<p>')) {
            formatted = `<p>${formatted}</p>`;
        }
        
        // Handle bullet points
        formatted = formatted.replace(/•\s*/g, '<br>• ');
        
        // Handle bold text
        formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        
        return formatted;
    }

    navigateToHome() {
        // Emit custom event for navigation
        const event = new CustomEvent('navigateToHome');
        document.dispatchEvent(event);
    }

    // Clear chat history
    clearChat() {
        this.chatHistory = [];
        const messagesContainer = document.getElementById('chat-messages');
        if (messagesContainer) {
            messagesContainer.innerHTML = `
                <div class="welcome-message">
                    <i class="fas fa-lightbulb"></i>
                    <h3>Welcome to VTU Study Assistant!</h3>
                    <p>Ask me anything about your engineering subjects. I'll provide structured, well-cited answers with relevant images!</p>
                </div>
            `;
        }
    }
}

// Export for use in main.js
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ChatPage;
}
