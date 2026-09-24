from django import forms
from .models import Vehicle

class VehicleForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = ['vehicle_number', 'model', 'connector_type', 'battery_capacity', 'nickname']
        widgets = {
            'vehicle_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. KA-01-EV-1234'}),
            'model': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Tata Nexon EV Max, Hyundai Ioniq 5'}),
            'connector_type': forms.Select(attrs={'class': 'form-select'}),
            'battery_capacity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'placeholder': 'e.g. 40.5'}),
            'nickname': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. My Primary EV (Optional)'}),
        }
        labels = {
            'battery_capacity': 'Battery Capacity (kWh)',
            'connector_type': 'Charging Connector Port',
        }
