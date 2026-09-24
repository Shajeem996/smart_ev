from django import forms
from django.core.exceptions import ValidationError
from datetime import date
from .models import QueueEntry
from stations.models import ChargingStation
from vehicles.models import Vehicle

class QueueJoinForm(forms.ModelForm):
    class Meta:
        model = QueueEntry
        fields = ['station', 'vehicle', 'requested_date', 'requested_time', 'duration_minutes', 'preferred_connector', 'priority']
        widgets = {
            'station': forms.Select(attrs={'class': 'form-select'}),
            'vehicle': forms.Select(attrs={'class': 'form-select'}),
            'requested_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'requested_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'duration_minutes': forms.Select(choices=[
                (30, '30 Minutes'),
                (60, '60 Minutes'),
                (90, '90 Minutes'),
                (120, '120 Minutes'),
            ], attrs={'class': 'form-select'}),
            'preferred_connector': forms.Select(choices=[
                ('CCS2', 'CCS-2 (DC Fast)'),
                ('TYPE2', 'Type 2 (AC Normal)'),
                ('CHADEMO', 'CHAdeMO (DC)'),
                ('GBT', 'GB/T (DC Fast)'),
            ], attrs={'class': 'form-select'}),
            'priority': forms.Select(choices=[
                (1, 'Normal Priority (Standard)'),
                (2, 'High Priority (Urgent Commute)'),
            ], attrs={'class': 'form-select'}),
        }

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['vehicle'].queryset = Vehicle.objects.filter(user=user)
        self.fields['station'].queryset = ChargingStation.objects.filter(status='ACTIVE')

    def clean_requested_date(self):
        req_date = self.cleaned_data.get('requested_date')
        if req_date and req_date < date.today():
            raise ValidationError("Requested date cannot be in the past.")
        return req_date
