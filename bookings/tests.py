from django.test import TestCase
from datetime import date, time, timedelta
from accounts.models import User
from stations.models import ChargingStation, ChargingPoint
from vehicles.models import Vehicle
from bookings.models import Booking

class BookingModelAndConflictTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='booking_user',
            email='booking@test.com',
            password='Password@123',
            role='USER'
        )
        self.station = ChargingStation.objects.create(
            name='Hub One',
            address='MG Road',
            city='Bengaluru',
            latitude=12.9716,
            longitude=77.5946,
            contact='+91 98888 77777',
            status='ACTIVE'
        )
        self.point = ChargingPoint.objects.create(
            station=self.station,
            point_number='Point A1',
            connector_type='CCS2',
            power_rating=50.0,
            status='AVAILABLE'
        )
        self.vehicle = Vehicle.objects.create(
            user=self.user,
            vehicle_number='KA-01-AB-1234',
            model='Tata Nexon EV',
            connector_type='CCS2',
            battery_capacity=40.5
        )

    def test_booking_creation_and_qr_generation(self):
        """Booking generates a unique EVB- prefix ID and QR code."""
        today = date.today() + timedelta(days=1)
        booking = Booking.objects.create(
            user=self.user,
            station=self.station,
            charging_point=self.point,
            vehicle=self.vehicle,
            date=today,
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            status='CONFIRMED'
        )
        self.assertTrue(booking.booking_id.startswith('EVB-'))
        self.assertTrue(bool(booking.qr_code))
        self.assertTrue(bool(booking.qr_token))

    def test_interval_conflict_detection(self):
        """Booking.check_conflict correctly detects overlapping time intervals."""
        today = date.today() + timedelta(days=1)
        Booking.objects.create(
            user=self.user,
            station=self.station,
            charging_point=self.point,
            vehicle=self.vehicle,
            date=today,
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            status='CONFIRMED'
        )

        # 1. Overlapping case: 10:30 to 11:30 (starts before previous ends)
        self.assertTrue(Booking.check_conflict(
            charging_point=self.point,
            check_date=today,
            start_t=time(10, 30),
            end_t=time(11, 30)
        ))

        # 2. Overlapping case: 09:30 to 10:30 (ends after previous starts)
        self.assertTrue(Booking.check_conflict(
            charging_point=self.point,
            check_date=today,
            start_t=time(9, 30),
            end_t=time(10, 30)
        ))

        # 3. Inside case: 10:15 to 10:45
        self.assertTrue(Booking.check_conflict(
            charging_point=self.point,
            check_date=today,
            start_t=time(10, 15),
            end_t=time(10, 45)
        ))

        # 4. Adjacent non-overlapping case: 11:00 to 12:00 -> NO conflict
        self.assertFalse(Booking.check_conflict(
            charging_point=self.point,
            check_date=today,
            start_t=time(11, 0),
            end_t=time(12, 0)
        ))

        # 5. Earlier non-overlapping case: 08:00 to 09:00 -> NO conflict
        self.assertFalse(Booking.check_conflict(
            charging_point=self.point,
            check_date=today,
            start_t=time(8, 0),
            end_t=time(9, 0)
        ))
