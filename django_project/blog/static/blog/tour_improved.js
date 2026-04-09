/**
 * ScrumManagement - Improved Onboarding Tour
 * Works across all major pages: Dashboard, Backlog, Active Sprint, Board, Issues, Roadmap, Reports, Settings
 */

(function() {
    'use strict';

    const STORAGE_KEY = 'scrum_tour_done_v2';

    // Comprehensive step definitions for all pages
    const ALL_STEPS = [
        // === DASHBOARD STEPS ===
        {
            selector: '.navbar-brand',
            title: '🏠 Navigation',
            icon: '🚀',
            desc: 'Le logo vous ramène au tableau de bord principal.',
            tip: 'Utilisez la navigation pour accéder rapidement à vos projets.',
            page: /^\/(projects\/?)?(list\/?)?$/,
            arrow: 'bottom',
            priority: 1
        },
        {
            selector: '.stats-grid .stat-card:first-child',
            title: '📊 Vue d\'ensemble',
            icon: '📈',
            desc: 'Visualisez rapidement le nombre de projets, tickets, et sprints actifs.',
            tip: 'Cliquez sur ces cartes pour voir plus de détails.',
            page: /^\/(projects\/?)?(list\/?)?$/,
            arrow: 'top',
            priority: 2
        },
        {
            selector: '.project-list .project-item:first-child',
            title: '📁 Projets récents',
            icon: '📂',
            desc: 'Accédez à vos projets récents directement depuis le dashboard.',
            tip: 'Cliquez sur un projet pour ouvrir son tableau Kanban.',
            page: /^\/(projects\/?)?(list\/?)?$/,
            arrow: 'top',
            priority: 3
        },
        {
            selector: '.quick-actions .quick-action:first-child',
            title: '⚡ Actions rapides',
            icon: '⚡',
            desc: 'Créez un projet, un ticket ou démarrez un sprint en un clic.',
            tip: 'Le bouton "Create" est aussi disponible dans la barre de navigation.',
            page: /^\/(projects\/?)?(list\/?)?$/,
            arrow: 'top',
            priority: 4
        },

        // === PROJECT BOARD / ACTIVE SPRINT STEPS ===
        {
            selector: '.sidebar .sidebar-link:first-child',
            title: '📋 Menu Projet',
            icon: '📋',
            desc: 'Navigation spécifique au projet : Backlog, Sprints, Issues, Roadmap, Reports.',
            tip: 'Le menu s\'adapte selon votre rôle (Admin, Contributor, Read-only).',
            page: /\/projects\/\d+\/(active-sprint|board|backlog|issues|roadmap|report|settings)/,
            arrow: 'right',
            priority: 1
        },
        {
            selector: '.as-banner, [data-tour="active-sprint-banner"]',
            title: '🏃 Sprint Actif',
            icon: '🏃',
            desc: 'Informations du sprint en cours : dates, progression, tickets.',
            tip: 'La barre de progression vous montre l\'avancement du sprint.',
            page: /\/projects\/\d+\/active-sprint/,
            arrow: 'bottom',
            priority: 2
        },
        {
            selector: '.kanban-board',
            title: '📊 Tableau Kanban',
            icon: '📊',
            desc: 'Glissez-déposez les tickets entre les colonnes : To Do → In Progress → Done.',
            tip: 'Les tickets rouges sont des bugs, les bleus des tâches, les verts des stories.',
            page: /\/projects\/\d+\/(active-sprint|board)/,
            arrow: 'top',
            priority: 3
        },
        {
            selector: '.backlog-quick-filters',
            title: '🔍 Filtres rapides',
            icon: '🔍',
            desc: 'Filtrez les tickets par assignation, date récente ou tickets bloqués.',
            tip: 'Utile pour se concentrer sur ses propres tâches.',
            page: /\/projects\/\d+\/(active-sprint|board)/,
            arrow: 'top',
            priority: 4
        },

        // === BACKLOG STEPS ===
        {
            selector: '.backlog-container, [data-tour="backlog"]',
            title: '📋 Product Backlog',
            icon: '📋',
            desc: 'Liste de tous les tickets non assignés à un sprint.',
            tip: 'Réorganisez par priorité avec les flèches ↑ ↓.',
            page: /\/projects\/\d+\/backlog/,
            arrow: 'top',
            priority: 1
        },
        {
            selector: '#globalCreateTicketModal, [data-target="#globalCreateTicketModal"]',
            title: '➕ Créer un ticket',
            icon: '➕',
            desc: 'Créez des Epics, Stories, Tasks ou Bugs directement depuis le backlog.',
            tip: 'Remplissez tous les champs pour bien catégoriser votre ticket.',
            page: /\/projects\/\d+\/(backlog|active-sprint|issues)/,
            arrow: 'bottom',
            priority: 2
        },

        // === ISSUES PAGE STEPS ===
        {
            selector: '.issues-toolbar',
            title: '🔎 Recherche et filtres',
            icon: '🔎',
            desc: 'Recherchez par mot-clé, filtrez par type, priorité ou assigné.',
            tip: 'La vue Groupée organise les tickets par statut.',
            page: /\/projects\/\d+\/issues/,
            arrow: 'bottom',
            priority: 1
        },
        {
            selector: '.issues-summary-bar',
            title: '📊 Résumé des tickets',
            icon: '📊',
            desc: 'Vue d\'ensemble des tickets par statut : To Do, In Progress, Done, Blocked.',
            tip: 'Cliquez sur un ticket pour voir ses détails dans le tiroir latéral.',
            page: /\/projects\/\d+\/issues/,
            arrow: 'top',
            priority: 2
        },

        // === ROADMAP STEPS ===
        {
            selector: '.roadmap-container, [data-tour="roadmap"]',
            title: '🗺️ Roadmap',
            icon: '🗺️',
            desc: 'Visualisation temporelle des Epics et des sprints planifiés.',
            tip: 'Planifiez vos releases et suivis à long terme.',
            page: /\/projects\/\d+\/roadmap/,
            arrow: 'top',
            priority: 1
        },

        // === REPORTS STEPS ===
        {
            selector: '#burndown-chart, .report-container',
            title: '📈 Burndown Chart',
            icon: '📈',
            desc: 'Suivez l\'avancement du sprint vs la capacité prévue.',
            tip: 'Idéal pour les rétrospectives de sprint.',
            page: /\/projects\/\d+\/report/,
            arrow: 'top',
            priority: 1
        },

        // === SETTINGS STEPS ===
        {
            selector: '#team-section, [data-tour="members"]',
            title: '👥 Gestion des membres',
            icon: '👥',
            desc: 'Invitez des membres et gérez leurs rôles (Admin, Contributor, Read-only).',
            tip: 'Seuls les Admins du projet peuvent modifier les rôles.',
            page: /\/projects\/\d+\/settings/,
            arrow: 'top',
            priority: 1
        },
        {
            selector: '#project-info-section',
            title: '⚙️ Paramètres du projet',
            icon: '⚙️',
            desc: 'Modifiez le nom, la description, le type de projet et la capacité.',
            tip: 'Les changements sont appliqués immédiatement.',
            page: /\/projects\/\d+\/settings/,
            arrow: 'top',
            priority: 2
        },

        // === CLOSE SPRINT STEPS ===
        {
            selector: '.cs-sprint-card:first-child',
            title: '📦 Sprints terminés',
            icon: '📦',
            desc: 'Historique des sprints complétés avec leurs tickets associés.',
            tip: 'Développez un sprint pour voir le détail des tickets.',
            page: /\/projects\/\d+\/close-sprint/,
            arrow: 'top',
            priority: 1
        },

        // === GLOBAL STEPS (any page) ===
        {
            selector: '.dropdown-toggle:contains("Projects")',
            title: '📁 Menu Projets',
            icon: '📁',
            desc: 'Changez de projet ou créez-en un nouveau.',
            tip: 'Le projet actif est affiché en surbrillance.',
            page: null,
            arrow: 'bottom',
            priority: 10
        },
        {
            selector: '[data-target="#globalCreateTicketModal"]',
            title: '➕ Création rapide',
            icon: '➕',
            desc: 'Créez un ticket depuis n\'importe quelle page sans interruption.',
            tip: 'Les tickets créés ici sont assignés au projet actif.',
            page: null,
            arrow: 'bottom',
            priority: 11
        },
        {
            selector: '.nav-item.dropdown:last-child .nav-link',
            title: '👤 Votre profil',
            icon: '👤',
            desc: 'Accédez à vos notifications, paramètres et déconnexion.',
            tip: 'Personnalisez votre avatar dans les paramètres de profil.',
            page: null,
            arrow: 'bottom',
            priority: 12
        }
    ];

    // Helper to get elements (supports multiple selectors)
    function getElement(selector) {
        if (!selector) return null;
        const selectors = selector.split(',').map(s => s.trim());
        for (const sel of selectors) {
            try {
                // Handle :contains pseudo-selector
                if (sel.includes(':contains')) {
                    const match = sel.match(/(.+):contains\(['"](.+)['"]\)/);
                    if (match) {
                        const baseSel = match[1];
                        const text = match[2];
                        const elements = document.querySelectorAll(baseSel);
                        for (const el of elements) {
                            if (el.textContent.includes(text)) return el;
                        }
                    }
                } else {
                    const el = document.querySelector(sel);
                    if (el) return el;
                }
            } catch(e) {}
        }
        return null;
    }

    // Get relevant steps for current page
    function getRelevantSteps() {
        const path = window.location.pathname;
        return ALL_STEPS
            .filter(step => step.page === null || step.page.test(path))
            .sort((a, b) => (a.priority || 99) - (b.priority || 99));
    }

    // Check if tour was already completed
    function isTourCompleted() {
        return localStorage.getItem(STORAGE_KEY) === 'true';
    }

    // Mark tour as completed
    function completeTour() {
        localStorage.setItem(STORAGE_KEY, 'true');
    }

    // Reset tour (for testing)
    window.resetTour = function() {
        localStorage.removeItem(STORAGE_KEY);
        location.reload();
    };

    // Initialize tour system
    class ScrumTour {
        constructor() {
            this.currentStep = 0;
            this.steps = [];
            this.active = false;
            this.overlay = null;
            this.spotlight = null;
            this.tooltip = null;
            this.launcher = null;
            this.welcomeModal = null;
        }

        init() {
            this.createDOM();
            this.attachEvents();

            // Show welcome modal only on dashboard and if tour not completed
            const isDashboard = /^\/(projects\/?)?(list\/?)?$/.test(window.location.pathname);
            if (!isTourCompleted() && isDashboard) {
                setTimeout(() => this.showWelcome(), 1000);
            }
        }

        createDOM() {
            // Overlay
            this.overlay = document.createElement('div');
            this.overlay.id = 'tour-overlay';
            this.overlay.className = 'tour-overlay';
            document.body.appendChild(this.overlay);

            // Spotlight
            this.spotlight = document.createElement('div');
            this.spotlight.id = 'tour-spotlight';
            this.spotlight.className = 'tour-spotlight hidden';
            document.body.appendChild(this.spotlight);

            // Tooltip
            this.tooltip = document.createElement('div');
            this.tooltip.id = 'tour-tooltip';
            this.tooltip.className = 'tour-tooltip';
            this.tooltip.innerHTML = `
                <div class="tour-header">
                    <div class="tour-badge">
                        <span class="tour-badge-dot"></span>
                        Guide interactif
                    </div>
                    <span class="tour-step-counter" id="tour-step-counter"></span>
                    <button id="tour-close-btn" class="tour-close"><i class="fas fa-times"></i></button>
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
                        <button class="tour-btn tour-btn-skip" id="tour-skip">Passer</button>
                        <button class="tour-btn tour-btn-prev" id="tour-prev" style="display:none;">← Précédent</button>
                        <button class="tour-btn tour-btn-next" id="tour-next">Suivant →</button>
                    </div>
                </div>
            `;
            document.body.appendChild(this.tooltip);

            // Launcher button
            this.launcher = document.createElement('button');
            this.launcher.id = 'tour-launcher';
            this.launcher.className = 'tour-launcher';
            this.launcher.innerHTML = '<i class="fas fa-question-circle"></i> Guide';
            this.launcher.title = 'Guide interactif';
            document.body.appendChild(this.launcher);

            // Welcome modal
            this.welcomeModal = document.createElement('div');
            this.welcomeModal.id = 'tour-welcome';
            this.welcomeModal.className = 'tour-welcome hidden';
            this.welcomeModal.innerHTML = `
                <div class="tour-welcome-card">
                    <div class="tour-welcome-hero">
                        <div class="tour-welcome-logo">🚀</div>
                        <h2>Bienvenue sur ScrumManagement !</h2>
                        <p>Votre outil de gestion de projet Agile</p>
                    </div>
                    <div class="tour-welcome-body">
                        <p>Découvrez les fonctionnalités principales en <strong>moins de 2 minutes</strong>.</p>
                        <div class="tour-welcome-features">
                            <div class="tour-welcome-feature"><i class="fas fa-columns"></i> Tableau Kanban</div>
                            <div class="tour-welcome-feature"><i class="fas fa-list"></i> Backlog produit</div>
                            <div class="tour-welcome-feature"><i class="fas fa-running"></i> Sprints actifs</div>
                            <div class="tour-welcome-feature"><i class="fas fa-chart-line"></i> Burndown chart</div>
                            <div class="tour-welcome-feature"><i class="fas fa-users"></i> Gestion des rôles</div>
                            <div class="tour-welcome-feature"><i class="fas fa-ticket-alt"></i> Tickets & Epics</div>
                        </div>
                        <div class="tour-welcome-actions">
                            <button class="tour-btn tour-btn-skip" id="tour-welcome-skip">Non merci</button>
                            <button class="tour-btn tour-btn-next" id="tour-welcome-start">Démarrer le tour →</button>
                        </div>
                    </div>
                </div>
            `;
            document.body.appendChild(this.welcomeModal);
        }

        attachEvents() {
            document.getElementById('tour-close-btn')?.addEventListener('click', () => this.end());
            document.getElementById('tour-skip')?.addEventListener('click', () => this.end());
            document.getElementById('tour-next')?.addEventListener('click', () => this.next());
            document.getElementById('tour-prev')?.addEventListener('click', () => this.prev());
            this.launcher?.addEventListener('click', () => this.start());
            document.getElementById('tour-welcome-skip')?.addEventListener('click', () => this.closeWelcome());
            document.getElementById('tour-welcome-start')?.addEventListener('click', () => {
                this.closeWelcome();
                this.start();
            });
            this.overlay?.addEventListener('click', (e) => {
                if (e.target === this.overlay) this.end();
            });

            // Keyboard navigation
            document.addEventListener('keydown', (e) => {
                if (!this.active) return;
                if (e.key === 'ArrowRight' || e.key === 'Enter') this.next();
                if (e.key === 'ArrowLeft') this.prev();
                if (e.key === 'Escape') this.end();
            });

            window.addEventListener('resize', () => {
                if (this.active) this.positionElements();
            });
            window.addEventListener('scroll', () => {
                if (this.active) this.positionElements();
            });
        }

        showWelcome() {
            this.welcomeModal?.classList.remove('hidden');
        }

        closeWelcome() {
            this.welcomeModal?.classList.add('hidden');
        }

        start() {
            this.steps = getRelevantSteps();
            if (this.steps.length === 0) {
                console.log('No steps for current page');
                return;
            }
            this.currentStep = 0;
            this.active = true;
            this.overlay?.classList.add('visible');
            this.launcher?.classList.add('hidden');
            this.renderStep();
        }

        end() {
            this.active = false;
            this.overlay?.classList.remove('visible');
            this.spotlight?.classList.add('hidden');
            this.tooltip?.classList.remove('visible');
            this.launcher?.classList.remove('hidden');
            completeTour();

            // Remove highlights
            document.querySelectorAll('.tour-highlight-target').forEach(el => {
                el.classList.remove('tour-highlight-target');
            });
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
            const msg = document.createElement('div');
            msg.className = 'tour-completion-toast';
            msg.innerHTML = `
                <i class="fas fa-check-circle"></i>
                <div>
                    <strong>Tour terminé !</strong><br>
                    Vous maîtrisez maintenant ScrumManagement.
                </div>
            `;
            document.body.appendChild(msg);
            setTimeout(() => msg.remove(), 3000);
        }

        renderStep() {
            const step = this.steps[this.currentStep];
            const total = this.steps.length;
            const isLast = this.currentStep === total - 1;
            const isFirst = this.currentStep === 0;

            // Update tooltip content
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

            // Update counter and progress
            document.getElementById('tour-step-counter').textContent = `${this.currentStep + 1} / ${total}`;
            document.getElementById('tour-progress-bar').style.width = `${((this.currentStep + 1) / total) * 100}%`;

            // Update dots
            const dots = document.getElementById('tour-dots');
            dots.innerHTML = '';
            for (let i = 0; i < total; i++) {
                const dot = document.createElement('span');
                dot.className = 'tour-dot';
                if (i === this.currentStep) dot.classList.add('active');
                if (i < this.currentStep) dot.classList.add('done');
                dots.appendChild(dot);
            }

            // Update buttons
            document.getElementById('tour-prev').style.display = isFirst ? 'none' : '';
            const nextBtn = document.getElementById('tour-next');
            nextBtn.textContent = isLast ? '✓ Terminer' : 'Suivant →';
            nextBtn.className = `tour-btn ${isLast ? 'tour-btn-finish' : 'tour-btn-next'}`;

            // Highlight target
            document.querySelectorAll('.tour-highlight-target').forEach(el => {
                el.classList.remove('tour-highlight-target');
            });

            const target = getElement(step.selector);
            if (target) {
                target.classList.add('tour-highlight-target');
                target.scrollIntoView({ behavior: 'smooth', block: 'center', inline: 'center' });
                setTimeout(() => this.positionElements(), 300);
            } else {
                console.warn(`Target not found: ${step.selector}`);
            }

            // Show tooltip
            this.tooltip.classList.remove('visible');
            setTimeout(() => this.tooltip.classList.add('visible'), 50);
        }

        positionElements() {
            const step = this.steps[this.currentStep];
            const target = getElement(step.selector);
            const PADDING = 12;
            const TT_W = 360;
            const TT_H = 280;
            const vw = window.innerWidth;
            const vh = window.innerHeight;

            if (!target) {
                this.spotlight.classList.add('hidden');
                this.tooltip.setAttribute('data-arrow', 'none');
                this.tooltip.style.left = `${(vw - TT_W) / 2}px`;
                this.tooltip.style.top = `${(vh - TT_H) / 2}px`;
                return;
            }

            // Position spotlight
            const rect = target.getBoundingClientRect();
            const scrollY = window.scrollY;
            const scrollX = window.scrollX;

            this.spotlight.classList.remove('hidden');
            this.spotlight.style.top = `${rect.top + scrollY - PADDING}px`;
            this.spotlight.style.left = `${rect.left + scrollX - PADDING}px`;
            this.spotlight.style.width = `${rect.width + PADDING * 2}px`;
            this.spotlight.style.height = `${rect.height + PADDING * 2}px`;

            // Position tooltip
            let top, left, arrow;
            const relativeTop = rect.top;
            const relativeBottom = rect.bottom;
            const relativeLeft = rect.left;
            const relativeRight = rect.right;

            // Try to place tooltip intelligently
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
            } else if (relativeRight + PADDING + TT_W < vw) {
                // Right
                top = Math.max(PADDING + scrollY, Math.min(relativeTop + scrollY, vh + scrollY - TT_H - PADDING));
                left = relativeRight + scrollX + PADDING;
                arrow = 'left';
            } else {
                // Left
                top = Math.max(PADDING + scrollY, Math.min(relativeTop + scrollY, vh + scrollY - TT_H - PADDING));
                left = relativeLeft + scrollX - PADDING - TT_W;
                arrow = 'right';
            }

            this.tooltip.setAttribute('data-arrow', arrow);
            this.tooltip.style.top = `${Math.max(PADDING + scrollY, top)}px`;
            this.tooltip.style.left = `${Math.max(PADDING + scrollX, left)}px`;
        }
    }

    // Initialize tour when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            window.scrumTour = new ScrumTour();
            window.scrumTour.init();
        });
    } else {
        window.scrumTour = new ScrumTour();
        window.scrumTour.init();
    }
})();