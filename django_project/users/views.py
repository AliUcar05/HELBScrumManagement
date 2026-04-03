from django.conf import settings
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import AdminCreateUserForm, UserUpdateForm, ProfileUpdateForm


def is_platform_admin(user):
    return user.is_authenticated and (
        user.is_superuser
        or user.is_staff
        or (
            hasattr(user, "profile")
            and user.profile.global_role.lower() == "admin"
        )
    )


@login_required
def profile(request):
    if request.method == "POST":
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)

        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, "Your account has been updated.")
            return redirect("profile")
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)

    return render(request, "users/profile.html", {
        "u_form": u_form,
        "p_form": p_form,
    })


@login_required
def change_password(request):
    if request.method == "POST":
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Your password was successfully updated.")
            return redirect("change_password")
    else:
        form = PasswordChangeForm(request.user)

    return render(request, "users/change_password.html", {"form": form})


@login_required
@user_passes_test(is_platform_admin, login_url="home")
def manage_users(request):
    back_url = request.GET.get("next") or request.POST.get("next") or reverse("home")

    if request.method == "POST":
        user_id = request.POST.get("user_id")
        new_role = request.POST.get("new_role")

        if new_role not in ["admin", "member", "read-only"]:
            messages.error(request, "Invalid global role.")
            return redirect(f"{reverse('manage-users')}?next={back_url}")

        target_user = get_object_or_404(User, id=user_id)

        if target_user == request.user and new_role != "admin":
            messages.error(request, "You cannot remove your own admin role.")
            return redirect(f"{reverse('manage-users')}?next={back_url}")

        if (
            target_user.profile.global_role == "admin"
            and new_role != "admin"
            and User.objects.filter(profile__global_role="admin").count() <= 1
        ):
            messages.error(request, "You cannot downgrade the last admin.")
            return redirect(f"{reverse('manage-users')}?next={back_url}")

        profile = target_user.profile
        profile.global_role = new_role
        profile.save()

        messages.success(
            request,
            f"The global role of {target_user.username} has been updated to '{new_role}'."
        )
        return redirect(f"{reverse('manage-users')}?next={back_url}")

    users = User.objects.all().select_related("profile").order_by("username")
    return render(request, "users/manage_users.html", {
        "users": users,
        "back_url": back_url,
    })


@login_required
@user_passes_test(is_platform_admin, login_url="home")
def create_user(request):
    back_url = request.GET.get("next") or reverse("manage-users")

    if request.method == "POST":
        form = AdminCreateUserForm(request.POST)
        back_url = request.POST.get("next") or back_url

        if form.is_valid():
            raw_password = form.cleaned_data["password1"]
            user = form.save()

            subject = "Your ScrumManagement account"
            message = f"""
Hello {user.first_name or user.username},

An account has been created for you on ScrumManagement.

Login URL: http://127.0.0.1:8000/login/
Username: {user.username}
Email: {user.email}
Password: {raw_password}
Global role: {user.profile.get_global_role_display()}
Scrum role: {user.profile.get_role_display()}

Please log in and change your password as soon as possible.
"""
            try:
                send_mail(
                    subject,
                    message.strip(),
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )
                messages.success(request, f"User '{user.username}' created and email sent.")
            except Exception as e:
                messages.warning(
                    request,
                    f"User '{user.username}' created, but email could not be sent: {e}"
                )

            return redirect(f"{reverse('manage-users')}?next={back_url}")
    else:
        form = AdminCreateUserForm()

    return render(request, "users/create_user.html", {
        "form": form,
        "back_url": back_url,
    })


@login_required
@user_passes_test(is_platform_admin, login_url="home")
def delete_user(request, user_id):
    if request.method != "POST":
        return redirect("manage-users")

    back_url = request.POST.get("next") or reverse("home")
    target_user = get_object_or_404(User, id=user_id)

    if target_user == request.user:
        messages.error(request, "You cannot delete your own account.")
        return redirect(f"{reverse('manage-users')}?next={back_url}")

    if (
        target_user.profile.global_role == "admin"
        and User.objects.filter(profile__global_role="admin").count() <= 1
    ):
        messages.error(request, "You cannot delete the last admin.")
        return redirect(f"{reverse('manage-users')}?next={back_url}")

    try:
        username = target_user.username
        target_user.delete()
        messages.success(request, f"User '{username}' deleted successfully.")
    except ProtectedError:
        messages.error(
            request,
            "This user cannot be deleted because they are linked to protected data "
            "(for example: created projects, tickets, or other required records)."
        )
    except Exception as e:
        messages.error(request, f"Unable to delete this user: {e}")

    return redirect(f"{reverse('manage-users')}?next={back_url}")