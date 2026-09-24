from django.db import models
from django.conf import settings

class QueueEntry(models.Model):
    STATUS_CHOICES = (
        ('WAITING', 'Waiting'),
        ('NOTIFIED', 'Slot Available (Notified)'),
        ('ASSIGNED', 'Assigned / Booked'),
        ('CANCELLED', 'Cancelled'),
        ('COMPLETED', 'Completed'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='queue_entries')
    vehicle = models.ForeignKey('vehicles.Vehicle', on_delete=models.CASCADE, related_name='queue_entries')
    station = models.ForeignKey('stations.ChargingStation', on_delete=models.CASCADE, related_name='queue_entries')
    requested_date = models.DateField()
    requested_time = models.TimeField()
    duration_minutes = models.PositiveIntegerField(default=60)
    preferred_connector = models.CharField(max_length=30, default='CCS2')
    queue_position = models.PositiveIntegerField(default=1)
    priority = models.PositiveIntegerField(default=1, help_text="Priority rank: 1 (Standard), 2 (Urgent/VIP)")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='WAITING')
    notified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-priority', 'created_at']

    def __str__(self):
        return f"Queue #{self.queue_position} - {self.user.username} @ {self.station.name} ({self.status})"
