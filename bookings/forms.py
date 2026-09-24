from django import forms
from django.core.exceptions import ValidationError
from datetime import datetime, date, time, timedelta
from .models import Booking
from stations.models import ChargingStation, ChargingPoint
from vehicles.models import Vehicle

class BookingForm(forms.ModelForm):
    DURATION_CHOICES = (
        (30, '30 Minutes (Quick Top-Up)'),
        (45, '45 Minutes'),
        (60, '60 Minutes (Standard 1 Hour)'),
        (90, '90 Minutes (1.5 Hours)'),
        (120, '120 Minutes (2 Hours)'),
    )

    duration_minutes = forms.ChoiceField(
        choices=DURATION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        initial=60
    )

    class Meta:
        model = Booking
        fields = ['station', 'charging_point', 'vehicle', 'date', 'start_time', 'duration_minutes']
        widgets = {
            'station': forms.Select(attrs={'class': 'form-select', 'id': 'id_station'}),
            'charging_point': forms.Select(attrs={'class': 'form-select', 'id': 'id_charging_point'}),
            'vehicle': forms.Select(attrs={'class': 'form-select', 'id': 'id_vehicle'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'id': 'id_date'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time', 'id': 'id_start_time'}),
        }

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        # Filter user vehicles
        self.fields['vehicle'].queryset = Vehicle.objects.filter(user=user)
        # Stations that are ACTIVE
        self.fields['station'].queryset = ChargingStation.objects.filter(status='ACTIVE')
        
        if 'station' in self.data:
            try:
                station_id = int(self.data.get('station'))
                self.fields['charging_point'].queryset = ChargingPoint.objects.filter(
                    station_id=station_id
                ).exclude(status='OUT_OF_SERVICE')
            except (ValueError, TypeError):
                self.fields['charging_point'].queryset = ChargingPoint.objects.none()
        elif self.instance.pk and self.instance.station:
            self.fields['charging_point'].queryset = self.instance.station.points.exclude(status='OUT_OF_SERVICE')
        else:
            self.fields['charging_point'].queryset = ChargingPoint.objects.exclude(status='OUT_OF_SERVICE')

    def clean_date(self):
        booking_date = self.cleaned_data.get('date')
        if booking_date and booking_date < date.today():
            raise ValidationError("Booking date cannot be in the past.")
        return booking_date

    def clean(self):
        cleaned_data = super().clean()
        charging_point = cleaned_data.get('charging_point')
        vehicle = cleaned_data.get('vehicle')
        booking_date = cleaned_data.get('date')
        start_time = cleaned_data.get('start_time')
        duration_minutes = int(cleaned_data.get('duration_minutes', 60))

        if not (charging_point and vehicle and booking_date and start_time):
            return cleaned_data

        # 1. Compatibility check
        if charging_point.connector_type != vehicle.connector_type:
            raise ValidationError(
                f"Connector Mismatch: Your vehicle ({vehicle.model}) uses '{vehicle.get_connector_type_display()}', "
                f"while the selected point offers '{charging_point.get_connector_type_display()}'."
            )

        # 2. Check if booking is in past for today
        if booking_date == date.today():
            now_time = datetime.now().time()
            if start_time < now_time:
                raise ValidationError("Start time cannot be in the past.")

        # 3. Calculate end time
        start_dt = datetime.combine(booking_date, start_time)
        end_dt = start_dt + timedelta(minutes=duration_minutes)
        end_time = end_dt.time()
        cleaned_data['end_time'] = end_time

        # 4. Strict Interval Overlap Conflict Check
        has_conflict = Booking.check_conflict(
            charging_point=charging_point,
            check_date=booking_date,
            start_t=start_time,
            end_t=end_time,
            exclude_id=self.instance.pk if self.instance else None
        )

        if has_conflict:
            raise ValidationError(
                f"Time Conflict: {charging_point.point_number} is already booked during "
                f"{start_time.strftime('%I:%M %p')} - {end_time.strftime('%I:%M %p')}. "
                f"Please choose another time, select another slot, or join the Station Waiting Queue."
            )

        return cleaned_data
