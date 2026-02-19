from django.conf import settings
from django.db import models
from django.utils import timezone


class Project(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    sprint_duration = models.PositiveIntegerField(default=14)

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

    def __str__(self):
        return self.name


class Membership(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)

    role = models.CharField(max_length=50, default="member")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "project"], name="uniq_membership_user_project")
        ]

    def __str__(self):
        return f"{self.user} -> {self.project} ({self.role})"


class Sprint(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="sprints")

    name = models.CharField(max_length=200)
    goals = models.TextField(blank=True)
    status = models.CharField(max_length=50, default="planned")

    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.project.name} - {self.name}"


class Ticket(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="tickets")

    parent_ticket = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="subtickets",
    )

    type = models.CharField(max_length=50)     # ex: bug / feature / task
    description = models.TextField()
    status = models.CharField(max_length=50, default="todo")

    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="requested_tickets",
    )
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_tickets",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    # M2M vers Sprint via table de jointure
    sprints = models.ManyToManyField("Sprint", through="SprintTicket", related_name="tickets", blank=True)

    def __str__(self):
        return f"Ticket #{self.pk} ({self.type})"


class SprintTicket(models.Model):
    sprint = models.ForeignKey(Sprint, on_delete=models.CASCADE, related_name="sprint_links")
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="ticket_links")

    added_at = models.DateTimeField(default=timezone.now, null=True, blank=True)
    position = models.IntegerField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["sprint", "ticket"], name="uniq_sprint_ticket")
        ]
        ordering = ["position", "added_at"]

    def __str__(self):
        return f"{self.sprint} <-> {self.ticket}"