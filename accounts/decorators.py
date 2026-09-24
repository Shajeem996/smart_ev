from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied

def ev_user_required(view_func):
    """
    Decorator for views that checks if the logged-in user is an EV User.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, "Please log in to continue.")
            return redirect('login')
        if request.user.role != 'USER':
            messages.error(request, "Access restricted: This area is only accessible to EV Users.")
            if request.user.role == 'OPERATOR':
                return redirect('operator_dashboard')
            elif request.user.role == 'ADMIN':
                return redirect('admin_dashboard')
            return redirect('landing')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def operator_required(view_func):
    """
    Decorator for views that checks if the logged-in user is a Station Operator.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, "Please log in with your Station Operator credentials.")
            return redirect('login')
        if request.user.role != 'OPERATOR':
            messages.error(request, "Access restricted: Station Operator privileges required.")
            if request.user.role == 'USER':
                return redirect('user_dashboard')
            elif request.user.role == 'ADMIN':
                return redirect('admin_dashboard')
            return redirect('landing')
        
        # Verify assigned station
        if not hasattr(request.user, 'operator_profile') or not request.user.operator_profile.assigned_station:
            messages.error(request, "You have not been assigned to a charging station yet. Please contact the System Administrator.")
            # Allow them to see profile or contact admin
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def admin_required(view_func):
    """
    Decorator for views that checks if the logged-in user is the System Admin.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, "Please log in with Administrator credentials.")
            return redirect('login')
        if request.user.role != 'ADMIN':
            messages.error(request, "Access denied: System Administrator privileges required.")
            if request.user.role == 'USER':
                return redirect('user_dashboard')
            elif request.user.role == 'OPERATOR':
                return redirect('operator_dashboard')
            return redirect('landing')
        return view_func(request, *args, **kwargs)
    return _wrapped_view
