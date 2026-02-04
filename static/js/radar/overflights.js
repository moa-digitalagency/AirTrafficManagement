    let map;
    let boundaryLayer;
    let trajectoriesLayer;
    let markersLayer;

    const activeOverflights = window.radarOverflightsContext.activeOverflights;
    const entryTimes = {};
    for (const [id, timeStr] of Object.entries(window.radarOverflightsContext.entryTimes)) {
        if (timeStr) {
            entryTimes[id] = new Date(timeStr);
        }
    }
    const i18n = window.radarOverflightsContext.i18n;

    function initMap() {
        map = L.map('overflight-map', {
            center: [-2.5, 23.5],
            zoom: 5,
            zoomControl: true,
            attributionControl: false
        });

        L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
            maxZoom: 19
        }).addTo(map);

        boundaryLayer = L.layerGroup().addTo(map);
        trajectoriesLayer = L.layerGroup().addTo(map);
        markersLayer = L.layerGroup().addTo(map);

        loadBoundary();
        loadActiveTrajectories();

        setInterval(updateDurations, 1000);
        setInterval(loadActiveTrajectories, 5000);
    }

    function toggleFullscreen() {
        const mapContainer = document.getElementById('overflight-map');
        const btn = document.getElementById('btn-fullscreen');

        mapContainer.classList.toggle('fullscreen');

        if (mapContainer.classList.contains('fullscreen')) {
            btn.innerHTML = `<i class="fas fa-compress mr-1"></i> ${i18n.exit_fullscreen}`;
            btn.classList.add('bg-primary-600', 'text-white');
            btn.classList.remove('bg-dark-300', 'text-gray-300');
        } else {
            btn.innerHTML = `<i class="fas fa-expand mr-1"></i> ${i18n.fullscreen}`;
            btn.classList.remove('bg-primary-600', 'text-white');
            btn.classList.add('bg-dark-300', 'text-gray-300');
        }

        setTimeout(() => {
            map.invalidateSize();
        }, 300);
    }

    function getAircraftIcon(flight) {
        const alt = flight ? (flight.altitude || 0) : 0;
        const type = (flight && flight.aircraft && flight.aircraft.type) ? flight.aircraft.type.toUpperCase() : '';
        const model = (flight && flight.aircraft && flight.aircraft.model) ? flight.aircraft.model.toUpperCase() : '';

        const isHeli = type.includes('H') || model.includes('HELI');
        const isJet = model.includes('B7') || model.includes('A3') || model.includes('ERJ') || model.includes('CRJ');
        const isSmall = model.includes('C172') || model.includes('PA28') || model.includes('CESSNA');

        let icon = 'fa-plane';
        if (isHeli) icon = 'fa-helicopter';

        let color = '#eab308'; // Default yellow for overflight active
        let size = 18;

        if (isHeli) size = 16;
        else if (isSmall) size = 14;
        else if (isJet) size = 24;

        return { icon, color, size };
    }

    function calculateHeading(lat1, lon1, lat2, lon2) {
        const toRad = (deg) => deg * Math.PI / 180;
        const toDeg = (rad) => rad * 180 / Math.PI;

        const dLon = toRad(lon2 - lon1);
        const y = Math.sin(dLon) * Math.cos(toRad(lat2));
        const x = Math.cos(toRad(lat1)) * Math.sin(toRad(lat2)) -
                  Math.sin(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.cos(dLon);

        let brng = toDeg(Math.atan2(y, x));
        return (brng + 360) % 360;
    }

    async function loadBoundary() {
        try {
            const response = await fetch('/radar/api/boundary');
            const boundary = await response.json();

            L.geoJSON(boundary, {
                style: {
                    color: '#3b82f6',
                    weight: 2,
                    opacity: 0.6,
                    fillColor: '#3b82f6',
                    fillOpacity: 0.05,
                    dashArray: '5, 5'
                }
            }).addTo(boundaryLayer);
        } catch (e) {
            console.error('Error loading boundary:', e);
        }
    }

    async function loadActiveTrajectories() {
        try {
            const response = await fetch('/radar/api/overflights/active');
            const overflights = await response.json();

            trajectoriesLayer.clearLayers();
            markersLayer.clearLayers();

            overflights.forEach(ovf => {
                if (ovf.entry_lat && ovf.entry_lon) {
                    const entryMarker = L.circleMarker([ovf.entry_lat, ovf.entry_lon], {
                        radius: 8,
                        fillColor: '#22c55e',
                        color: 'white',
                        weight: 2,
                        fillOpacity: 0.9
                    });
                    entryMarker.bindTooltip(`<b>${i18n.legend.entry}: ${ovf.session_id}</b><br>Alt: FL${Math.round(ovf.entry_alt / 100)}`, {
                        className: 'trajectory-tooltip'
                    });
                    entryMarker.addTo(markersLayer);
                }

                if (ovf.exit_lat && ovf.exit_lon) {
                    const exitMarker = L.circleMarker([ovf.exit_lat, ovf.exit_lon], {
                        radius: 8,
                        fillColor: '#ef4444',
                        color: 'white',
                        weight: 2,
                        fillOpacity: 0.9
                    });
                    exitMarker.bindTooltip(`<b>${i18n.legend.exit}: ${ovf.session_id}</b><br>Alt: FL${Math.round(ovf.exit_alt / 100)}`, {
                        className: 'trajectory-tooltip'
                    });
                    exitMarker.addTo(markersLayer);
                }

                if (ovf.trajectory && ovf.trajectory.length > 0) {
                    const coords = ovf.trajectory.map(p => [p.lat, p.lon]);
                    const line = L.polyline(coords, {
                        color: '#3b82f6',
                        weight: 3,
                        opacity: 0.8,
                        dashArray: null
                    });
                    line.addTo(trajectoriesLayer);

                    ovf.trajectory.forEach((pos, idx) => {
                        if (idx % 5 === 0 || idx === ovf.trajectory.length - 1) {
                            const dot = L.circleMarker([pos.lat, pos.lon], {
                                radius: 3,
                                fillColor: '#3b82f6',
                                color: '#3b82f6',
                                fillOpacity: 0.8,
                                weight: 0
                            });
                            dot.addTo(trajectoriesLayer);
                        }
                    });
                }

                if (ovf.current_lat && ovf.current_lon) {
                    const flightData = ovf.flight || {};
                    const { icon: iconClass, color, size } = getAircraftIcon(flightData);

                    let heading = 0;
                    if (ovf.trajectory && ovf.trajectory.length >= 2) {
                        const last = ovf.trajectory[ovf.trajectory.length - 1];
                        const prev = ovf.trajectory[ovf.trajectory.length - 2];
                        heading = calculateHeading(prev.lat, prev.lon, last.lat, last.lon);
                    }

                    const icon = L.divIcon({
                        className: 'aircraft-marker',
                        html: `<div class="aircraft-icon" style="transform: rotate(${heading}deg); color: ${color}; font-size: ${size}px;">
                                 <i class="fas ${iconClass}"></i>
                               </div>`,
                        iconSize: [size + 4, size + 4],
                        iconAnchor: [(size + 4) / 2, (size + 4) / 2]
                    });

                    const currentMarker = L.marker([ovf.current_lat, ovf.current_lon], { icon });

                    const tooltipContent = `
                        <div class="flex flex-col gap-0.5">
                            <div class="flex items-center gap-2">
                                <span class="font-bold text-white">${flightData.callsign || ovf.session_id}</span>
                                ${flightData.flight_number ? `<span class="text-xs text-gray-300">${flightData.flight_number}</span>` : ''}
                            </div>
                            ${flightData.aircraft && flightData.aircraft.operator ? `<div class="text-[9px] text-blue-300 truncate max-w-[100px]">${flightData.aircraft.operator}</div>` : ''}
                            <div class="flex items-center gap-2 text-[10px] text-gray-300">
                                <span><i class="fas fa-tachometer-alt mr-0.5 text-green-400"></i>${Math.round(flightData.ground_speed || 0)} kts</span>
                                <span><i class="fas fa-arrows-alt-v mr-0.5 text-yellow-400"></i>FL${Math.round((flightData.altitude || 0) / 100)}</span>
                            </div>
                        </div>
                    `;

                    currentMarker.bindTooltip(tooltipContent, {
                        permanent: true,
                        direction: 'right',
                        offset: [12, 0],
                        className: 'trajectory-tooltip'
                    });
                    currentMarker.addTo(markersLayer);
                }
            });

            document.getElementById('active-count').textContent = overflights.length;

        } catch (e) {
            console.error('Error loading trajectories:', e);
        }
    }

    function updateDurations() {
        const now = new Date();

        for (const id in entryTimes) {
            const entryTime = entryTimes[id];
            if (entryTime && !isNaN(entryTime.getTime())) {
                const diffMs = now - entryTime;
                const diffMins = Math.floor(diffMs / 60000);
                const hours = Math.floor(diffMins / 60);
                const mins = diffMins % 60;
                const secs = Math.floor((diffMs % 60000) / 1000);

                const el = document.getElementById(`duration-${id}`);
                if (el) {
                    if (hours > 0) {
                        el.textContent = `${hours}h ${mins}m ${secs}s`;
                    } else {
                        el.textContent = `${mins}m ${secs}s`;
                    }
                }
            }
        }
    }

    function focusOverflight(id) {
        const ovf = activeOverflights.find(o => o.toString() === id.toString());
    }

    async function showTrajectory(overflightId) {
        try {
            const response = await fetch(`/radar/api/overflights/${overflightId}/trajectory`);
            const data = await response.json();

            trajectoriesLayer.clearLayers();
            markersLayer.clearLayers();

            if (data.entry_lat && data.entry_lon) {
                const entryMarker = L.circleMarker([data.entry_lat, data.entry_lon], {
                    radius: 10,
                    fillColor: '#22c55e',
                    color: 'white',
                    weight: 2,
                    fillOpacity: 0.9
                });
                entryMarker.bindPopup(`<b>${i18n.legend.entry}</b><br>Lat: ${data.entry_lat.toFixed(4)}<br>Lon: ${data.entry_lon.toFixed(4)}<br>Alt: FL${Math.round(data.entry_alt / 100)}`);
                entryMarker.addTo(markersLayer);
            }

            if (data.exit_lat && data.exit_lon) {
                const exitMarker = L.circleMarker([data.exit_lat, data.exit_lon], {
                    radius: 10,
                    fillColor: '#ef4444',
                    color: 'white',
                    weight: 2,
                    fillOpacity: 0.9
                });
                exitMarker.bindPopup(`<b>${i18n.legend.exit}</b><br>Lat: ${data.exit_lat.toFixed(4)}<br>Lon: ${data.exit_lon.toFixed(4)}<br>Alt: FL${Math.round(data.exit_alt / 100)}`);
                exitMarker.addTo(markersLayer);
            }

            if (data.trajectory && data.trajectory.length > 0) {
                const coords = data.trajectory.map(p => [p.lat, p.lon]);
                const line = L.polyline(coords, {
                    color: '#3b82f6',
                    weight: 3,
                    opacity: 0.9
                });
                line.addTo(trajectoriesLayer);

                data.trajectory.forEach((pos, idx) => {
                    if (idx % 3 === 0) {
                        const dot = L.circleMarker([pos.lat, pos.lon], {
                            radius: 4,
                            fillColor: '#60a5fa',
                            color: '#3b82f6',
                            fillOpacity: 0.8,
                            weight: 1
                        });
                        dot.bindTooltip(`FL${Math.round(pos.alt / 100)}`, { className: 'trajectory-tooltip' });
                        dot.addTo(trajectoriesLayer);
                    }
                });

                map.fitBounds(line.getBounds(), { padding: [50, 50] });
            } else if (data.entry_lat && data.exit_lat) {
                const line = L.polyline([
                    [data.entry_lat, data.entry_lon],
                    [data.exit_lat, data.exit_lon]
                ], {
                    color: '#3b82f6',
                    weight: 3,
                    opacity: 0.8,
                    dashArray: '10, 5'
                });
                line.addTo(trajectoriesLayer);
                map.fitBounds(line.getBounds(), { padding: [50, 50] });
            }

        } catch (e) {
            console.error('Error loading trajectory:', e);
        }
    }

    async function generateInvoice(overflightId) {
        if (!confirm(i18n.overflights.confirm_invoice)) return;

        try {
            const response = await fetch(`/invoices/generate/overflight/${overflightId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });

            const data = await response.json();

            if (data.success) {
                alert(i18n.billing.generated_success + ' (' + data.invoice_number + ')');
                window.location.reload();
            } else {
                const unknown = i18n.common.error.unknown || 'Unknown error';
                const prefix = i18n.common.error.generic || 'Error';
                alert(prefix + ': ' + (data.error || unknown));
            }
        } catch (e) {
            console.error('Error generating invoice:', e);
            const unknown = i18n.common.error.unknown || 'Unknown error';
            alert(unknown);
        }
    }

    document.addEventListener('DOMContentLoaded', initMap);
