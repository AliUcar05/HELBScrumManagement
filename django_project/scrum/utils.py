from scrum.models import Activity

def log_activity(user, project, action, ticket=None, sprint=None, message=""):
    Activity.objects.create(
        user=user,
        project=project,
        ticket=ticket,
        sprint=sprint,
        action=action,
        description=message
    )