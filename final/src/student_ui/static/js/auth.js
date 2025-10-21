class AuthManager {
    constructor() {
        this.currentUser = null;
        this.tokens = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.checkAuthState();
    }

    setupEventListeners() {
        // Tab switching
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.switchTab(e.target.dataset.tab);
            });
        });

        // Form submissions
        document.getElementById('loginForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleLogin(e);
        });

        document.getElementById('registerForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleRegister(e);
        });

        // Google login
        document.getElementById('google-login').addEventListener('click', (e) => {
            e.preventDefault();
            this.handleGoogleLogin();
        });
    }

    switchTab(tab) {
        // Update tab buttons
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tab}"]`).classList.add('active');

        // Update forms
        document.querySelectorAll('.auth-form').forEach(form => {
            form.classList.remove('active');
        });
        document.getElementById(`${tab}-form`).classList.add('active');

        // Clear messages
        this.clearMessages();
    }

    async handleLogin(e) {
        const formData = new FormData(e.target);
        const loginBtn = e.target.querySelector('button[type="submit"]');
        
        try {
            this.setLoading(loginBtn, true);
            this.clearMessages();

            const response = await fetch('/auth/login', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (response.ok) {
                this.showMessage('Login successful! Redirecting...', 'success');
                this.tokens = data.tokens;
                this.currentUser = data.user;
                this.saveAuthData();
                
                setTimeout(() => {
                    window.location.href = '/';
                }, 1500);
            } else {
                this.showMessage(data.detail || 'Login failed', 'error');
            }
        } catch (error) {
            console.error('Login error:', error);
            this.showMessage('Network error. Please try again.', 'error');
        } finally {
            this.setLoading(loginBtn, false);
        }
    }

    async handleRegister(e) {
        const formData = new FormData(e.target);
        const registerBtn = e.target.querySelector('button[type="submit"]');
        
        try {
            this.setLoading(registerBtn, true);
            this.clearMessages();

            const response = await fetch('/auth/register', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (response.ok) {
                this.showMessage('Registration successful! Redirecting...', 'success');
                this.tokens = data.tokens;
                this.currentUser = data.user;
                this.saveAuthData();
                
                setTimeout(() => {
                    window.location.href = '/';
                }, 1500);
            } else {
                this.showMessage(data.detail || 'Registration failed', 'error');
            }
        } catch (error) {
            console.error('Registration error:', error);
            this.showMessage('Network error. Please try again.', 'error');
        } finally {
            this.setLoading(registerBtn, false);
        }
    }

    handleGoogleLogin() {
        // Redirect to Google OAuth
        window.location.href = '/auth/google';
    }

    async checkAuthState() {
        const tokens = this.getStoredTokens();
        if (tokens) {
            try {
                const response = await fetch('/auth/me', {
                    headers: {
                        'Authorization': `Bearer ${tokens.access_token}`
                    }
                });

                if (response.ok) {
                    const userData = await response.json();
                    this.currentUser = userData;
                    this.tokens = tokens;
                    // User is authenticated, redirect to main app
                    window.location.href = '/';
                } else {
                    // Invalid token, clear storage
                    this.clearAuthData();
                }
            } catch (error) {
                console.error('Auth check error:', error);
                this.clearAuthData();
            }
        }
    }

    saveAuthData() {
        if (this.tokens) {
            localStorage.setItem('vtu_tokens', JSON.stringify(this.tokens));
        }
        if (this.currentUser) {
            localStorage.setItem('vtu_user', JSON.stringify(this.currentUser));
        }
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

    clearAuthData() {
        localStorage.removeItem('vtu_tokens');
        localStorage.removeItem('vtu_user');
        this.tokens = null;
        this.currentUser = null;
    }

    setLoading(button, loading) {
        if (loading) {
            button.classList.add('loading');
            button.disabled = true;
        } else {
            button.classList.remove('loading');
            button.disabled = false;
        }
    }

    showMessage(message, type) {
        this.clearMessages();
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        messageDiv.textContent = message;
        
        const activeForm = document.querySelector('.auth-form.active');
        activeForm.insertBefore(messageDiv, activeForm.firstChild);
    }

    clearMessages() {
        document.querySelectorAll('.message').forEach(msg => {
            msg.remove();
        });
    }

    // Static method to check if user is authenticated
    static isAuthenticated() {
        try {
            const tokens = localStorage.getItem('vtu_tokens');
            return tokens !== null;
        } catch {
            return false;
        }
    }

    // Static method to get current user
    static getCurrentUser() {
        try {
            const user = localStorage.getItem('vtu_user');
            return user ? JSON.parse(user) : null;
        } catch {
            return null;
        }
    }

    // Static method to logout
    static logout() {
        localStorage.removeItem('vtu_tokens');
        localStorage.removeItem('vtu_user');
        window.location.href = '/auth.html';
    }
}

// Initialize auth manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new AuthManager();
});

// Export for use in other scripts
window.AuthManager = AuthManager;
