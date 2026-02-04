/* * Nom de l'application : ATM-RDC
 * Description : Source file: index.js
 * Produit de : MOA Digital Agency, www.myoneart.com
 * Fait par : Aisance KALONJI, www.aisancekalonji.com
 * Auditer par : La CyberConfiance, www.cyberconfiance.com
 */

    const i18n = window.radarIndexContext.i18n;
    const unitSettings = window.radarIndexContext.unitSettings || { altitude: 'ft', speed: 'kts' };

    function formatAltitude(ft, short = false) {
        ft = ft || 0;
        if (unitSettings.altitude === 'm') {
            const m = Math.round(ft * 0.3048);
            if (short) return `${Math.round(m / 100) / 10}km`; // e.g. 10.5km
            return `${m.toLocaleString()} m`;
        }
        // Imperial (ft)
        if (short) return `FL${Math.round(ft / 100)}`;
        return `${Math.round(ft).toLocaleString()} ft`;
    }

    function formatSpeed(kts) {
        kts = kts || 0;
        if (unitSettings.speed === 'km/h') {
            return `${Math.round(kts * 1.852)} km/h`;
        }
        if (unitSettings.speed === 'mach') {
            // Approx mach at standard altitude, very rough
            return `M${(kts / 661.47).toFixed(2)}`;
        }
        return `${Math.round(kts)} kts`;
    }

    // Aircraft SVGs
    const aircraftIcons = {
        jet: `<svg viewBox="0 0 512 512" fill="currentColor"><path d="M427.6 236.8L352 192l0-106.3c0-37.4-30.6-67.7-68.3-67.7s-68.3 30.4-68.3 67.7L215.4 192l-76-44.3 0-25.3c0-8.9-7.2-16-16-16s-16 7.2-16 16l0 35L15.6 205.4C6.1 210.9 0 220.8 0 231.8s6.1 20.9 15.6 26.4l91.8 47.7 0 35c0 8.9 7.2 16 16 16s16-7.2 16-16l0-25.3 76-44.3 0 106.3c0 37.4 30.6 67.7 68.3 67.7s68.3-30.4 68.3-67.7l0-106.3 75.6-44.8c18.6-11 30.3-31 30.3-52.6s-11.7-41.6-30.3-52.6z"/></svg>`,
        prop: `<svg viewBox="0 0 576 512" fill="currentColor"><path d="M400 128l0-16c0-17.7-14.3-32-32-32s-32 14.3-32 32l0 16-176 0c-35.3 0-64 28.7-64 64l0 128c0 35.3 28.7 64 64 64l176 0 0 16c0 17.7 14.3 32 32 32s32-14.3 32-32l0-16 23.4 0c44.2 0 80 35.8 80 80c0 8.8 7.2 16 16 16s16-7.2 16-16c0-61.9-50.1-112-112-112l-23.4 0 0-160L400 128zM368 256l112 0c8.8 0 16-7.2 16-16s-7.2-16-16-16l-112 0 0 32zM32 240c-17.7 0-32 14.3-32 32s14.3 32 32 32l64 0 0-64-64 0z"/></svg>`, // Using a simpler plane icon as placeholder for prop
        heli: `<svg viewBox="0 0 640 512" fill="currentColor"><path d="M349.9 59.5C335.8 52.8 320.1 52.8 306 59.5L13.8 198.5C5.3 202.5 0 211.2 0 220.6c0 9.4 5.3 18.1 13.8 22.1l65.8 31.3c8.3-3.1 17.1-4.9 26.2-5.3L153.2 227l-55-73.4c-5.7-7.6-4.5-18.3 2.7-24.5l26.2-22.6c6.5-5.6 16.3-5.2 22.3 1L200.7 161l254.6 0 51.3-53.5c6-6.1 15.8-6.6 22.3-1l26.2 22.6c7.2 6.2 8.4 16.9 2.7 24.5L502.8 227l47.5 41.7c9.2 .4 17.9 2.2 26.2 5.3l65.8-31.3c8.5-4 13.8-12.7 13.8-22.1c0-9.4-5.3-18.1-13.8-22.1L349.9 59.5zM368 224l0 96 16 0c26.5 0 48 21.5 48 48l0 16 0 32 32 0 0-32c0-8.8 7.2-16 16-16s16 7.2 16 16l0 32c0 17.7-14.3 32-32 32l-32 0 0 16c0 8.8-7.2 16-16 16s-16-7.2-16-16l0-16-64 0 0 16c0 8.8-7.2 16-16 16s-16-7.2-16-16l0-16-48 0c-17.7 0-32-14.3-32-32l0-32c0-8.8 7.2-16 16-16s16 7.2 16 16l0 32 32 0 0-16c0-26.5 21.5-48 48-48l16 0 0-96 32 0z"/></svg>`,
        plane: `<svg viewBox="0 0 576 512" fill="currentColor"><path d="M482.3 192c34.2 0 58.1-12.2 73.7-26.4c8.8-8 16.6-17.8 20-27.7l0 0c2.5-7.4-4-15-11.7-16c-8.8-1.1-17.7-1.5-26.4-1.5c-22.5 0-43.9 3.1-63.7 8.5L343.9 16l-48.4 0c-4.4 0-8 3.6-8 8l0 125.7-93.6 28.6L125 106.8c-3.7-6.9-10.8-11.2-18.6-11.2l-37.1 0c-5.5 0-9.4 5.4-7.7 10.6l21.2 63.6L16 189.2C7.2 192 1.4 200.4 1.4 209.7c0 9.2 5.6 17.4 14.2 20.3l66.9 22.3L61.6 316c-1.7 5.2 2.2 10.6 7.7 10.6l37.1 0c7.8 0 14.9-4.3 18.6-11.2l68.9-71.5 93.6 31.2L287.5 400c0 4.4 3.6 8 8 8l48.4 0 130.3-112.9c19.8 5.4 41.2 8.5 63.7 8.5c8.8 0 17.7-.4 26.4-1.5c7.7-1 14.1-8.6 11.7-16l0 0c-3.4-9.9-11.2-19.7-20-27.7c-15.6-14.2-39.6-26.4-73.7-26.4l-112.5 0-112.5 0z"/></svg>`
    };

    let map;
    let flightsLayer;
    let boundaryLayer;
    let airportsLayer;
    let weatherLayer;
    let precipitationLayer;
    let basemapLayer;
    let flights = [];
    let filteredFlights = [];
    let weatherEnabled = false;
    let weatherTiles = null;

    const airports = window.radarIndexContext.airports;

    const basemaps = {
        dark: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
        satellite: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        streets: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'
    };

    function initMap() {
        map = L.map('radar-map', {
            center: [-2.5, 23.5],
            zoom: 5,
            zoomControl: true,
            attributionControl: false
        });

        basemapLayer = L.tileLayer(basemaps.dark, { maxZoom: 19 }).addTo(map);

        flightsLayer = L.layerGroup().addTo(map);
        boundaryLayer = L.layerGroup().addTo(map);
        airportsLayer = L.layerGroup().addTo(map);
        weatherLayer = L.layerGroup();
        precipitationLayer = L.layerGroup();

        loadBoundary();
        loadAirports();
        loadFlights();
        loadWeatherTiles();

        // Add zoom listener for dynamic icon scaling
        map.on('zoomend', () => {
            updateFlightsOnMap();
        });

        // Add Immersive Controls on the map
        const ImmersiveControl = L.Control.extend({
            onAdd: function(map) {
                const div = L.DomUtil.create('div', 'leaflet-bar leaflet-control');
                div.style.backgroundColor = 'rgba(15, 23, 42, 0.9)';
                div.style.border = '1px solid rgba(255, 255, 255, 0.2)';

                div.innerHTML = `
                    <a href="#" role="button" title="${i18n.fullscreen}" onclick="toggleFullscreen(); return false;" style="color: white; width: 34px; height: 34px; line-height: 34px; text-align: center; display: block; border-bottom: 1px solid rgba(255,255,255,0.1);">
                        <i class="fas fa-expand"></i>
                    </a>
                    <a href="#" role="button" title="${i18n.scan_effect}" onclick="toggleScan(); return false;" style="color: white; width: 34px; height: 34px; line-height: 34px; text-align: center; display: block;">
                        <i class="fas fa-satellite-dish"></i>
                    </a>
                `;
                return div;
            }
        });

        map.addControl(new ImmersiveControl({ position: 'topright' }));

        setInterval(loadFlights, 10000);
        updateTime();
        setInterval(updateTime, 1000);
    }

    function updateTime() {
        const now = new Date();
        document.getElementById('last-update').textContent = now.toLocaleTimeString('fr-FR');
    }

    async function loadWeatherTiles() {
        try {
            const response = await fetch('/radar/api/weather/tiles');
            const data = await response.json();

            if (data.configured && data.layers) {
                weatherTiles = data.layers;

                if (data.layers.clouds) {
                    L.tileLayer(data.layers.clouds, { opacity: 0.5 }).addTo(weatherLayer);
                }
                if (data.layers.precipitation) {
                    L.tileLayer(data.layers.precipitation, { opacity: 0.6 }).addTo(precipitationLayer);
                }
            }
        } catch (e) {
            console.error('Error loading weather tiles:', e);
        }
    }

    async function loadBoundary() {
        try {
            const response = await fetch('/radar/api/boundary');
            const boundary = await response.json();

            L.geoJSON(boundary, {
                style: {
                    color: '#3b82f6',
                    weight: 2,
                    opacity: 0.8,
                    fillColor: '#3b82f6',
                    fillOpacity: 0.05,
                    dashArray: '5, 5'
                }
            }).addTo(boundaryLayer);
        } catch (e) {
            console.error('Error loading boundary:', e);
        }
    }

    function loadAirports() {
        airports.forEach(airport => {
            if (airport.latitude && airport.longitude) {
                const marker = L.circleMarker([airport.latitude, airport.longitude], {
                    radius: 8,
                    fillColor: '#3b82f6',
                    color: '#1e40af',
                    weight: 2,
                    opacity: 1,
                    fillOpacity: 0.8
                });

                marker.bindTooltip(`
                    <div class="text-center">
                        <b>${airport.icao_code}</b><br>
                        <span class="text-gray-300">${airport.name}</span><br>
                        <span class="text-gray-400 text-xs">${airport.city || ''}</span>
                    </div>
                `, {
                    permanent: false,
                    direction: 'top',
                    className: 'aircraft-data-tag'
                });

                marker.on('click', () => showAirportWeather(airport.icao_code));
                marker.addTo(airportsLayer);
            }
        });
    }

    async function showAirportWeather(icao) {
        try {
            const response = await fetch(`/radar/api/weather/airport/${icao}`);
            const data = await response.json();

            let content = `<div class="p-3"><b>${icao}</b>`;

            if (data.metar && data.metar.raw) {
                content += `<div class="mt-2 text-xs font-mono bg-dark-300 p-2 rounded">${data.metar.raw}</div>`;
                content += `<div class="mt-2 text-sm">
                    <span class="text-gray-400">${i18n.cat}:</span> <span class="${data.metar.flight_category === 'VFR' ? 'text-green-400' : 'text-yellow-400'}">${data.metar.flight_category || 'N/A'}</span>
                </div>`;
            }

            if (data.weather) {
                content += `<div class="mt-2 text-sm">
                    <span class="text-gray-400">${i18n.temp}:</span> ${data.weather.temperature || '-'}°C |
                    <span class="text-gray-400">${i18n.wind}:</span> ${data.weather.wind_speed || '-'} m/s
                </div>`;
            }

            content += '</div>';

            const airport = airports.find(a => a.icao_code === icao);
            if (airport) {
                L.popup()
                    .setLatLng([airport.latitude, airport.longitude])
                    .setContent(content)
                    .openOn(map);
            }
        } catch (e) {
            console.error('Error loading airport weather:', e);
        }
    }

    async function loadFlights() {
        try {
            const response = await fetch('/radar/api/flights');
            flights = await response.json();

            updateOperatorFilter();
            applyFilters();

            document.getElementById('flights-count').textContent = `${flights.length} ${i18n.flights_active}`;
        } catch (e) {
            console.error('Error loading flights:', e);
        }
    }

    function updateOperatorFilter() {
        const select = document.getElementById('filter-operator');
        const operators = [...new Set(flights.map(f => f.aircraft?.operator).filter(Boolean))];

        const currentValue = select.value;
        select.innerHTML = `<option value="all">${i18n.all_operators}</option>`;
        operators.forEach(op => {
            const safeOp = window.escapeHtml(op);
            select.innerHTML += `<option value="${safeOp}">${safeOp}</option>`;
        });
        select.value = currentValue || 'all';
    }

    function applyFilters() {
        const search = document.getElementById('filter-search').value.toLowerCase();
        const altMin = parseInt(document.getElementById('filter-altitude-min').value);
        const altMax = parseInt(document.getElementById('filter-altitude-max').value);
        const operator = document.getElementById('filter-operator').value;

        const statusFilters = {
            in_flight: document.querySelector('[data-status="in_flight"]').checked,
            approaching: document.querySelector('[data-status="approaching"]').checked,
            on_ground: document.querySelector('[data-status="on_ground"]').checked
        };
        const inRdcOnly = document.querySelector('[data-status="in_rdc"]').checked;

        document.getElementById('altitude-value').textContent =
            `${formatAltitude(altMin)} - ${formatAltitude(altMax)}`;

        filteredFlights = flights.filter(flight => {
            if (search && !matchesSearch(flight, search)) return false;

            const alt = flight.altitude || 0;
            if (alt < altMin || alt > altMax) return false;

            if (operator !== 'all' && flight.aircraft?.operator !== operator) return false;

            if (!statusFilters[flight.status]) return false;

            if (inRdcOnly && !flight.in_rdc) return false;

            return true;
        });

        updateFlightsOnMap();
        updateFlightsList();

        document.getElementById('filtered-count').textContent =
            filteredFlights.length !== flights.length ?
            `${filteredFlights.length}/${flights.length}` : '';
    }

    function matchesSearch(flight, search) {
        return (flight.callsign || '').toLowerCase().includes(search) ||
               (flight.flight_number || '').toLowerCase().includes(search) ||
               (flight.aircraft?.operator || '').toLowerCase().includes(search) ||
               (flight.aircraft?.registration || '').toLowerCase().includes(search) ||
               (flight.departure || '').toLowerCase().includes(search) ||
               (flight.arrival || '').toLowerCase().includes(search);
    }

    function getAircraftIcon(flight) {
        const alt = flight.altitude || 0;
        const isEmergency = flight.squawk === '7700';

        const type = (flight.aircraft?.type || '').toUpperCase();
        const model = (flight.aircraft?.model || '').toUpperCase();

        const isHeli = type.includes('H') || model.includes('HELI');
        const isJet = model.includes('B7') || model.includes('A3') || model.includes('ERJ') || model.includes('CRJ') || type === 'J';
        const isProp = model.includes('C172') || model.includes('PA28') || model.includes('CESSNA') || model.includes('DH8') || model.includes('ATR');

        let svg = aircraftIcons.plane;
        if (isHeli) svg = aircraftIcons.heli;
        else if (isJet) svg = aircraftIcons.jet;
        else if (isProp) svg = aircraftIcons.prop;

        let color = '#22c55e';
        if (isEmergency) color = '#ef4444';
        else if (flight.status === 'approaching') color = '#eab308';
        else if (flight.status === 'on_ground') color = '#3b82f6';
        else if (alt < 10000) color = '#38bdf8';

        // Base size, scaled by map zoom later via CSS or JS
        let size = 24;
        if (isHeli) size = 20;
        else if (isJet) size = 28;

        return { svg, color, size };
    }

    function updateFlightsOnMap() {
        flightsLayer.clearLayers();

        const zoom = map.getZoom();
        const scaleFactor = Math.max(0.6, Math.min(1.5, zoom / 8));

        filteredFlights.forEach(flight => {
            if (!flight.latitude || !flight.longitude) return;

            const { svg, color, size } = getAircraftIcon(flight);
            const rotation = flight.heading || 0;
            const currentSize = size * scaleFactor;

            const icon = L.divIcon({
                className: 'aircraft-marker',
                html: `<div class="aircraft-icon-svg" style="transform: rotate(${rotation}deg); color: ${color}; width: ${currentSize}px; height: ${currentSize}px;">
                         ${svg}
                       </div>`,
                iconSize: [currentSize + 20, currentSize + 20],
                iconAnchor: [(currentSize + 20) / 2, (currentSize + 20) / 2]
            });

            const marker = L.marker([flight.latitude, flight.longitude], { icon });

            const operator = flight.aircraft?.operator || '';
            const iata = flight.aircraft?.airline_iata || '';

            // Smart Label (Logo, Callsign, Stats)
            const logoUrl = iata ? `https://content.airhex.com/content/logos/airlines_${iata}_200_200_s.png` : '';
            const logoImg = logoUrl ? `<img src="${logoUrl}" class="smart-label-logo" onerror="this.style.display='none'; this.nextElementSibling.style.display='block'">` : '';
            const operatorText = `<span style="${logoUrl ? 'display:none' : ''}" class="text-[9px] text-gray-300 truncate max-w-[80px]">${window.escapeHtml(operator)}</span>`;

            const smartLabelHtml = `
                <div class="smart-label">
                    <div class="smart-label-header">
                        <div class="smart-label-callsign">${window.escapeHtml(flight.callsign)}</div>
                        ${logoImg}
                        ${operatorText}
                    </div>
                    <div class="smart-label-stats">
                        <span><i class="fas fa-tachometer-alt mr-0.5 text-green-400"></i>${formatSpeed(flight.ground_speed).replace(/ .*/, '')}</span>
                        <span><i class="fas fa-arrows-alt-v mr-0.5 text-yellow-400"></i>${formatAltitude(flight.altitude, true)}</span>
                    </div>
                </div>
            `;

            marker.bindTooltip(smartLabelHtml, {
                permanent: true,
                direction: 'right',
                offset: [currentSize / 2 + 5, 0],
                className: 'leaflet-tooltip-empty' // Use custom class to remove default styles if needed, or override
            });

            // Enhanced Popup
            const popupContent = `
                <div class="p-2">
                    <div class="flex items-center justify-between mb-2">
                        <div class="font-bold text-lg">${window.escapeHtml(flight.callsign)}</div>
                        ${iata ? `<img src="${logoUrl}" class="h-6 object-contain" onerror="this.style.display='none'">` : ''}
                    </div>
                    ${operator ? `<div class="text-xs text-primary-400 mb-2 font-semibold">${window.escapeHtml(operator)}</div>` : ''}

                    <div class="grid grid-cols-2 gap-3 text-sm">
                        <div class="bg-dark-300 p-1.5 rounded"><span class="text-gray-400 block text-xs">${i18n.dep}</span> ${window.escapeHtml(flight.departure || '???')}</div>
                        <div class="bg-dark-300 p-1.5 rounded"><span class="text-gray-400 block text-xs">${i18n.arr}</span> ${window.escapeHtml(flight.arrival || '???')}</div>

                        <div><span class="text-gray-400 text-xs block">${i18n.alt_abbr}</span> ${formatAltitude(flight.altitude, false)}</div>
                        <div><span class="text-gray-400 text-xs block">${i18n.speed}</span> ${formatSpeed(flight.ground_speed)}</div>
                        <div><span class="text-gray-400 text-xs block">${i18n.heading}</span> ${Math.round(flight.heading || 0)}°</div>
                        <div><span class="text-gray-400 text-xs block">${i18n.squawk}</span> ${flight.squawk || '-'}</div>
                    </div>

                    ${flight.aircraft ? `
                    <div class="mt-2 pt-2 border-t border-dark-100 text-sm">
                        <div class="flex justify-between">
                            <span class="text-gray-400">${window.escapeHtml(flight.aircraft.model || '-')}</span>
                            <span class="font-mono text-gray-300">${window.escapeHtml(flight.aircraft.registration || '-')}</span>
                        </div>
                    </div>
                    ` : ''}
                    ${flight.in_rdc ? `<div class="mt-2 text-xs text-primary-400"><i class="fas fa-check-circle mr-1"></i>${i18n.in_rdc}</div>` : ''}
                </div>
            `;

            marker.bindPopup(popupContent, {
                className: 'flight-info-popup',
                maxWidth: 300
            });

            marker.addTo(flightsLayer);
        });
    }

    function toggleFullscreen() {
        const mapContainer = document.getElementById('radar-map');
        const btn = document.getElementById('btn-fullscreen');

        mapContainer.classList.toggle('fullscreen');

        if (mapContainer.classList.contains('fullscreen')) {
            btn.innerHTML = `<i class="fas fa-compress"></i>`;
            btn.setAttribute('data-tooltip', i18n.exit_fullscreen);
            btn.classList.add('bg-primary-600', 'text-white', 'hover:bg-primary-500');
            btn.classList.remove('bg-dark-300', 'text-gray-300', 'hover:bg-gray-700');
        } else {
            btn.innerHTML = `<i class="fas fa-expand"></i>`;
            btn.setAttribute('data-tooltip', i18n.fullscreen);
            btn.classList.remove('bg-primary-600', 'text-white', 'hover:bg-primary-500');
            btn.classList.add('bg-dark-300', 'text-gray-300', 'hover:bg-gray-700');
        }

        setTimeout(() => {
            map.invalidateSize();
        }, 300);
    }

    function toggleScan() {
        const overlay = document.getElementById('radar-scan-overlay');
        const btn = document.getElementById('btn-scan');

        overlay.classList.toggle('active');

        if (overlay.classList.contains('active')) {
            btn.classList.add('bg-primary-600', 'text-white', 'hover:bg-primary-500');
            btn.classList.remove('bg-dark-300', 'text-gray-300', 'hover:bg-gray-700');
        } else {
            btn.classList.remove('bg-primary-600', 'text-white', 'hover:bg-primary-500');
            btn.classList.add('bg-dark-300', 'text-gray-300', 'hover:bg-gray-700');
        }
    }

    function updateFlightsList() {
        const container = document.getElementById('flights-list');

        if (filteredFlights.length === 0) {
            container.innerHTML = `
                <div class="text-center py-8 text-gray-400">
                    <i class="fas fa-plane-slash text-2xl mb-2"></i>
                    <p class="text-sm">${i18n.no_match}</p>
                </div>
            `;
            return;
        }

        container.innerHTML = filteredFlights.map(flight => {
            const { color } = getAircraftIcon(flight);
            const callsign = window.escapeHtml(flight.callsign);
            const departure = window.escapeHtml(flight.departure || '???');
            const arrival = window.escapeHtml(flight.arrival || '???');
            const operator = window.escapeHtml(flight.aircraft?.operator || '');

            return `
                <div class="p-3 rounded-lg hover:bg-dark-300 cursor-pointer transition-colors mb-2"
                     onclick="focusFlight(${flight.latitude}, ${flight.longitude})"
                     data-testid="flight-item-${flight.id}">
                    <div class="flex items-center justify-between mb-1">
                        <span class="font-medium text-white">${callsign}</span>
                        <div class="flex items-center gap-2">
                            ${flight.in_rdc ? '<i class="fas fa-check-circle text-primary-400 text-xs"></i>' : ''}
                            <span class="w-2 h-2 rounded-full" style="background: ${color}"></span>
                        </div>
                    </div>
                    <div class="flex items-center gap-2 text-xs text-gray-400">
                        <span>${departure}</span>
                        <i class="fas fa-long-arrow-alt-right"></i>
                        <span>${arrival}</span>
                    </div>
                    <div class="text-xs text-gray-500 mt-1">
                        ${formatAltitude(flight.altitude, true)} | ${formatSpeed(flight.ground_speed)} | ${Math.round(flight.heading || 0)}°
                    </div>
                    ${operator ? `<div class="text-xs text-gray-600 mt-1">${operator}</div>` : ''}
                </div>
            `;
        }).join('');
    }

    function focusFlight(lat, lon) {
        if (lat && lon) {
            map.setView([lat, lon], 8);
        }
    }

    function zoomToRDC() {
        map.setView([-2.5, 23.5], 5);
    }

    function toggleLayerControl() {
        document.getElementById('layer-control').classList.toggle('show');
    }

    function toggleLayer(layer) {
        switch(layer) {
            case 'boundary':
                if (map.hasLayer(boundaryLayer)) map.removeLayer(boundaryLayer);
                else map.addLayer(boundaryLayer);
                break;
            case 'airports':
                if (map.hasLayer(airportsLayer)) map.removeLayer(airportsLayer);
                else map.addLayer(airportsLayer);
                break;
            case 'flights':
                if (map.hasLayer(flightsLayer)) map.removeLayer(flightsLayer);
                else map.addLayer(flightsLayer);
                break;
            case 'weather':
                if (map.hasLayer(weatherLayer)) map.removeLayer(weatherLayer);
                else map.addLayer(weatherLayer);
                break;
            case 'precipitation':
                if (map.hasLayer(precipitationLayer)) map.removeLayer(precipitationLayer);
                else map.addLayer(precipitationLayer);
                break;
        }
    }

    function toggleWeather() {
        weatherEnabled = !weatherEnabled;
        const btn = document.getElementById('btn-weather');

        if (weatherEnabled) {
            map.addLayer(weatherLayer);
            btn.classList.add('bg-primary-600', 'text-white', 'hover:bg-primary-500');
            btn.classList.remove('bg-dark-300', 'text-gray-300', 'hover:bg-gray-700');
            document.getElementById('layer-weather').checked = true;
        } else {
            map.removeLayer(weatherLayer);
            btn.classList.remove('bg-primary-600', 'text-white', 'hover:bg-primary-500');
            btn.classList.add('bg-dark-300', 'text-gray-300', 'hover:bg-gray-700');
            document.getElementById('layer-weather').checked = false;
        }
    }

    function changeBasemap() {
        const selected = document.getElementById('basemap-select').value;
        map.removeLayer(basemapLayer);
        basemapLayer = L.tileLayer(basemaps[selected], { maxZoom: 19 }).addTo(map);
    }

    function refreshFlights() {
        const btn = document.getElementById('btn-refresh');
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        loadFlights().then(() => {
            btn.innerHTML = '<i class="fas fa-sync-alt"></i>';
        });
    }

    document.addEventListener('DOMContentLoaded', initMap);
