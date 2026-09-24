from django.test import TestCase, Client
from django.urls import reverse
from stations.models import ChargingStation, ChargingPoint

class StationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.station = ChargingStation.objects.create(
            name='Solar Hub',
            address='Outer Ring Road',
            city='Bengaluru',
            latitude=12.9279,
            longitude=77.6271,
            contact='+91 95555 44444',
            status='ACTIVE'
        )
        self.p1 = ChargingPoint.objects.create(
            station=self.station,
            point_number='P-1',
            connector_type='CCS2',
            power_rating=50.0,
            status='AVAILABLE'
        )
        self.p2 = ChargingPoint.objects.create(
            station=self.station,
            point_number='P-2',
            connector_type='TYPE2',
            power_rating=22.0,
            status='CHARGING'
        )

    def test_station_properties(self):
        """Station calculated properties return correct counts."""
        self.assertEqual(self.station.total_points, 2)
        self.assertEqual(self.station.available_points, 1)
        self.assertEqual(self.station.charging_points, 1)
        self.assertIn('CCS2', self.station.connector_types)
        self.assertIn('TYPE2', self.station.connector_types)

    def test_api_stations_data(self):
        """Map API returns active stations with coordinates and availability."""
        response = self.client.get(reverse('api_stations_data'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('stations', data)
        self.assertEqual(len(data['stations']), 1)
        st = data['stations'][0]
        self.assertEqual(st['name'], 'Solar Hub')
        self.assertEqual(st['available_points'], 1)
        self.assertEqual(st['total_points'], 2)
