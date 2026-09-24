from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import UserRegistrationForm, LoginForm, ProfileForm
from .models import User

def login_view(request):
    """
    Common login view for all three roles:
    EV User, Station Operator, and System Admin.
    """
    if request.user.is_authenticated:
        return redirect('role_redirect')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            return redirect('role_redirect')
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})


def role_redirect(request):
    """
    Directs authenticated user to their respective distinct dashboard.
    EV User -> user_dashboard
    Station Operator -> operator_dashboard
    System Admin -> admin_dashboard
    """
    if not request.user.is_authenticated:
        return redirect('login')

    if request.user.role == 'ADMIN':
        return redirect('admin_dashboard')
    elif request.user.role == 'OPERATOR':
        return redirect('operator_dashboard')
    else:
        return redirect('user_dashboard')


def register_view(request):
    """
    Registration page strictly for EV Users.
    Operators are created exclusively by Admin.
    Admin registration is forbidden.
    """
    if request.user.is_authenticated:
        return redirect('role_redirect')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Account created successfully! Welcome to Smart EVCharge.")
            return redirect('user_dashboard')
    else:
        form = UserRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


def logout_view(request):
    """
    Logs out the current session and redirects to landing page.
    """
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect('landing')


@login_required
def profile_view(request):
    """
    Manage user profile details.
    """
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('profile')
    else:
        form = ProfileForm(instance=request.user)

    return render(request, 'accounts/profile.html', {'form': form})
