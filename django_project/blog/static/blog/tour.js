/**
 * ScrumManagement — Onboarding Tour (Ultimate Edition)
 * Auto-detects current page and shows the right steps.
 * Stores completion in localStorage with user-specific key.
 *
 * Features:
 * - Smart element detection with fallbacks
 * - Persistent "don't show again" option
 * - Smooth animations and responsive design
 * - Complete keyboard navigation
 * - Works with Bootstrap modals
 */

(function() {
    'use strict';

    /* ══════════════════════════════════════════
       CONFIGURATION
    ══════════════════════════════════════════ */
    const STORAGE_KEY = 'scrum_tour_completed_v3';
    const DONT_SHOW_AGAIN_KEY = 'scrum_tour_dont_show_again';

    // Debug mode (set to false in production)
    const DEBUG = false;

    function log(...args) {
        if (DEBUG) console.log('[Tour]', ...args);
    }

    /* ══════════════════════════════════════════
       STEP DEFINITIONS (Améliorées)
    ══════════════════════════════════════════ */
    const ALL_STEPS = [
        // === DASHBOARD / ACCUEIL ===
        {
            selector: '.navbar-brand, .logo, [href*="project-list"], [href*="/projects/"]',
            title: '🏠 Navigation principale',
            icon: '🚀',
            desc: 'La barre de navigation vous donne accès à <strong>tous vos projets</strong> et fonctionnalités.',
            tip: 'Cliquez sur le logo ScrumManagement pour revenir à l\'accueil à tout moment.',
            page: null,  // Toutes les pages
            arrow: 'bottom',
            priority: 0
        },
        {
            selector: '.project-card, .project-item, [data-tour="project"]',
            title: '📁 Vos projets',
            icon: '📂',
            desc: 'Chaque projet est présenté sous forme de carte. Cliquez sur un projet pour accéder à son tableau de bord.',
            tip: 'Seuls les projets où vous êtes membre ou admin apparaissent ici.',
            page: /^\/(projects\/?)?(list\/?)?$/,
            arrow: 'top',
            priority: 1
        },
        {
            selector: '.btn-create-project, a[href*="project-create"], a[href$="/create/"]',
            title: '✨ Créer un projet',
            icon: '✨',
            desc: 'En tant qu\'administrateur, vous pouvez créer un nouveau projet Scrum.',
            tip: 'Définissez le nom, le type (Software/Business) et la capacité de l\'équipe.',
            page: /projects/,
            arrow: 'bottom',
            priority: 2
        },

        // === TABLEAU KANBAN ===
        {
            selector: '.kanban-board, .board-columns, [data-tour="board"]',
            title: '🗂️ Tableau Kanban',
            icon: '📊',
            desc: 'Visualisez et gérez vos tickets du <strong>sprint actif</strong> : To Do → In Progress → Done.',
            tip: 'Glissez-déposez les tickets entre les colonnes pour changer leur statut.',
            page: /board/,
            arrow: 'top',
            priority: 1
        },
        {
            selector: '.column-todo, .column-to-do, [data-status="todo"]',
            title: '📝 Colonne "À faire"',
            icon: '📝',
            desc: 'Les tickets prêts à être développés mais pas encore commencés.',
            tip: 'Démarrez un ticket en le glissant vers "In Progress".',
            page: /board/,
            arrow: 'top',
            priority: 2
        },
        {
            selector: '.column-progress, .column-in-progress, [data-status="in-progress"]',
            title: '⚙️ En cours',
            icon: '⚙️',
            desc: 'Les tickets actuellement en développement.',
            tip: 'Un ticket ne devrait rester que quelques jours dans cette colonne.',
            page: /board/,
            arrow: 'top',
            priority: 2
        },
        {
            selector: '.column-done, .column-completed, [data-status="done"]',
            title: '✅ Terminé',
            icon: '✅',
            desc: 'Les tickets complétés et prêts pour la revue.',
            tip: 'À la fin du sprint, tous les tickets doivent être ici.',
            page: /board/,
            arrow: 'top',
            priority: 2
        },

        // === BACKLOG ===
        {
            selector: '.backlog-list, #backlog-container, [data-tour="backlog"]',
            title: '📋 Product Backlog',
            icon: '📋',
            desc: 'Tous les tickets non assignés à un sprint. C\'est ici que vous priorisez le travail à venir.',
            tip: 'Cliquez sur les flèches ↑ ↓ pour réorganiser la priorité.',
            page: /backlog/,
            arrow: 'top',
            priority: 1
        },
        {
            selector: '#createTicketBtn, [data-target="#globalCreateTicketModal"], .btn-create-ticket',
            title: '➕ Créer un ticket',
            icon: '➕',
            desc: 'Créez des <strong>Epics</strong>, <strong>User Stories</strong>, <strong>Bugs</strong> ou <strong>Tasks</strong>.',
            tip: 'Remplissez le titre, la description, l\'assigné et les story points.',
            page: /(backlog|active-sprint|issues)/,
            arrow: 'bottom',
            priority: 3
        },

        // === SPRINT ACTIF ===
        {
            selector: '.active-sprint, .sprint-active, [data-tour="sprint"]',
            title: '🏃 Sprint actif',
            icon: '🏃',
            desc: 'Le sprint en cours avec sa date de fin et sa progression.',
            tip: 'La barre de progression se met à jour automatiquement.',
            page: /(active-sprint|sprints)/,
            arrow: 'top',
            priority: 1
        },
        {
            selector: '.sprint-progress-bar, .progress-bar',
            title: '📊 Progression',
            icon: '📈',
            desc: 'Visualisez l\'avancement du sprint en temps réel.',
            tip: 'Objectif : 100% des story points complétés à la fin du sprint.',
            page: /(active-sprint|sprints)/,
            arrow: 'top',
            priority: 2
        },

        // === DÉTAIL D'UN TICKET ===
        {
            selector: '.ticket-detail, .issue-detail, [data-tour="ticket"]',
            title: '🐞 Détail du ticket',
            icon: '🔍',
            desc: 'Chaque ticket a un type, une priorité, un assigné et des story points.',
            tip: 'Ajoutez des commentaires et sous-tâches pour mieux suivre l\'avancement.',
            page: /issues\/\d+/,
            arrow: 'top',
            priority: 1
        },

        // === MEMBRES ===
        {
            selector: '.members-list, #team-section, [data-tour="members"]',
            title: '👥 Équipe et rôles',
            icon: '👥',
            desc: 'Gérez les membres du projet et leurs rôles : Viewer, Contributor, Admin.',
            tip: 'Seuls les admins peuvent inviter et modifier les rôles.',
            page: /members/,
            arrow: 'top',
            priority: 1
        },

        // === RAPPORTS ===
        {
            selector: '#burndown-chart, .report-container, canvas',
            title: '📊 Burndown Chart',
            icon: '📉',
            desc: 'Suivez la vélocité de l\'équipe et l\'avancement par rapport à la capacité prévue.',
            tip: 'Utile pour les rétrospectives de sprint et l\'amélioration continue.',
            page: /report/,
            arrow: 'top',
            priority: 1
        },

        // === STEP FINAL ===
        {
            selector: null,
            title: '🎉 Félicitations !',
            icon: '🎊',
            desc: 'Vous connaissez maintenant les bases de ScrumManagement.<br><br>Commencez par explorer votre premier projet ou créez-en un nouveau !',
            tip: 'Le bouton "Guide" (❓) est toujours disponible en bas à droite.',
            page: null,
            arrow: 'none',
            priority: 999
        }
    ];

    /* ══════════════════════════════════════════
       UTILITAIRES AMÉLIORÉS
    ══════════════════════════════════════════ */

    /**
     * Récupère un élément avec plusieurs sélecteurs de fallback
     */
    function getElement(selector) {
        if (!selector) return null;

        // Gère les sélecteurs multiples
        const selectors = selector.split(',').map(s => s.trim());

        for (const sel of selectors) {
            try {
                // Support du pseudo-sélecteur :contains (personnalisé)
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
                    if (el && el.offsetParent !== null) { // Vérifie que l'élément est visible
                        return el;
                    }
                }
            } catch(e) {
                log('Selector error:', sel, e);
            }
        }
        return null;
    }

    /**
     * Vérifie si le tour doit être montré
     */
    function shouldShowTour() {
        // Ne pas montrer si déjà complété
        if (localStorage.getItem(STORAGE_KEY) === 'true') {
            log('Tour déjà complété');
            return false;
        }

        // Ne pas montrer si "Ne plus afficher"
        if (localStorage.getItem(DONT_SHOW_AGAIN_KEY) === 'true') {
            log('Utilisateur a choisi "Ne plus afficher"');
            return false;
        }

        // Vérifie le flag Django
        if (window.TOUR_SHOW_WELCOME !== true) {
            log('Flag Django non actif');
            return false;
        }

        return true;
    }

    /**
     * Filtre les étapes pertinentes pour la page actuelle
     */
    function getRelevantSteps() {
        const path = window.location.pathname;
        const relevant = ALL_STEPS
            .filter(step => step.page === null || step.page.test(path))
            .sort((a, b) => (a.priority || 99) - (b.priority || 99));

        log(`${relevant.length} étapes pertinentes trouvées`);
        return relevant;
    }

    /* ══════════════════════════════════════════
       CLASSE PRINCIPALE
    ══════════════════════════════════════════ */

    class ScrumTour {
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

            // Montre la modale de bienvenue si nécessaire
            if (shouldShowTour()) {
                // Attendre que la page soit complètement chargée
                if (document.readyState === 'loading') {
                    document.addEventListener('DOMContentLoaded', () => setTimeout(() => this.showWelcome(), 500));
                } else {
                    setTimeout(() => this.showWelcome(), 500);
                }
            } else if (localStorage.getItem(STORAGE_KEY) !== 'true') {
                // Le tour n'a pas été montré mais ne doit pas l'être (pas de flag)
                // On pourrait montrer le launcher mais pas la modale auto
                log('Tour non montré auto (pas de flag)');
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
                        Guide interactif
                    </div>
                    <span class="tour-step-counter" id="tour-step-counter"></span>
                    <button id="tour-close-btn" title="Fermer"><i class="fas fa-times"></i></button>
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
                        <button class="tour-btn tour-btn-dont-show" id="tour-dont-show">Ne plus afficher</button>
                        <button class="tour-btn tour-btn-prev" id="tour-prev" style="display:none;">←</button>
                        <button class="tour-btn tour-btn-next" id="tour-next">Suivant →</button>
                    </div>
                </div>
            `;
            document.body.appendChild(this.elements.tooltip);

            // Launcher (bouton flottant)
            this.elements.launcher = document.createElement('button');
            this.elements.launcher.id = 'tour-launcher';
            this.elements.launcher.innerHTML = '<i class="fas fa-question-circle"></i> Guide';
            this.elements.launcher.title = 'Ouvrir le guide interactif';
            document.body.appendChild(this.elements.launcher);

            // Welcome modal
            this.elements.welcome = document.createElement('div');
            this.elements.welcome.id = 'tour-welcome';
            this.elements.welcome.classList.add('hidden');
            this.elements.welcome.innerHTML = `
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
                            <div class="tour-welcome-feature"><i class="fas fa-list"></i> Product Backlog</div>
                            <div class="tour-welcome-feature"><i class="fas fa-running"></i> Sprints actifs</div>
                            <div class="tour-welcome-feature"><i class="fas fa-chart-line"></i> Burndown chart</div>
                            <div class="tour-welcome-feature"><i class="fas fa-users"></i> Gestion des rôles</div>
                            <div class="tour-welcome-feature"><i class="fas fa-ticket-alt"></i> Tickets & Epics</div>
                        </div>
                        <div class="tour-welcome-actions">
                            <button class="tour-btn tour-btn-skip" id="tour-welcome-dont-show">Ne plus afficher</button>
                            <button class="tour-btn tour-btn-skip" id="tour-welcome-skip">Non merci</button>
                            <button class="tour-btn tour-btn-next" id="tour-welcome-start">Démarrer →</button>
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
            this.showToast('✓ Guide désactivé', 'Vous pourrez le réactiver dans les paramètres.');
        }

        start() {
            this.steps = getRelevantSteps();
            if (this.steps.length === 0) {
                log('Aucune étape pour cette page');
                this.showToast('ℹ️ Guide', 'Aucun élément à vous montrer sur cette page.');
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

            // Nettoyer les highlights
            document.querySelectorAll('.tour-highlight-target').forEach(el => {
                el.classList.remove('tour-highlight-target');
            });

            // Marquer comme complété
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
            this.showToast('🎉 Tour terminé !', 'Vous maîtrisez maintenant ScrumManagement.');
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
                // Mode centré (pas de target)
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
                // En dessous
                top = relativeBottom + scrollY + PADDING;
                left = Math.max(PADDING, Math.min(relativeLeft + scrollX, vw - TT_W - PADDING));
                arrow = 'top';
            } else if (relativeTop - PADDING - TT_H > 0) {
                // Au-dessus
                top = relativeTop + scrollY - PADDING - TT_H;
                left = Math.max(PADDING, Math.min(relativeLeft + scrollX, vw - TT_W - PADDING));
                arrow = 'bottom';
            } else if (rect.right + PADDING + TT_W < vw) {
                // À droite
                top = Math.max(PADDING + scrollY, Math.min(relativeTop + scrollY, vh + scrollY - TT_H - PADDING));
                left = rect.right + scrollX + PADDING;
                arrow = 'left';
            } else {
                // À gauche
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
       INITIALISATION
    ══════════════════════════════════════════ */

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            window.scrumTour = new ScrumTour();
            window.scrumTour.init();
        });
    } else {
        window.scrumTour = new ScrumTour();
        window.scrumTour.init();
    }

    // Expose pour debugging
    window.resetTour = function() {
        localStorage.removeItem(STORAGE_KEY);
        localStorage.removeItem(DONT_SHOW_AGAIN_KEY);
        location.reload();
    };

})();