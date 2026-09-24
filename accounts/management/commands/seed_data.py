import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from accounts.models import User, OperatorProfile
from stations.models import ChargingStation, ChargingPoint
from vehicles.models import Vehicle
from bookings.models import Booking
from charging.models import ChargingSession
from queue_management.models import QueueEntry
from notifications.utils import send_notification

class Command(BaseCommand):
    help = "Seeds database with initial demo data for MCA project demonstration"

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.NOTICE("Beginning Smart EVCharge database seeding..."))

        # 1. Create EXACTLY ONE System Admin
        admin_user = User.objects.filter(role='ADMIN').first()
        if not admin_user:
            admin_user = User(
                username='admin',
                email='admin@smartev.com',
                first_name='System',
                last_name='Administrator',
                role='ADMIN',
                is_staff=True,
                is_superuser=True
            )
            admin_user.set_password('Admin@123')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS("Created System Admin account: admin / Admin@123"))
        else:
            self.stdout.write(self.style.NOTICE(f"System Admin already exists ({admin_user.username}). Single-admin rule verified."))

        # 2. Create Sample Charging Stations
        stations_data = [
            {
                'name': 'EcoCharge Metro Hub',
                'address': 'MG Road Metro Station, Central Boulevard',
                'city': 'Bengaluru',
                'latitude': 12.975200,
                'longitude': 77.608000,
                'contact': '+91 98450 11223',
                'operating_hours': '24/7 (Always Open)',
                'description': 'Flagship ultra-fast charging hub with waiting lounge, coffee shop, and tyre pressure station.',
                'status': 'ACTIVE'
            },
            {
                'name': 'GreenCharge Station',
                'address': 'Koramangala 5th Block, 80 Feet Road',
                'city': 'Bengaluru',
                'latitude': 12.935200,
                'longitude': 77.624500,
                'contact': '+91 98450 44556',
                'operating_hours': '06:00 AM - 11:30 PM',
                'description': 'Solar canopy equipped urban charging facility situated near shopping complex.',
                'status': 'ACTIVE'
            },
            {
                'name': 'FastCharge Hub',
                'address': 'Whitefield Main Road, ITPL Tech Park',
                'city': 'Bengaluru',
                'latitude': 12.986400,
                'longitude': 77.738000,
                'contact': '+91 98450 77889',
                'operating_hours': '24/7 (Always Open)',
                'description': 'High-power multi-standard charging bays tailored for commercial & private EVs.',
                'status': 'ACTIVE'
            }
        ]

        created_stations = {}
        for s_data in stations_data:
            station, created = ChargingStation.objects.get_or_create(
                name=s_data['name'],
                defaults=s_data
            )
            created_stations[station.name] = station
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created Station: {station.name}"))

        # 3. Create Charging Points for each station
        points_config = [
            # EcoCharge Metro Hub
            ('EcoCharge Metro Hub', 'Slot 1 (CCS2 Fast)', 'CCS2', 50.0, 'FAST_DC', 'AVAILABLE'),
            ('EcoCharge Metro Hub', 'Slot 2 (CCS2 Rapid)', 'CCS2', 60.0, 'RAPID_DC', 'CHARGING'),
            ('EcoCharge Metro Hub', 'Slot 3 (Type 2 Normal)', 'TYPE2', 22.0, 'STANDARD_AC', 'RESERVED'),
            ('EcoCharge Metro Hub', 'Slot 4 (CCS2 Fast)', 'CCS2', 50.0, 'FAST_DC', 'AVAILABLE'),

            # GreenCharge Station
            ('GreenCharge Station', 'Slot 1 (CCS2 Fast)', 'CCS2', 50.0, 'FAST_DC', 'AVAILABLE'),
            ('GreenCharge Station', 'Slot 2 (CHAdeMO DC)', 'CHADEMO', 50.0, 'FAST_DC', 'AVAILABLE'),
            ('GreenCharge Station', 'Slot 3 (Type 2 AC)', 'TYPE2', 11.0, 'STANDARD_AC', 'AVAILABLE'),

            # FastCharge Hub
            ('FastCharge Hub', 'Bay 1 (CCS2 Rapid)', 'CCS2', 120.0, 'RAPID_DC', 'AVAILABLE'),
            ('FastCharge Hub', 'Bay 2 (CCS2 Fast)', 'CCS2', 50.0, 'FAST_DC', 'AVAILABLE'),
            ('FastCharge Hub', 'Bay 3 (GB/T Fast)', 'GBT', 60.0, 'FAST_DC', 'AVAILABLE'),
        ]

        created_points = {}
        for station_name, pt_num, conn, pwr, spd, st in points_config:
            station = created_stations.get(station_name)
            if station:
                pt, created = ChargingPoint.objects.get_or_create(
                    station=station,
                    point_number=pt_num,
                    defaults={
                        'connector_type': conn,
                        'power_rating': pwr,
                        'charging_speed': spd,
                        'status': st
                    }
                )
                created_points[(station_name, pt_num)] = pt

        self.stdout.write(self.style.SUCCESS(f"Configured {len(points_config)} charging points with diverse connectors."))

        # 4. Create Station Operators (Admin-delegated only)
        operators_data = [
            {
                'username': 'operator1',
                'email': 'operator1@smartev.com',
                'name': 'Ramesh Kumar',
                'phone': '+91 98111 22334',
                'password': 'Operator@123',
                'station': created_stations.get('EcoCharge Metro Hub')
            },
            {
                'username': 'operator2',
                'email': 'operator2@smartev.com',
                'name': 'Suresh Nair',
                'phone': '+91 98222 33445',
                'password': 'Operator@123',
                'station': created_stations.get('GreenCharge Station')
            }
        ]

        for op_info in operators_data:
            op_user = User.objects.filter(username=op_info['username']).first()
            if not op_user:
                op_user = User.objects.create_user(
                    username=op_info['username'],
                    email=op_info['email'],
                    first_name=op_info['name'],
                    phone=op_info['phone'],
                    role='OPERATOR'
                )
                op_user.set_password(op_info['password'])
                op_user.save()
                OperatorProfile.objects.create(
                    user=op_user,
                    assigned_station=op_info['station'],
                    status='ACTIVE'
                )
                self.stdout.write(self.style.SUCCESS(f"Created Operator: {op_info['username']} / Operator@123 -> {op_info['station'].name}"))

        # 5. Create Sample EV Users
        user1 = User.objects.filter(username='user1').first()
        if not user1:
            user1 = User.objects.create_user(
                username='user1',
                email='user1@gmail.com',
                first_name='Rahul Sharma',
                phone='+91 98765 00001',
                role='USER'
            )
            user1.set_password('User@123')
            user1.save()
            self.stdout.write(self.style.SUCCESS("Created EV User: user1 / User@123"))

        user2 = User.objects.filter(username='user2').first()
        if not user2:
            user2 = User.objects.create_user(
                username='user2',
                email='user2@gmail.com',
                first_name='Priya Patel',
                phone='+91 98765 00002',
                role='USER'
            )
            user2.set_password('User@123')
            user2.save()
            self.stdout.write(self.style.SUCCESS("Created EV User: user2 / User@123"))

        # 6. Create Vehicles for users
        v1, _ = Vehicle.objects.get_or_create(
            user=user1,
            vehicle_number='KA-01-EV-2024',
            defaults={
                'model': 'Tata Nexon EV Max',
                'connector_type': 'CCS2',
                'battery_capacity': 40.5,
                'nickname': 'Daily Nexon'
            }
        )
        v2, _ = Vehicle.objects.get_or_create(
            user=user1,
            vehicle_number='KA-05-EV-9999',
            defaults={
                'model': 'Hyundai Ioniq 5',
                'connector_type': 'CCS2',
                'battery_capacity': 72.6,
                'nickname': 'Family Ioniq'
            }
        )
        v3, _ = Vehicle.objects.get_or_create(
            user=user2,
            vehicle_number='KA-03-EV-5555',
            defaults={
                'model': 'MG ZS EV',
                'connector_type': 'CCS2',
                'battery_capacity': 50.3,
                'nickname': 'Commuter EV'
            }
        )

        # 7. Create Sample Bookings & Charging Sessions
        today = datetime.date.today()
        station_eco = created_stations.get('EcoCharge Metro Hub')
        slot2 = created_points.get(('EcoCharge Metro Hub', 'Slot 2 (CCS2 Rapid)'))
        slot3 = created_points.get(('EcoCharge Metro Hub', 'Slot 3 (Type 2 Normal)'))

        if station_eco and slot2:
            # Active charging booking
            b_active, created = Booking.objects.get_or_create(
                user=user1,
                station=station_eco,
                charging_point=slot2,
                vehicle=v1,
                date=today,
                defaults={
                    'start_time': datetime.time(10, 0),
                    'end_time': datetime.time(11, 0),
                    'duration_minutes': 60,
                    'status': 'CHARGING'
                }
            )
            if created:
                operator_ramesh = User.objects.filter(username='operator1').first()
                ChargingSession.objects.create(
                    booking=b_active,
                    operator=operator_ramesh,
                    status='IN_PROGRESS',
                    initial_soc=20,
                    final_soc=80
                )
                self.stdout.write(self.style.SUCCESS(f"Created active charging session for Booking #{b_active.booking_id}"))

        if station_eco and slot3:
            # Upcoming reserved booking
            b_reserved, _ = Booking.objects.get_or_create(
                user=user2,
                station=station_eco,
                charging_point=slot3,
                vehicle=v3,
                date=today,
                defaults={
                    'start_time': datetime.time(14, 0),
                    'end_time': datetime.time(15, 0),
                    'duration_minutes': 60,
                    'status': 'CONFIRMED'
                }
            )

        # 8. Create Waiting Queue sample
        if station_eco:
            QueueEntry.objects.get_or_create(
                user=user2,
                vehicle=v3,
                station=station_eco,
                requested_date=today,
                requested_time=datetime.time(10, 30),
                defaults={
                    'duration_minutes': 60,
                    'preferred_connector': 'CCS2',
                    'queue_position': 1,
                    'priority': 1,
                    'status': 'WAITING'
                }
            )
            self.stdout.write(self.style.SUCCESS("Created demo Queue entry (#1 in line at EcoCharge Metro Hub)"))

        # 9. Create Notifications
        send_notification(
            user=user1,
            title="⚡ EV Charging Started!",
            message="Your Tata Nexon EV Max is currently charging at EcoCharge Metro Hub (Slot 2). Live progress is available on your dashboard.",
            notification_type='CHARGING',
            link="/user/dashboard/"
        )
        send_notification(
            user=user2,
            title="Slot Reservation Confirmed",
            message="Your reservation at EcoCharge Metro Hub (Slot 3) has been confirmed. Scan your QR upon arrival.",
            notification_type='BOOKING',
            link="/bookings/my-bookings/"
        )

        self.stdout.write(self.style.SUCCESS("\nDemo seed data successfully loaded into Smart EVCharge system!"))
