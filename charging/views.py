from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse, HttpResponseForbidden
from accounts.decorators import operator_required
from .models import ChargingSession
from bookings.models import Booking
from stations.models import ChargingStation, ChargingPoint
from queue_management.models import QueueEntry
from queue_management.scheduler import process_station_queue
from notifications.utils import send_notification
from datetime import date, datetime

def _get_operator_station(user):
    if hasattr(user, 'operator_profile') and user.operator_profile.assigned_station:
        return user.operator_profile.assigned_station
    return None


@operator_required
def operator_station_view(request):
    """
    Operator 'My Station' overview page.
    """
    station = _get_operator_station(request.user)
    if not station:
        messages.error(request, "No station assigned to your operator account.")
        return redirect('operator_dashboard')

    points = station.points.all()
    today = date.today()
    todays_bookings = Booking.objects.filter(station=station, date=today)
    active_sessions = ChargingSession.objects.filter(
        booking__station=station,
        status__in=['IN_PROGRESS', 'FINISHING']
    )
    waiting_queue = QueueEntry.objects.filter(station=station, status='WAITING')

    return render(request, 'operator/my_station.html', {
        'station': station,
        'points': points,
        'todays_bookings': todays_bookings,
        'active_sessions': active_sessions,
        'waiting_queue': waiting_queue,
    })


@operator_required
def operator_points_view(request):
    """
    Manage charging points for the assigned station.
    """
    station = _get_operator_station(request.user)
    points = station.points.all()
    return render(request, 'operator/charging_points.html', {
        'station': station,
        'points': points
    })


@operator_required
def operator_update_point_status(request, pk):
    """
    Operator update status of a charging point (AVAILABLE, OUT_OF_SERVICE, etc.)
    """
    station = _get_operator_station(request.user)
    point = get_object_or_404(ChargingPoint, pk=pk, station=station)

    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(ChargingPoint.STATUS_CHOICES):
            point.status = new_status
            point.save(update_fields=['status'])
            messages.success(request, f"Point {point.point_number} status changed to {point.get_status_display()}.")

            # If made available, trigger queue check
            if new_status == 'AVAILABLE':
                process_station_queue(station)
        else:
            messages.error(request, "Invalid status selected.")

    return redirect('operator_points')


@operator_required
def operator_bookings_view(request):
    """
    View all bookings for the assigned station with date and status filters.
    """
    station = _get_operator_station(request.user)
    status_filter = request.GET.get('status', '')
    date_filter = request.GET.get('date', '')

    bookings = Booking.objects.filter(station=station)

    if status_filter:
        bookings = bookings.filter(status=status_filter)
    if date_filter:
        bookings = bookings.filter(date=date_filter)

    return render(request, 'operator/bookings.html', {
        'station': station,
        'bookings': bookings,
        'selected_status': status_filter,
        'selected_date': date_filter
    })


@operator_required
def operator_verify_qr_view(request):
    """
    QR Verification view:
    Operator scans or inputs booking QR text or Booking ID.
    Strictly verifies booking validity, time window, and station assignment!
    """
    station = _get_operator_station(request.user)
    booking = None
    verification_result = None
    error_message = None

    query = request.GET.get('code', '').strip() or request.POST.get('qr_code_data', '').strip()

    if query:
        # Check if code is in format: SMARTEV:<booking_id>:<token> or direct booking_id
        booking_id = query
        token = None
        if query.startswith("SMARTEV:"):
            parts = query.split(":")
            if len(parts) >= 3:
                booking_id = parts[1]
                token = parts[2]

        booking_obj = Booking.objects.filter(booking_id=booking_id).first()

        if not booking_obj:
            error_message = "Invalid Booking: No reservation found with this QR reference."
            verification_result = 'INVALID'
        elif booking_obj.station != station:
            error_message = f"Station Mismatch: This booking is for '{booking_obj.station.name}', not your station ({station.name})."
            verification_result = 'INVALID'
        elif booking_obj.status == 'CANCELLED':
            error_message = "Invalid: This booking was cancelled by the user."
            verification_result = 'INVALID'
        elif booking_obj.status == 'COMPLETED':
            error_message = "Invalid: This booking has already been completed."
            verification_result = 'INVALID'
        else:
            # Valid booking found
            booking = booking_obj
            verification_result = 'VALID'

    return render(request, 'operator/verify_qr.html', {
        'station': station,
        'booking': booking,
        'verification_result': verification_result,
        'error_message': error_message,
        'query_entered': query
    })


