from django.contrib.auth import update_session_auth_hash
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import UserRegisterForm, UserUpdateForm, ProfileUpdateForm
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User

# --- HELPER DE SÉCURITÉ MIS À JOUR ---
def is_authorized_user(user):
    # On autorise le rôle 'member' à accéder à la gestion des utilisateurs
    return user.is_authenticated and hasattr(user, 'profile') and user.profile.global_role.lower() == 'member'

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f'Your account has been created! You are now able to log in')
            return redirect('login')
    else:
        form = UserRegisterForm()
    return render(request, 'users/register.html', {'form': form})

@login_required
def profile(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, f'Your account has been updated!')
            return redirect('profile')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)

    context = {'u_form': u_form, 'p_form': p_form}
    return render(request, 'users/profile.html', context)

def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password was successfully updated!')
            return redirect('change_password')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'users/change_password.html', {'form': form })

# --- VUE MANAGE USERS (ACCÈS AUTORISÉ POUR 'MEMBER') ---
@login_required
@user_passes_test(is_authorized_user, login_url='home') 
def manage_users(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        new_role = request.POST.get('new_role')
        target_user = get_object_or_404(User, id=user_id)
        
        profile = target_user.profile
        profile.global_role = new_role
        profile.save()
        
        messages.success(request, f"Le rôle de {target_user.username} a été changé en '{new_role}'.")
        return redirect('manage-users')

    users = User.objects.all().select_related('profile')
    return render(request, 'users/manage_users.html', {'users': users})