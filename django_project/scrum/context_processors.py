from django.contrib.auth import get_user_model

from users.forms import AdminCreateUserForm
from users.models import Notification

from .forms import MembershipForm, TicketForm
from .models import Project


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

    is_platform_admin = (
        hasattr(request.user, "profile")
        and request.user.profile.global_role.lower() == "admin"
    )

    create_user_form = None
    if is_platform_admin:
        create_user_form = AdminCreateUserForm(can_assign_global_role=True)

    membership_form_modal = None
    if current_project:
        membership_form_modal = MembershipForm(
            project=current_project,
            current_user=request.user,
        )

    recent_notifications = list(
        Notification.objects.filter(recipient=request.user)
        .select_related("sender")[:5]
    )
    unread_notifications_count = Notification.objects.filter(
        recipient=request.user,
        is_read=False,
    ).count()

    return {
        "user_projects": user_projects,
        "current_project": current_project,
        "ticket_form": ticket_form,
        "create_user_form": create_user_form,
        "membership_form": membership_form_modal,
        "can_create_user": is_platform_admin,
        "is_platform_admin": is_platform_admin,
        "recent_notifications": recent_notifications,
        "unread_notifications_count": unread_notifications_count,
    }