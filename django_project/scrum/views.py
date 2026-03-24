import os
import uuid
from io import BytesIO

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import transaction
from django.db.models import Max
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

from .forms import (
    ProjectForm,
    MembershipForm,
    TicketForm,
    TicketEditForm,
    SprintForm,
    CommentForm,
)
from .models import (
    Project,
    Membership,
    Ticket,
    Sprint,
    SprintTicket,
    Comment,
    Column,
)
from .utils import log_activity


def project_queryset_for(user):
    return (
        Project.objects.filter(created_by=user)
        | Project.objects.filter(members=user)
    ).distinct()


def user_can_access_project(user, project):
    return (
        project.created_by_id == user.id
        or project.members.filter(id=user.id).exists()
    )


def get_membership_role(user, project):
    m = project.memberships.filter(user=user).first()
    return m.role.lower() if m else None

def is_project_admin(user, project):
    if project.created_by_id == user.id:
        return True
    return get_membership_role(user, project) == "admin"

def is_contributor_or_admin(user, project):
    if project.created_by_id == user.id:
        return True
    return get_membership_role(user, project) in ("admin", "contributor")


def normalize_backlog_order(project):
    tickets = list(
        Ticket.objects.filter(project=project)
        .order_by("backlog_order", "created_at", "pk")
    )

    tickets_to_update = []
    for index, ticket in enumerate(tickets, start=1):
        if ticket.backlog_order != index:
            ticket.backlog_order = index
            tickets_to_update.append(ticket)

    if tickets_to_update:
        Ticket.objects.bulk_update(tickets_to_update, ["backlog_order"])

    return tickets


KANBAN_STATUS_TO_COLUMN = {
    "todo": "To Do",
    "in_progress": "In Progress",
    "in_review": "In Review",
    "done": "Done",
    "blocked": "Blocked",
    "open": "To Do",
}

COLUMN_TO_KANBAN_STATUS = {
    "to do": "todo",
    "in progress": "in_progress",
    "in review": "in_review",
    "done": "done",
    "blocked": "blocked",
}


def get_status_for_column(column_name):
    return COLUMN_TO_KANBAN_STATUS.get((column_name or "").strip().lower(), "todo")


def get_default_column_for_status(board, status):
    desired_name = KANBAN_STATUS_TO_COLUMN.get(status, "To Do")
    column = board.columns.filter(name__iexact=desired_name).first()
    if column:
        return column
    return board.columns.order_by("order").first()


def ensure_ticket_column(ticket, board=None):
    board = board or getattr(ticket.project, "board", None)
    if not board:
        return None

    expected_column = get_default_column_for_status(board, ticket.status)
    if expected_column and ticket.column_id != expected_column.id:
        ticket.column = expected_column
        ticket.save(update_fields=["column", "updated_at"])
    return expected_column


@login_required
def project_board(request, pk):
    project = get_object_or_404(Project, pk=pk)
    request.session["current_project_id"] = project.id
    return redirect('project-active-sprint', pk=pk)

def project_report(request, pk):
    project = get_object_or_404(Project, pk=pk)
    membership = project.memberships.filter(user=request.user).first()

    context = {
        "project": project,
        "membership": membership,
    }
    return render(request,"scrum/project_report.html",context)


@login_required
def project_members_json(request, pk):
    """Return JSON list of project members for assignee dropdown"""
    project = get_object_or_404(Project, pk=pk)

    # Check if user has access to this project
    if not user_can_access_project(request.user, project):
        return JsonResponse({"error": "Access denied"}, status=403)

    members = project.members.all().select_related('profile')
    members_data = []

    for member in members:
        members_data.append({
            'id': member.id,
            'name': member.get_full_name() or member.username,
            'email': member.email,
            'avatar': member.profile.image.url if hasattr(member, 'profile') and member.profile.image else None,
            'initials': f"{member.first_name[:1] if member.first_name else ''}{member.last_name[:1] if member.last_name else ''}" or member.username[
                :2].upper()
        })

    return JsonResponse({"members": members_data})


@login_required
def active_sprint(request, pk):
    project = get_object_or_404(Project, pk=pk)
    request.session["current_project_id"] = project.id

    if not user_can_access_project(request.user, project):
        messages.error(request, "You don't have access to this project.")
        return redirect("project-list")

    board = getattr(project, "board", None)
    if not board:
        messages.warning(request, "No board found for this project.")
        return redirect("project-detail", pk=project.pk)

    columns = list(board.columns.all().order_by("order"))
    membership = project.memberships.filter(user=request.user).first()
    active_sprint = project.sprints.filter(status="active").first()

    sprint_tickets = Ticket.objects.none()

    if active_sprint:
        sprint_tickets = (
            active_sprint.tickets
            .select_related("assignee", "assignee__profile", "column", "parent")
            .order_by("board_order", "created_at", "pk")
            .distinct()
        )

        for ticket in sprint_tickets:
            ensure_ticket_column(ticket, board)

        active_sprint.total_issues = sprint_tickets.count()
        active_sprint.todo_count = sprint_tickets.filter(status="todo").count()
        active_sprint.inprogress_count = sprint_tickets.filter(status="in_progress").count()
        active_sprint.inreview_count = sprint_tickets.filter(status="in_review").count()
        active_sprint.done_count = sprint_tickets.filter(status="done").count()
        active_sprint.blocked_count = sprint_tickets.filter(status="blocked").count()
        active_sprint.completion_percentage = (
            int((active_sprint.done_count / active_sprint.total_issues) * 100)
            if active_sprint.total_issues else 0
        )

        if active_sprint.end_date:
            from datetime import date
            today = date.today()
            active_sprint.days_remaining = max((active_sprint.end_date - today).days, 0)
        else:
            active_sprint.days_remaining = None

    for column in columns:
        ticket_status = get_status_for_column(column.name)
        column.tickets = sprint_tickets.filter(status=ticket_status).order_by("board_order", "created_at", "pk")

    context = {
        "project": project,
        "board": board,
        "columns": columns,
        "membership": membership,
        "active_sprint": active_sprint,
        "planned_sprints": project.sprints.filter(status="planned").order_by("start_date"),
        "can_manage_sprint": bool(membership and membership.team_role == "scrum_master") or is_project_admin(request.user, project),
        "can_edit_board": is_contributor_or_admin(request.user, project),
    }
    return render(request, "scrum/sprint/active_sprint.html", context)

