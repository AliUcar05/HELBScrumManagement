from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from scrum.models import Project, Ticket, Sprint, Membership, Activity




@login_required
def home(request):
    user = request.user
    user_projects = Project.objects.filter(members=user)
    recent_activity = Activity.objects.filter(project__members=user).select_related("user", "ticket", "sprint").order_by("-created_at")[:15]
    active_sprints = Sprint.objects.filter(project__members=user,status='active').select_related('project')[:5]
    my_tickets = Ticket.objects.filter(assignee=user).exclude(status='done').select_related('project')[:5]

    context = {
        'user_projects_count':  Project.objects.filter(members=user).count(),
        'open_tickets_count':   Ticket.objects.filter(project__members=user).exclude(status='done').count(),
        'my_tickets_count':     Ticket.objects.filter(assignee=user).exclude(status='done').count(),
        'active_sprints_count': Sprint.objects.filter(project__members=user, status='active').count(),
        'recent_projects':      user_projects.order_by('-start_date')[:5],
        'active_sprints': active_sprints,
        'my_tickets': my_tickets,
        'user_memberships':     Membership.objects.filter(user=user).select_related('project')[:5],
        'recent_activity': recent_activity,

    }
    return render(request, 'blog/home.html', context)