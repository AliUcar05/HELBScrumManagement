---

#  Ordre de développement recommandé

L'ordre est important — chaque étape dépend de la précédente.

---

##  Sprint 1 (17/02 → 03/03) — Foundation

- `admin.py`
  - Enregistrer tous les modèles pour tests via l’interface admin

- **Auth**
  - Pages login / logout / register
  - Django auth views suffisantes pour commencer

- **Dashboard**
  - Liste des projets de l'utilisateur connecté

- **CRUD Project**
  - Créer un projet
  - Modifier un projet
  - Supprimer un projet

---

##  Sprint 2 (03/03 → 17/03) — Tickets & Backlog

- CRUD Issue *(Epic / Story / Task / Bug)*
- Product backlog :
  - Liste ordonnée par `backlog_order`
  - Boutons priorité ↑ ↓
- Page détail issue avec commentaires

---

##  Sprint 3 (17/03 → 31/03) — Sprints

- CRUD Sprint
- Ajouter / retirer des issues d'un sprint *(via `SprintIssue`)*
- Démarrer un sprint
- Clôturer un sprint
- Sprint backlog *(même logique que product backlog)*

---

##  Sprint 4 (31/03 → 14/04) — Board & Polish

- Board Kanban :
  - Colonnes
  - Drag & drop *(SortableJS — bibliothèque gratuite)*

- Gestion des membres :
  - Inviter
  - Changer rôle

- Permissions :
  - Décorateurs ou mixins selon le rôle

- Tests
- Corrections
- Préparation présentation

---
