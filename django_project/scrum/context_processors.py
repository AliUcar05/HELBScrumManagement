from .models import Project

def current_project(request):
    project_id = request.session.get("current_project_id")

    project = None
    if project_id:
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            pass

    return {
        "current_project": project
    }