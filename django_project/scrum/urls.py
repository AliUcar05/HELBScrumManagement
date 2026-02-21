from django.urls import path

from . import views
from .views import (
    ProjectListView, ProjectDetailView, ProjectCreateView,
    ProjectUpdateView, ProjectDeleteView
)

urlpatterns = [
    path("projects/", ProjectListView.as_view(), name="project-list"),
    path("projects/new/", ProjectCreateView.as_view(), name="project-create"),
    path("projects/<int:pk>/", ProjectDetailView.as_view(), name="project-detail"),
    path("projects/<int:pk>/update/", ProjectUpdateView.as_view(), name="project-update"),
    path("projects/<int:pk>/delete/", ProjectDeleteView.as_view(), name="project-delete"),

]