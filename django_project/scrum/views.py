from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import Project, Sprint, Ticket
from .forms import ProjectForm


class ProjectListView(LoginRequiredMixin, ListView):
    model = Project
    template_name = "scrum/project_list.html"
    context_object_name = "projects"
    ordering = ["-id"]

    def get_queryset(self):
        # Affiche les projets où l'user est créateur OU membre
        user = self.request.user
        return (
            Project.objects.filter(created_by=user)
            | Project.objects.filter(members=user)
        ).distinct()


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
        context["tickets"] = project.tickets.filter(parent_ticket__isnull=True)
        return context


class ProjectCreateView(LoginRequiredMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = "scrum/project_form.html"
    success_url = reverse_lazy("project-list") 

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class ProjectUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = "scrum/project_form.html"
    success_url = reverse_lazy("project-list") 

    def test_func(self):
        return self.get_object().created_by == self.request.user


class ProjectDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Project
    template_name = "scrum/project_confirm_delete.html"
    success_url = reverse_lazy("project-list")

    def get_queryset(self):
        # Seul le créateur peut supprimer
        return Project.objects.filter(created_by=self.request.user)

    def test_func(self):
        return self.get_object().created_by == self.request.user

