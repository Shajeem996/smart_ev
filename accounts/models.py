from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError

class User(AbstractUser):
    ROLE_CHOICES = (
        ('USER', 'EV User'),
        ('OPERATOR', 'Station Operator'),
        ('ADMIN', 'System Admin'),
    )
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='USER')
    phone = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        super().clean()
        # Strict enforcement: Exactly ONE System Admin account in the application
        if self.role == 'ADMIN':
            existing_admin = User.objects.filter(role='ADMIN').exclude(pk=self.pk).first()
            if existing_admin:
                raise ValidationError("Only ONE System Admin is allowed in the application. Additional admin accounts cannot be created.")

    def save(self, *args, **kwargs):
        self.full_clean()
        if self.role == 'ADMIN':
            self.is_staff = True
            self.is_superuser = True
        super().save(*args, **kwargs)

    @property
    def is_ev_user(self):
        return self.role == 'USER'

    @property
    def is_operator(self):
        return self.role == 'OPERATOR'

    @property
    def is_admin_user(self):
        return self.role == 'ADMIN'

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class OperatorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='operator_profile')
    assigned_station = models.ForeignKey(
        'stations.ChargingStation',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_operators'
    )
    badge_number = models.CharField(max_length=50, blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=[('ACTIVE', 'Active'), ('INACTIVE', 'Inactive')],
        default='ACTIVE'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        station_name = self.assigned_station.name if self.assigned_station else 'Unassigned'
        return f"Operator: {self.user.username} - Station: {station_name}"
