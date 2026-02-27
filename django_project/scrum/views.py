from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import JsonResponse, request
from django.shortcuts import redirect, get_object_or_404, render
from django.urls import reverse_lazy, reverse
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import Project, Sprint, Column, Board
from .forms import ProjectForm, MembershipForm


@login_required
def project_board(request, pk):
    project = get_object_or_404(Project, pk=pk)

    # sauvegarde projet courant (menu navbar)
    request.session["current_project_id"] = project.id

    # récupérer le board principal
    board = getattr(project, "board", None)

    # sécurité
    if not board:
        messages.warning(request, "No board found for this project.")
        return redirect("project-detail", pk=project.pk)

    columns = board.columns.all().order_by("order")

    membership = project.memberships.filter(user=request.user).first()

    context = {
        "project": project,
        "board": board,
        "columns": columns,
        "membership": membership
    }

    return render(request, "scrum/project_board.html", context)

#================================================
#          PROJECTS CLASS BASED VIEWS
#=================================================
class ProjectListView(LoginRequiredMixin, ListView):
    model = Project
    template_name = "scrum/project_list.html"
    context_object_name = "projects"
    ordering = ["-id"]

    def get_queryset(self):
        # Affiche les projets où l'user est créateur OU membre
        user = self.request.user
        return (Project.objects.filter(created_by=user)| Project.objects.filter(members=user)).distinct()

class ProjectDetailView(LoginRequiredMixin, DetailView):
    model = Project
    template_name = "scrum/project_detail.html"

    def get_queryset(self):
        # Empêche d'accéder à un projet dont tu n'es ni membre ni créateur
        user = self.request.user
        return (
            Project.objects.filter(created_by=user)
            | Project.objects.filter(members=user)
        ).distinct()

    # Optionnel: pour afficher sprints / tickets dans le template
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.object
        context["sprints"] = project.sprints.all()
        context["membership"] = project.memberships.filter(user=self.request.user).first()
        return context

class ProjectSettingsView(UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = "scrum/project_settings.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        project = self.object

        context["memberships"] = project.memberships.select_related("user")
        context["membership_form"] = MembershipForm()

        return context

class ProjectCreateView(LoginRequiredMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = "scrum/project_form.html"

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)

        # crée board auto si pas déjà existant
        board, created = Board.objects.get_or_create(
            project=self.object,
            defaults={"name": "Main Board"}
        )

        # créer les colonnes uniquement si le board vient d’être créé
        if created:
            Column.objects.bulk_create([
                Column(board=board, name="To Do", order=1),
                Column(board=board, name="In Progress", order=2),
                Column(board=board, name="Done", order=3),
            ])

        return response

    def get_success_url(self):
        return reverse_lazy("project-board", kwargs={'pk': self.object.pk})

class ProjectUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = "scrum/project_form.html"
    success_url = reverse_lazy("project-list")

    def test_func(self):
        return self.get_object().created_by == self.request.user

class ProjectUpdateModalView(LoginRequiredMixin, View):

    def post(self, request, pk):
        project = get_object_or_404(Project, pk=pk)
        if project.created_by != request.user:
            return JsonResponse({"error": "You are not allowed to edit this project."}, status=403)

        project.name = request.POST.get("name", project.name)
        project.code = request.POST.get("code", project.code)
        project.description = request.POST.get("description", project.description)
        project.project_type = request.POST.get("project_type", project.project_type)
        project.board_type = request.POST.get("board_type", project.board_type)
        project.save()
        return redirect('project-list')

class ProjectDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Project
    template_name = "scrum/project_confirm_delete.html"
    success_url = reverse_lazy("project-list")

    def get_queryset(self):
        # Seul le créateur peut supprimer
        return Project.objects.filter(created_by=self.request.user)

    def test_func(self):
        return self.get_object().created_by == self.request.user

#==========================================================================================================
#                   MEMBERSHIP CLASSES BASED VIEWS AND FUNCTIONS
#==========================================================================================================
class MembershipAddView(View):

    def post(self, request, pk):
        project = get_object_or_404(Project, pk=pk)

        form = MembershipForm(request.POST)
        if form.is_valid():
            membership = form.save(commit=False)
            membership.project = project
            membership.save()

        return redirect("project-settings", pk=pk)
    

class MembershipDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk, membership_pk):
        project = get_object_or_404(Project, pk=pk)
        if project.created_by != request.user:
            messages.error(request, "You are not allowed to remove members.")
            return redirect("project-settings", pk=pk)
        
        from .models import Membership
        membership = get_object_or_404(Membership, pk=membership_pk, project=project)
        membership.delete()
        messages.success(request, "Member removed successfully.")
        return redirect("project-settings", pk=pk)


class MembershipUpdateRoleView(LoginRequiredMixin, View):
    def post(self, request, pk, membership_pk):
        project = get_object_or_404(Project, pk=pk)
        if project.created_by != request.user:
            messages.error(request, "You are not allowed to change roles.")
            return redirect("project-settings", pk=pk)
        
        from .models import Membership
        membership = get_object_or_404(Membership, pk=membership_pk, project=project)
        new_role = request.POST.get("role")
        if new_role in ["admin", "contributor", "read-only"]:
            membership.role = new_role
            membership.save()
            messages.success(request, "Role updated successfully.")
        return redirect("project-settings", pk=pk)
    
#==========================================================================================================
#                   BOARD CLASSES BASED VIEWS AND FUNCTIONS
#==========================================================================================================

#==========================================================================================================
#                   COLUMNS CLASSES BASED VIEWS AND FUNCTIONS
#==========================================================================================================

#==========================================================================================================
#                   SPRINT CLASSES BASED VIEWS AND FUNCTIONS
#==========================================================================================================

#==========================================================================================================
#                   ISSUES CLASSES BASED VIEWS AND FUNCTIONS
#==========================================================================================================