@login_required
def project_roadmap(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if not user_can_access_project(request.user, project):
        messages.error(request, "You don't have access to this project.")
        return redirect("project-list")

    membership = project.memberships.filter(user=request.user).first()

    # Epics avec stats
    raw_epics = Ticket.objects.filter(
        project=project, type='epic'
    ).order_by("created_at")

    epics = []
    for epic in raw_epics:
        subs = epic.subtickets.all()
        epic.stat_total = subs.count()
        epic.stat_done = subs.filter(status='done').count()
        epic.stat_pts = sum(t.story_points for t in subs if t.story_points)
        epics.append(epic)

    # Sprints avec stats
    sprints = project.sprints.all().order_by('start_date')
    for sprint in sprints:
        tickets = sprint.tickets.all()
        sprint.total_issues = tickets.count()
        sprint.done_issues = tickets.filter(status='done').count()

    # Calculer la progression globale du projet
    all_tickets = project.tickets.exclude(type='epic')
    total_tickets = all_tickets.count()
    done_tickets = all_tickets.filter(status='done').count()
    project_completion = int((done_tickets / total_tickets * 100)) if total_tickets > 0 else 0

    # Calculer les jours restants jusqu'à la deadline
    from datetime import date
    today = date.today()
    days_remaining = None
    if project.end_date:
        days_remaining = max((project.end_date - today).days, 0)

    context = {
        "project":    project,
        "membership": membership,
        "epics":      epics,
        "sprints":    sprints,
        "can_create": is_contributor_or_admin(request.user, project),
        "project_completion": project_completion,
        "days_remaining": days_remaining,
        "total_tickets": total_tickets,
        "done_tickets": done_tickets,
    }
    return render(request, "scrum/project_roadmap.html", context)


@login_required
def project_releases(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if not user_can_access_project(request.user, project):
        messages.error(request, "You don't have access to this project.")
        return redirect("project-list")

    sprints = project.sprints.all().order_by('-created_at')
    membership = project.memberships.filter(user=request.user).first()

    for sprint in sprints:
        tickets = sprint.tickets.all()
        sprint.total_issues     = tickets.count()
        sprint.done_count       = tickets.filter(status='done').count()
        sprint.completion_percentage = (
            int((sprint.done_count / sprint.total_issues) * 100)
            if sprint.total_issues else 0
        )

    context = {
        "project": project,
        "membership": membership,
        "sprints": sprints,
    }
    return render(request, "scrum/project_releases.html", context)

class ProjectListView(LoginRequiredMixin, ListView):
    model = Project
    template_name = "scrum/project_list.html"
    context_object_name = "projects"
    ordering = ["-id"]

    def get_queryset(self):
        return project_queryset_for(self.request.user)

class ProjectIssuesView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Ticket
    template_name = "scrum/project_issues.html"
    context_object_name = "tickets"

    def test_func(self):
        return user_can_access_project(
            self.request.user,
            get_object_or_404(Project, pk=self.kwargs["pk"])
        )

    def handle_no_permission(self):
        messages.error(self.request, "You don't have access to this project.")
        return redirect("project-list")

    def get_queryset(self):
        self.project = get_object_or_404(Project, pk=self.kwargs["pk"])
        self.request.session["current_project_id"] = self.project.id

        qs = (
            Ticket.objects
            .filter(project=self.project)
            .select_related("assignee", "assignee__profile", "parent")
            .prefetch_related("sprints")
            .order_by("-updated_at")  # most recently updated first
        )

        self.search = self.request.GET.get("q", "").strip()
        self.f_type = self.request.GET.get("type", "")
        self.f_status = self.request.GET.get("status", "")
        self.f_priority = self.request.GET.get("priority", "")
        self.f_assignee = self.request.GET.get("assignee", "")

        if self.search:
            qs = qs.filter(title__icontains=self.search)
        if self.f_type:
            qs = qs.filter(type=self.f_type)
        if self.f_status:
            qs = qs.filter(status=self.f_status)
        if self.f_priority:
            qs = qs.filter(priority=self.f_priority)
        if self.f_assignee:
            qs = qs.filter(assignee__id=self.f_assignee)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tickets = self.get_queryset()

        # Status groups — ordered: open/todo first, done/closed last
        STATUS_ORDER = [
            ("todo", "To Do"),
            ("in_progress", "In Progress"),
            ("in_review", "In Review"),
            ("open", "Open"),
            ("blocked", "Blocked"),
            ("done", "Done"),
        ]

        status_groups = []
        for key, label in STATUS_ORDER:
            group_tickets = [t for t in tickets if t.status == key]
            status_groups.append({
                "key": key,
                "label": label,
                "tickets": group_tickets,
            })

        context["project"] = self.project
        context["membership"] = self.project.memberships.filter(user=self.request.user).first()
        context["can_create"] = is_contributor_or_admin(self.request.user, self.project)
        context["can_delete"] = is_project_admin(self.request.user, self.project)
        context["members"] = self.project.members.select_related("profile")
        context["search"] = self.search
        context["f_type"] = self.f_type
        context["f_status"] = self.f_status
        context["f_priority"] = self.f_priority
        context["f_assignee"] = self.f_assignee
        context["total"] = tickets.count()
        context["status_groups"] = status_groups

        # Counts for summary bar
        context["count_todo"] = tickets.filter(status="todo").count()
        context["count_inprogress"] = tickets.filter(status="in_progress").count()
        context["count_inreview"] = tickets.filter(status="in_review").count()
        context["count_done"] = tickets.filter(status="done").count()
        context["count_blocked"] = tickets.filter(status="blocked").count()

        return context


class ProjectDetailView(LoginRequiredMixin, DetailView):
    model = Project
    template_name = "scrum/project_detail.html"

    def get_queryset(self):
        return project_queryset_for(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.object
        self.request.session["current_project_id"] = project.id
        context["sprints"] = project.sprints.all()
        context["membership"] = project.memberships.filter(user=self.request.user).first()
        return context


class ProjectSettingsView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = "scrum/project_settings.html"

    def test_func(self):
        project = self.get_object()
        return user_can_access_project(self.request.user, project)  # tous les membres peuvent voir

    def handle_no_permission(self):
        messages.error(self.request, "You don't have access to this project.")
        return redirect("project-board", pk=self.get_object().pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.object
        self.request.session["current_project_id"] = project.id
        context["memberships"] = project.memberships.select_related("user")
        context["membership_form"] = MembershipForm()
        context["membership"] = project.memberships.filter(user=self.request.user).first()
        context["is_admin"] = is_project_admin(self.request.user, project)  # <-- nouveau
        return context

    def post(self, request, *args, **kwargs):
        project = self.get_object()
        if not is_project_admin(request.user, project):
            messages.error(request, "Only admins can modify project settings.")
            return redirect("project-settings", pk=project.pk)
        return super().post(request, *args, **kwargs)

    def get_success_url(self):
        return reverse("project-settings", kwargs={"pk": self.object.pk})


class ProjectCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = "scrum/project_form.html"

    def test_func(self):
        return self.request.user.profile.global_role.lower() == "admin"

    def handle_no_permission(self):
        messages.error(self.request, "Only admins can create projects.")
        return redirect("home")

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        self.request.session["current_project_id"] = self.object.pk
        return response

    def get_success_url(self):
        return reverse_lazy("project-board", kwargs={"pk": self.object.pk})


class ProjectUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = "scrum/project_form.html"

    def test_func(self):
        return self.get_object().created_by == self.request.user

    def handle_no_permission(self):
        messages.error(self.request, "Only the project creator can update this project.")
        return redirect("home")

    def get_success_url(self):
        return reverse("project-detail", kwargs={"pk": self.object.pk})


class ProjectUpdateModalView(LoginRequiredMixin, View):
    def post(self, request, pk):
        project = get_object_or_404(Project, pk=pk)

        if project.created_by != request.user:
            return JsonResponse(
                {"error": "Only the project creator can edit this project."},
                status=403
            )

        project.name = request.POST.get("name", project.name)
        project.code = request.POST.get("code", project.code)
        project.description = request.POST.get("description", project.description)
        project.project_type = request.POST.get("project_type", project.project_type)
        project.board_type = request.POST.get("board_type", project.board_type)
        project.save()

        return redirect("project-list")


class ProjectDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Project
    template_name = "scrum/project_confirm_delete.html"
    success_url = reverse_lazy("project-list")

    def get_queryset(self):
        return Project.objects.filter(created_by=self.request.user)

    def test_func(self):
        return self.get_object().created_by == self.request.user

    def handle_no_permission(self):
        messages.error(self.request, "Only the project creator can delete this project.")
        return redirect("home")



class MembershipAddView(LoginRequiredMixin, View):
    def post(self, request, pk):
        project = get_object_or_404(Project, pk=pk)

        if project.created_by != request.user:
            messages.error(request, "Only the project creator can add members.")
            return redirect("project-board", pk=pk)

        form = MembershipForm(request.POST)
        if form.is_valid():
            membership = form.save(commit=False)
            membership.project = project
            membership.save()
            messages.success(request, "Member added successfully.")
        else:
            messages.error(request, "Unable to add this member.")

        return redirect("project-settings", pk=pk)

class MembershipUpdateRoleView(LoginRequiredMixin, View):
    def post(self, request, pk, membership_pk):
        project = get_object_or_404(Project, pk=pk)
        if project.created_by != request.user:
            messages.error(request, "Only the project creator can change member roles.")
            return redirect("project-board", pk=pk)
        membership = get_object_or_404(Membership, pk=membership_pk, project=project)
        new_role = request.POST.get("role")
        new_team_role = request.POST.get("team_role")
        if new_role in ["admin", "contributor", "read-only"]:
            membership.role = new_role
        if new_team_role in ["developer", "scrum_master", "product_owner", "tester", "designer", "other"]:
            membership.team_role = new_team_role
        membership.save()
        messages.success(request, "Role updated successfully.")
        return redirect("project-settings", pk=pk)


class MembershipDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk, membership_pk):
        project = get_object_or_404(Project, pk=pk)

        if project.created_by != request.user:
            messages.error(request, "Only the project creator can remove members.")
            return redirect("project-board", pk=pk)

        membership = get_object_or_404(Membership, pk=membership_pk, project=project)
        membership.delete()
        messages.success(request, "Member removed successfully.")
        return redirect("project-settings", pk=pk)


class MembershipUpdateRoleView(LoginRequiredMixin, View):
    def post(self, request, pk, membership_pk):
        project = get_object_or_404(Project, pk=pk)

        if project.created_by != request.user:
            messages.error(request, "Only the project creator can change member roles.")
            return redirect("project-board", pk=pk)

        membership = get_object_or_404(Membership, pk=membership_pk, project=project)
        new_role = request.POST.get("role")

        if new_role in ["admin", "contributor", "read-only"]:
            membership.role = new_role
            membership.save()
            messages.success(request, "Role updated successfully.")
        else:
            messages.error(request, "Invalid role.")

        return redirect("project-settings", pk=pk)



#TICKET LOGIC 
class TicketCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Ticket
    form_class = TicketForm

    def test_func(self):
        return is_contributor_or_admin(self.request.user, get_object_or_404(Project, pk=self.kwargs["pk"]))

    def handle_no_permission(self):
        messages.error(self.request, "You don't have permission to create issues.")
        return redirect("product-backlog", pk=self.kwargs["pk"])

    def get_initial(self):
        initial = super().get_initial()
        title = self.request.GET.get('title', '').strip()
        ticket_type = self.request.GET.get('type', '').strip().lower()
        status = self.request.GET.get('status', '').strip().lower()

        if title:
            initial['title'] = title

        # Mapper le statut depuis le nom de la colonne
        status_map = {
            'to do': 'todo',
            'in progress': 'in_progress',
            'in review': 'in_review',
            'done': 'done',
            'blocked': 'blocked'
        }

        if status in status_map:
            initial['status'] = status_map[status]

        TYPE_MAP = {
            'story': 'user story',
            'user_story': 'user story',
            'bug': 'bug',
            'task': 'task',
            'epic': 'epic',
        }
        mapped = TYPE_MAP.get(ticket_type)
        if mapped:
            initial['type'] = mapped

        return initial

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        project = get_object_or_404(Project, pk=self.kwargs["pk"])
        form.fields["assignee"].queryset = project.members.all()
        form.fields["parent"].queryset = project.tickets.all()
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = get_object_or_404(Project, pk=self.kwargs["pk"])
        return context

    def form_valid(self, form):
        project = get_object_or_404(Project, pk=self.kwargs["pk"])
        form.instance.project = project
        form.instance.requester = self.request.user

        if not form.instance.status:
            form.instance.status = "todo"

        self.object = form.save()

        sprint_id = self.request.POST.get("_sprint_id", "").strip()
        if sprint_id:
            sprint = Sprint.objects.filter(pk=sprint_id, project=project).first()
            if sprint:
                SprintTicket.objects.get_or_create(sprint=sprint, ticket=self.object)
                if sprint.status == "active":
                    ensure_ticket_column(self.object, project.board)

        log_activity(
            self.request.user, project, "create_ticket",
            ticket=self.object, message=f"created ticket {self.object.title}"
        )
        messages.success(self.request, f'Issue "{form.instance.title}" created.')
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse("product-backlog", kwargs={"pk": self.kwargs["pk"]})

class TicketListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Ticket
    template_name = "scrum/ticket/product_backlog.html"
    context_object_name = "tickets"

    def test_func(self):
        return user_can_access_project(self.request.user, get_object_or_404(Project, pk=self.kwargs["pk"]))

    def handle_no_permission(self):
        messages.error(self.request, "You don't have access to this project.")
        return redirect("project-list")

    def get_queryset(self):
        self.project = get_object_or_404(Project, pk=self.kwargs["pk"])
        self.request.session["current_project_id"] = self.project.id
        normalize_backlog_order(self.project)

        qs = (
            Ticket.objects
            .filter(project=self.project)
            .exclude(type='epic')
            # EXCLURE LES TICKETS QUI SONT DANS UN SPRINT ACTIF OU PLANNED
            .exclude(sprints__status__in=['active', 'planned'])
            # EXCLURE LES TICKETS DONE DU BACKLOG
            .exclude(status='done')
            .select_related("assignee", "assignee__profile", "parent")
            .prefetch_related("sprints")
            .order_by("backlog_order", "created_at")
        )

        # Filtres GET
        type_filter = self.request.GET.get("type", "")
        priority_filter = self.request.GET.get("priority", "")
        epic_filter = self.request.GET.get("epic", "")
        status_filter = self.request.GET.get("status", "")

        if epic_filter:
            qs = qs.filter(parent__id=epic_filter)
        if type_filter:
            qs = qs.filter(type=type_filter)
        if priority_filter:
            qs = qs.filter(priority=priority_filter)
        if status_filter:
            qs = qs.filter(status=status_filter)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.project
        context["membership"] = self.project.memberships.filter(user=self.request.user).first()
        context["can_create"] = is_contributor_or_admin(self.request.user, self.project)
        context["can_delete"] = is_project_admin(self.request.user, self.project)
        context["can_reorder"] = is_contributor_or_admin(self.request.user, self.project)
        context["filter_type"] = self.request.GET.get("type", "")
        context["filter_priority"] = self.request.GET.get("priority", "")
        context["filter_status"] = self.request.GET.get("status", "")
        context["filter_epic"] = self.request.GET.get("epic", "")
        context["active_filters"] = any([
            context["filter_type"],
            context["filter_priority"],
            context["filter_status"],
        ])

        # EPICS avec stats
        raw_epics = Ticket.objects.filter(
            project=self.project, type='epic'
        ).order_by("backlog_order", "created_at")

        epics = []
        for epic in raw_epics:
            subs = epic.subtickets.all()
            total = subs.count()
            done = subs.filter(status='done').count()
            pts = sum(t.story_points for t in subs if t.story_points)
            unest = subs.filter(story_points__isnull=True).count()
            epic.stat_total = total
            epic.stat_done = done
            epic.stat_pts = pts
            epic.stat_unest = unest
            epics.append(epic)

        context["epics"] = epics

        # SPRINTS
        from django.contrib.auth import get_user_model
        User = get_user_model()
        sprints = self.project.sprints.all().order_by('-created_at')
        for sprint in sprints:
            tickets = sprint.tickets.all()
            sprint.total_issues = tickets.count()
            sprint.todo_count = tickets.filter(status='todo').count()
            sprint.inprogress_count = tickets.filter(status='in_progress').count()
            sprint.done_count = tickets.filter(status='done').count()
            assignee_ids = tickets.exclude(assignee=None).values_list('assignee_id', flat=True).distinct()
            sprint.assignees = list(User.objects.filter(id__in=assignee_ids).select_related('profile'))
        context["sprints"] = list(sprints)
        context["active_sprint"] = self.project.sprints.filter(status="active").first()

        return context


class TicketDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Ticket
    context_object_name = "ticket"
    pk_url_kwarg = "ticket_pk"

    def test_func(self):
        return user_can_access_project(self.request.user, self.get_object().project)

    def handle_no_permission(self):
        messages.error(self.request, "You don't have access to this project.")
        return redirect("project-list")

    def get_template_names(self):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest' or self.request.GET.get('drawer'):
            return ['scrum/ticket/ticket_drawer.html']
        return ['scrum/ticket/ticket_form_partial.html']

    def get(self, request, *args, **kwargs):
        if not request.GET.get('drawer') and not request.headers.get('x-requested-with'):
            ticket = self.get_object()
            return redirect(reverse("product-backlog", kwargs={"pk": ticket.project.pk}))
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ticket  = self.object
        project = ticket.project
        self.request.session["current_project_id"] = project.id
        edit_form = TicketEditForm(instance=ticket)
        edit_form.fields["assignee"].queryset = project.members.all()
        edit_form.fields["parent"].queryset   = project.tickets.exclude(pk=ticket.pk)
        
        context.update({
            "project":   project,
            "children":  Ticket.objects.filter(parent=ticket),
            "comments":  ticket.comments.select_related("author").order_by("created_at"),
            "comment_form": CommentForm(), # <-- J'AI AJOUTÉ CECI POUR LE FORMULAIRE DE CRÉATION DE COMMENTAIRE
            "can_edit":  is_contributor_or_admin(self.request.user, project),
            "can_delete": is_project_admin(self.request.user, project),
            "edit_form": edit_form,
            "ticket_form": edit_form,
            "membership": project.memberships.filter(user=self.request.user).first(),
        })
        return context

class TicketUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Ticket
    form_class = TicketEditForm
    pk_url_kwarg = "ticket_pk"

    def test_func(self):
        return is_contributor_or_admin(self.request.user, self.get_object().project)

    def handle_no_permission(self):
        messages.error(self.request, "You don't have permission to edit this issue.")
        return redirect("product-backlog", pk=self.kwargs["pk"])

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        project = self.get_object().project
        form.fields["assignee"].queryset = project.members.all()
        form.fields["parent"].queryset   = project.tickets.exclude(pk=self.object.pk)
        return form

    def get_template_names(self):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return ['scrum/ticket/ticket_form_partial.html']
        return ['scrum/ticket/ticket_form.html']

    def form_valid(self, form):
        old_status = self.get_object().status
        self.object = form.save()  # <-- sauvegarde directe
        ticket = self.object

        if old_status != ticket.status:
            log_activity(self.request.user, ticket.project, "status_change",
                         ticket=ticket, message=f"moved {ticket.title} to {ticket.status}")
        else:
            log_activity(self.request.user, ticket.project, "update_ticket",
                         ticket=ticket, message=f"updated {ticket.title}")

        if self.request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"success": True})  # <-- manquait

        messages.success(self.request, f'Issue "{ticket.title}" updated.')
        return redirect(self.get_success_url())

    def form_invalid(self, form):
        if self.request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"success": False, "errors": form.errors}, status=400)
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse("product-backlog", kwargs={"pk": self.kwargs["pk"]})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.object.project
        return context


class TicketDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Ticket
    pk_url_kwarg = "ticket_pk"

    def test_func(self):
        return is_contributor_or_admin(self.request.user, self.get_object().project)

    def handle_no_permission(self):
        messages.error(self.request, "Only contributors and admins can delete issues.")
        return redirect("product-backlog", pk=self.kwargs["pk"])

    def delete(self, request, *args, **kwargs):
        ticket = self.get_object()
        Ticket.objects.filter(parent=ticket).update(parent=None)
        messages.success(request, f'Issue "{ticket.title}" deleted.')
        return super().delete(request, *args, **kwargs)

    def get_success_url(self):
        return reverse("product-backlog", kwargs={"pk": self.kwargs["pk"]})


class TicketReorderView(LoginRequiredMixin, View):
    def post(self, request, pk, ticket_pk, direction):
        project = get_object_or_404(Project, pk=pk)

        if not is_contributor_or_admin(request.user, project):
            messages.error(request, "Only project admins and contributors can reorder the backlog.")
            return redirect("product-backlog", pk=pk)

        if direction not in ("up", "down"):
            messages.error(request, "Invalid reorder action.")
            return redirect("product-backlog", pk=pk)

        with transaction.atomic():
            tickets = normalize_backlog_order(project)
            current_ticket = get_object_or_404(Ticket, pk=ticket_pk, project=project)

            current_index = next((index for index, ticket in enumerate(tickets) if ticket.pk == current_ticket.pk), None)
            if current_index is None:
                messages.error(request, "Issue not found in backlog.")
                return redirect("product-backlog", pk=pk)

            swap_index = current_index - 1 if direction == "up" else current_index + 1

            if swap_index < 0 or swap_index >= len(tickets):
                return redirect("product-backlog", pk=pk)

            swap_ticket = tickets[swap_index]
            current_ticket.backlog_order, swap_ticket.backlog_order = swap_ticket.backlog_order, current_ticket.backlog_order
            Ticket.objects.bulk_update([current_ticket, swap_ticket], ["backlog_order"])

        return redirect("product-backlog", pk=pk)

