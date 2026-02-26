from django.conf import settings
from django.db import models
from django.utils import timezone
from PIL import Image



#================================================
#          PROJECT MODELS
#================================================

class Project(models.Model):
    """
       Espace projet.

       Requis par le CDC:
       - code (prefixe tickets, ex: PROJ)
       - nom, description
       - date debut / fin
       - unite de mesure de charge
       - duree des sprints
       - capacite globale ou par user
       - board_type: scrum | kanban
    """

    BOARD_TYPES = [
        ("scrum", "Scrum"),
        ("kanban", "Kanban"),
    ]

    PROJECT_TYPES = [
        ("software", "Software"),
        ("marketing", "Marketing"),
        ("business", "Business"),
    ]

    PROJECT_TYPE_IMAGES = {
        "software": "project_types/software.png",
        "marketing": "project_types/marketing.png",
        "business": "project_types/business.png",
    }

    EFFORT_UNITS = [
        ("story_points", "Story Points"),
        ("man_days", "Man-Days"),
        ("man_hours", "Man-Hours"),
    ]

    image = models.ImageField(
        upload_to="project_icons/",
        default="project_icons/default.png",
        blank=True
    )
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=10,unique=True,help_text="Prefix used for ticket IDs (e.g. PROJ -> PROJ-1, PROJ-2 ...)")
    description = models.TextField(blank=True)

    # --- Type ---
    board_type = models.CharField(max_length=10, choices=BOARD_TYPES, default="scrum")
    project_type = models.CharField(max_length=20, choices=PROJECT_TYPES, default="software")

    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_projects",
    )

    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="Membership",
        related_name="projects",
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    # --- Capacite / estimation ---
    effort_unit = models.CharField(
        max_length=20,
        choices=EFFORT_UNITS,
        default="story_points",
        help_text="Unit used to estimate effort on tickets"
    )
    sprint_duration = models.PositiveIntegerField(
        default=14,
        help_text="Default sprint duration in days (e.g. 14 = 2 weeks)"
    )
    global_capacity = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text=(
            "Global team capacity per sprint (in effort_unit). "
            "If null, capacity is managed per member."
        )
    )


    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.code}] {self.name}"

    @property
    def active_sprint(self):
        return self.sprints.filter(status="active").first()

    @property
    def is_scrum(self):
        return self.board_type == "scrum"

    @property
    def is_kanban(self):
        return self.board_type == "kanban"

    @property
    def project_type_image(self):
        path = self.PROJECT_TYPE_IMAGES.get(self.project_type,"project_types/default.png")
        return f"{settings.MEDIA_URL}{path}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        img = Image.open(self.image.path)

        if img.height > 300 or img.width > 300:
            output_size = (300, 300)
            img.thumbnail(output_size)
            img.save(self.image.path)


#================================================
#          MEMBERSHIP MODELS  (role par projet)
#================================================
class Membership(models.Model):
    """
       Lien User <-> Project avec role projet.

       Roles projet (independants du global_role User):
         admin       : CRUD complet, gestion des membres du projet
         contributor : peut creer/modifier tickets et sprints
         read-only      : lecture seule (read-only)
    """

    ROLE_CHOICES = [
        ("admin", "Admin"),
        ("contributor", "Contributor"),
        ("read-only", "Read-only"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="memberships")
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="memberships")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="contributor")

    # Capacite individuelle dans ce projet (en effort_unit du projet)
    capacity_per_sprint = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text=(
            "Individual capacity per sprint (in project effort_unit). "
            "Used when global_capacity is not set on the project."
        )
    )

    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "project"],name="uniq_membership_user_project",)
        ]

    def __str__(self):
        return f"{self.user.username} -> [{self.project.code}] ({self.role})"

    @property
    def can_edit(self):
        return self.role in ("admin", "contributor")

    @property
    def can_manage(self):
        return self.role == "admin"


#================================================
#          BOARD MODELS
#================================================
class Board(models.Model):
    """
        Un projet possede exactement un Board (OneToOne).
        Cree automatiquement a la creation du Project via signal post_save.
    """

    project = models.OneToOneField(
        Project,
        on_delete=models.CASCADE,
        related_name="board"
    )

    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.project.code} Board"


#================================================
#          COLUMN MODELS
#================================================
class Column(models.Model):
    """
        Colonnes du board (ex: To Do / In Progress / Done).
        Ordonnees par `order`. Unicite (board, order) garantie.
    """

    board = models.ForeignKey(
        Board,
        on_delete=models.CASCADE,
        related_name="columns"
    )

    name = models.CharField(max_length=50)
    order = models.PositiveIntegerField()

    class Meta:
        ordering = ["order"]
        constraints = [
            models.UniqueConstraint(
                fields=["board", "order"],
                name="uniq_column_order_per_board"
            )
        ]

    def __str__(self):
        return f"{self.board.project.code} | {self.name} (#{self.order})"


