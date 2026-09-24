from django.db import models
from django.conf import settings

class Vehicle(models.Model):
    CONNECTOR_CHOICES = (
        ('CCS2', 'CCS-2 (DC Fast)'),
        ('TYPE2', 'Type 2 (AC Normal)'),
        ('CHADEMO', 'CHAdeMO (DC)'),
        ('GBT', 'GB/T (DC Fast)'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='vehicles')
    vehicle_number = models.CharField(max_length=30)
    model = models.CharField(max_length=100) # e.g. "Tata Nexon EV Max"
    connector_type = models.CharField(max_length=20, choices=CONNECTOR_CHOICES, default='CCS2')
    battery_capacity = models.DecimalField(max_digits=6, decimal_places=2, help_text="Battery capacity in kWh")
    nickname = models.CharField(max_length=60, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        display_name = self.nickname if self.nickname else self.model
        return f"{display_name} ({self.vehicle_number}) - {self.connector_type}"