@login_required
def quick_create_ticket(request, pk):
    project = get_object_or_404(Project, pk=pk)

    if not is_contributor_or_admin(request.user, project):
        messages.error(request, "You don't have permission to create issues.")
        return redirect("product-backlog", pk=pk)

    title = request.GET.get('title', '').strip()
    ticket_type = request.GET.get('type', 'user story').strip().lower()

    TYPE_MAP = {
        'story':      'user story',
        'user_story': 'user story',
        'user story': 'user story',
        'bug':        'bug',
        'task':       'task',
        'epic':       'epic',
    }
    ticket_type = TYPE_MAP.get(ticket_type, 'user story')

    if not title:
        messages.error(request, "Title is required.")
        return redirect("product-backlog", pk=pk)

    ticket = Ticket.objects.create(
        project=project,
        title=title,
        type=ticket_type,
        status='todo',
        requester=request.user,
    )
    messages.success(request, f'Issue "{ticket.title}" created.')
    return redirect("product-backlog", pk=pk)


@login_required
def ticket_inline_update(request, pk, ticket_pk):
    project = get_object_or_404(Project, pk=pk)
    ticket = get_object_or_404(Ticket, pk=ticket_pk, project=project)

    if not is_contributor_or_admin(request.user, project):
        return JsonResponse({"success": False, "error": "Permission denied"}, status=403)

    if request.method != "POST":
        return JsonResponse({"success": False, "error": "POST only"}, status=405)

    field = request.POST.get("field")
    value = request.POST.get("value", "")

    ALLOWED_FIELDS = [
        "title", "description", "priority", "status", "story_points",
        "assignee_id", "due_date", "parent_id", "labels", "type"
    ]

    if field not in ALLOWED_FIELDS:
        return JsonResponse({"success": False, "error": f"Field '{field}' not allowed"}, status=400)

    try:
        if field == "story_points":
            ticket.story_points = int(value) if value else None
            ticket.save(update_fields=["story_points"])
        elif field == "assignee_id":
            from django.contrib.auth import get_user_model
            User = get_user_model()
            ticket.assignee = User.objects.get(pk=value) if value else None
            ticket.save(update_fields=["assignee"])
        elif field == "parent_id":
            ticket.parent = Ticket.objects.get(pk=value, project=project) if value else None
            ticket.save(update_fields=["parent"])
        elif field == "due_date":
            ticket.due_date = value if value else None
            ticket.save(update_fields=["due_date"])
        else:
            setattr(ticket, field, value)
            ticket.save(update_fields=[field])
        log_activity(request.user, project, "update_ticket",
                     ticket=ticket, message=f"updated {field} on {ticket.title}")
        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)


