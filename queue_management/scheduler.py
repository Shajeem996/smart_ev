"""
Smart EV Scheduling & Priority Queue Module.

Concepts demonstrated for MCA Project:
- Interval Scheduling Algorithm: checks for overlapping intervals [start, end)
- Priority Queue (FIFO with Priority Boost): sorts by priority desc, created_at asc
- Event-driven auto-promotion: triggered when charging sessions end or bookings are cancelled
"""

from datetime import datetime, timedelta, time
from django.utils import timezone
from stations.models import ChargingPoint
from bookings.models import Booking
from notifications.utils import send_notification

def is_point_available_for_interval(charging_point, check_date, start_time, end_time, exclude_booking_id=None):
    """
    Checks if a given charging point has any overlapping bookings or is out of service.
    """
    if charging_point.status == 'OUT_OF_SERVICE':
        return False

    # Check interval overlap
    has_conflict = Booking.check_conflict(
        charging_point=charging_point,
        check_date=check_date,
        start_t=start_time,
        end_t=end_time,
        exclude_id=exclude_booking_id
    )
    return not has_conflict


def find_best_charging_point(station, check_date, start_time, end_time, connector_type=None):
    """
    Finds the first available charging point that satisfies:
    1. Belongs to the requested station
    2. Matches the vehicle's connector type (if specified)
    3. Has status != OUT_OF_SERVICE
    4. Has no conflicting bookings during [start_time, end_time)
    """
    points = station.points.exclude(status='OUT_OF_SERVICE')
    if connector_type:
        points = points.filter(connector_type=connector_type)

    for point in points:
        if is_point_available_for_interval(point, check_date, start_time, end_time):
            return point
    return None


def recalculate_queue_positions(station):
    """
    Updates the queue_position integer (1, 2, 3...) for all WAITING entries at a station.
    Follows priority queue ordering (-priority, created_at).
    """
    from .models import QueueEntry
    waiting_entries = QueueEntry.objects.filter(
        station=station,
        status='WAITING'
    ).order_by('-priority', 'created_at')

    for idx, entry in enumerate(waiting_entries, start=1):
        if entry.queue_position != idx:
            entry.queue_position = idx
            entry.save(update_fields=['queue_position'])


def process_station_queue(station):
    """
    Event-driven Queue Scheduler:
    Triggered when a charging point becomes AVAILABLE.
    Inspects waiting users, assigns or notifies the top eligible queued user.
    """
    from .models import QueueEntry
    
    # 1. Update queue order positions
    recalculate_queue_positions(station)

    # 2. Get top waiting users
    waiting_entries = QueueEntry.objects.filter(
        station=station,
        status='WAITING'
    ).order_by('-priority', 'created_at')

    if not waiting_entries.exists():
        return None

    # Check station's currently available physical points
    available_points = station.points.filter(status='AVAILABLE')
    if not available_points.exists():
        return None

    for entry in waiting_entries:
        # Check if an available point matches connector type
        matching_point = available_points.filter(connector_type=entry.preferred_connector).first()
        if not matching_point:
            # If no strict match, check if any available point can serve
            matching_point = available_points.first()

        if matching_point:
            # Promote this queued user
            entry.status = 'NOTIFIED'
            entry.notified_at = timezone.now()
            entry.save(update_fields=['status', 'notified_at'])

            # Send Notification to User
            send_notification(
                user=entry.user,
                title="⚡ Slot Available at " + station.name,
                message=f"Good news! Charging slot ({matching_point.point_number}) is now ready for your vehicle ({entry.vehicle.model}). Click here to confirm and reserve your slot immediately!",
                notification_type='QUEUE',
                link=f"/book/?station={station.id}&point={matching_point.id}&queue_id={entry.id}"
            )

            # Recalculate remaining queue
            recalculate_queue_positions(station)
            return entry

    return None
