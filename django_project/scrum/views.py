from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import JsonResponse
from django.db import transaction
from django.db.models import Max
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

from .forms import ProjectForm, MembershipForm, TicketForm, TicketEditForm, SprintForm
from .models import Project, Membership, Ticket
from .models import Project, Membership, Ticket, Sprint


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
def active_sprint(request, pk):
    project = get_object_or_404(Project, pk=pk)
    request.session["current_project_id"] = project.id

    board = getattr(project, "board", None)
    if not board:
        messages.warning(request, "No board found for this project.")
        return redirect("project-detail", pk=project.pk)

    columns = board.columns.all().order_by("order")
    membership = project.memberships.filter(user=request.user).first()

    # Sprint actif
    active_sprint = project.sprints.filter(status='active').first()

    context = {
        "project": project,
        "board": board,
        "columns": columns,
        "membership": membership,
        "active_sprint": active_sprint,
        "planned_sprints": project.sprints.filter(status="planned").order_by("start_date"),

    }
    return render(request, "scrum/sprint/active_sprint.html", context)





class ProjectListView(LoginRequiredMixin, ListView):
    model = Project
    template_name = "scrum/project_list.html"
    context_object_name = "projects"
    ordering = ["-id"]

    def get_queryset(self):
        return project_queryset_for(self.request.user)


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
        return project.created_by == self.request.user

    def handle_no_permission(self):
        messages.error(self.request, "Only the project creator can access project settings.")
        return redirect("project-board", pk=self.get_object().pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.object
        self.request.session["current_project_id"] = project.id
        context["memberships"] = project.memberships.select_related("user")
        context["membership_form"] = MembershipForm()
        return context

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
    template_name = "scrum/ticket/ticket_form.html"  # ← ajoute cette ligne

    def test_func(self):
        return is_contributor_or_admin(self.request.user, get_object_or_404(Project, pk=self.kwargs["pk"]))

    def handle_no_permission(self):
        messages.error(self.request, "You don't have permission to create issues.")
        return redirect("product-backlog", pk=self.kwargs["pk"])

    def get_initial(self):
        def get_initial(self):
            initial = super().get_initial()
            title = self.request.GET.get('title', '').strip()
            ticket_type = self.request.GET.get('type', '').strip().lower()

            if title:
                initial['title'] = title

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
        form.instance.status = "todo"
        if self.request.headers.get("x-requested-with") == "XMLHttpRequest":
            self.object = form.save()
            return JsonResponse({"success": True, "ticket_id": self.object.pk})
        messages.success(self.request, f'Issue "{form.instance.title}" created.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("product-backlog", kwargs={"pk": self.kwargs["pk"]})

class TicketListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Ticket
    template_name = "scrum/ticket/product_backlog.html"
    context_object_name = "tickets"

    def test_func(self):
        return user_can_access_project(self.request.user,get_object_or_404(Project, pk=self.kwargs["pk"]))

    def handle_no_permission(self):
        messages.error(self.request, "You don't have access to this project.")
        return redirect("project-list")

    def get_queryset(self):
        self.project = get_object_or_404(Project, pk=self.kwargs["pk"])
        self.request.session["current_project_id"] = self.project.id
        normalize_backlog_order(self.project)
        
        qs = Ticket.objects.filter(project=self.project).select_related("assignee", "assignee__profile", "parent").order_by("backlog_order", "created_at")
        
        # Filtres GET
        type_filter = self.request.GET.get("type", "")
        priority_filter = self.request.GET.get("priority", "")
        status_filter = self.request.GET.get("status", "")
        
        if type_filter:
            qs = qs.filter(type=type_filter)
        if priority_filter:
            qs = qs.filter(priority=priority_filter)
        if status_filter:
            qs = qs.filter(status=status_filter)
        
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"]    = self.project
        context["membership"] = self.project.memberships.filter(user=self.request.user).first()
        context["can_create"] = is_contributor_or_admin(self.request.user, self.project)
        context["can_delete"] = is_project_admin(self.request.user, self.project)
        context["can_reorder"] = is_contributor_or_admin(self.request.user, self.project)
        context["filter_type"] = self.request.GET.get("type", "")
        context["filter_priority"] = self.request.GET.get("priority", "")
        context["filter_status"] = self.request.GET.get("status", "")
        context["active_filters"] = any([
            context["filter_type"],
            context["filter_priority"],
            context["filter_status"]
        ])

        sprints = self.project.sprints.all().order_by('-created_at')

        for sprint in sprints:
            tickets = sprint.tickets.all()
            sprint.total_issues      = tickets.count()
            sprint.completed_issues  = tickets.filter(status='done').count()
            sprint.completion_percentage = (
                int((sprint.completed_issues / sprint.total_issues) * 100)
                if sprint.total_issues else 0
            )
            if sprint.status == 'active' and sprint.end_date:
                from datetime import date
                today = date.today()
                sprint.days_remaining = max((sprint.end_date - today).days, 0)
        context["sprints"] = sprints
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
        # drawer=1 → charge le partial, sinon redirige
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
            "can_edit":  is_contributor_or_admin(self.request.user, project),
            "can_delete": is_project_admin(self.request.user, project),
            "edit_form": edit_form,
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
        if self.request.headers.get("x-requested-with") == "XMLHttpRequest":
            self.object = form.save()
            return JsonResponse({"success": True})
        messages.success(self.request, f'Issue "{form.instance.title}" updated.')
        return super().form_valid(form)

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
    """Création rapide depuis le backlog inline row."""
    project = get_object_or_404(Project, pk=pk)

    if not is_contributor_or_admin(request.user, project):
        messages.error(request, "You don't have permission to create issues.")
        return redirect("product-backlog", pk=pk)

    title = request.GET.get('title', '').strip()
    ticket_type = request.GET.get('type', 'user story').strip().lower()

    # Mapper les valeurs du JS vers les choices du modèle
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
        type=ticket_type,       # ← champ correct dans le modèle
        status='todo',
        requester=request.user,
    )
    messages.success(request, f'Issue "{ticket.title}" created.')
    return redirect("product-backlog", pk=pk)

class SprintCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Sprint
    form_class = SprintForm
    template_name = "scrum/sprint/sprint_form.html"

    def test_func(self):
        project = get_object_or_404(Project, pk=self.kwargs["pk"])
        return is_contributor_or_admin(self.request.user, project)

    def handle_no_permission(self):
        messages.error(self.request, "Only contributors and admins can create sprints.")
        return redirect("project-active-sprint", pk=self.kwargs["pk"])

    def form_valid(self, form):
        project = get_object_or_404(Project, pk=self.kwargs["pk"])
        form.instance.project = project
        messages.success(self.request, f'Sprint "{form.instance.name}" created successfully!')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = get_object_or_404(Project, pk=self.kwargs["pk"])
        return context

    def get_success_url(self):
        return reverse("project-active-sprint", kwargs={"pk": self.kwargs["pk"]})






































