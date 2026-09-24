from django.db import models
from django.conf import settings
from django.utils import timezone

class ChargingSession(models.Model):
    STATUS_CHOICES = (
        ('IN_PROGRESS', 'In Progress (Charging)'),
        ('FINISHING', 'Finishing'),
        ('COMPLETED', 'Completed'),
    )

    booking = models.OneToOneField('bookings.Booking', on_delete=models.CASCADE, related_name='charging_session')
    operator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='operated_sessions')
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='IN_PROGRESS')
    initial_soc = models.PositiveIntegerField(default=25, help_text="Initial State of Charge (%)")
    final_soc = models.PositiveIntegerField(default=85, help_text="Final State of Charge (%)")
    energy_delivered_kwh = models.DecimalField(max_digits=6, decimal_places=2, default=0.0)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-started_at']

    def calculate_energy(self):
        """
        Estimate energy delivered based on duration and point power rating.
        Energy (kWh) = Power (kW) * Hours * efficiency (approx 0.90)
        """
        if self.ended_at and self.started_at:
            duration_hours = (self.ended_at - self.started_at).total_seconds() / 3600.0
        else:
            duration_hours = (timezone.now() - self.started_at).total_seconds() / 3600.0
        
        power = float(self.booking.charging_point.power_rating)
        delivered = round(power * duration_hours * 0.92, 2)
        return max(delivered, 2.5) # Minimum realistic baseline for simulation

    def __str__(self):
        return f"Session for {self.booking.booking_id} [{self.get_status_display()}]"