@login_required
def move_ticket_kanban(request, pk, ticket_pk):
    project = get_object_or_404(Project, pk=pk)
    ticket = get_object_or_404(Ticket, pk=ticket_pk, project=project)

    if request.method != "POST":
        return JsonResponse({"success": False, "error": "POST only"}, status=405)

    if not is_contributor_or_admin(request.user, project):
        return JsonResponse({"success": False, "error": "Permission denied"}, status=403)

    active_sprint = project.sprints.filter(status="active").first()
    if not active_sprint or not SprintTicket.objects.filter(sprint=active_sprint, ticket=ticket).exists():
        return JsonResponse({"success": False, "error": "Ticket is not in the active sprint"}, status=400)

    column_id = request.POST.get("column_id")
    target_column = get_object_or_404(Column, pk=column_id, board=project.board)
    new_status = get_status_for_column(target_column.name)

    max_order = (
        Ticket.objects.filter(project=project, column=target_column, sprints=active_sprint)
        .exclude(pk=ticket.pk)
        .aggregate(max_value=Max("board_order"))["max_value"] or 0
    )

    ticket.column = target_column
    ticket.status = new_status
    ticket.board_order = max_order + 1
    ticket.save(update_fields=["column", "status", "board_order", "updated_at"])

    log_activity(
        request.user,
        project,
        "status_change",
        ticket=ticket,
        sprint=active_sprint,
        message=f"moved {ticket.title} to {target_column.name}",
    )

    return JsonResponse({
        "success": True,
        "ticket_id": ticket.pk,
        "status": ticket.status,
        "column_id": target_column.id,
        "column_name": target_column.name,
    })

