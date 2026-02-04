    let map;
    let drawnItems;
    let drawControl;

    // Existing GeoJSON passed from backend
    const existingGeoJSON = window.adminAirspaceContext.existingGeoJSON;
    const i18n = window.adminAirspaceContext.i18n || {};

    function initMap() {
        // Initialize map centered on RDC
        map = L.map('map').setView([-2.5, 23.5], 5);

        // Add dark basemap
        L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
            subdomains: 'abcd',
            maxZoom: 20
        }).addTo(map);

        // FeatureGroup is to store editable layers
        drawnItems = new L.FeatureGroup();
        map.addLayer(drawnItems);

        // Initialize Draw Control
        drawControl = new L.Control.Draw({
            draw: {
                polyline: false,
                marker: false,
                circle: false,
                circlemarker: false,
                rectangle: false, // We prefer polygons for irregular airspace
                polygon: {
                    allowIntersection: false,
                    showArea: true,
                    drawError: {
                        color: '#e1e100', // Color the shape will turn when intersects
                        message: i18n.airspace_map ? i18n.airspace_map.draw_error : 'Error: Intersection' // Message that will show when intersect
                    },
                    shapeOptions: {
                        color: '#3b82f6'
                    }
                }
            },
            edit: {
                featureGroup: drawnItems,
                remove: true
            }
        });
        map.addControl(drawControl);

        // Load existing geometry if available
        if (existingGeoJSON) {
            L.geoJSON(existingGeoJSON, {
                onEachFeature: function (feature, layer) {
                    drawnItems.addLayer(layer);
                },
                style: {
                    color: '#3b82f6',
                    weight: 2,
                    opacity: 0.8,
                    fillOpacity: 0.1
                }
            });

            // Fit bounds to existing shape
            if (drawnItems.getLayers().length > 0) {
                map.fitBounds(drawnItems.getBounds());
            }
        }

        // Event handlers for draw events
        map.on(L.Draw.Event.CREATED, function (e) {
            var type = e.layerType,
                layer = e.layer;

            // If we only allow one main airspace definition, clear previous ones?
            // For now, let's allow multi-polygons implicitly by having multiple layers,
            // but usually we want one unified area.
            // Let's keep it simple: Add to group.
            drawnItems.addLayer(layer);
        });
    }

    async function saveAirspace() {
        // Convert drawn items to GeoJSON
        const data = drawnItems.toGeoJSON();

        // We expect a FeatureCollection. We might want to save the first Feature's geometry
        // or a MultiPolygon of all features.
        // The backend expects 'geojson' which contains 'geometry' or 'features'.

        if (data.features.length === 0) {
            alert(i18n.airspace_map ? i18n.airspace_map.draw_empty : "Please draw zone.");
            return;
        }

        // If multiple features, we might need to combine them on backend or assume single polygon.
        // Backend handles FeatureCollection by taking the first feature currently.
        // Ideally we should union them but that's complex client side.
        // Warn if multiple
        if (data.features.length > 1) {
            const msg = i18n.airspace_map ? i18n.airspace_map.multiple_zones : "Multiple zones.";
            if (!confirm(msg)) {
                return;
            }
        }

        try {
            const response = await fetch(window.adminAirspaceContext.saveUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': window.adminAirspaceContext.csrfToken
                },
                body: JSON.stringify({
                    geojson: data
                })
            });

            const result = await response.json();

            if (result.success) {
                // Show success notification (using simple alert for now, or toast if available)
                alert(i18n.airspace_map ? i18n.airspace_map.save_success : "Saved!");
            } else {
                const prefix = i18n.airspace_map ? i18n.airspace_map.save_error : "Error: ";
                alert(prefix + result.message);
            }
        } catch (error) {
            console.error("Error:", error);
            const err = i18n.common && i18n.common.error ? i18n.common.error.connection : "Connection Error";
            alert(err);
        }
    }

    document.addEventListener('DOMContentLoaded', initMap);
