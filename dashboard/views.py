from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import date, datetime, timedelta

from accounts.decorators import ev_user_required, operator_required, admin_required
from accounts.models import User, OperatorProfile
from accounts.forms import OperatorCreationForm
from stations.models import ChargingStation, ChargingPoint
from stations.forms import ChargingStationForm, ChargingPointForm
from vehicles.models import Vehicle
from bookings.models import Booking
from charging.models import ChargingSession
from queue_management.models import QueueEntry
from notifications.models import Notification

def landing_view(request):
    """
    Public Landing Page for Smart EVCharge.
    """
    stations = ChargingStation.objects.filter(status='ACTIVE')[:4]
    total_stations = ChargingStation.objects.filter(status='ACTIVE').count()
    total_points = ChargingPoint.objects.count()
    total_bookings = Booking.objects.count()

    return render(request, 'landing.html', {
        'stations': stations,
        'total_stations': total_stations,
        'total_points': total_points,
        'total_bookings': total_bookings
    })


# ==========================================
# EV USER DASHBOARD
# ==========================================
@ev_user_required
def user_dashboard(request):
    """
    EV User Dashboard with greeting, active booking, queue position,
    vehicles, upcoming slots, and recent alerts.
    """
    user = request.user
    today = date.today()

    # Active or In-Progress Booking
    active_booking = Booking.objects.filter(
        user=user,
        status__in=['CONFIRMED', 'CHARGING']
    ).order_by('date', 'start_time').first()

    # Active Charging Session
    active_session = None
    if active_booking:
        active_session = ChargingSession.objects.filter(
            booking=active_booking,
            status__in=['IN_PROGRESS', 'FINISHING']
        ).first()

    # User's active queue position
    active_queue = QueueEntry.objects.filter(
        user=user,
        status__in=['WAITING', 'NOTIFIED']
    ).first()

    # Upcoming Bookings
    upcoming_bookings = Booking.objects.filter(
        user=user,
        date__gte=today,
        status='CONFIRMED'
    ).order_by('date', 'start_time')[:5]

    # Completed Sessions Count
    completed_sessions_count = Booking.objects.filter(
        user=user,
        status='COMPLETED'
    ).count()

    # User Vehicles
    vehicles = Vehicle.objects.filter(user=user)[:4]

    # Recent Alerts
    recent_alerts = Notification.objects.filter(user=user)[:5]

    return render(request, 'user/dashboard.html', {
        'active_booking': active_booking,
        'active_session': active_session,
        'active_queue': active_queue,
        'upcoming_bookings': upcoming_bookings,
        'completed_sessions_count': completed_sessions_count,
        'vehicles': vehicles,
        'recent_alerts': recent_alerts
    })


# ==========================================
# OPERATOR DASHBOARD
# ==========================================
@operator_required
def operator_dashboard(request):
    """
    Station Operator Dashboard:
    Limited strictly to the station assigned to this operator.
    """
    operator_profile = getattr(request.user, 'operator_profile', None)
    station = operator_profile.assigned_station if operator_profile else None

    if not station:
        messages.error(request, "No charging station is assigned to your account. Please contact system admin.")
        return render(request, 'operator/unassigned.html')

    today = date.today()
    points = station.points.all()
    todays_bookings = Booking.objects.filter(station=station, date=today)
    active_sessions = ChargingSession.objects.filter(
        booking__station=station,
        status__in=['IN_PROGRESS', 'FINISHING']
    )
    waiting_queue_count = QueueEntry.objects.filter(station=station, status='WAITING').count()

    # Status counts
    available_cnt = points.filter(status='AVAILABLE').count()
    reserved_cnt = points.filter(status='RESERVED').count()
    charging_cnt = points.filter(status='CHARGING').count()
    finishing_cnt = points.filter(status='FINISHING').count()
    out_of_service_cnt = points.filter(status='OUT_OF_SERVICE').count()

    return render(request, 'operator/dashboard.html', {
        'station': station,
        'points': points,
        'todays_bookings': todays_bookings,
        'active_sessions': active_sessions,
        'waiting_queue_count': waiting_queue_count,
        'available_cnt': available_cnt,
        'reserved_cnt': reserved_cnt,
        'charging_cnt': charging_cnt,
        'finishing_cnt': finishing_cnt,
        'out_of_service_cnt': out_of_service_cnt,
    })


