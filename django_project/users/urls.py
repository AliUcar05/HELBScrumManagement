from django.urls import path
from . import views

urlpatterns = [
    path("notifications/", views.notifications_list, name="notifications-list"),
    path("notifications/mark-all-read/", views.mark_all_notifications_read, name="notifications-mark-all-read"),
    path("manage-users/", views.manage_users, name="manage-users"),
    path("users/create/", views.create_user, name="create-user"),
    path("users/<int:user_id>/delete/", views.delete_user, name="delete-user"),
]