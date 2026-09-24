/**
 * Leaflet.js OpenStreetMap Integration for Smart EVCharge
 */

document.addEventListener('DOMContentLoaded', function () {
    const mapElement = document.getElementById('map');
    if (!mapElement) return;

    // Default center (Bangalore coordinates or first station)
    const defaultLat = 12.9716;
    const defaultLng = 77.5946;
    const map = L.map('map').setView([defaultLat, defaultLng], 12);

    // OpenStreetMap Tile Layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    // Custom Icon Generator
    function createEVMarkerIcon(isAvailable) {
        const color = isAvailable ? '#10b981' : '#64748b';
        return L.divIcon({
            className: 'custom-ev-marker',
            html: `
                <div style="
                    background-color: ${color};
                    width: 32px;
                    height: 32px;
                    border-radius: 50%;
                    border: 3px solid #ffffff;
                    box-shadow: 0 2px 6px rgba(0,0,0,0.3);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: #ffffff;
                    font-size: 16px;
                ">
                    ⚡
                </div>
            `,
            iconSize: [32, 32],
            iconAnchor: [16, 16],
            popupAnchor: [0, -18]
        });
    }

    // Fetch stations and render markers
    fetch('/stations/api/all/')
        .then(response => response.json())
        .then(data => {
            const stations = data.stations;
            if (!stations || stations.length === 0) return;

            const bounds = [];

            stations.forEach(station => {
                const lat = station.lat;
                const lng = station.lng;
                bounds.push([lat, lng]);

                const isAvailable = station.available_points > 0;
                const marker = L.marker([lat, lng], {
                    icon: createEVMarkerIcon(isAvailable)
                }).addTo(map);

                // Connector badges
                const connectorBadges = station.connectors.map(c => 
                    `<span class="badge bg-secondary me-1">${c}</span>`
                ).join(' ');

                // Station popup content
                const popupContent = `
                    <div style="min-width: 220px; font-family: inherit;">
                        <h6 class="fw-bold mb-1" style="color: #0f172a;">${station.name}</h6>
                        <p class="text-muted small mb-2"><i class="bi bi-geo-alt"></i> ${station.address}, ${station.city}</p>
                        
                        <div class="d-flex align-items-center justify-content-between mb-2 p-2 bg-light rounded">
                            <span class="small fw-semibold text-muted">Availability</span>
                            <span class="badge ${isAvailable ? 'bg-success' : 'bg-warning text-dark'}">
                                ${station.available_points} / ${station.total_points} Slots Free
                            </span>
                        </div>
                        
                        <div class="mb-3">
                            <div class="small text-muted mb-1">Connectors:</div>
                            ${connectorBadges || '<span class="small text-muted">None</span>'}
                        </div>

                        <div class="d-grid gap-2">
                            <a href="${station.book_url}" class="btn btn-sm btn-success text-white fw-bold">⚡ Book Slot</a>
                            <a href="${station.detail_url}" class="btn btn-sm btn-outline-secondary">View Station Details</a>
                        </div>
                    </div>
                `;

                marker.bindPopup(popupContent);
            });

            if (bounds.length > 0) {
                map.fitBounds(bounds, { padding: [40, 40] });
            }
        })
        .catch(err => console.error("Error loading stations on map:", err));
});
