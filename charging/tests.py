from django.test import TestCase, Client
from django.urls import reverse
from datetime import date, time, timedelta
from accounts.models import User, OperatorProfile
from stations.models import ChargingStation, ChargingPoint
from vehicles.models import Vehicle
from bookings.models import Booking
from charging.models import ChargingSession
from queue_management.models import QueueEntry

class ChargingLifecycleTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Stations
        self.station1 = ChargingStation.objects.create(name='Station Alpha', address='Road 1', city='Bengaluru', latitude=12.9, longitude=77.6, contact='111', status='ACTIVE')
        self.station2 = ChargingStation.objects.create(name='Station Beta', address='Road 2', city='Bengaluru', latitude=12.8, longitude=77.5, contact='222', status='ACTIVE')

        # Operator assigned to Station Alpha
        self.operator = User.objects.create_user(username='op_alpha', email='op1@test.com', password='Password@123', role='OPERATOR')
        self.profile = OperatorProfile.objects.create(user=self.operator, assigned_station=self.station1, status='ACTIVE')

        # EV User & Vehicle
        self.user = User.objects.create_user(username='ev_driver', email='driver@test.com', password='Password@123', role='USER')
        self.vehicle = Vehicle.objects.create(user=self.user, vehicle_number='KA-04-EV-1000', model='Tata Tiago EV', connector_type='CCS2', battery_capacity=24.0)

        # Points
        self.point1 = ChargingPoint.objects.create(station=self.station1, point_number='Alpha Bay 1', connector_type='CCS2', power_rating=50.0, status='RESERVED')
        self.point2 = ChargingPoint.objects.create(station=self.station2, point_number='Beta Bay 1', connector_type='CCS2', power_rating=50.0, status='RESERVED')

        # Booking at Station Alpha
        today = date.today()
        self.booking1 = Booking.objects.create(
            user=self.user,
            station=self.station1,
            charging_point=self.point1,
            vehicle=self.vehicle,
            date=today,
            start_time=time(14, 0),
            end_time=time(15, 0),
            status='CONFIRMED'
        )

        # Booking at Station Beta (different station)
        self.booking2 = Booking.objects.create(
            user=self.user,
            station=self.station2,
            charging_point=self.point2,
            vehicle=self.vehicle,
            date=today,
            start_time=time(14, 0),
            end_time=time(15, 0),
            status='CONFIRMED'
        )

    def test_qr_verification_valid(self):
        """Operator can verify valid booking QR code for assigned station."""
        self.client.login(username='op_alpha', password='Password@123')
        qr_string = f"SMARTEV:{self.booking1.booking_id}:{self.booking1.qr_token}"
        response = self.client.get(reverse('operator_verify_qr') + f"?code={qr_string}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['verification_result'], 'VALID')

    def test_qr_verification_station_mismatch(self):
        """Operator cannot verify a booking from another station."""
        self.client.login(username='op_alpha', password='Password@123')
        qr_string = f"SMARTEV:{self.booking2.booking_id}:{self.booking2.qr_token}"
        response = self.client.get(reverse('operator_verify_qr') + f"?code={qr_string}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['verification_result'], 'INVALID')
        self.assertIn("Station Mismatch", response.context['error_message'])

    def test_charging_lifecycle_start_and_end(self):
        """Complete lifecycle: start charging, transition point, complete session and free point."""
        self.client.login(username='op_alpha', password='Password@123')

        # 1. Start Charging
        start_resp = self.client.post(reverse('operator_start_charging', args=[self.booking1.id]))
        self.assertEqual(start_resp.status_code, 302)

        self.booking1.refresh_from_db()
        self.point1.refresh_from_db()
        self.assertEqual(self.booking1.status, 'CHARGING')
        self.assertEqual(self.point1.status, 'CHARGING')

        session = ChargingSession.objects.filter(booking=self.booking1).first()
        self.assertIsNotNone(session)
        self.assertEqual(session.status, 'IN_PROGRESS')

        # 2. Add a waiting queue user to verify auto-promotion on completion
        q_user = User.objects.create_user(username='q_waiter', email='waiter@test.com', password='Password@123', role='USER')
        q_vehicle = Vehicle.objects.create(user=q_user, vehicle_number='KA-05-EV-8888', model='Tata Tigor EV', connector_type='CCS2', battery_capacity=26.0)
        q_entry = QueueEntry.objects.create(
            user=q_user,
            vehicle=q_vehicle,
            station=self.station1,
            requested_date=date.today(),
            requested_time=time(15, 0),
            preferred_connector='CCS2',
            status='WAITING'
        )

        # 3. End Charging
        end_resp = self.client.post(reverse('operator_end_charging', args=[session.id]))
        self.assertEqual(end_resp.status_code, 302)

        session.refresh_from_db()
        self.booking1.refresh_from_db()
        self.point1.refresh_from_db()

        self.assertEqual(session.status, 'COMPLETED')
        self.assertEqual(self.booking1.status, 'COMPLETED')
        self.assertEqual(self.point1.status, 'AVAILABLE')
        self.assertGreater(session.energy_delivered_kwh, 0)

        # 4. Verify queued user was promoted to NOTIFIED
        q_entry.refresh_from_db()
        self.assertEqual(q_entry.status, 'NOTIFIED')