# ==========================================
# SYSTEM ADMIN DASHBOARD & MANAGEMENT
# ==========================================
@admin_required
def admin_dashboard(request):
    """
    System Admin Dashboard:
    System-wide overview, KPI counters, and Chart.js analytics.
    """
    total_users = User.objects.filter(role='USER').count()
    total_operators = User.objects.filter(role='OPERATOR').count()
    total_stations = ChargingStation.objects.count()
    total_points = ChargingPoint.objects.count()

    # Points status breakdown
    available_points = ChargingPoint.objects.filter(status='AVAILABLE').count()
    reserved_points = ChargingPoint.objects.filter(status='RESERVED').count()
    charging_points = ChargingPoint.objects.filter(status='CHARGING').count()
    finishing_points = ChargingPoint.objects.filter(status='FINISHING').count()
    out_of_service_points = ChargingPoint.objects.filter(status='OUT_OF_SERVICE').count()

    # Bookings & Sessions
    total_bookings = Booking.objects.count()
    active_bookings = Booking.objects.filter(status__in=['CONFIRMED', 'CHARGING']).count()
    completed_bookings = Booking.objects.filter(status='COMPLETED').count()
    cancelled_bookings = Booking.objects.filter(status='CANCELLED').count()
    active_sessions = ChargingSession.objects.filter(status='IN_PROGRESS').count()
    queue_entries_count = QueueEntry.objects.filter(status='WAITING').count()

    # Chart data: Station Utilization
    stations = ChargingStation.objects.annotate(
        b_count=Count('bookings'),
        p_count=Count('points')
    )[:6]
    station_names = [s.name for s in stations]
    station_booking_counts = [s.b_count for s in stations]

    recent_bookings = Booking.objects.select_related('user', 'station', 'charging_point').order_by('-created_at')[:8]

    return render(request, 'admin_panel/dashboard.html', {
        'total_users': total_users,
        'total_operators': total_operators,
        'total_stations': total_stations,
        'total_points': total_points,
        'available_points': available_points,
        'reserved_points': reserved_points,
        'charging_points': charging_points,
        'finishing_points': finishing_points,
        'out_of_service_points': out_of_service_points,
        'total_bookings': total_bookings,
        'active_bookings': active_bookings,
        'completed_bookings': completed_bookings,
        'cancelled_bookings': cancelled_bookings,
        'active_sessions': active_sessions,
        'queue_entries_count': queue_entries_count,
        'station_names': station_names,
        'station_booking_counts': station_booking_counts,
        'recent_bookings': recent_bookings,
    })


# Admin: User Management
@admin_required
def admin_users_list(request):
    q = request.GET.get('q', '').strip()
    users = User.objects.filter(role='USER')
    if q:
        users = users.filter(Q(username__icontains=q) | Q(email__icontains=q) | Q(first_name__icontains=q))
    return render(request, 'admin_panel/users.html', {'users': users, 'query': q})


@admin_required
def admin_user_toggle_status(request, pk):
    user = get_object_or_404(User, pk=pk, role='USER')
    user.is_active = not user.is_active
    user.save(update_fields=['is_active'])
    action = "activated" if user.is_active else "deactivated"
    messages.success(request, f"User {user.username} has been {action}.")
    return redirect('admin_users')


# Admin: Stations Management
@admin_required
def admin_stations_list(request):
    stations = ChargingStation.objects.all()
    return render(request, 'admin_panel/stations.html', {'stations': stations})


@admin_required
def admin_station_create(request):
    if request.method == 'POST':
        form = ChargingStationForm(request.POST)
        if form.is_valid():
            station = form.save()
            messages.success(request, f"Charging Station '{station.name}' created successfully!")
            return redirect('admin_stations')
    else:
        form = ChargingStationForm()
    return render(request, 'admin_panel/station_form.html', {'form': form, 'title': 'Create New Charging Station'})


