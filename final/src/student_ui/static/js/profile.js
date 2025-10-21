class ProfileManager {
    constructor() {
        this.currentUser = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadProfile();
    }

    setupEventListeners() {
        // Edit profile button
        document.getElementById('edit-profile-btn').addEventListener('click', () => {
            this.openEditModal();
        });

        // Close modal
        document.getElementById('close-modal').addEventListener('click', () => {
            this.closeEditModal();
        });

        document.getElementById('cancel-edit').addEventListener('click', () => {
            this.closeEditModal();
        });

        // Edit form submission
        document.getElementById('edit-profile-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleProfileUpdate(e);
        });

        // Logout button
        document.getElementById('logout-btn').addEventListener('click', () => {
            this.handleLogout();
        });

        // Close modal on outside click
        document.getElementById('edit-modal').addEventListener('click', (e) => {
            if (e.target.id === 'edit-modal') {
                this.closeEditModal();
            }
        });
    }

    async loadProfile() {
        try {
            const tokens = this.getStoredTokens();
            if (!tokens) {
                this.redirectToAuth();
                return;
            }

            const response = await fetch('/auth/profile', {
                headers: {
                    'Authorization': `Bearer ${tokens.access_token}`
                }
            });

            if (response.ok) {
                this.currentUser = await response.json();
                this.displayProfile();
            } else if (response.status === 401) {
                this.redirectToAuth();
            } else {
                this.showError('Failed to load profile');
            }
        } catch (error) {
            console.error('Profile load error:', error);
            this.showError('Network error. Please try again.');
        }
    }

    displayProfile() {
        if (!this.currentUser) return;

        const profile = this.currentUser.profile || {};
        
        // Basic info
        document.getElementById('profile-name').textContent = profile.name || 'Not set';
        document.getElementById('profile-email').textContent = this.currentUser.email;
        document.getElementById('profile-email-detail').textContent = this.currentUser.email;
        
        // User type
        const userType = this.currentUser.user_type || 'student';
        document.getElementById('profile-type').textContent = userType.charAt(0).toUpperCase() + userType.slice(1);
        document.getElementById('profile-account-type').textContent = userType.charAt(0).toUpperCase() + userType.slice(1);

        // Academic info
        document.getElementById('profile-college').textContent = profile.college || 'Not set';
        document.getElementById('profile-branch').textContent = profile.branch || 'Not set';
        document.getElementById('profile-year').textContent = profile.year ? `${profile.year}${this.getOrdinalSuffix(profile.year)} Year` : 'Not set';
        document.getElementById('profile-semester').textContent = profile.semester ? `${profile.semester}${this.getOrdinalSuffix(profile.semester)} Semester` : 'Not set';

        // Profile picture
        this.setupProfilePicture(profile.picture, profile.name);

        // Member since (if available)
        if (this.currentUser.created_at) {
            const date = new Date(this.currentUser.created_at);
            document.getElementById('profile-created').textContent = date.toLocaleDateString();
        }
    }

    setupProfilePicture(pictureUrl, name) {
        const avatarImg = document.getElementById('profile-picture');
        const avatarPlaceholder = document.getElementById('avatar-placeholder');
        const avatarInitials = document.getElementById('avatar-initials');

        if (pictureUrl) {
            avatarImg.src = pictureUrl;
            avatarImg.style.display = 'block';
            avatarPlaceholder.style.display = 'none';
        } else {
            avatarImg.style.display = 'none';
            avatarPlaceholder.style.display = 'flex';
            
            // Set initials
            const initials = this.getInitials(name);
            avatarInitials.textContent = initials;
        }
    }

    getInitials(name) {
        if (!name) return '?';
        return name.split(' ')
            .map(word => word.charAt(0))
            .join('')
            .toUpperCase()
            .slice(0, 2);
    }

    getOrdinalSuffix(num) {
        const j = num % 10;
        const k = num % 100;
        if (j === 1 && k !== 11) return 'st';
        if (j === 2 && k !== 12) return 'nd';
        if (j === 3 && k !== 13) return 'rd';
        return 'th';
    }

    openEditModal() {
        if (!this.currentUser) return;

        const profile = this.currentUser.profile || {};
        
        // Populate form
        document.getElementById('edit-name').value = profile.name || '';
        document.getElementById('edit-college').value = profile.college || '';
        document.getElementById('edit-year').value = profile.year || 1;
        document.getElementById('edit-semester').value = profile.semester || 1;
        document.getElementById('edit-branch').value = profile.branch || '';

        // Show modal
        document.getElementById('edit-modal').classList.add('active');
    }

    closeEditModal() {
        document.getElementById('edit-modal').classList.remove('active');
    }

    async handleProfileUpdate(e) {
        const formData = new FormData(e.target);
        const updateBtn = e.target.querySelector('button[type="submit"]');
        
        try {
            this.setLoading(updateBtn, true);

            const profileData = {
                name: formData.get('name'),
                college: formData.get('college'),
                year: parseInt(formData.get('year')),
                semester: parseInt(formData.get('semester')),
                branch: formData.get('branch')
            };

            const tokens = this.getStoredTokens();
            const response = await fetch('/auth/profile', {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${tokens.access_token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(profileData)
            });

            if (response.ok) {
                // Update local user data
                this.currentUser.profile = { ...this.currentUser.profile, ...profileData };
                this.saveUserData();
                
                // Refresh display
                this.displayProfile();
                
                // Close modal
                this.closeEditModal();
                
                this.showSuccess('Profile updated successfully!');
            } else {
                const error = await response.json();
                this.showError(error.detail || 'Failed to update profile');
            }
        } catch (error) {
            console.error('Profile update error:', error);
            this.showError('Network error. Please try again.');
        } finally {
            this.setLoading(updateBtn, false);
        }
    }

    handleLogout() {
        if (confirm('Are you sure you want to logout?')) {
            this.clearAuthData();
            window.location.href = '/auth.html';
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

    saveUserData() {
        if (this.currentUser) {
            localStorage.setItem('vtu_user', JSON.stringify(this.currentUser));
        }
    }

    clearAuthData() {
        localStorage.removeItem('vtu_tokens');
        localStorage.removeItem('vtu_user');
    }

    redirectToAuth() {
        window.location.href = '/auth.html';
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

    showError(message) {
        this.showMessage(message, 'error');
    }

    showSuccess(message) {
        this.showMessage(message, 'success');
    }

    showMessage(message, type) {
        // Remove existing messages
        document.querySelectorAll('.message').forEach(msg => msg.remove());

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        messageDiv.textContent = message;
        
        const profileContainer = document.querySelector('.profile-container');
        profileContainer.insertBefore(messageDiv, profileContainer.firstChild);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            messageDiv.remove();
        }, 5000);
    }
}

// Initialize profile manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ProfileManager();
});
