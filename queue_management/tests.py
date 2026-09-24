from django.test import TestCase
from datetime import date, time
from accounts.models import User
from stations.models import ChargingStation, ChargingPoint
from vehicles.models import Vehicle
from queue_management.models import QueueEntry
from queue_management.scheduler import process_station_queue, recalculate_queue_positions
from notifications.models import Notification

class QueueSchedulerTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='q_user1', email='q1@test.com', password='Password@123', role='USER')
        self.user2 = User.objects.create_user(username='q_user2', email='q2@test.com', password='Password@123', role='USER')
        self.station = ChargingStation.objects.create(
            name='Express Hub',
            address='Indiranagar',
            city='Bengaluru',
            latitude=12.9784,
            longitude=77.6408,
            contact='+91 97777 66666',
            status='ACTIVE'
        )
        self.point = ChargingPoint.objects.create(
            station=self.station,
            point_number='Bay 1',
            connector_type='CCS2',
            power_rating=60.0,
            status='CHARGING' # currently occupied
        )
        self.vehicle1 = Vehicle.objects.create(user=self.user1, vehicle_number='KA-01-Q1', model='MG ZS EV', connector_type='CCS2', battery_capacity=50.3)
        self.vehicle2 = Vehicle.objects.create(user=self.user2, vehicle_number='KA-01-Q2', model='Hyundai Kona', connector_type='CCS2', battery_capacity=39.2)

    def test_queue_registration_and_positions(self):
        """Queue entries are sequenced properly in priority FIFO order."""
        today = date.today()
        q1 = QueueEntry.objects.create(
            user=self.user1,
            vehicle=self.vehicle1,
            station=self.station,
            requested_date=today,
            requested_time=time(11, 0),
            preferred_connector='CCS2',
            priority=1,
            queue_position=1
        )
        q2 = QueueEntry.objects.create(
            user=self.user2,
            vehicle=self.vehicle2,
            station=self.station,
            requested_date=today,
            requested_time=time(11, 30),
            preferred_connector='CCS2',
            priority=1,
            queue_position=2
        )

        recalculate_queue_positions(self.station)
        q1.refresh_from_db()
        q2.refresh_from_db()
        self.assertEqual(q1.queue_position, 1)
        self.assertEqual(q2.queue_position, 2)

    def test_event_driven_auto_promotion(self):
        """When a point becomes AVAILABLE, process_station_queue notifies the top waiting user."""
        today = date.today()
        q1 = QueueEntry.objects.create(
            user=self.user1,
            vehicle=self.vehicle1,
            station=self.station,
            requested_date=today,
            requested_time=time(11, 0),
            preferred_connector='CCS2',
            priority=1,
            status='WAITING'
        )

        # Free the charging point
        self.point.status = 'AVAILABLE'
        self.point.save()

        # Trigger scheduler
        promoted = process_station_queue(self.station)
        self.assertIsNotNone(promoted)
        self.assertEqual(promoted.id, q1.id)

        q1.refresh_from_db()
        self.assertEqual(q1.status, 'NOTIFIED')

        # Check notification sent to user
        notif = Notification.objects.filter(user=self.user1, notification_type='QUEUE').first()
        self.assertIsNotNone(notif)
        self.assertIn("Slot Available", notif.title)