@admin_required
def admin_station_edit(request, pk):
    station = get_object_or_404(ChargingStation, pk=pk)
    if request.method == 'POST':
        form = ChargingStationForm(request.POST, instance=station)
        if form.is_valid():
            form.save()
            messages.success(request, f"Station '{station.name}' updated successfully!")
            return redirect('admin_stations')
    else:
        form = ChargingStationForm(instance=station)
    return render(request, 'admin_panel/station_form.html', {'form': form, 'title': 'Edit Charging Station', 'station': station})


@admin_required
def admin_station_delete(request, pk):
    station = get_object_or_404(ChargingStation, pk=pk)
    if request.method == 'POST':
        name = station.name
        station.delete()
        messages.info(request, f"Station '{name}' has been deleted.")
        return redirect('admin_stations')
    return render(request, 'admin_panel/confirm_delete.html', {'item': station, 'type': 'Station'})


# Admin: Operators Management
@admin_required
def admin_operators_list(request):
    operators = User.objects.filter(role='OPERATOR').select_related('operator_profile__assigned_station')
    return render(request, 'admin_panel/operators.html', {'operators': operators})


@admin_required
def admin_operator_create(request):
    """
    Creates station operator account and assigns to a charging station.
    Strict single-admin rule is respected (only role='OPERATOR' can be created here).
    """
    if request.method == 'POST':
        form = OperatorCreationForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            phone = form.cleaned_data['phone']
            password = form.cleaned_data['password']
            station = form.cleaned_data['station']
            status = form.cleaned_data['status']

            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=name,
                phone=phone,
                role='OPERATOR'
            )

            OperatorProfile.objects.create(
                user=user,
                assigned_station=station,
                status=status
            )

            messages.success(request, f"Station Operator '{username}' created and assigned to {station.name}!")
            return redirect('admin_operators')
    else:
        form = OperatorCreationForm()
    return render(request, 'admin_panel/operator_form.html', {'form': form, 'title': 'Add New Station Operator'})


@admin_required
def admin_operator_edit(request, pk):
    operator_user = get_object_or_404(User, pk=pk, role='OPERATOR')
    profile, _ = OperatorProfile.objects.get_or_create(user=operator_user)

    if request.method == 'POST':
        station_id = request.POST.get('station')
        phone = request.POST.get('phone', '')
        name = request.POST.get('name', '')
        status = request.POST.get('status', 'ACTIVE')

        operator_user.first_name = name
        operator_user.phone = phone
        operator_user.save()

        if station_id:
            profile.assigned_station = ChargingStation.objects.get(id=station_id)
        profile.status = status
        profile.save()

        messages.success(request, f"Operator {operator_user.username} updated successfully.")
        return redirect('admin_operators')

    stations = ChargingStation.objects.all()
    return render(request, 'admin_panel/operator_edit.html', {
        'operator_user': operator_user,
        'profile': profile,
        'stations': stations
    })


@admin_required
def admin_operator_toggle(request, pk):
    user = get_object_or_404(User, pk=pk, role='OPERATOR')
    user.is_active = not user.is_active
    user.save(update_fields=['is_active'])
    action = "activated" if user.is_active else "deactivated"
    messages.success(request, f"Operator {user.username} has been {action}.")
    return redirect('admin_operators')


# Admin: Charging Points Management
@admin_required
def admin_points_list(request):
    station_id = request.GET.get('station')
    points = ChargingPoint.objects.select_related('station')
    if station_id:
        points = points.filter(station_id=station_id)
    stations = ChargingStation.objects.all()
    return render(request, 'admin_panel/charging_points.html', {'points': points, 'stations': stations, 'selected_station': station_id})


@admin_required
def admin_point_create(request):
    if request.method == 'POST':
        form = ChargingPointForm(request.POST)
        if form.is_valid():
            point = form.save()
            messages.success(request, f"Charging Point '{point.point_number}' added to {point.station.name}!")
            return redirect('admin_points')
    else:
        form = ChargingPointForm()
    return render(request, 'admin_panel/point_form.html', {'form': form, 'title': 'Add Charging Point'})


