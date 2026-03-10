from .forms import TicketForm
from .models import Project


def global_context(request):
    if not request.user.is_authenticated:
        return {}

    # Tous les projets accessibles par l'user
    user_projects = (
        Project.objects.filter(created_by=request.user)
        | Project.objects.filter(members=request.user)
    ).distinct().order_by("name")

    # Projet courant depuis la session
    current_project = None
    current_project_id = request.session.get("current_project_id")
    if current_project_id:
        current_project = user_projects.filter(pk=current_project_id).first()

    # Formulaire de création de ticket
    ticket_form = None
    if current_project:
        ticket_form = TicketForm()
        ticket_form.fields["assignee"].queryset = current_project.members.all()
        ticket_form.fields["parent"].queryset = current_project.tickets.all()

    return {
        "user_projects": user_projects,
        "current_project": current_project,
        "ticket_form": ticket_form,
    }

