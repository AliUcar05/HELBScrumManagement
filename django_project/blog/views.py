from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from scrum.models import Project, Ticket, Sprint, Membership


@login_required
def home(request):
    user = request.user
    context = {
        'user_projects_count':  Project.objects.filter(members=user).count(),
        'open_tickets_count':   Ticket.objects.filter(project__members=user).exclude(status='done').count(),
        'my_tickets_count':     Ticket.objects.filter(assignee=user).exclude(status='done').count(),
        'active_sprints_count': Sprint.objects.filter(project__members=user, status='active').count(),
        'recent_projects':      Project.objects.filter(members=user).order_by('-start_date')[:5],
        'active_sprints':       Sprint.objects.filter(project__members=user, status='active')[:3],
        'my_tickets':           Ticket.objects.filter(assignee=user).exclude(status='done')[:6],
        'user_memberships':     Membership.objects.filter(user=user).select_related('project')[:5],
    }
    return render(request, 'blog/home.html', context)