@admin_required
def admin_point_edit(request, pk):
    point = get_object_or_404(ChargingPoint, pk=pk)
    if request.method == 'POST':
        form = ChargingPointForm(request.POST, instance=point)
        if form.is_valid():
            form.save()
            messages.success(request, f"Charging Point '{point.point_number}' updated successfully!")
            return redirect('admin_points')
    else:
        form = ChargingPointForm(instance=point)
    return render(request, 'admin_panel/point_form.html', {'form': form, 'title': 'Edit Charging Point', 'point': point})


@admin_required
def admin_point_delete(request, pk):
    point = get_object_or_404(ChargingPoint, pk=pk)
    if request.method == 'POST':
        point_num = point.point_number
        point.delete()
        messages.info(request, f"Point '{point_num}' removed.")
        return redirect('admin_points')
    return render(request, 'admin_panel/confirm_delete.html', {'item': point, 'type': 'Charging Point'})


# Admin: Bookings Management
@admin_required
def admin_bookings_list(request):
    station_id = request.GET.get('station')
    status_filter = request.GET.get('status')
    date_filter = request.GET.get('date')

    bookings = Booking.objects.select_related('user', 'station', 'charging_point', 'vehicle').order_by('-date', '-start_time')

    if station_id:
        bookings = bookings.filter(station_id=station_id)
    if status_filter:
        bookings = bookings.filter(status=status_filter)
    if date_filter:
        bookings = bookings.filter(date=date_filter)

    stations = ChargingStation.objects.all()
    return render(request, 'admin_panel/bookings.html', {
        'bookings': bookings,
        'stations': stations,
        'selected_station': station_id,
        'selected_status': status_filter,
        'selected_date': date_filter
    })


# Admin: Charging Sessions Management
@admin_required
def admin_sessions_list(request):
    sessions = ChargingSession.objects.select_related('booking__station', 'booking__user', 'operator').order_by('-started_at')
    return render(request, 'admin_panel/sessions.html', {'sessions': sessions})


# Admin: Queue Management
@admin_required
def admin_queue_list(request):
    station_id = request.GET.get('station')
    queues = QueueEntry.objects.select_related('user', 'station', 'vehicle').order_by('-priority', 'created_at')
    if station_id:
        queues = queues.filter(station_id=station_id)
    stations = ChargingStation.objects.all()
    return render(request, 'admin_panel/queue.html', {'queues': queues, 'stations': stations, 'selected_station': station_id})


# Admin: Reports
@admin_required
def admin_reports_view(request):
    total_bookings = Booking.objects.count()
    completed_bookings = Booking.objects.filter(status='COMPLETED').count()
    cancelled_bookings = Booking.objects.filter(status='CANCELLED').count()
    confirmed_bookings = Booking.objects.filter(status='CONFIRMED').count()

    total_sessions = ChargingSession.objects.filter(status='COMPLETED')
    total_energy_delivered = sum([float(s.energy_delivered_kwh) for s in total_sessions])

    # Station Utilization data
    stations = ChargingStation.objects.annotate(
        total_b=Count('bookings'),
        completed_b=Count('bookings', filter=Q(bookings__status='COMPLETED'))
    )

    station_names = [s.name for s in stations]
    station_bookings = [s.total_b for s in stations]
    station_completed = [s.completed_b for s in stations]

    return render(request, 'admin_panel/reports.html', {
        'total_bookings': total_bookings,
        'completed_bookings': completed_bookings,
        'cancelled_bookings': cancelled_bookings,
        'confirmed_bookings': confirmed_bookings,
        'total_energy_delivered': round(total_energy_delivered, 2),
        'station_names': station_names,
        'station_bookings': station_bookings,
        'station_completed': station_completed,
    })


# Admin: System Settings
@admin_required
def admin_settings_view(request):
    admin_user = User.objects.filter(role='ADMIN').first()
    return render(request, 'admin_panel/settings.html', {
        'admin_user': admin_user,
        'server_time': timezone.now()
    })
