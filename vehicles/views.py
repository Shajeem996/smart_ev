from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from accounts.decorators import ev_user_required
from .models import Vehicle
from .forms import VehicleForm

@ev_user_required
def vehicle_list_view(request):
    vehicles = Vehicle.objects.filter(user=request.user)
    return render(request, 'user/vehicles.html', {'vehicles': vehicles})


@ev_user_required
def vehicle_create_view(request):
    if request.method == 'POST':
        form = VehicleForm(request.POST)
        if form.is_valid():
            vehicle = form.save(commit=False)
            vehicle.user = request.user
            vehicle.save()
            messages.success(request, f"Vehicle '{vehicle.model}' added successfully!")
            return redirect('vehicle_list')
    else:
        form = VehicleForm()
    return render(request, 'user/vehicle_form.html', {'form': form, 'title': 'Add New EV Vehicle'})


@ev_user_required
def vehicle_edit_view(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk, user=request.user)
    if request.method == 'POST':
        form = VehicleForm(request.POST, instance=vehicle)
        if form.is_valid():
            form.save()
            messages.success(request, f"Vehicle '{vehicle.model}' updated successfully!")
            return redirect('vehicle_list')
    else:
        form = VehicleForm(instance=vehicle)
    return render(request, 'user/vehicle_form.html', {'form': form, 'title': 'Edit Vehicle', 'vehicle': vehicle})


@ev_user_required
def vehicle_delete_view(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk, user=request.user)
    if request.method == 'POST':
        model_name = vehicle.model
        vehicle.delete()
        messages.info(request, f"Vehicle '{model_name}' removed.")
        return redirect('vehicle_list')
    return render(request, 'user/vehicle_confirm_delete.html', {'vehicle': vehicle})
