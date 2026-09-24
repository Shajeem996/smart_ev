from django.test import TestCase, Client
from django.urls import reverse
from django.core.exceptions import ValidationError
from accounts.models import User, OperatorProfile
from stations.models import ChargingStation

class AuthenticationAndRoleTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Admin
        self.admin = User.objects.create_user(
            username='admin_test',
            email='admin@test.com',
            password='Password@123',
            role='ADMIN'
        )
        # Station
        self.station = ChargingStation.objects.create(
            name='Test Central Station',
            address='123 Main St',
            city='Bengaluru',
            latitude=12.9716,
            longitude=77.5946,
            contact='+91 99999 88888',
            status='ACTIVE'
        )
        # Operator
        self.operator = User.objects.create_user(
            username='operator_test',
            email='op@test.com',
            password='Password@123',
            role='OPERATOR'
        )
        self.operator_profile = OperatorProfile.objects.create(
            user=self.operator,
            assigned_station=self.station,
            status='ACTIVE'
        )
        # EV User
        self.user = User.objects.create_user(
            username='user_test',
            email='user@test.com',
            password='Password@123',
            role='USER'
        )

    def test_single_admin_enforcement(self):
        """Strict rule: An application-level ValidationError is raised if a 2nd admin is created."""
        second_admin = User(
            username='admin2',
            email='admin2@test.com',
            role='ADMIN'
        )
        second_admin.set_password('Password@123')
        with self.assertRaises(ValidationError):
            second_admin.clean()

    def test_user_registration(self):
        """EV User registration creates an account with role='USER'."""
        response = self.client.post(reverse('register'), {
            'first_name': 'New EV Driver',
            'email': 'driver@test.com',
            'phone': '+91 91234 56789',
            'password': 'StrongPassword@123',
            'confirm_password': 'StrongPassword@123',
        })
        self.assertEqual(response.status_code, 302)
        new_user = User.objects.get(email='driver@test.com')
        self.assertEqual(new_user.role, 'USER')
        self.assertTrue(new_user.is_ev_user)

    def test_login_and_role_redirect(self):
        """User is redirected to their specific dashboard based on role."""
        # 1. EV User Login
        self.client.login(username='user_test', password='Password@123')
        resp = self.client.get(reverse('role_redirect'))
        self.assertRedirects(resp, reverse('user_dashboard'))
        self.client.logout()

        # 2. Operator Login
        self.client.login(username='operator_test', password='Password@123')
        resp = self.client.get(reverse('role_redirect'))
        self.assertRedirects(resp, reverse('operator_dashboard'))
        self.client.logout()

        # 3. Admin Login
        self.client.login(username='admin_test', password='Password@123')
        resp = self.client.get(reverse('role_redirect'))
        self.assertRedirects(resp, reverse('admin_dashboard'))
        self.client.logout()

    def test_role_access_security(self):
        """EV Users cannot access Admin Panel or Operator areas."""
        self.client.login(username='user_test', password='Password@123')
        
        # User tries to access Admin Dashboard
        admin_resp = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(admin_resp.status_code, 302)
        self.assertRedirects(admin_resp, reverse('user_dashboard'))

        # User tries to access Operator Dashboard
        op_resp = self.client.get(reverse('operator_dashboard'))
        self.assertEqual(op_resp.status_code, 302)
        self.assertRedirects(op_resp, reverse('user_dashboard'))
        self.client.logout()

    def test_operator_cannot_access_admin(self):
        """Station Operators cannot access Admin management views."""
        self.client.login(username='operator_test', password='Password@123')
        resp = self.client.get(reverse('admin_stations'))
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, reverse('operator_dashboard'))
        self.client.logout()
