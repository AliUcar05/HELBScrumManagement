from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

from .forms import ProjectForm, MembershipForm
from .models import Project, Membership


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


@login_required
def project_board(request, pk):
    project = get_object_or_404(Project, pk=pk)

    if not user_can_access_project(request.user, project):
        messages.error(request, "You are not allowed to access this project.")
        return redirect("home")

    request.session["current_project_id"] = project.id

    board = getattr(project, "board", None)
    if not board:
        messages.warning(request, "No board found for this project.")
        return redirect("project-detail", pk=project.pk)

    columns = board.columns.all().order_by("order")
    membership = project.memberships.filter(user=request.user).first()

    context = {
        "project": project,
        "board": board,
        "columns": columns,
        "membership": membership,
        "active_sprint": project.active_sprint,
    }
    return render(request, "scrum/project_board.html", context)


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