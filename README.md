# Project Management Application (Scrum-compatible)

A lightweight web application for managing software projects using the Scrum framework.  
Designed as a cost-effective alternative to Jira for academic use at **HELB**, focusing on the features actually needed in project management courses.

## Purpose
HELB currently provides Jira to students for project management exercises, but Jira comes with a significant monthly cost compared to the features used.  
This project aims to deliver a **Scrum-oriented project management tool** with essential functionalities: project spaces, tickets, backlog prioritization, sprint management, and user access control.


## Key Features

### 1) Project Spaces
CRUD management of project spaces with:
- Project code (prefix)
- Name, description
- Start date, end date
- Workload unit: **man-days**, **man-hours**, or **story points**
- Sprint duration
- Capacity: global or per user

### 2) Ticket Management
Supports 4 ticket types:
- **Epics**
- **User Stories**
- **Bugs**
- **Tasks**

Hierarchy:
- Epics → User Stories
- Bugs → Tasks

Common fields (all ticket types):
- Human-readable identifier
- Project
- Title, description
- Status
- Requester user
- Assignee user

Type-specific fields:
- **Epic**: start date, end date, absolute priority
- **User story / Bug / Task**: start date, end date, initial workload, remaining workload, completed workload, associated sprint

Minimal status sets:
- **Epic**: `active`, `completed`, `cancelled`
- **User story & Bug**: `new`, `active`, `closed`, `cancelled`
- **Task**: `new`, `active`, `closed`, `cancelled`

### 3) Product Backlog
- Displays **user stories and bugs** ordered by **relative priority**
- Shows related epic (if applicable)
- Allows reordering items (move up / move down)

### 4) Sprints
CRUD for sprints with:
- Name, start date, end date
- Goal
- Status

Sprint capabilities:
- Capacity tracking: global or per user
- Actions:
  - Start a sprint
  - Close a sprint
  - Add stories/bugs to sprint
  - Move stories/bugs between sprint and product backlog
- Sprint backlog: same behavior as product backlog
- Kanban view of the sprint with drag/move between statuses
- Constraint: **only one active sprint at a time**

### 5) Users & Access Control
Authentication:
- Sign up
- Log in

User fields:
- Email
- Last name, first name
- Username (pseudo)

Roles:
- Admin
- Contributor

Project permissions:
- Admin
- Contributor
- Read-only

### 6) Language
- The entire application UI and content must be **in English**.

## Suggested / Optional Enhancements (Nice-to-have)
Ordered by added value:
- Statistics module (per sprint, burndown chart, velocity, points per user, etc.)
- Basic Git integration (link commits to tickets)
- File attachments (project-level and/or ticket-level)
- User profile picture
- Create a new user story directly from the product backlog
- Configurable story point values (e.g., Fibonacci) per project space
- Tags on tickets
- Custom ticket statuses and allowed transitions
- Links between user stories/bugs (e.g., “blocked by”)
- Ticket templates (pre-filled descriptions, e.g., “As a…, I want…, so that…”)
- Epic color

## Expected Deliverables
- Project Charter
- High-level design
- Versioned source code on HELB GitHub
- Final product presentation

## Differentiation vs Jira
Each team must propose **at least 3 significant differences** compared to Jira and justify them.  
The best solution may become the base for future course usage, and contributors may be credited in the application.

## Tech Stack (Recommended)
- **Backend:** Python (Django recommended)
- **Frontend:** HTML, CSS, JavaScript (Bootstrap or Angular)
- **Database:** MariaDB or PostgreSQL

## License
Specify the project license here (e.g., MIT) if applicable.

## Credits
Add team members and contributors here. If parts of this project are adopted for future course versions, contributors may be listed in the app.
