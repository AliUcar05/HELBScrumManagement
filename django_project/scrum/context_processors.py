from django.contrib.auth import get_user_model
from .forms import TicketForm, MembershipForm
from .models import Project
from users.forms import AdminCreateUserForm


def global_context(request):
    if not request.user.is_authenticated:
        return {}

    User = get_user_model()

    user_projects = (
        Project.objects.filter(created_by=request.user)
        | Project.objects.filter(members=request.user)
    ).distinct().order_by("name")

    current_project = None
    current_project_id = request.session.get("current_project_id")
    if current_project_id:
        current_project = user_projects.filter(pk=current_project_id).first()

    ticket_form = None
    if current_project:
        ticket_form = TicketForm()
        ticket_form.fields["assignee"].queryset = current_project.members.all()
        ticket_form.fields["parent"].queryset = current_project.tickets.all()

    create_user_form = None
    if hasattr(request.user, 'profile') and request.user.profile.global_role.lower() == 'admin':
        create_user_form = AdminCreateUserForm()

    membership_form_modal = None
    if current_project:
        membership_form_modal = MembershipForm()
        membership_form_modal.fields["user"].queryset = (
            User.objects.exclude(id__in=current_project.members.values_list('id', flat=True))
                        .exclude(id=request.user.id)
                        .order_by("username")
        )

    return {
        "user_projects": user_projects,
        "current_project": current_project,
        "ticket_form": ticket_form,
        "create_user_form": create_user_form,
        "membership_form": membership_form_modal,
    }