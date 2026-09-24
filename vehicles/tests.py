from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User
from vehicles.models import Vehicle

class VehicleTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='vehicle_user', email='v@test.com', password='Password@123', role='USER')
        self.client.login(username='vehicle_user', password='Password@123')

    def test_vehicle_crud(self):
        """User can add, edit, and list vehicles."""
        # Add vehicle
        response = self.client.post(reverse('vehicle_add'), {
            'vehicle_number': 'KA-01-MJ-1234',
            'model': 'Tata Nexon EV Max',
            'connector_type': 'CCS2',
            'battery_capacity': '40.5',
            'nickname': 'Blue Lightning'
        })
        self.assertEqual(response.status_code, 302)
        vehicle = Vehicle.objects.get(vehicle_number='KA-01-MJ-1234')
        self.assertEqual(vehicle.user, self.user)
        self.assertEqual(float(vehicle.battery_capacity), 40.5)

        # Edit vehicle
        edit_response = self.client.post(reverse('vehicle_edit', args=[vehicle.id]), {
            'vehicle_number': 'KA-01-MJ-1234',
            'model': 'Tata Nexon EV Max updated',
            'connector_type': 'CCS2',
            'battery_capacity': '40.5',
            'nickname': 'Super Nexon'
        })
        self.assertEqual(edit_response.status_code, 302)
        vehicle.refresh_from_db()
        self.assertEqual(vehicle.model, 'Tata Nexon EV Max updated')
