from django import forms
from .models import ChargingStation, ChargingPoint

class ChargingStationForm(forms.ModelForm):
    class Meta:
        model = ChargingStation
        fields = ['name', 'address', 'city', 'latitude', 'longitude', 'contact', 'operating_hours', 'status', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. EcoCharge Metro Hub'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Full street address'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City name'}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001', 'placeholder': 'e.g. 12.971598'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001', 'placeholder': 'e.g. 77.594562'}),
            'contact': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+91 98765 43210'}),
            'operating_hours': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '24/7 or 06:00 AM - 11:00 PM'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Amenities, parking details, landmarks...'}),
        }


class ChargingPointForm(forms.ModelForm):
    class Meta:
        model = ChargingPoint
        fields = ['station', 'point_number', 'connector_type', 'power_rating', 'charging_speed', 'status']
        widgets = {
            'station': forms.Select(attrs={'class': 'form-select'}),
            'point_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Slot 1 (CCS2 Fast)'}),
            'connector_type': forms.Select(attrs={'class': 'form-select'}),
            'power_rating': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5', 'placeholder': 'e.g. 50.0'}),
            'charging_speed': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }
