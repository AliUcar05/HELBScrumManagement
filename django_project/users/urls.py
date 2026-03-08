from django.urls import path
from . import views

urlpatterns = [
    path("manage-users/", views.manage_users, name="manage-users"),
    path("users/create/", views.create_user, name="create-user"),
    path("users/<int:user_id>/delete/", views.delete_user, name="delete-user"),
]