#Sprint ======================
class SprintCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Sprint
    form_class = SprintForm
    template_name = "scrum/sprint/_sprint_modal.html"

    def test_func(self):
        project = get_object_or_404(Project, pk=self.kwargs["pk"])
        return is_contributor_or_admin(self.request.user, project)

    def handle_no_permission(self):
        messages.error(self.request, "Only contributors and admins can create sprints.")
        return redirect("project-active-sprint", pk=self.kwargs["pk"])

    def form_valid(self, form):
        project = get_object_or_404(Project, pk=self.kwargs["pk"])
        form.instance.project = project

        self.object = form.save()

        log_activity(self.request.user,project,"create_sprint",
            sprint=self.object,message=f"created sprint {self.object.name}"
        )

        messages.success(self.request, f'Sprint "{form.instance.name}" created successfully!')
        return redirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = get_object_or_404(Project, pk=self.kwargs["pk"])
        return context

    def get_success_url(self):
        return reverse("product-backlog", kwargs={"pk": self.kwargs["pk"]})

class SprintUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Sprint
    form_class = SprintForm
    pk_url_kwarg = "sprint_pk"

    def test_func(self):
        sprint = get_object_or_404(Sprint, pk=self.kwargs["sprint_pk"], project__pk=self.kwargs["pk"])
        return is_contributor_or_admin(self.request.user, sprint.project)

    def handle_no_permission(self):
        messages.error(self.request, "Permission denied.")
        return redirect("product-backlog", pk=self.kwargs["pk"])

    def get_object(self, queryset=None):
        return get_object_or_404(Sprint, pk=self.kwargs["sprint_pk"], project__pk=self.kwargs["pk"])

    def form_valid(self, form):
        sprint = form.save()
        log_activity(self.request.user,sprint.project,"create_sprint",sprint=sprint, message=f"updated sprint {sprint.name}")
        messages.success(self.request, f'Sprint "{sprint.name}" updated.')
        return redirect("product-backlog", pk=self.kwargs["pk"])

    def form_invalid(self, form):
        # Le modal passe par POST, on redirige avec un message d'erreur
        messages.error(self.request, "Error updating sprint. Please check the fields.")
        return redirect("product-backlog", pk=self.kwargs["pk"])

    def get_success_url(self):
        return reverse("product-backlog", kwargs={"pk": self.kwargs["pk"]})

