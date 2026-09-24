from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from accounts.decorators import ev_user_required
from .models import QueueEntry
from .forms import QueueJoinForm
from .scheduler import recalculate_queue_positions
from vehicles.models import Vehicle
from stations.models import ChargingStation
from notifications.utils import send_notification

@ev_user_required
def user_queue_view(request):
    """
    Shows the user's active and historical queue entries with real-time queue position.
    """
    active_queues = QueueEntry.objects.filter(
        user=request.user,
        status__in=['WAITING', 'NOTIFIED']
    ).order_by('-created_at')

    past_queues = QueueEntry.objects.filter(
        user=request.user
    ).exclude(status__in=['WAITING', 'NOTIFIED']).order_by('-created_at')

    return render(request, 'user/queue.html', {
        'active_queues': active_queues,
        'past_queues': past_queues
    })


@ev_user_required
def join_queue_view(request):
    """
    Join station waiting queue when charging points are fully booked.
    """
    user_vehicles = Vehicle.objects.filter(user=request.user)
    if not user_vehicles.exists():
        messages.warning(request, "Please add your EV vehicle first before joining a waiting queue.")
        return redirect('vehicle_add')

    initial_data = {}
    station_id = request.GET.get('station')
    if station_id:
        initial_data['station'] = station_id

    if request.method == 'POST':
        form = QueueJoinForm(request.user, request.POST)
        if form.is_valid():
            station = form.cleaned_data['station']
            # Check if user already waiting in queue for this station
            already_waiting = QueueEntry.objects.filter(
                user=request.user,
                station=station,
                status='WAITING'
            ).exists()

            if already_waiting:
                messages.warning(request, f"You are already in the waiting queue for {station.name}.")
                return redirect('user_queue')

            queue_entry = form.save(commit=False)
            queue_entry.user = request.user
            # Position is current waiting count + 1
            existing_count = QueueEntry.objects.filter(station=station, status='WAITING').count()
            queue_entry.queue_position = existing_count + 1
            queue_entry.status = 'WAITING'
            queue_entry.save()

            recalculate_queue_positions(station)

            # Send Notification
            send_notification(
                user=request.user,
                title="Joined Waiting Queue",
                message=f"You are currently #{queue_entry.queue_position} in the queue at {station.name}. We will notify you instantly when a slot opens.",
                notification_type='QUEUE',
                link="/queue/"
            )

            messages.success(request, f"You have joined the queue at {station.name}! Your position is #{queue_entry.queue_position}.")
            return redirect('user_queue')
    else:
        form = QueueJoinForm(request.user, initial=initial_data)

    stations = ChargingStation.objects.filter(status='ACTIVE')
    return render(request, 'user/join_queue.html', {'form': form, 'stations': stations})


@ev_user_required
def cancel_queue_view(request, pk):
    """
    Cancel waiting queue spot and recalculate queue order.
    """
    queue_entry = get_object_or_404(QueueEntry, pk=pk, user=request.user)
    station = queue_entry.station
    queue_entry.status = 'CANCELLED'
    queue_entry.save(update_fields=['status'])

    # Recalculate positions for remaining entries
    recalculate_queue_positions(station)

    messages.info(request, "You have exited the waiting queue.")
    return redirect('user_queue')