#================================================
#          SPRINT MODELS
#================================================
class Sprint(models.Model):
    """
        Iteration Scrum.

        Cycle de vie (actions du CDC):
          planned -> [demarrer] -> active -> [cloture] -> completed
        Contrainte: un seul sprint actif par projet a la fois.
    """
    STATUS_CHOICES = [
        ("planned", "Planned"),
        ("active", "Active"),
        ("completed", "Completed"),
    ]

    project = models.ForeignKey(Project,on_delete=models.CASCADE,related_name="sprints")

    name = models.CharField(max_length=200)
    goals = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="planned")

    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    # Capacite du sprint (en effort_unit du projet)
    sprint_capacity = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Total team capacity for this sprint (in project effort_unit)"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-start_date"]
        constraints = [
            # Un seul sprint actif par projet
            models.UniqueConstraint(
                fields=["project"],
                condition=models.Q(status="active"),
                name="uniq_active_sprint_per_project",
            )
        ]

    def __str__(self):
        return f"[{self.project.code}] {self.name} ({self.status})"

    @property
    def is_active(self):
        return self.status == "active"

    @property
    def total_estimated(self):
        """Somme des estimations des issues dans ce sprint."""
        return (self.sprint_links.aggregate(total=models.Sum("issue__story_points"))["total"] or 0)


#=================================================================
#          ISSUE (TICKET) MODELS (Epic > User Story > Task > Bug)
#=================================================================
class Ticket(models.Model):
    """
       Ticket avec hierarchie: Epic -> User Story -> Task.
       Les bugs peuvent etre au niveau Story ou Task.

       Requis par le CDC:
       - 3 types avec hierarchie
       - ID, projet, demandeur, assigne, dates, statuts
       - Priorite relative dans le product backlog (backlog_order)
       - Estimation en effort_unit du projet
    """

    TICKET_TYPES = [
        ("task", "Task"),
        ("bug", "Bug"),
        ("user story", "User Story"),
        ("epic", "Epic"),
    ]

    # Statuts utilises selon le type:
    #   Epic        : open -> in_progress -> done
    #   Story / Bug : todo -> in_progress -> in_review -> done | blocked
    #   Task        : todo -> in_progress -> done
    TICKET_STATUSES = [
        ("open", "Open"),
        ("todo", "To Do"),
        ("in_progress", "In Progress"),
        ("in_review", "In Review"),
        ("done", "Done"),
        ("blocked", "Blocked"),
    ]

    TICKET_PRIORITIES = [
        ("lowest", "Lowest"),
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("highest", "Highest"),
    ]

    project = models.ForeignKey(Project,on_delete=models.CASCADE,related_name="tickets")

    # Hierarchie: Story.parent = Epic, Task.parent = Story
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="subtickets",
        help_text="Parent issue (Epic for Stories, Story for Tasks)"
    )

    # Column on the board (Kanban / Scrum board)
    column = models.ForeignKey(
        Column,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="issues"
    )

    # M2M to Sprint via SprintIssue join table, Sprint: une issue peut changer de sprint
    sprints = models.ManyToManyField(
        "Sprint",
        through="SprintTicket",
        related_name="tickets",
        blank=True
    )

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    labels = models.CharField(max_length=255, blank=True,help_text="Comma-separated labels (e.g. 'frontend,auth')")

    type = models.CharField(max_length=10, choices=TICKET_TYPES, default="user story")  # ex: bug / feature / task
    status = models.CharField(max_length=20, choices=TICKET_STATUSES, default="todo")
    priority = models.CharField(max_length=10, choices=TICKET_PRIORITIES, default="medium")

    # Estimation (en effort_unit du projet)
    story_points = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Effort estimate (in project effort_unit)"
    )

    attachments = models.FileField(upload_to="attachments/", blank=True)
    due_date = models.DateField(null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)

    # ---- People ----
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_tickets"
    )

    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="requested_tickets"
    )

    # ---- Ordering ----
    # Product backlog: priorite relative (plus petit = plus prioritaire)
    backlog_order = models.PositiveIntegerField(default=0,help_text="Relative priority in product backlog (lower = higher priority)")
    # Board: drag & drop (float pour inserer entre deux issues sans tout recalculer)
    board_order = models.FloatField(default=0,help_text="Visual ordering on the board column")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["backlog_order", "created_at"]

    def __str__(self):
        return f"{self.project.code}-{self.pk} [{self.type.upper()}] {self.title}"

    @property
    def ticket_id(self):
        """Ex: PROJ-42"""
        return f"{self.project.code}-{self.pk}"

    @property
    def is_epic(self):
        return self.type == "epic"


#================================================
#          SPRINT <-> ISSUE JOIN TABLE
#================================================
class SprintTicket(models.Model):
    """
        Table de jointure Sprint <-> Issue.

        Permet:
        - d'ajouter / retirer une issue d'un sprint
        - de la deplacer vers un autre sprint (historique conserve)
        - de connaitre l'ordre dans le sprint backlog (position)
    """

    sprint = models.ForeignKey(Sprint,on_delete=models.CASCADE,related_name="sprint_links")
    ticket = models.ForeignKey(Ticket,on_delete=models.CASCADE,related_name="ticket_links")

    added_at = models.DateTimeField(default=timezone.now)
    position = models.IntegerField(null=True, blank=True,help_text="Order in the sprint backlog (lower = higher priority)")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["sprint", "ticket"],
                name="uniq_sprint_ticket",
            )
        ]
        ordering = ["position", "added_at"]

    def __str__(self):
        return f"{self.sprint} <-> {self.ticket.ticket_id}"


# ===========================================================
#   COMMENT
# ===========================================================

class Comment(models.Model):
    """Commentaire sur une issue (v1 simple)."""

    ticket = models.ForeignKey(Ticket,on_delete=models.CASCADE,related_name="comments",) #ISSUES
    author = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="comments",)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Comment by {self.author.username} on {self.ticket.ticket_id}"