from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.db.models import Q
from .models import ChargingStation, ChargingPoint

def live_map_view(request):
    """
    Renders interactive Leaflet OpenStreetMap view with all charging stations.
    """
    stations = ChargingStation.objects.filter(status='ACTIVE')
    return render(request, 'user/live_map.html', {'stations': stations})


def stations_list_view(request):
    """
    Search and filter stations by city, name, connector type, and availability.
    """
    query = request.GET.get('q', '').strip()
    connector = request.GET.get('connector', '').strip()
    city = request.GET.get('city', '').strip()

    stations = ChargingStation.objects.all()

    if query:
        stations = stations.filter(
            Q(name__icontains=query) | Q(address__icontains=query) | Q(city__icontains=query)
        )
    if city:
        stations = stations.filter(city__iexact=city)
    if connector:
        stations = stations.filter(points__connector_type=connector).distinct()

    cities = ChargingStation.objects.values_list('city', flat=True).distinct()

    return render(request, 'user/stations_list.html', {
        'stations': stations,
        'cities': cities,
        'selected_connector': connector,
        'selected_city': city,
        'search_query': query,
    })


def station_detail_view(request, pk):
    """
    Detailed station page with live charging point statuses.
    """
    station = get_object_or_404(ChargingStation, pk=pk)
    points = station.points.all()
    return render(request, 'user/station_detail.html', {
        'station': station,
        'points': points
    })


def api_stations_data(request):
    """
    REST JSON endpoint returning station markers data for Leaflet map.
    """
    stations = ChargingStation.objects.filter(status='ACTIVE')
    data = []
    for s in stations:
        data.append({
            'id': s.id,
            'name': s.name,
            'address': s.address,
            'city': s.city,
            'lat': float(s.latitude),
            'lng': float(s.longitude),
            'status': s.status,
            'operating_hours': s.operating_hours,
            'total_points': s.total_points,
            'available_points': s.available_points,
            'charging_points': s.charging_points,
            'reserved_points': s.reserved_points,
            'connectors': s.connector_types,
            'detail_url': f"/stations/{s.id}/",
            'book_url': f"/book/?station={s.id}"
        })
    return JsonResponse({'stations': data})


def api_station_points(request, station_id):
    """
    REST JSON endpoint returning points for a given station to populate dropdowns.
    """
    connector = request.GET.get('connector')
    points = ChargingPoint.objects.filter(station_id=station_id).exclude(status='OUT_OF_SERVICE')
    if connector:
        points = points.filter(connector_type=connector)

    data = [
        {
            'id': p.id,
            'point_number': p.point_number,
            'connector_type': p.connector_type,
            'connector_display': p.get_connector_type_display(),
            'power_rating': float(p.power_rating),
            'charging_speed': p.get_charging_speed_display(),
            'status': p.status,
            'status_display': p.get_status_display()
        }
        for p in points
    ]
    return JsonResponse({'points': data})
