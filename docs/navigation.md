# 📌 Navigation & Page Flow — Project Management App

---

## 👤 Que voit l'utilisateur selon son état ?

### 1️⃣ User non connecté

- `/login` → Formulaire connexion
- `/register` → Formulaire inscription

---

### 2️⃣ User connecté (après login)

➡️ Redirection vers : `/dashboard`

#### Dashboard

- Liste de ses projets  
  *(cards : nom, code, board_type, dernière activité)*
- Bouton **Create Project** (visible pour tous les membres)
- Issues assignées à l'utilisateur
- **Section Admin** *(si `global_role == "admin"`)* :
  - Gestion des utilisateurs
  - Changer rôle global
  - Désactiver utilisateur

#### Navigation globale (Topbar)

- Logo → `/dashboard`
- My Projects → `/dashboard`
- Avatar menu :
  - Profile → `/profile`
  - Settings → `/settings`
  - Logout

---

## 📂 Dans un projet `/projects/<code>/`

### Sidebar (visible partout)

- Board → `/projects/<code>/board/`
- Backlog → `/projects/<code>/backlog/`
- Sprints → `/projects/<code>/sprints/`
- Members → `/projects/<code>/members/`
- Settings → `/projects/<code>/settings/` *(admin only)*

---

## 🧩 Pages Projet

### 🟦 Board
`/projects/<code>/board/`

- Vue Kanban (To Do | In Progress | Done)
- Issues draggable
- Clic → détail issue
- Filtres : assignee, priority, issue_type

---

### 📋 Backlog
`/projects/<code>/backlog/`

- Issues hors sprint actif
- Drag & drop pour réordonner
- Boutons priorité ↑ ↓
- Filtres : type, status, priority
- `+ Add Issue`

---

### 🏃 Sprints
`/projects/<code>/sprints/`

- Sprint actif avec progression
- Clôturer sprint
- Sprints planifiés :
  - Démarrer
  - Éditer / Supprimer
  - Sprint backlog (drag & drop)
- Archives
- `+ Create Sprint`

---

### 🐞 Issue Detail
`/projects/<code>/issues/<id>/`

- Titre, description
- Type, status, priority
- Assignee / reporter
- Story points
- Parent / enfants (Epic → Stories → Tasks)
- Sprint actuel
- Commentaires

---

### 👥 Members
`/projects/<code>/members/`

- Liste des membres + rôle
- Invitation (admin seulement)
- Modification des rôles

---

### ⚙️ Settings
`/projects/<code>/settings/`

- Modifier projet
- Capacité globale / par membre
- Colonnes du board
- Danger zone :
  - Archiver
  - Supprimer projet

---

## 👤 Profil
`/profile/`

- Avatar, nom, email
- Bio, job_title
- Changer mot de passe
- Préférences (langue, timezone)

---

## 🔐 Accès et Permissions

| Action | Viewer | Contributor | Project Admin | Platform Admin |
|--------|--------|-------------|---------------|----------------|
| Voir board/backlog/sprints | ✅ | ✅ | ✅ | ✅ |
| Créer / modifier issue | ❌ | ✅ | ✅ | ✅ |
| Drag & drop status | ❌ | ✅ | ✅ | ✅ |
| Gérer sprints | ❌ | ✅ | ✅ | ✅ |
| Inviter membres | ❌ | ❌ | ✅ | ✅ |
| Modifier settings | ❌ | ❌ | ✅ | ✅ |
| Supprimer projet | ❌ | ❌ | ✅ | ✅ |
| Gérer utilisateurs plateforme | ❌ | ❌ | ❌ | ✅ |

---

## 🌐 URLs suggérées (`urls.py`)

```python
urlpatterns = [
    # Auth
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("register/", views.register_view, name="register"),

    # Dashboard
    path("dashboard/", views.dashboard, name="dashboard"),
    path("profile/", views.profile, name="profile"),

    # Projects
    path("projects/create/", views.project_create, name="project-create"),
    path("projects/<str:code>/", views.project_board, name="project-board"),
    path("projects/<str:code>/backlog/", views.project_backlog, name="project-backlog"),
    path("projects/<str:code>/sprints/", views.project_sprints, name="project-sprints"),
    path("projects/<str:code>/members/", views.project_members, name="project-members"),
    path("projects/<str:code>/settings/", views.project_settings, name="project-settings"),

    # Issues
    path("projects/<str:code>/issues/create/", views.issue_create, name="issue-create"),
    path("projects/<str:code>/issues/<int:pk>/", views.issue_detail, name="issue-detail"),

    # Platform Admin
    path("admin/users/", views.admin_users, name="admin-users"),
]
