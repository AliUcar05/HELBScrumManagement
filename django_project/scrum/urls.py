from django.urls import path

from . import views
from .views import (
    ProjectListView, ProjectDetailView, ProjectCreateView,
    ProjectUpdateView, ProjectDeleteView, ProjectSettingsView, MembershipAddView,
    MembershipDeleteView, MembershipUpdateRoleView

)

urlpatterns = [
    path("projects/", ProjectListView.as_view(), name="project-list"),
    path("projects/new/", ProjectCreateView.as_view(), name="project-create"),
    path("projects/<int:pk>/", ProjectDetailView.as_view(), name="project-detail"),
    path("projects/<int:pk>/update/", ProjectUpdateView.as_view(), name="project-update"),
    path("projects/<int:pk>/delete/", ProjectDeleteView.as_view(), name="project-delete"),


    path("projects/<int:pk>/board/", views.project_board, name="project-board"),
    path("projects/<int:pk>/update-modal/", views.ProjectUpdateModalView.as_view(), name="project-update-modal"),
    path("projects/<int:pk>/settings/",ProjectSettingsView.as_view(),name="project-settings"),
    path("projects/<int:pk>/members/add/",MembershipAddView.as_view(),name="membership-add"), 

    path("projects/<int:pk>/members/<int:membership_pk>/delete/", MembershipDeleteView.as_view(), name="membership-delete"),
    path("projects/<int:pk>/members/<int:membership_pk>/role/", MembershipUpdateRoleView.as_view(), name="membership-update-role"),

]