class SprintDeleteView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        sprint = get_object_or_404(Sprint, pk=self.kwargs["sprint_pk"], project__pk=self.kwargs["pk"])
        return is_project_admin(self.request.user, sprint.project)

    def handle_no_permission(self):
        messages.error(self.request, "Only admins can delete sprints.")
        return redirect("product-backlog", pk=self.kwargs["pk"])

    def post(self, request, pk, sprint_pk):
        sprint = get_object_or_404(Sprint, pk=sprint_pk, project__pk=pk)
        name = sprint.name

        # Détache ce sprint de tous les tickets liés
        for ticket in sprint.tickets.all():
            ticket.sprints.remove(sprint)  # <-- correct pour ManyToManyField

        # Supprime le sprint
        sprint.delete()
        messages.success(request, f'Sprint "{name}" deleted.')
        return redirect("product-backlog", pk=pk)

@login_required
def sprint_start(request, pk, sprint_pk):
    project = get_object_or_404(Project, pk=pk)
    if not is_contributor_or_admin(request.user, project):
        messages.error(request, "Permission denied.")
        return redirect("product-backlog", pk=pk)

    sprint = get_object_or_404(Sprint, pk=sprint_pk, project=project)

    if request.method == "POST":
        project.sprints.filter(status='active').update(status='completed')
        sprint.status = 'active'
        sprint.save()

        for ticket in sprint.tickets.all():
            ensure_ticket_column(ticket, project.board)

        log_activity(
            request.user,
            project,
            "create_sprint",
            sprint=sprint,
            message=f"started sprint {sprint.name}"
        )
        messages.success(request, f'Sprint "{sprint.name}" started.')

    return redirect("product-backlog", pk=pk)


@login_required
def sprint_complete(request, pk, sprint_pk):
    project = get_object_or_404(Project, pk=pk)
    if not is_contributor_or_admin(request.user, project):
        messages.error(request, "Permission denied.")
        return redirect("product-backlog", pk=pk)

    sprint = get_object_or_404(Sprint, pk=sprint_pk, project=project)

    if request.method == "POST":
        sprint.status = 'completed'
        sprint.save()
        log_activity(
            request.user,
            project,
            "create_sprint",
            sprint=sprint,
            message=f"completed sprint {sprint.name}"
        )
        messages.success(request, f'Sprint "{sprint.name}" completed.')

    return redirect("product-backlog", pk=pk)


@login_required
def ticket_remove_from_sprint(request, pk):
    project = get_object_or_404(Project, pk=pk)

    if request.method != "POST":
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"success": False, "error": "POST only"}, status=405)
        return redirect("product-backlog", pk=pk)

    if not is_contributor_or_admin(request.user, project):
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"success": False, "error": "Permission denied"}, status=403)
        messages.error(request, "Permission denied.")
        return redirect("product-backlog", pk=pk)

    ticket_id = request.POST.get("ticket_id")
    sprint_id = request.POST.get("sprint_id")

    ticket = get_object_or_404(Ticket, pk=ticket_id, project=project)

    sprint = None
    if sprint_id:
        sprint = Sprint.objects.filter(pk=sprint_id, project=project).first()
    if sprint is None:
        sprint = project.sprints.filter(status="active").first()

    if sprint:
        SprintTicket.objects.filter(sprint=sprint, ticket=ticket).delete()
        log_activity(
            request.user,
            project,
            "update_description",
            ticket=ticket,
            sprint=sprint,
            message=f"moved {ticket.title} back to backlog",
        )

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({
            "success": True,
            "ticket_id": ticket.id,
            "sprint_id": sprint.id if sprint else None,
        })

    messages.success(request, f'"{ticket.title}" moved back to backlog.')
    return redirect("product-backlog", pk=pk)


##################comment ticket###########

@login_required
def add_comment(request, ticket_pk):
    """Permet d'ajouter un commentaire à un ticket spécifique."""
    ticket = get_object_or_404(Ticket, pk=ticket_pk)

    
    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.ticket = ticket
            comment.author = request.user
            comment.save()
            log_activity(request.user,ticket.project,
                "comment",ticket=ticket,message=f"commented on {ticket.title}"
            )
            messages.success(request, "Commentaire ajouté.")
            
    # Redirige vers la page d'où vient l'utilisateur (utile car tes tickets sont dans des "drawers")
    return redirect(request.META.get('HTTP_REFERER', reverse('product-backlog', kwargs={'pk': ticket.project.pk})))

