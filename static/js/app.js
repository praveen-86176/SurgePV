/**
 * Issue Tracker Frontend Application
 */
const app = {
    // API Configuration
    apiBase: '/issues',

    // State
    state: {
        issues: [],
        filters: {
            status: ''
        },
        loading: false
    },

    // Initialization
    init() {
        this.cacheDOM();
        this.bindEvents();
        this.fetchIssues();
    },

    // Cache DOM Elements
    cacheDOM() {
        this.dom = {
            issuesGrid: document.getElementById('issuesGrid'),
            loadingState: document.getElementById('loadingState'),
            errorState: document.getElementById('errorState'),
            newIssueBtn: document.getElementById('newIssueBtn'),
            refreshBtn: document.getElementById('refreshBtn'),
            statusFilter: document.getElementById('statusFilter'),
            issueModal: document.getElementById('issueModal'),
            createIssueForm: document.getElementById('createIssueForm'),
            closeModalBtns: document.querySelectorAll('.close-modal'),
            toast: document.getElementById('toast')
        };
    },

    // Bind Event Listeners
    bindEvents() {
        this.dom.newIssueBtn.addEventListener('click', () => this.openModal());
        this.dom.refreshBtn.addEventListener('click', () => this.fetchIssues());
        this.dom.statusFilter.addEventListener('change', (e) => this.handleFilterChange(e));

        this.dom.closeModalBtns.forEach(btn => {
            btn.addEventListener('click', () => this.closeModal());
        });

        this.dom.issueModal.addEventListener('click', (e) => {
            if (e.target === this.dom.issueModal) this.closeModal();
        });

        this.dom.createIssueForm.addEventListener('submit', (e) => this.handleCreateIssue(e));
    },

    // Fetch Issues from API
    async fetchIssues() {
        this.setLoading(true);
        this.dom.errorState.classList.add('hidden');
        this.dom.issuesGrid.innerHTML = '';

        try {
            // Build query string
            const params = new URLSearchParams({ limit: 100 });
            if (this.state.filters.status) {
                params.append('status', this.state.filters.status);
            }

            const response = await fetch(`${this.apiBase}?${params.toString()}`);

            if (!response.ok) throw new Error('Failed to fetch issues');

            const data = await response.json();
            this.state.issues = data.items || [];
            this.renderIssues();
        } catch (error) {
            console.error('Error fetching issues:', error);
            this.dom.errorState.classList.remove('hidden');
        } finally {
            this.setLoading(false);
        }
    },

    // Render Issues Grid
    renderIssues() {
        if (this.state.issues.length === 0) {
            this.dom.issuesGrid.innerHTML = `
                <div style="grid-column: 1/-1; text-align: center; color: var(--text-secondary); padding: 40px;">
                    <p>No issues found matching your criteria.</p>
                </div>
            `;
            return;
        }

        const fragment = document.createDocumentFragment();

        this.state.issues.forEach(issue => {
            const card = document.createElement('article');
            card.className = 'issue-card';
            card.innerHTML = `
                <div class="card-header">
                    <h3 class="issue-title">${this.escapeHtml(issue.title)}</h3>
                    <span class="badge badge-status status-${issue.status.toLowerCase()}">${issue.status.replace('_', ' ')}</span>
                </div>
                <p class="issue-description">${this.escapeHtml(issue.description || 'No description provided.')}</p>
                <div class="card-footer">
                    <span class="badge badge-priority priority-${issue.priority.toLowerCase()}">${issue.priority}</span>
                    <span class="issue-id">ID: #${issue.id}</span>
                </div>
            `;
            // Add click listener (optional: for detailed view)
            card.addEventListener('click', () => console.log('Clicked issue', issue.id));
            fragment.appendChild(card);
        });

        this.dom.issuesGrid.appendChild(fragment);
    },

    // Handle Create Issue
    async handleCreateIssue(e) {
        e.preventDefault();

        const submitBtn = this.dom.createIssueForm.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;
        submitBtn.textContent = 'Creating...';
        submitBtn.disabled = true;

        const formData = new FormData(e.target);
        const payload = {
            title: formData.get('title'),
            description: formData.get('description'),
            priority: formData.get('priority'),
            status: formData.get('status'),
            assignee_id: formData.get('assignee_id') ? parseInt(formData.get('assignee_id')) : null
        };

        try {
            const response = await fetch(this.apiBase, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to create issue');
            }

            this.showToast('Issue created successfully!');
            this.closeModal();
            this.dom.createIssueForm.reset();
            this.fetchIssues(); // Refresh list
        } catch (error) {
            console.error('Error creating issue:', error);
            alert(`Error: ${error.message}`);
        } finally {
            submitBtn.textContent = originalText;
            submitBtn.disabled = false;
        }
    },

    // Filter Logic
    handleFilterChange(e) {
        this.state.filters.status = e.target.value;
        this.fetchIssues();
    },

    // UI Helpers
    setLoading(isLoading) {
        this.state.loading = isLoading;
        if (isLoading) {
            this.dom.loadingState.classList.remove('hidden');
            this.dom.issuesGrid.classList.add('hidden');
        } else {
            this.dom.loadingState.classList.add('hidden');
            this.dom.issuesGrid.classList.remove('hidden');
        }
    },

    openModal() {
        this.dom.issueModal.classList.remove('hidden');
        document.body.style.overflow = 'hidden'; // Prevent background scrolling
    },

    closeModal() {
        this.dom.issueModal.classList.add('hidden');
        document.body.style.overflow = '';
    },

    showToast(message) {
        this.dom.toast.textContent = message;
        this.dom.toast.classList.remove('hidden');
        setTimeout(() => {
            this.dom.toast.classList.add('hidden');
        }, 3000);
    },

    escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
};

// Start the app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    app.init();
});
