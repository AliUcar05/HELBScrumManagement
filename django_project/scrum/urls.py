from django.urls import path

from . import views
from .views import (
    ProjectListView, ProjectDetailView, ProjectCreateView,
    ProjectUpdateView, ProjectDeleteView, ProjectSettingsView, MembershipAddView,
    MembershipDeleteView, MembershipUpdateRoleView,
    SprintCreateView,

    TicketCreateView,
    TicketUpdateView,
    TicketDetailView,
    TicketDeleteView, TicketListView, TicketReorderView, SprintDeleteView, ProjectIssuesView
)

urlpatterns = [
    path("projects/", ProjectListView.as_view(), name="project-list"),
    path("projects/new/", ProjectCreateView.as_view(), name="project-create"),
    path("projects/<int:pk>/", ProjectDetailView.as_view(), name="project-detail"),
    path("projects/<int:pk>/update/", ProjectUpdateView.as_view(), name="project-update"),
    path("projects/<int:pk>/delete/", ProjectDeleteView.as_view(), name="project-delete"),


    path("projects/<int:pk>/board/", views.project_board, name="project-board"),
    path("projects/<int:pk>/update-modal/", views.ProjectUpdateModalView.as_view(), name="project-update-modal"),
    path("projects/<int:pk>/members/add/",MembershipAddView.as_view(),name="membership-add"),

    path("projects/<int:pk>/members/<int:membership_pk>/delete/", MembershipDeleteView.as_view(), name="membership-delete"),
    path("projects/<int:pk>/members/<int:membership_pk>/role/", MembershipUpdateRoleView.as_view(), name="membership-update-role"),

    # URLS SIDEBAR PROJECT BOARD
    path('projects/<int:pk>/active-sprint/', views.active_sprint, name='project-active-sprint'),
    path('projects/<int:pk>/report/', views.project_report, name='project-report'),
    path("projects/<int:pk>/settings/", ProjectSettingsView.as_view(), name="project-settings"),
    path("projects/<int:pk>/issues/", ProjectIssuesView.as_view(), name="project-issues"),
    path('projects/<int:pk>/roadmap/',  views.project_roadmap,  name='project-roadmap'),
    path('projects/<int:pk>/releases/', views.project_releases, name='project-releases'),


    # TICKET ISSUES URL
    path('projects/<int:pk>/ticket/create/',TicketCreateView.as_view(),name='ticket-create'),
    path('projects/<int:pk>/ticket/quick-create/', views.quick_create_ticket, name='ticket-quick-create'),
    path("projects/<int:pk>/backlog/",TicketListView.as_view(), name="product-backlog"),
    path('projects/<int:pk>/ticket/detail/<int:ticket_pk>/',TicketDetailView.as_view(),name='ticket-detail'),
    path('projects/<int:pk>/ticket/update/<int:ticket_pk>/edit/',TicketUpdateView.as_view(),name='ticket-update'),
    path('projects/<int:pk>/ticket/delete/<int:ticket_pk>/delete/',TicketDeleteView.as_view(),name='ticket-delete'),
    path('projects/<int:pk>/ticket/<int:ticket_pk>/reorder/<str:direction>/', TicketReorderView.as_view(), name='ticket-reorder'),

    path('projects/<int:pk>/ticket/<int:ticket_pk>/inline-update/',views.ticket_inline_update, name='ticket-inline-update'),
    path('projects/<int:pk>/members-json/', views.project_members_json, name='project-members-json'),

    # SPRINT 
    path("projects/<int:pk>/sprints/create/", SprintCreateView.as_view(), name="sprint-create"),
    path("projects/<int:pk>/sprints/<int:sprint_pk>/delete/", SprintDeleteView.as_view(), name="sprint-delete"),
    path("projects/<int:pk>/sprints/<int:sprint_pk>/start/",    views.sprint_start,    name="sprint-start"),
    path("projects/<int:pk>/sprints/<int:sprint_pk>/complete/", views.sprint_complete, name="sprint-complete"),

    #TICKET COMMENTS
    path('ticket/<int:ticket_pk>/comment/add/', views.add_comment, name='add_comment'),
    path('comment/<int:comment_pk>/edit/', views.edit_comment, name='edit_comment'),
    path('comment/<int:comment_pk>/delete/', views.delete_comment, name='delete_comment'),

]