/**
 * Main application JavaScript for Smart EVCharge
 */

document.addEventListener('DOMContentLoaded', function () {
    // Auto dismiss alert messages after 5 seconds
    setTimeout(function () {
        const alerts = document.querySelectorAll('.alert-dismissible');
        alerts.forEach(function (alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 6000);

    // Dynamic charging point dropdown based on selected station
    const stationSelect = document.getElementById('id_station');
    const pointSelect = document.getElementById('id_charging_point');

    if (stationSelect && pointSelect) {
        stationSelect.addEventListener('change', function () {
            const stationId = this.value;
            pointSelect.innerHTML = '<option value="">-- Loading Slots... --</option>';

            if (!stationId) {
                pointSelect.innerHTML = '<option value="">-- Select Station First --</option>';
                return;
            }

            fetch(`/stations/api/${stationId}/points/`)
                .then(response => response.json())
                .then(data => {
                    pointSelect.innerHTML = '<option value="">-- Select Charging Point --</option>';
                    if (data.points && data.points.length > 0) {
                        data.points.forEach(point => {
                            const option = document.createElement('option');
                            option.value = point.id;
                            option.textContent = `${point.point_number} - ${point.connector_display} (${point.power_rating} kW) [${point.status_display}]`;
                            pointSelect.appendChild(option);
                        });
                    } else {
                        pointSelect.innerHTML = '<option value="">No points available at this station</option>';
                    }
                })
                .catch(err => {
                    console.error("Error fetching points:", err);
                    pointSelect.innerHTML = '<option value="">Error loading slots</option>';
                });
        });
    }

    // Active charging timer simulation (if on user dashboard or active session)
    const timerElem = document.getElementById('charging-session-timer');
    if (timerElem) {
        let seconds = parseInt(timerElem.getAttribute('data-seconds-elapsed') || '0', 10);
        setInterval(function () {
            seconds++;
            const hrs = Math.floor(seconds / 3600);
            const mins = Math.floor((seconds % 3600) / 60);
            const secs = seconds % 60;
            timerElem.textContent = `${hrs.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        }, 1000);
    }
});
