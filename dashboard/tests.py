from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User, OperatorProfile
from stations.models import ChargingStation

class DashboardAndAdminTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_user(username='superadmin', email='super@test.com', password='Password@123', role='ADMIN')
        self.station = ChargingStation.objects.create(
            name='Alpha Station',
            address='Koramangala',
            city='Bengaluru',
            latitude=12.93,
            longitude=77.62,
            contact='1234567890',
            status='ACTIVE'
        )
        self.operator = User.objects.create_user(username='op_dash', email='opdash@test.com', password='Password@123', role='OPERATOR')
        self.profile = OperatorProfile.objects.create(user=self.operator, assigned_station=self.station, status='ACTIVE')
        self.user = User.objects.create_user(username='user_dash', email='udash@test.com', password='Password@123', role='USER')

    def test_landing_page(self):
        """Landing page renders successfully for public visitors."""
        response = self.client.get(reverse('landing'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Smart EVCharge')

    def test_user_dashboard(self):
        """EV User dashboard loads with personal metrics."""
        self.client.login(username='user_dash', password='Password@123')
        response = self.client.get(reverse('user_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Welcome, user_dash!')

    def test_operator_dashboard(self):
        """Operator dashboard loads with assigned station data."""
        self.client.login(username='op_dash', password='Password@123')
        response = self.client.get(reverse('operator_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Alpha Station')

    def test_admin_dashboard_and_station_creation(self):
        """Admin dashboard loads and admin can add a new charging station."""
        self.client.login(username='superadmin', password='Password@123')
        resp = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(resp.status_code, 200)

        # Admin creates new station
        create_resp = self.client.post(reverse('admin_station_create'), {
            'name': 'New Tech Hub Station',
            'address': 'Electronic City',
            'city': 'Bengaluru',
            'latitude': '12.8452',
            'longitude': '77.6602',
            'contact': '+91 91111 22222',
            'operating_hours': '24/7 (Always Open)',
            'status': 'ACTIVE',
            'description': 'Modern hub'
        })
        self.assertEqual(create_resp.status_code, 302)
        self.assertTrue(ChargingStation.objects.filter(name='New Tech Hub Station').exists())
