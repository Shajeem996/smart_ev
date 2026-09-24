from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from accounts.decorators import ev_user_required
from .models import Booking
from .forms import BookingForm
from stations.models import ChargingStation, ChargingPoint
from vehicles.models import Vehicle
from queue_management.models import QueueEntry
from queue_management.scheduler import process_station_queue
from notifications.utils import send_notification

@ev_user_required
def book_slot_view(request):
    """
    EV User Slot Booking view with real-time interval scheduling & conflict prevention.
    """
    user_vehicles = Vehicle.objects.filter(user=request.user)
    if not user_vehicles.exists():
        messages.warning(request, "Please add your EV vehicle first before reserving a charging slot.")
        return redirect('vehicle_add')

    # Pre-selection from query params (e.g. from Map or Station Details or Queue promotion)
    initial_data = {}
    station_id = request.GET.get('station')
    point_id = request.GET.get('point')
    queue_id = request.GET.get('queue_id')

    if station_id:
        initial_data['station'] = station_id
    if point_id:
        initial_data['charging_point'] = point_id

    if request.method == 'POST':
        form = BookingForm(request.user, request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.user = request.user
            booking.end_time = form.cleaned_data['end_time']
            booking.status = 'CONFIRMED'
            booking.save()

            # Update charging point status to RESERVED
            point = booking.charging_point
            if point.status == 'AVAILABLE':
                point.status = 'RESERVED'
                point.save(update_fields=['status'])

            # If promoted from a queue entry, mark queue entry as ASSIGNED
            if queue_id:
                queue_entry = QueueEntry.objects.filter(id=queue_id, user=request.user).first()
                if queue_entry:
                    queue_entry.status = 'ASSIGNED'
                    queue_entry.save(update_fields=['status'])

            # Send Notification to User
            send_notification(
                user=request.user,
                title="Booking Confirmed! Reference #" + booking.booking_id,
                message=f"Your charging slot at {booking.station.name} ({booking.charging_point.point_number}) is reserved for {booking.date} from {booking.start_time.strftime('%I:%M %p')} to {booking.end_time.strftime('%I:%M %p')}.",
                notification_type='BOOKING',
                link=f"/bookings/{booking.id}/"
            )

            # Notify Assigned Station Operators
            for operator in booking.station.assigned_operators.filter(status='ACTIVE'):
                send_notification(
                    user=operator.user,
                    title="New Booking Reserved",
                    message=f"User {request.user.get_full_name() or request.user.username} reserved {booking.charging_point.point_number} on {booking.date} at {booking.start_time.strftime('%I:%M %p')}.",
                    notification_type='OPERATOR',
                    link="/operator/bookings/"
                )

            messages.success(request, f"Booking #{booking.booking_id} confirmed successfully! Your verification QR Code is ready.")
            return redirect('booking_detail', pk=booking.id)
    else:
        form = BookingForm(request.user, initial=initial_data)

    stations = ChargingStation.objects.filter(status='ACTIVE')
    return render(request, 'user/book_slot.html', {
        'form': form,
        'stations': stations,
        'vehicles': user_vehicles
    })


@ev_user_required
def booking_detail_view(request, pk):
    """
    Shows full booking details, QR code, charging point specs, and actions.
    """
    booking = get_object_or_404(Booking, pk=pk, user=request.user)
    return render(request, 'user/booking_detail.html', {'booking': booking})


@ev_user_required
def my_bookings_view(request):
    """
    List of user's bookings (Active, Upcoming, Completed, Cancelled).
    """
    bookings = Booking.objects.filter(user=request.user).order_by('-date', '-start_time')
    return render(request, 'user/my_bookings.html', {'bookings': bookings})


@ev_user_required
def cancel_booking_view(request, pk):
    """
    Allows user to cancel their booking if it has not started yet.
    Frees the charging point and triggers queue recalculation.
    """
    booking = get_object_or_404(Booking, pk=pk, user=request.user)
    if booking.status in ['COMPLETED', 'CANCELLED']:
        messages.warning(request, "This booking cannot be cancelled.")
        return redirect('booking_detail', pk=booking.id)

    if request.method == 'POST':
        booking.status = 'CANCELLED'
        booking.save(update_fields=['status'])

        # Free charging point if currently reserved
        point = booking.charging_point
        if point.status == 'RESERVED':
            point.status = 'AVAILABLE'
            point.save(update_fields=['status'])

        # Send cancellation notification
        send_notification(
            user=request.user,
            title="Booking Cancelled",
            message=f"Booking #{booking.booking_id} at {booking.station.name} has been cancelled.",
            notification_type='BOOKING',
            link=f"/bookings/{booking.id}/"
        )

        # Trigger smart queue recalculation for this station!
        process_station_queue(booking.station)

        messages.info(request, f"Booking #{booking.booking_id} has been cancelled.")
        return redirect('my_bookings')

    return render(request, 'user/booking_confirm_cancel.html', {'booking': booking})
