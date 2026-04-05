# Scrum Project Management Application

A lightweight, Scrum-compatible project management web application built with Django, designed as a cost-effective alternative to Jira for academic use at **HELB**.

---

## Table of Contents

- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Database Setup](#database-setup)
- [Running the Application](#running-the-application)
- [Loading Demo Data](#loading-demo-data)
- [Demo Accounts](#demo-accounts)
- [Application Structure](#application-structure)
- [Key Features](#key-features)

---

## Overview

This application provides a Scrum-oriented project management tool with essential functionalities: project spaces, ticket management, product backlog prioritization, sprint management, a Kanban board, and role-based access control.

---

## Tech Stack

| Layer      | Technology                         |
|------------|-------------------------------------|
| Backend    | Python 3 / Django 5.2              |
| Frontend   | HTML, CSS, Bootstrap                |
| Database   | PostgreSQL                          |
| Forms      | django-crispy-forms + crispy-bootstrap4 |

---

## Prerequisites

Before getting started, make sure the following are installed on your machine:

- Python 3.10 or higher
- pip
- PostgreSQL (running on port `5432`)
- Git

---

## Installation

**1. Clone the repository**

```bash
git clone <repository-url>
cd <repository-folder>
```

**2. (Optional but recommended) Create a virtual environment**

```bash
python -m venv venv
source venv/bin/activate        # macOS / Linux
venv\Scripts\activate           # Windows
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

---

## Database Setup

**1. Open a PostgreSQL session and run the following commands:**

```sql
CREATE USER django_user WITH PASSWORD 'Garedumidi';
CREATE DATABASE django_project_db OWNER django_user;
GRANT ALL PRIVILEGES ON DATABASE django_project_db TO django_user;
```

**2. Verify the Django database settings in `django_project/settings.py`:**

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'django_project_db',
        'USER': 'django_user',
        'PASSWORD': 'Garedumidi',
        'HOST': '127.0.0.1',
        'PORT': '5432',
    }
}
```

**3. Apply migrations:**

```bash
cd django_project
python manage.py migrate
```

---

## Running the Application

```bash
python manage.py runserver
```

The application will be accessible at:

- **Main app:** http://127.0.0.1:8000/
- **Django admin panel:** http://127.0.0.1:8000/admin/

---

## Loading Demo Data

A demo fixture is provided to populate the application with a realistic sample project (**SNA — Suivi des Notes Académiques**), including sprints, tickets, comments, and activity logs.

**To load demo data into a fresh database:**

```bash
# Place the fixture file:
# django_project/scrum/fixtures/demo_sna_notes_fixture.json

cd django_project
python manage.py flush --noinput
python manage.py migrate
python manage.py loaddata demo_sna_notes_fixture
```

**To promote the `admin` account to global admin:**

```bash
python manage.py shell -c "from django.contrib.auth.models import User; u=User.objects.get(username='admin'); u.profile.global_role='admin'; u.profile.save(); print('Done')"
```

> **Note:** The fixture is intended for a clean database. Running it on an existing database may cause ID or username conflicts.

---

## Demo Accounts

All demo accounts share the same password:

```
Password: Demo1234!
```

| Username | Role            |
|----------|-----------------|
| admin    | Platform Admin  |
| po       | Product Owner   |
| sm       | Scrum Master    |
| dev      | Developer       |
| test     | Tester          |
| viewer   | Read-only       |

---

## Application Structure

```
django_project/
├── manage.py
├── scrum/
│   ├── fixtures/
│   │   └── demo_sna_notes_fixture.json
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   └── templates/
└── settings.py
```

---

## Key Features

- **Project Spaces** — Create and manage projects with sprint duration, workload units, and team capacity settings
- **Ticket Management** — Supports Epics, User Stories, Bugs, and Tasks with full hierarchy
- **Product Backlog** — Priority ordering with move up / move down controls
- **Sprint Management** — Start, close, and track sprints; only one active sprint at a time
- **Kanban Board** — Drag-and-drop ticket status management (To Do / In Progress / Done)
- **Role-Based Access Control** — Platform admin, project admin, contributor, and read-only roles
- **Statistics** — Burndown chart and sprint progress reporting

---

## Superuser (Manual Creation)

If you prefer to create a superuser manually instead of using the demo fixture:

```bash
python manage.py createsuperuser
```

Suggested credentials used during development:
- **Username:** Helb
- **Password:** Garedumidi
