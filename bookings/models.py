import uuid
import io
import qrcode
from django.db import models
from django.conf import settings
from django.core.files.base import ContentFile
from datetime import datetime, date, time

class Booking(models.Model):
    STATUS_CHOICES = (
        ('CONFIRMED', 'Confirmed'),
        ('CHARGING', 'Charging'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
        ('NO_SHOW', 'No Show'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookings')
    vehicle = models.ForeignKey('vehicles.Vehicle', on_delete=models.CASCADE, related_name='bookings')
    station = models.ForeignKey('stations.ChargingStation', on_delete=models.CASCADE, related_name='bookings')
    charging_point = models.ForeignKey('stations.ChargingPoint', on_delete=models.CASCADE, related_name='bookings')
    booking_id = models.CharField(max_length=32, unique=True, editable=False)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    duration_minutes = models.PositiveIntegerField(default=60)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='CONFIRMED')
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True)
    qr_token = models.CharField(max_length=64, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-start_time']

    def save(self, *args, **kwargs):
        if not self.booking_id:
            unique_part = uuid.uuid4().hex[:6].upper()
            self.booking_id = f"EVB-{unique_part}"
        if not self.qr_token:
            self.qr_token = uuid.uuid4().hex

        is_new = self.pk is None
        super().save(*args, **kwargs)

        # Generate QR code if not already generated
        if not self.qr_code or is_new:
            self.generate_qr_code()
            super().save(update_fields=['qr_code'])

    def generate_qr_code(self):
        # QR payload contains verifiable reference:
        # Avoid sensitive data while maintaining secure verification
        payload = f"SMARTEV:{self.booking_id}:{self.qr_token}"
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=8,
            border=2,
        )
        qr.add_data(payload)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#0f172a", back_color="#ffffff")
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        filename = f"{self.booking_id}.png"
        self.qr_code.save(filename, ContentFile(buffer.getvalue()), save=False)

    @staticmethod
    def check_conflict(charging_point, check_date, start_t, end_t, exclude_id=None):
        """
        Interval overlap check:
        Two intervals [S1, E1) and [S2, E2) overlap if:
        S1 < E2 and E1 > S2
        """
        conflicts = Booking.objects.filter(
            charging_point=charging_point,
            date=check_date,
            status__in=['CONFIRMED', 'CHARGING'],
            start_time__lt=end_t,
            end_time__gt=start_t
        )
        if exclude_id:
            conflicts = conflicts.exclude(id=exclude_id)
        return conflicts.exists()

    def __str__(self):
        return f"{self.booking_id} - {self.user.username} @ {self.station.name} [{self.date} {self.start_time}-{self.end_time}]"