@login_required
def edit_comment(request, comment_pk):
    """Permet à l'auteur de modifier son propre commentaire."""
    comment = get_object_or_404(Comment, pk=comment_pk)
    
    # Vérification de sécurité : seul l'auteur peut modifier
    if comment.author != request.user:
        messages.error(request, "Vous ne pouvez modifier que vos propres commentaires.")
        return redirect(request.META.get('HTTP_REFERER', reverse('product-backlog', kwargs={'pk': comment.ticket.project.pk})))

    if request.method == "POST":
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            messages.success(request, "Commentaire mis à jour.")
            return redirect(request.META.get('HTTP_REFERER', reverse('product-backlog', kwargs={'pk': comment.ticket.project.pk})))
    else:
        form = CommentForm(instance=comment)
    
    # Si on arrive ici, c'est un "GET", on retourne donc un petit template avec le formulaire de modification
    context = {'form': form, 'comment': comment, 'project': comment.ticket.project}
    return render(request, 'scrum/ticket/edit_comment.html', context)

@login_required
def delete_comment(request, comment_pk):
    """Permet à l'auteur de supprimer son propre commentaire."""
    comment = get_object_or_404(Comment, pk=comment_pk)
    
    # Vérification de sécurité : seul l'auteur peut supprimer
    if comment.author != request.user:
        messages.error(request, "Vous ne pouvez supprimer que vos propres commentaires.")
    else:
        comment.delete()
        messages.success(request, "Commentaire supprimé.")
        
    return redirect(request.META.get('HTTP_REFERER', reverse('product-backlog', kwargs={'pk': comment.ticket.project.pk})))

@login_required
def add_ticket_to_sprint(request, pk, ticket_pk):
    project = get_object_or_404(Project, pk=pk)
    ticket = get_object_or_404(Ticket, pk=ticket_pk, project=project)

    if request.method != "POST":
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"success": False, "error": "POST only"}, status=405)
        return redirect("product-backlog", pk=pk)

    if not is_contributor_or_admin(request.user, project):
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"success": False, "error": "Permission denied"}, status=403)
        messages.error(request, "You don't have permission to add issues to a sprint.")
        return redirect("product-backlog", pk=pk)

    sprint_pk = request.POST.get("sprint_id")
    sprint = get_object_or_404(Sprint, pk=sprint_pk, project=project)

    link, created = SprintTicket.objects.get_or_create(sprint=sprint, ticket=ticket)

    if sprint.status == "active":
        ensure_ticket_column(ticket, project.board)

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({
            "success": True,
            "created": created,
            "ticket_id": ticket.id,
            "sprint_id": sprint.id,
        })

    if created:
        messages.success(request, f'Issue "{ticket.title}" added to sprint "{sprint.name}".')
    else:
        messages.warning(request, f'Issue already in sprint "{sprint.name}".')

    return redirect("product-backlog", pk=pk)

    if request.method == "POST":
        sprint_pk = request.POST.get("sprint_id")
        sprint = get_object_or_404(Sprint, pk=sprint_pk, project=project)

        if SprintTicket.objects.filter(sprint=sprint, ticket=ticket).exists():
            messages.warning(request, f'Issue already in sprint "{sprint.name}".')
            return redirect("product-backlog", pk=pk)

        SprintTicket.objects.create(sprint=sprint, ticket=ticket)
        messages.success(request, f'Issue "{ticket.title}" added to sprint "{sprint.name}".')

    return redirect("product-backlog", pk=pk)


#═══════════════════════════════════════════════════════════════
@login_required
def upload_description_image(request, pk):
    """
    Upload + redimensionne une image pour Quill (description ticket).
    - Max 900px de large (préserve le ratio)
    - Max 5MB en entrée
    - Retourne {"url": "..."} pour Quill
    """
    project = get_object_or_404(Project, pk=pk)

    if not is_contributor_or_admin(request.user, project):
        return JsonResponse({"error": "Permission denied"}, status=403)

    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    image_file = request.FILES.get("image")
    if not image_file:
        return JsonResponse({"error": "No image provided"}, status=400)

    allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    if image_file.content_type not in allowed_types:
        return JsonResponse({"error": "Use JPG, PNG, GIF or WebP."}, status=400)

    if image_file.size > 5 * 1024 * 1024:
        return JsonResponse({"error": "Max 5MB."}, status=400)

    try:
        from PIL import Image as PilImage
        img = PilImage.open(image_file)

        # Convertir en RGB si nécessaire (PNG avec transparence → garder RGBA)
        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGBA" if img.format == "PNG" else "RGB")

        # Redimensionner si plus large que 900px
        MAX_WIDTH = 900
        if img.width > MAX_WIDTH:
            ratio = MAX_WIDTH / img.width
            new_h = int(img.height * ratio)
            img = img.resize((MAX_WIDTH, new_h), PilImage.LANCZOS)

        # Sauvegarder en mémoire
        output = BytesIO()
        fmt = "PNG" if img.mode == "RGBA" else "JPEG"
        ext = ".png" if fmt == "PNG" else ".jpg"
        save_kwargs = {"quality": 85, "optimize": True} if fmt == "JPEG" else {"optimize": True}
        img.save(output, format=fmt, **save_kwargs)
        output.seek(0)

        filename = f"{uuid.uuid4().hex}{ext}"
        save_path = os.path.join("description_images", filename)

        from django.core.files.storage import default_storage
        saved = default_storage.save(save_path, ContentFile(output.read()))
        url = default_storage.url(saved)

        return JsonResponse({"url": url})

    except Exception as e:
        return JsonResponse({"error": f"Image processing failed: {str(e)}"}, status=500)
