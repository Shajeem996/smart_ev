from django.db import models

class ChargingStation(models.Model):
    STATUS_CHOICES = (
        ('ACTIVE', 'Active'),
        ('TEMPORARILY_CLOSED', 'Temporarily Closed'),
        ('MAINTENANCE', 'Under Maintenance'),
    )

    name = models.CharField(max_length=150)
    address = models.TextField()
    city = models.CharField(max_length=100)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    contact = models.CharField(max_length=30)
    operating_hours = models.CharField(max_length=100, default='24/7 (Always Open)')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='ACTIVE')
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - {self.city}"

    @property
    def total_points(self):
        return self.points.count()

    @property
    def available_points(self):
        return self.points.filter(status='AVAILABLE').count()

    @property
    def reserved_points(self):
        return self.points.filter(status='RESERVED').count()

    @property
    def charging_points(self):
        return self.points.filter(status='CHARGING').count()

    @property
    def finishing_points(self):
        return self.points.filter(status='FINISHING').count()

    @property
    def out_of_service_points(self):
        return self.points.filter(status='OUT_OF_SERVICE').count()

    @property
    def connector_types(self):
        return list(self.points.values_list('connector_type', flat=True).distinct())


class ChargingPoint(models.Model):
    STATUS_CHOICES = (
        ('AVAILABLE', 'Available'),
        ('RESERVED', 'Reserved'),
        ('CHARGING', 'Charging'),
        ('FINISHING', 'Finishing'),
        ('OUT_OF_SERVICE', 'Out of Service'),
    )

    CONNECTOR_CHOICES = (
        ('CCS2', 'CCS-2 (DC Fast)'),
        ('TYPE2', 'Type 2 (AC Normal)'),
        ('CHADEMO', 'CHAdeMO (DC)'),
        ('GBT', 'GB/T (DC Fast)'),
    )

    SPEED_CHOICES = (
        ('STANDARD_AC', 'Standard AC (7 - 22 kW)'),
        ('FAST_DC', 'Fast DC (30 - 60 kW)'),
        ('RAPID_DC', 'Rapid DC (60 - 150 kW)'),
    )

    station = models.ForeignKey(ChargingStation, on_delete=models.CASCADE, related_name='points')
    point_number = models.CharField(max_length=50) # e.g. "Slot 1 (CCS2)"
    connector_type = models.CharField(max_length=20, choices=CONNECTOR_CHOICES, default='CCS2')
    power_rating = models.DecimalField(max_digits=6, decimal_places=2, help_text="Power rating in kW (e.g. 50.0)")
    charging_speed = models.CharField(max_length=20, choices=SPEED_CHOICES, default='FAST_DC')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='AVAILABLE')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['station', 'point_number']
        unique_together = ('station', 'point_number')

    def __str__(self):
        return f"{self.station.name} - {self.point_number} ({self.connector_type} {self.power_rating}kW)"
