/**
 * ScrumManagement — Professional Interactive Guide
 * Professional SaaS-style onboarding experience
 * Smart page detection, persistent state, keyboard navigation
 */

(function() {
    'use strict';

    /* ══════════════════════════════════════════
       CONFIGURATION
    ══════════════════════════════════════════ */
    const STORAGE_KEY = 'scrum_guide_completed_v4';
    const DONT_SHOW_AGAIN_KEY = 'scrum_guide_dont_show_again';
    const DEBUG = false;

    function log(...args) {
        if (DEBUG) console.log('[Guide]', ...args);
    }

    /* ══════════════════════════════════════════
       PROFESSIONAL GUIDE STEPS
    ══════════════════════════════════════════ */
    const ALL_STEPS = [
        // === PROJECTS & NAVIGATION ===
        {
            selector: '.navbar-brand, [href*="project-list"]',
            title: '🏠 Welcome to ScrumManagement',
            icon: '🚀',
            desc: 'Your complete <strong>Agile project management platform</strong> for managing sprints, backlogs, and team collaboration.',
            tip: 'Click the logo anytime to return to your projects dashboard.',
            page: null,
            arrow: 'bottom',
            priority: 0
        },
        {
            selector: '.project-card, .card.project-item, [data-tour="project"]',
            title: '📁 Your Projects',
            icon: '📂',
            desc: 'Each card represents a project you\'re a member of. Click any project to access its <strong>Active Sprint</strong>, <strong>Backlog</strong>, and <strong>Reports</strong>.',
            tip: 'You only see projects where you have access as a member or admin.',
            page: /^\/(projects\/?)?(list\/?)?$/,
            arrow: 'top',
            priority: 1
        },
        {
            selector: '.btn-create-project, a[href*="project-create"], a[href$="/new/"]',
            title: '✨ Create New Project',
            icon: '✨',
            desc: 'As an administrator, create new Scrum projects. Define the project name, type (Software/Business), and team capacity.',
            tip: 'Each project has its own backlog, sprints, and team members.',
            page: /projects/,
            arrow: 'bottom',
            priority: 2
        },

        // === PRODUCT BACKLOG ===
        {
            selector: '.backlog-list, #backlog-tbody, [data-tour="backlog"]',
            title: '📋 Product Backlog',
            icon: '📋',
            desc: 'The <strong>Product Backlog</strong> contains all tickets not assigned to a sprint. Prioritize work by dragging tickets up or down.',
            tip: 'Use the ↑ ↓ arrows to reorder tickets by priority.',
            page: /backlog/,
            arrow: 'top',
            priority: 1
        },
        {
            selector: '#createTicketBtn, [data-target="#globalCreateTicketModal"], .btn-create-ticket, button:contains("Create")',
            title: '➕ Create Tickets',
            icon: '➕',
            desc: 'Create <strong>Epics</strong>, <strong>User Stories</strong>, <strong>Bugs</strong>, or <strong>Tasks</strong>. Assign them to team members and estimate story points.',
            tip: 'Always provide a clear title, description, and priority for better tracking.',
            page: /(backlog|active-sprint|issues)/,
            arrow: 'bottom',
            priority: 3
        },
        {
            selector: '.sprint-section, .sprint-card, [data-tour="sprint-planning"]',
            title: '🎯 Sprint Planning',
            icon: '🎯',
            desc: 'Organize tickets into <strong>Sprints</strong>. Drag tickets from the backlog into a sprint to plan upcoming work.',
            tip: 'Sprints typically last 1-4 weeks. Plan capacity based on your team\'s velocity.',
            page: /backlog/,
            arrow: 'top',
            priority: 2
        },

        // === ACTIVE SPRINT & KANBAN BOARD ===
        {
            selector: '.kanban-board, .board-columns, [data-tour="board"]',
            title: '🗂️ Kanban Board',
            icon: '📊',
            desc: 'The <strong>Kanban Board</strong> visualizes your active sprint. Move tickets through columns: <strong>To Do → In Progress → Done</strong>.',
            tip: 'Drag and drop tickets between columns to update their status in real-time.',
            page: /(active-sprint|board)/,
            arrow: 'top',
            priority: 1
        },
        {
            selector: '.as-banner, .active-sprint-header, [data-tour="sprint"]',
            title: '🏃 Active Sprint Overview',
            icon: '🏃',
            desc: 'View your current sprint\'s <strong>timeline</strong>, <strong>goals</strong>, and <strong>progress</strong>. Track how many days remain and completion percentage.',
            tip: 'The progress bar updates automatically as tickets move to Done.',
            page: /(active-sprint|sprints)/,
            arrow: 'top',
            priority: 2
        },
        {
            selector: '.kanban-column, .column-todo',
            title: '📝 To Do Column',
            icon: '📝',
            desc: 'Tickets ready to start but not yet in progress. These are planned for the current sprint.',
            tip: 'Move tickets to "In Progress" when you begin working on them.',
            page: /(active-sprint|board)/,
            arrow: 'top',
            priority: 3
        },
        {
            selector: '.column-in-progress, [data-status="in_progress"]',
            title: '⚙️ In Progress',
            icon: '⚙️',
            desc: 'Tickets currently being developed or worked on by the team.',
            tip: 'Limit work in progress (WIP) to maintain focus and flow.',
            page: /(active-sprint|board)/,
            arrow: 'top',
            priority: 3
        },
        {
            selector: '.column-done, [data-status="done"]',
            title: '✅ Done',
            icon: '✅',
            desc: 'Completed tickets ready for review or deployment. At sprint end, all tickets should ideally be here.',
            tip: 'Move tickets to Done only when they meet your Definition of Done.',
            page: /(active-sprint|board)/,
            arrow: 'top',
            priority: 3
        },

        // === SPRINT MANAGEMENT ===
        {
            selector: '.btn-start-sprint, [data-action="start-sprint"]',
            title: '▶️ Start Sprint',
            icon: '▶️',
            desc: 'Once you\'ve planned tickets, <strong>start the sprint</strong> to begin tracking progress.',
            tip: 'Set a clear sprint goal and timeline before starting.',
            page: /backlog/,
            arrow: 'bottom',
            priority: 4
        },
        {
            selector: '.as-complete-btn, #completeSprintBtn',
            title: '🏁 Complete Sprint',
            icon: '🏁',
            desc: 'When the sprint ends, complete it to review results. Decide what to do with unfinished tickets.',
            tip: 'You\'ll be asked whether to move unfinished tickets back to the backlog or mark them as done.',
            page: /active-sprint/,
            arrow: 'left',
            priority: 5
        },

        // === TICKET DETAILS ===
        {
            selector: '.ticket-card, .issue-row, [data-ticket-id]',
            title: '🎫 Ticket Details',
            icon: '🔍',
            desc: 'Each ticket has a <strong>type</strong>, <strong>priority</strong>, <strong>assignee</strong>, and <strong>story points</strong>. Click any ticket to view full details.',
            tip: 'Add comments and attachments to collaborate with your team.',
            page: null,
            arrow: 'top',
            priority: 1
        },

        // === TEAM & MEMBERS ===
        {
            selector: '.members-list, #team-section, [data-tour="members"]',
            title: '👥 Team Management',
            icon: '👥',
            desc: 'Manage project members and assign roles: <strong>Read-Only</strong>, <strong>Contributor</strong>, or <strong>Admin</strong>.',
            tip: 'Only admins can invite members and change permissions.',
            page: /(members|settings)/,
            arrow: 'top',
            priority: 1
        },

        // === REPORTS & ANALYTICS ===
        {
            selector: '#burndown-chart, .report-container, canvas',
            title: '📊 Reports & Analytics',
            icon: '📈',
            desc: 'Track team <strong>velocity</strong>, view <strong>burndown charts</strong>, and analyze sprint performance.',
            tip: 'Use reports during retrospectives to identify improvement opportunities.',
            page: /report/,
            arrow: 'top',
            priority: 1
        },

        // === ROADMAP ===
        {
            selector: '.roadmap-container, [data-tour="roadmap"]',
            title: '🗓️ Product Roadmap',
            icon: '🗺️',
            desc: 'Visualize your long-term product plan with <strong>epics</strong> and <strong>milestones</strong>.',
            tip: 'Plan multiple sprints ahead to align with business objectives.',
            page: /roadmap/,
            arrow: 'top',
            priority: 1
        },

        // === FINAL STEP ===
        {
            selector: null,
            title: '🎉 You\'re All Set!',
            icon: '🎊',
            desc: 'You now understand the core features of ScrumManagement.<br><br><strong>Ready to start?</strong> Create your first project or join an existing team!',
            tip: 'Access this guide anytime by clicking the <strong>Guide</strong> button in the navigation bar.',
            page: null,
            arrow: 'none',
            priority: 999
        }
    ];

    /* ══════════════════════════════════════════
       UTILITIES
    ══════════════════════════════════════════ */

    function getElement(selector) {
        if (!selector) return null;

        const selectors = selector.split(',').map(s => s.trim());

        for (const sel of selectors) {
            try {
                // Support for :contains
                if (sel.includes(':contains')) {
                    const match = sel.match(/(.+):contains\(['"](.+)['"]\)/);
                    if (match) {
                        const baseSel = match[1];
                        const searchText = match[2];
                        const elements = document.querySelectorAll(baseSel);
                        for (const el of elements) {
                            if (el.textContent && el.textContent.includes(searchText)) {
                                return el;
                            }
                        }
                    }
                } else {
                    const el = document.querySelector(sel);
                    if (el && el.offsetParent !== null) {
                        return el;
                    }
                }
            } catch(e) {
                log('Selector error:', sel, e);
            }
        }
        return null;
    }

    function shouldShowGuide() {
        if (localStorage.getItem(STORAGE_KEY) === 'true') {
            log('Guide already completed');
            return false;
        }

        if (localStorage.getItem(DONT_SHOW_AGAIN_KEY) === 'true') {
            log('User chose "Don\'t show again"');
            return false;
        }

        if (window.TOUR_SHOW_WELCOME !== true) {
            log('Django flag not active');
            return false;
        }

        return true;
    }

    function getRelevantSteps() {
        const path = window.location.pathname;
        const relevant = ALL_STEPS
            .filter(step => step.page === null || step.page.test(path))
            .sort((a, b) => (a.priority || 99) - (b.priority || 99));

        log(`${relevant.length} relevant steps found for ${path}`);
        return relevant;
    }

    /* ══════════════════════════════════════════
       MAIN TOUR CLASS
    ══════════════════════════════════════════ */

    class ScrumGuide {
        constructor() {
            this.steps = [];
            this.currentStep = 0;
            this.active = false;
            this.elements = {};
            this.positionTimeout = null;
        }

        init() {
            this.createDOM();
            this.attachEvents();

            if (shouldShowGuide()) {
                if (document.readyState === 'loading') {
                    document.addEventListener('DOMContentLoaded', () => setTimeout(() => this.showWelcome(), 500));
                } else {
                    setTimeout(() => this.showWelcome(), 500);
                }
            }
        }

        createDOM() {
            // Overlay
            this.elements.overlay = document.createElement('div');
            this.elements.overlay.id = 'tour-overlay';
            document.body.appendChild(this.elements.overlay);

            // Spotlight
            this.elements.spotlight = document.createElement('div');
            this.elements.spotlight.id = 'tour-spotlight';
            this.elements.spotlight.classList.add('hidden');
            document.body.appendChild(this.elements.spotlight);

            // Tooltip
            this.elements.tooltip = document.createElement('div');
            this.elements.tooltip.id = 'tour-tooltip';
            this.elements.tooltip.innerHTML = `
                <div class="tour-header">
                    <div class="tour-badge">
                        <span class="tour-badge-dot"></span>
                        Interactive Guide
                    </div>
                    <span class="tour-step-counter" id="tour-step-counter"></span>
                    <button id="tour-close-btn" title="Close"><i class="fas fa-times"></i></button>
                </div>
                <div class="tour-progress">
                    <div class="tour-progress-bar" id="tour-progress-bar"></div>
                </div>
                <div class="tour-body">
                    <div class="tour-icon" id="tour-icon"></div>
                    <div class="tour-title" id="tour-title"></div>
                    <div class="tour-desc" id="tour-desc"></div>
                    <div class="tour-tip" id="tour-tip" style="display:none;"></div>
                </div>
                <div class="tour-footer">
                    <div class="tour-dots" id="tour-dots"></div>
                    <div class="tour-nav">
                        <button class="tour-btn tour-btn-skip" id="tour-skip">Skip</button>
                        <button class="tour-btn tour-btn-dont-show" id="tour-dont-show">Don't Show Again</button>
                        <button class="tour-btn tour-btn-prev" id="tour-prev" style="display:none;">←</button>
                        <button class="tour-btn tour-btn-next" id="tour-next">Next →</button>
                    </div>
                </div>
            `;
            document.body.appendChild(this.elements.tooltip);

            // Launcher (floating button)
            this.elements.launcher = document.createElement('button');
            this.elements.launcher.id = 'tour-launcher';
            this.elements.launcher.innerHTML = '<i class="fas fa-question-circle"></i> Guide';
            this.elements.launcher.title = 'Open Interactive Guide';
            document.body.appendChild(this.elements.launcher);

            // Welcome modal
            this.elements.welcome = document.createElement('div');
            this.elements.welcome.id = 'tour-welcome';
            this.elements.welcome.classList.add('hidden');
            this.elements.welcome.innerHTML = `
                <div class="tour-welcome-card">
                    <div class="tour-welcome-hero">
                        <div class="tour-welcome-logo">🚀</div>
                        <h2>Welcome to ScrumManagement!</h2>
                        <p>Your professional Agile project management platform</p>
                    </div>
                    <div class="tour-welcome-body">
                        <p>Take a <strong>2-minute interactive tour</strong> to learn the key features and get started quickly.</p>
                        <div class="tour-welcome-features">
                            <div class="tour-welcome-feature"><i class="fas fa-columns"></i> Kanban Boards</div>
                            <div class="tour-welcome-feature"><i class="fas fa-list"></i> Product Backlog</div>
                            <div class="tour-welcome-feature"><i class="fas fa-running"></i> Sprint Planning</div>
                            <div class="tour-welcome-feature"><i class="fas fa-chart-line"></i> Burndown Charts</div>
                            <div class="tour-welcome-feature"><i class="fas fa-users"></i> Team Management</div>
                            <div class="tour-welcome-feature"><i class="fas fa-ticket-alt"></i> Ticket Tracking</div>
                        </div>
                        <div class="tour-welcome-actions">
                            <button class="tour-btn tour-btn-skip" id="tour-welcome-dont-show">Don't Show Again</button>
                            <button class="tour-btn tour-btn-skip" id="tour-welcome-skip">Skip Tour</button>
                            <button class="tour-btn tour-btn-next" id="tour-welcome-start">Start Tour →</button>
                        </div>
                    </div>
                </div>
            `;
            document.body.appendChild(this.elements.welcome);
        }

        attachEvents() {
            // Tooltip buttons
            document.getElementById('tour-close-btn')?.addEventListener('click', () => this.end());
            document.getElementById('tour-skip')?.addEventListener('click', () => this.end());
            document.getElementById('tour-dont-show')?.addEventListener('click', () => this.dontShowAgain());
            document.getElementById('tour-next')?.addEventListener('click', () => this.next());
            document.getElementById('tour-prev')?.addEventListener('click', () => this.prev());

            // Launcher
            this.elements.launcher?.addEventListener('click', () => this.start());

            // Welcome modal buttons
            document.getElementById('tour-welcome-skip')?.addEventListener('click', () => this.closeWelcome());
            document.getElementById('tour-welcome-dont-show')?.addEventListener('click', () => {
                this.dontShowAgain();
                this.closeWelcome();
            });
            document.getElementById('tour-welcome-start')?.addEventListener('click', () => {
                this.closeWelcome();
                this.start();
            });

            // Close on overlay click
            this.elements.overlay?.addEventListener('click', (e) => {
                if (e.target === this.elements.overlay) this.end();
            });

            // Keyboard navigation
            document.addEventListener('keydown', (e) => {
                if (!this.active) return;
                if (e.key === 'ArrowRight' || e.key === 'Enter') this.next();
                if (e.key === 'ArrowLeft') this.prev();
                if (e.key === 'Escape') this.end();
            });

            // Reposition on scroll/resize
            window.addEventListener('resize', () => this.debouncedPosition());
            window.addEventListener('scroll', () => this.debouncedPosition());
        }

        debouncedPosition() {
            if (this.positionTimeout) clearTimeout(this.positionTimeout);
            this.positionTimeout = setTimeout(() => {
                if (this.active) this.positionElements();
            }, 100);
        }

        showWelcome() {
            if (this.elements.welcome) {
                this.elements.welcome.classList.remove('hidden');
            }
        }

        closeWelcome() {
            if (this.elements.welcome) {
                this.elements.welcome.classList.add('hidden');
            }
        }

        dontShowAgain() {
            localStorage.setItem(DONT_SHOW_AGAIN_KEY, 'true');
            localStorage.setItem(STORAGE_KEY, 'true');
            this.end();
            this.showToast('✓ Guide Disabled', 'You can re-enable it from your profile settings.');
        }

        start() {
            this.steps = getRelevantSteps();
            if (this.steps.length === 0) {
                log('No steps for this page');
                this.showToast('ℹ️ Guide', 'No guide steps available for this page.');
                return;
            }

            this.currentStep = 0;
            this.active = true;
            this.elements.overlay.classList.add('visible');
            this.elements.launcher.style.display = 'none';
            this.renderStep();
        }

        end() {
            this.active = false;
            this.elements.overlay.classList.remove('visible');
            this.elements.spotlight.classList.add('hidden');
            this.elements.tooltip.classList.remove('visible');
            this.elements.launcher.style.display = '';

            document.querySelectorAll('.tour-highlight-target').forEach(el => {
                el.classList.remove('tour-highlight-target');
            });

            if (localStorage.getItem(DONT_SHOW_AGAIN_KEY) !== 'true') {
                localStorage.setItem(STORAGE_KEY, 'true');
            }
        }

        next() {
            if (this.currentStep < this.steps.length - 1) {
                this.currentStep++;
                this.renderStep();
            } else {
                this.end();
                this.showCompletionMessage();
            }
        }

        prev() {
            if (this.currentStep > 0) {
                this.currentStep--;
                this.renderStep();
            }
        }

        showCompletionMessage() {
            this.showToast('🎉 Tour Complete!', 'You\'re ready to start managing your projects.');
        }

        showToast(title, message) {
            const toast = document.createElement('div');
            toast.className = 'tour-completion-toast';
            toast.innerHTML = `
                <i class="fas fa-check-circle"></i>
                <div>
                    <strong>${title}</strong><br>
                    ${message}
                </div>
            `;
            document.body.appendChild(toast);
            setTimeout(() => toast.remove(), 4000);
        }

        renderStep() {
            const step = this.steps[this.currentStep];
            const total = this.steps.length;
            const isLast = this.currentStep === total - 1;
            const isFirst = this.currentStep === 0;

            // Update content
            document.getElementById('tour-icon').textContent = step.icon || '🎯';
            document.getElementById('tour-title').textContent = step.title;
            document.getElementById('tour-desc').innerHTML = step.desc;

            const tipEl = document.getElementById('tour-tip');
            if (step.tip) {
                tipEl.innerHTML = `<i class="fas fa-lightbulb"></i> ${step.tip}`;
                tipEl.style.display = '';
            } else {
                tipEl.style.display = 'none';
            }

            // Counter & progress
            document.getElementById('tour-step-counter').textContent = `${this.currentStep + 1} / ${total}`;
            document.getElementById('tour-progress-bar').style.width = `${((this.currentStep + 1) / total) * 100}%`;

            // Dots
            const dots = document.getElementById('tour-dots');
            dots.innerHTML = '';
            for (let i = 0; i < total; i++) {
                const dot = document.createElement('span');
                dot.className = 'tour-dot';
                if (i === this.currentStep) dot.classList.add('active');
                if (i < this.currentStep) dot.classList.add('done');
                dots.appendChild(dot);
            }

            // Buttons
            document.getElementById('tour-prev').style.display = isFirst ? 'none' : '';
            const nextBtn = document.getElementById('tour-next');
            nextBtn.textContent = isLast ? '✓ Finish' : 'Next →';
            nextBtn.className = `tour-btn ${isLast ? 'tour-btn-finish' : 'tour-btn-next'}`;

            // Highlight target
            document.querySelectorAll('.tour-highlight-target').forEach(el => {
                el.classList.remove('tour-highlight-target');
            });

            const target = getElement(step.selector);
            if (target) {
                target.classList.add('tour-highlight-target');
                target.scrollIntoView({ behavior: 'smooth', block: 'center', inline: 'center' });
            }

            // Position tooltip
            setTimeout(() => this.positionElements(), 200);

            // Show tooltip with animation
            this.elements.tooltip.classList.remove('visible');
            setTimeout(() => this.elements.tooltip.classList.add('visible'), 50);
        }

        positionElements() {
            const step = this.steps[this.currentStep];
            const target = getElement(step.selector);
            const PADDING = 12;
            const TT_W = 360;
            const TT_H = 280;
            const vw = window.innerWidth;
            const vh = window.innerHeight;
            const scrollY = window.scrollY;
            const scrollX = window.scrollX;

            if (!target) {
                // Centered mode (no target)
                this.elements.spotlight.classList.add('hidden');
                this.elements.tooltip.setAttribute('data-arrow', 'none');
                this.elements.tooltip.style.left = `${(vw - TT_W) / 2}px`;
                this.elements.tooltip.style.top = `${(vh - TT_H) / 2 + scrollY}px`;
                return;
            }

            // Position spotlight
            const rect = target.getBoundingClientRect();
            this.elements.spotlight.classList.remove('hidden');
            this.elements.spotlight.style.top = `${rect.top + scrollY - PADDING}px`;
            this.elements.spotlight.style.left = `${rect.left + scrollX - PADDING}px`;
            this.elements.spotlight.style.width = `${rect.width + PADDING * 2}px`;
            this.elements.spotlight.style.height = `${rect.height + PADDING * 2}px`;

            // Position tooltip
            let top, left, arrow;
            const relativeTop = rect.top;
            const relativeBottom = rect.bottom;
            const relativeLeft = rect.left;

            if (relativeBottom + PADDING + TT_H < vh) {
                // Below
                top = relativeBottom + scrollY + PADDING;
                left = Math.max(PADDING, Math.min(relativeLeft + scrollX, vw - TT_W - PADDING));
                arrow = 'top';
            } else if (relativeTop - PADDING - TT_H > 0) {
                // Above
                top = relativeTop + scrollY - PADDING - TT_H;
                left = Math.max(PADDING, Math.min(relativeLeft + scrollX, vw - TT_W - PADDING));
                arrow = 'bottom';
            } else if (rect.right + PADDING + TT_W < vw) {
                // Right
                top = Math.max(PADDING + scrollY, Math.min(relativeTop + scrollY, vh + scrollY - TT_H - PADDING));
                left = rect.right + scrollX + PADDING;
                arrow = 'left';
            } else {
                // Left
                top = Math.max(PADDING + scrollY, Math.min(relativeTop + scrollY, vh + scrollY - TT_H - PADDING));
                left = rect.left + scrollX - PADDING - TT_W;
                arrow = 'right';
            }

            this.elements.tooltip.setAttribute('data-arrow', arrow);
            this.elements.tooltip.style.top = `${Math.max(PADDING + scrollY, top)}px`;
            this.elements.tooltip.style.left = `${Math.max(PADDING + scrollX, left)}px`;
        }
    }

    /* ══════════════════════════════════════════
       INITIALIZATION
    ══════════════════════════════════════════ */

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            window.scrumTour = new ScrumGuide();
            window.scrumTour.init();
        });
    } else {
        window.scrumTour = new ScrumGuide();
        window.scrumTour.init();
    }

    // Expose for debugging
    window.resetGuide = function() {
        localStorage.removeItem(STORAGE_KEY);
        localStorage.removeItem(DONT_SHOW_AGAIN_KEY);
        location.reload();
    };

})();