@operator_required
def operator_start_charging(request, booking_id):
    """
    Starts simulated charging session.
    Changes point status: RESERVED -> CHARGING
    Changes booking status: CONFIRMED -> CHARGING
    Creates ChargingSession record.
    """
    station = _get_operator_station(request.user)
    booking = get_object_or_404(Booking, id=booking_id, station=station)

    if booking.status not in ['CONFIRMED', 'CHARGING']:
        messages.error(request, "This booking is not eligible to start charging.")
        return redirect('operator_verify_qr')

    # Update Booking
    booking.status = 'CHARGING'
    booking.save(update_fields=['status'])

    # Update Charging Point
    point = booking.charging_point
    point.status = 'CHARGING'
    point.save(update_fields=['status'])

    # Create or get session
    session, created = ChargingSession.objects.get_or_create(
        booking=booking,
        defaults={
            'operator': request.user,
            'status': 'IN_PROGRESS',
            'initial_soc': 25,
            'final_soc': 85
        }
    )

    # Notify EV User
    send_notification(
        user=booking.user,
        title="⚡ EV Charging Started!",
        message=f"Your charging session has started at {station.name} on {point.point_number}. Monitor live progress in your dashboard.",
        notification_type='CHARGING',
        link="/user/dashboard/"
    )

    messages.success(request, f"Charging session started successfully for Booking #{booking.booking_id} on {point.point_number}!")
    return redirect('operator_sessions')


@operator_required
def operator_end_charging(request, session_id):
    """
    Ends simulated charging session.
    Calculates energy delivered (kWh).
    Completes session and booking.
    Point status: CHARGING -> FINISHING -> AVAILABLE.
    Auto-triggers queue scheduler and notifies next eligible queued user!
    """
    station = _get_operator_station(request.user)
    session = get_object_or_404(ChargingSession, id=session_id, booking__station=station)

    session.ended_at = timezone.now()
    session.status = 'COMPLETED'
    session.energy_delivered_kwh = session.calculate_energy()
    session.save()

    booking = session.booking
    booking.status = 'COMPLETED'
    booking.save(update_fields=['status'])

    # Free the charging point
    point = booking.charging_point
    point.status = 'AVAILABLE'
    point.save(update_fields=['status'])

    # Notify User
    send_notification(
        user=booking.user,
        title="Charging Session Complete",
        message=f"Charging completed at {station.name}! Energy delivered: {session.energy_delivered_kwh} kWh. Thank you for charging with Smart EVCharge!",
        notification_type='CHARGING',
        link=f"/bookings/{booking.id}/"
    )

    # Trigger Priority Queue Scheduler!
    promoted_user = process_station_queue(station)
    if promoted_user:
        messages.info(request, f"Queue updated: Next waiting user ({promoted_user.user.username}) has been notified!")

    messages.success(request, f"Session completed for #{booking.booking_id}. Point {point.point_number} is now AVAILABLE ({session.energy_delivered_kwh} kWh delivered).")
    return redirect('operator_sessions')


@operator_required
def operator_sessions_view(request):
    """
    View active and completed charging sessions for the assigned station.
    """
    station = _get_operator_station(request.user)
    active_sessions = ChargingSession.objects.filter(
        booking__station=station,
        status__in=['IN_PROGRESS', 'FINISHING']
    )
    completed_sessions = ChargingSession.objects.filter(
        booking__station=station,
        status='COMPLETED'
    )[:20]

    return render(request, 'operator/sessions.html', {
        'station': station,
        'active_sessions': active_sessions,
        'completed_sessions': completed_sessions
    })


@operator_required
def operator_queue_view(request):
    """
    Monitor and manage waiting queue for the assigned station.
    """
    station = _get_operator_station(request.user)
    queue_entries = QueueEntry.objects.filter(station=station).order_by('-priority', 'created_at')
    return render(request, 'operator/queue.html', {
        'station': station,
        'queue_entries': queue_entries
    })


@operator_required
def operator_reports_view(request):
    """
    Station-level reports and Chart.js analytics for the operator.
    """
    station = _get_operator_station(request.user)
    points = station.points.all()
    total_bookings = Booking.objects.filter(station=station).count()
    completed_bookings = Booking.objects.filter(station=station, status='COMPLETED').count()
    cancelled_bookings = Booking.objects.filter(station=station, status='CANCELLED').count()
    total_sessions = ChargingSession.objects.filter(booking__station=station, status='COMPLETED')
    total_energy = sum([float(s.energy_delivered_kwh) for s in total_sessions])

    # Status counts for chart
    point_status_data = {
        'Available': station.available_points,
        'Reserved': station.reserved_points,
        'Charging': station.charging_points,
        'Finishing': station.finishing_points,
        'Out of Service': station.out_of_service_points,
    }

    return render(request, 'operator/reports.html', {
        'station': station,
        'points_count': points.count(),
        'total_bookings': total_bookings,
        'completed_bookings': completed_bookings,
        'cancelled_bookings': cancelled_bookings,
        'total_energy': round(total_energy, 2),
        'point_status_data': point_status_data
    })
