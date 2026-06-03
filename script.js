// Dummy data for cities
const cities = [
    "Amsterdam", "Rotterdam", "The Hague", "Utrecht", "Eindhoven", "Groningen", "Tilburg", "Almere", "Breda", "Nijmegen"
];

// City coordinates
const cityCoords = {
    "Amsterdam": [52.37, 4.895],
    "Rotterdam": [51.92, 4.48],
    "The Hague": [52.07, 4.3],
    "Utrecht": [52.09, 5.12],
    "Eindhoven": [51.44, 5.48],
    "Groningen": [53.22, 6.57],
    "Tilburg": [51.56, 5.09],
    "Almere": [52.37, 5.22],
    "Breda": [51.59, 4.78],
    "Nijmegen": [51.81, 5.85]
};

// Current selected city and date
let selectedCity = "Amsterdam";
let selectedDate = new Date().toISOString().split('T')[0];
let activeMode = 'congestion';
let selectedCell = null;
let activeMarker = null;

const tooltipTexts = {
    'top-logo': 'GridView visualizes electricity grid congestion risk for Amsterdam using real satellite-derived features and network data. Congestion predictions come from a trained <span class="tooltip-highlight">Random Forest</span> model. Solar radiation figures are estimated.',
    'layer-congestion': 'The congestion layer shows predicted grid overload risk per 1×1 km cell. <span class="tooltip-highlight">Red</span> = high risk, <span class="tooltip-highlight">orange</span> = medium, <span class="tooltip-highlight">green</span> = low, <span class="tooltip-highlight">grey</span> = no prediction available. Predictions are based on satellite-derived features like NDBI, PV penetration, and land use.',
    'layer-radiation': 'The radiation layer shows how much solar radiation each cell receives compared to the city average (ROI). <span class="tooltip-highlight">Red</span> = above average, <span class="tooltip-highlight">blue</span> = below average. Based on <span class="tooltip-highlight">Meteosat</span> satellite data.',
    'sidebar-congestion-level': 'Congestion happens when too much electricity is pushed back into the grid from solar panels, overloading cables and transformers. The level (<span class="tooltip-highlight">High/Medium/Low</span>) is predicted by a <span class="tooltip-highlight">Random Forest classifier</span> trained on Amsterdam grid cells.',
    'sidebar-capacity-usage': `This cell's electricity consumption as a percentage of the highest-consuming cell in the dataset. A high value means this area draws a lot from the grid relative to others — relevant because high consumption can mask or amplify solar feed-in congestion.`,
    'sidebar-solar-radiation': `The estimated daily solar energy hitting a horizontal surface in this cell, measured in kilowatt-hours per square meter. Higher values mean more solar production and more potential feed-in to the grid.`,
    'sidebar-radiation-roi': `ROI (Return on Irradiance) compares this cell's solar radiation to the city average. <span class="tooltip-highlight">110%</span> means 10% more sun than average. Higher ROI in a congested cell confirms the solar-grid mismatch.`,
    'sidebar-cloud-factor': `A value between <span class="tooltip-highlight">0</span> and <span class="tooltip-highlight">1</span> representing how much cloud cover reduces incoming sunlight. <span class="tooltip-highlight">1.0</span> means perfectly clear sky. <span class="tooltip-highlight">0.6</span> means heavy cloud cover blocking 40% of potential radiation.`,
    'sidebar-building-density': `Derived from the <span class="tooltip-highlight">NDBI</span> (Normalized Difference Built-up Index) computed from <span class="tooltip-highlight">Sentinel-2</span> satellite bands. Higher values mean more built-up surface area in the cell, which generally correlates with more rooftop solar potential.`,
    'sidebar-pv-clustering': `Share of grid connections in this cell that have solar panels installed, from network operator data. High penetration on the same feeder causes more congestion than the same number of panels spread across feeders.`,
    'sidebar-land-use': `Residential areas generate solar power during the day when consumption is low, causing reverse power flow. Industrial zones consume during the day, absorbing solar production locally. The mismatch between generation and consumption patterns drives congestion.`,
    'layer-building-density': `Derived from the <span class="tooltip-highlight">NDBI</span> (Normalized Difference Built-up Index) from <span class="tooltip-highlight">Sentinel-2</span> imagery. More yellow = higher built-up density. Dense areas have more rooftops and higher solar feed-in potential.`,
    'layer-pv-clustering': `Share of grid connections with solar panels installed per cell, from network operator data. More red = higher PV penetration. Concentrated installations on one feeder stress the grid more than spread-out ones.`,
    'layer-land-use': `Classified using <span class="tooltip-highlight">Sentinel-2</span> spectral indices (NDVI, NDBI) combined with <span class="tooltip-highlight">CBS</span> population density. Purple = Residential/Mixed · Red = Dense Urban · Yellow = Industrial/Commercial · Green = Agricultural.`
};

const tooltipPopup = document.createElement('div');
tooltipPopup.className = 'tooltip-popup hidden';
document.body.appendChild(tooltipPopup);

function showTooltip(trigger, tooltipKey) {
    const tooltipHtml = tooltipTexts[tooltipKey];
    if (!tooltipHtml) return;
    tooltipPopup.innerHTML = tooltipHtml;
    tooltipPopup.classList.remove('hidden');
    tooltipPopup.style.left = '0px';
    tooltipPopup.style.top = '0px';

    const rect = trigger.getBoundingClientRect();
    const width = tooltipPopup.offsetWidth || 260;
    const height = tooltipPopup.offsetHeight || 80;
    const top = Math.max(12, rect.top + window.scrollY - height / 2 + rect.height / 2);
    const left = Math.min(window.innerWidth - width - 16, rect.right + 12);

    tooltipPopup.style.top = `${top}px`;
    tooltipPopup.style.left = `${left}px`;
}

function hideTooltip() {
    tooltipPopup.classList.add('hidden');
}

document.body.addEventListener('click', function(e) {
    const infoButton = e.target.closest('.info-button');
    if (infoButton) {
        e.stopPropagation();
        showTooltip(infoButton, infoButton.dataset.tooltipKey);
        return;
    }
    if (!e.target.closest('.tooltip-popup')) {
        hideTooltip();
    }
});

document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        hideTooltip();
    }
});

// Initialize map
const map = L.map('map').setView([52.37, 4.895], 12);

// Base layers
const osmLayer = L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_nolabels/{z}/{x}/{y}@2x.png', {
    attribution: '&copy; CartoDB',
    className: 'bright-tiles'
});
const labelOverlay = L.tileLayer('https://services.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}', {
    attribution: 'Labels © Esri',
    pane: 'overlayPane'
});

const satelliteLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
    attribution: 'Tiles © Esri'
});

satelliteLayer.addTo(map);
labelOverlay.addTo(map);
document.getElementById('standard-btn').classList.remove('active');
document.getElementById('satellite-btn').classList.add('active');

// Additional layers - per-cell overlays based on grid data
const cloudLayer = L.layerGroup();
const terrainLayer = L.layerGroup();
const greennessLayer = L.layerGroup();

function refreshCloudLayer() {
    cloudLayer.clearLayers();
    gridCells.forEach(cell => {
        if (cell.ndbiPct === null) return;
        const opacity = Math.max(0.02, Math.min(0.4, cell.ndbiPct / 100 * 0.4));
        L.rectangle([cell.sw, cell.ne], {
            color: 'none', fillColor: '#FACC15', fillOpacity: opacity, weight: 0
        }).addTo(cloudLayer);
    });
}

function refreshTerrainLayer() {
    terrainLayer.clearLayers();
    gridCells.forEach(cell => {
        if (cell.pvPct === null) return;
        const opacity = Math.max(0.02, Math.min(0.4, cell.pvPct / 100 * 0.4));
        L.rectangle([cell.sw, cell.ne], {
            color: 'none', fillColor: '#F87171', fillOpacity: opacity, weight: 0
        }).addTo(terrainLayer);
    });
}

function refreshGreenessLayer() {
    greennessLayer.clearLayers();
    const landUseColors = {
        'Residential / Mixed': '#818CF8',
        'Dense Urban': '#F87171',
        'Industrial / Commercial': '#FBBF24',
        'Agricultural / Green': '#34D399',
        'Mixed': '#94A3B8',
        'Unknown': 'transparent'
    };
    gridCells.forEach(cell => {
        const color = landUseColors[cell.landUse] || '#94A3B8';
        if (color === 'transparent') return;
        L.rectangle([cell.sw, cell.ne], {
            color: 'none', fillColor: color, fillOpacity: 0.25, weight: 0
        }).addTo(greennessLayer);
    });
}

// Layer controls
let layersVisible = {
    clouds: false,
    terrain: false,
    greenness: false
};

function setActiveMarker(marker) {
    if (activeMarker && activeMarker !== marker) {
        activeMarker.setStyle({ weight: 1 });
    }
    activeMarker = marker;
    marker.setStyle({ weight: 3 });
}

// Add draw and cell layers
const drawnItems = new L.FeatureGroup();
map.addLayer(drawnItems);

const cellLayer = new L.FeatureGroup();
map.addLayer(cellLayer);

// Navigation links
const mapNavLink = document.getElementById('map-nav');
const knowledgeNavLink = document.getElementById('knowledge-nav');
const pageMap = document.getElementById('page-map');
const pageKnowledge = document.getElementById('page-knowledge');

function showPage(page) {
    if (page === 'map') {
        pageMap.classList.remove('hidden');
        pageKnowledge.classList.add('hidden');
        mapNavLink.classList.add('active');
        knowledgeNavLink.classList.remove('active');
        map.invalidateSize();
    } else {
        pageMap.classList.add('hidden');
        pageKnowledge.classList.remove('hidden');
        mapNavLink.classList.remove('active');
        knowledgeNavLink.classList.add('active');
    }
}

mapNavLink.addEventListener('click', function(e) {
    e.preventDefault();
    showPage('map');
});

knowledgeNavLink.addEventListener('click', function(e) {
    e.preventDefault();
    showPage('knowledge');
});

showPage('map');

// Urban grid state
let gridCells = [];


function getRadiationColor(roi) {
    const lowBlue = { r: 35, g: 117, b: 255 };
    const highRed = { r: 239, g: 76, b: 64 };
    const white = { r: 255, g: 255, b: 255 };

    if (roi <= 90) {
        return `rgb(${lowBlue.r},${lowBlue.g},${lowBlue.b})`;
    }
    if (roi < 100) {
        const t = (roi - 90) / 10;
        const r = Math.round(lowBlue.r * (1 - t) + white.r * t);
        const g = Math.round(lowBlue.g * (1 - t) + white.g * t);
        const b = Math.round(lowBlue.b * (1 - t) + white.b * t);
        return `rgb(${r},${g},${b})`;
    }
    if (roi <= 110) {
        const t = (roi - 100) / 10;
        const r = Math.round(white.r * (1 - t) + highRed.r * t);
        const g = Math.round(white.g * (1 - t) + highRed.g * t);
        const b = Math.round(white.b * (1 - t) + highRed.b * t);
        return `rgb(${r},${g},${b})`;
    }
    return `rgb(${highRed.r},${highRed.g},${highRed.b})`;
}

function getRadiationOpacity(roi) {
    return Math.max(0.2, Math.min(0.6, Math.abs(roi - 100) / 20 * 0.6));
}

function getCongestionColor(level) {
    if (level === 'high') return '#F87171';
    if (level === 'medium') return '#FBBF24';
    if (level === 'low') return '#34D399';
    return '#6B7280';
}

function updateGridStyle() {
    cellLayer.clearLayers();

    gridCells.forEach(cell => {
        let color;
        let opacity;

        if (activeMode === 'congestion') {
            color = getCongestionColor(cell.congestion);
            opacity = 0.35;
        } else {
            color = getRadiationColor(cell.roi);
            opacity = getRadiationOpacity(cell.roi);
        }

        const rect = L.rectangle([cell.sw, cell.ne], {
            color: color,
            fillColor: color,
            fillOpacity: opacity,
            weight: selectedCell === cell ? 3 : 1
        });

        rect.on('mouseover', () => {
            rect.setStyle({ weight: 2.5 });
            const congestionLabel = cell.congestion
                ? cell.congestion.charAt(0).toUpperCase() + cell.congestion.slice(1)
                : 'No data';
            const tooltipText = activeMode === 'congestion'
                ? `${cell.id} • Congestion: ${congestionLabel}`
                : `${cell.id} • ROI ${cell.roi.toFixed(1)}%`;
            rect.bindTooltip(tooltipText, { permanent: false }).openTooltip();
        });

        rect.on('mouseout', () => {
            rect.setStyle({ weight: selectedCell === cell ? 3 : 1 });
            rect.closeTooltip();
        });

        rect.on('click', (e) => {
            selectedCell = cell;
            setActiveLayerMode('congestion'); // Always switch to congestion mode when selecting a cell
            setActiveMarker(rect);
            updateSidebar(cell);
            document.getElementById('empty-state').style.display = 'none';
        });

        cell.rect = rect;
        rect.addTo(cellLayer);
    });

    updateLegend();
    
    // Refresh overlay layers if enabled
    if (layersVisible.clouds) refreshCloudLayer();
    if (layersVisible.terrain) refreshTerrainLayer();
    if (layersVisible.greenness) refreshGreenessLayer();
}

let legendControl;

function updateLegend() {
    if (!legendControl || !legendControl._div) return;
    const legendDiv = legendControl._div;

    if (activeMode === 'congestion') {
        legendDiv.innerHTML = `
            <div class="legend-title">Congestion level</div>
            <div class="legend-item"><div class="legend-color" style="background: #F87171;"></div><span>High</span></div>
            <div class="legend-item"><div class="legend-color" style="background: #FBBF24;"></div><span>Medium</span></div>
            <div class="legend-item"><div class="legend-color" style="background: #34D399;"></div><span>Low</span></div>
            <div class="legend-item"><div class="legend-color" style="background: #6B7280;"></div><span>No data</span></div>
        `;
    } else {
        legendDiv.innerHTML = `
            <div class="legend-title">Radiation ROI</div>
            <div class="legend-gradient"></div>
            <div style="display:flex; justify-content:space-between; font-size:12px; color:#4B5563; margin-top:4px;"><span>90%</span><span>100%</span><span>110%</span></div>
        `;
    }
}

function updateMapOutput(cell) {
    // map-output UI panel removed as per user request; this function is now a no-op.
}

let geojsonData = null;

async function loadGridData() {
    const response = await fetch(GRID_GEOJSON_URL);
    geojsonData = await response.json();
    buildGridCells(52.30, 4.77, 52.43, 5.00);
}

function buildGridCells(swLat, swLng, neLat, neLng) {
    selectedCell = null;
    gridCells = [];
    geojsonData.features.forEach((feature) => {
        const props = feature.properties;
        const coords = feature.geometry.coordinates[0];

        const lats = coords.map(c => c[1]);
        const lngs = coords.map(c => c[0]);
        const cellSwLat = Math.min(...lats);
        const cellSwLng = Math.min(...lngs);
        const cellNeLat = Math.max(...lats);
        const cellNeLng = Math.max(...lngs);
        const centerLat = (cellSwLat + cellNeLat) / 2;
        const centerLng = (cellSwLng + cellNeLng) / 2;

        if (centerLat < swLat || centerLat > neLat || centerLng < swLng || centerLng > neLng) return;

        const rawLabel = props.congestion_label || props.pred_label || null;
        const congestion = rawLabel ? rawLabel.toLowerCase() : null;

        gridCells.push({
            id: `cell-${props.cell_id}`,
            sw: [cellSwLat, cellSwLng],
            ne: [cellNeLat, cellNeLng],
            center: [centerLat, centerLng],
            congestion: congestion,
            congestionScore: props.congestion_score ?? null,
            consumptionPct: props.consumption_pct ?? null,
            ndbiPct: props.ndbi_pct ?? null,
            pvPct: props.pv_penetration_pct ?? null,
            feedinRatio: props.feedin_ratio ?? null,
            landUse: props.land_use_type || 'Unknown',
            roi: 85 + Math.random() * 30,
            irradiance: 3.5 + Math.random() * 1.5,
            cloudFactor: 0.6 + Math.random() * 0.35,
            rect: null
        });
    });

    updateGridStyle();
    document.getElementById('empty-state').style.display = 'none';
}

const drawControl = new L.Control.Draw({
    edit: { featureGroup: drawnItems },
    draw: { polygon: false, polyline: false, circle: false, marker: false, circlemarker: false, rectangle: true }
});
map.addControl(drawControl);

// Add click handler to cancel drawing
map.on('click', function(e) {
    // Cancel rectangle drawing if active
    if (drawControl._toolbars && drawControl._toolbars.draw && drawControl._toolbars.draw._modes.rectangle) {
        const mode = drawControl._toolbars.draw._modes.rectangle;
        if (mode.handler && mode.handler.enabled()) {
            mode.handler.disable();
        }
    }
});

map.on(L.Draw.Event.CREATED, function(event) {
    drawnItems.clearLayers();
    drawnItems.addLayer(event.layer);
    const bounds = event.layer.getBounds();
    buildGridCells(bounds.getSouth(), bounds.getWest(), bounds.getNorth(), bounds.getEast());
});

// Legend
legendControl = L.control({ position: 'bottomleft' });
legendControl.onAdd = function() {
    this._div = L.DomUtil.create('div', 'legend');
    return this._div;
};
legendControl.addTo(map);
updateLegend();

// Generate initial grid on page load
window.addEventListener('load', function() {
    loadGridData();
});

// Toggle layers
function setActiveLayerMode(mode) {
    activeMode = mode;
    document.getElementById('congestion-btn').classList.toggle('active', mode === 'congestion');
    document.getElementById('radiation-btn').classList.toggle('active', mode === 'radiation');
    document.querySelector('.sidebar-title').textContent = mode === 'congestion' ? 'Area details' : 'Radiation details';
    updateGridStyle();
    if (selectedCell) {
        updateSidebar(selectedCell);
        updateMapOutput(selectedCell);
    }
}

document.getElementById('congestion-btn').addEventListener('click', () => setActiveLayerMode('congestion'));
document.getElementById('radiation-btn').addEventListener('click', () => setActiveLayerMode('radiation'));

document.getElementById('standard-btn').addEventListener('click', function() {
    map.removeLayer(satelliteLayer);
    map.addLayer(osmLayer);
    if (!map.hasLayer(labelOverlay)) {
        labelOverlay.addTo(map);
    }
    this.classList.add('active');
    document.getElementById('satellite-btn').classList.remove('active');
});

document.getElementById('satellite-btn').addEventListener('click', function() {
    map.removeLayer(osmLayer);
    map.addLayer(satelliteLayer);
    if (!map.hasLayer(labelOverlay)) {
        labelOverlay.addTo(map);
    }
    this.classList.add('active');
    document.getElementById('standard-btn').classList.remove('active');
});

// City search with suggestions
const citySearchInput = document.getElementById('city-search-input');
const suggestionsDiv = document.getElementById('suggestions');

citySearchInput.addEventListener('input', function() {
    const query = this.value.toLowerCase();
    let matches = cities.filter(city => city.toLowerCase().includes(query));
    if (matches.length === 0 && query.length > 2) {
        // Simple fuzzy match for misspelling
        const levenshtein = (a, b) => {
            const matrix = [];
            for (let i = 0; i <= b.length; i++) matrix[i] = [i];
            for (let j = 0; j <= a.length; j++) matrix[0][j] = j;
            for (let i = 1; i <= b.length; i++) {
                for (let j = 1; j <= a.length; j++) {
                    if (b.charAt(i - 1) === a.charAt(j - 1)) {
                        matrix[i][j] = matrix[i - 1][j - 1];
                    } else {
                        matrix[i][j] = Math.min(
                            matrix[i - 1][j - 1] + 1,
                            matrix[i][j - 1] + 1,
                            matrix[i - 1][j] + 1
                        );
                    }
                }
            }
            return matrix[b.length][a.length];
        };
        const suggestions = cities.map(city => ({ city, distance: levenshtein(query, city.toLowerCase()) }))
            .filter(item => item.distance <= 2)
            .sort((a, b) => a.distance - b.distance)
            .slice(0, 3);
        if (suggestions.length > 0) {
            matches = [`Did you mean: ${suggestions.map(s => s.city).join(', ')}`];
        }
    }
    if (matches.length > 0 && query.length > 0) {
        suggestionsDiv.innerHTML = matches.map(match => `<div class="suggestion-item">${match}</div>`).join('');
        suggestionsDiv.style.display = 'block';
    } else {
        suggestionsDiv.style.display = 'none';
    }
});

suggestionsDiv.addEventListener('click', function(e) {
    if (e.target.classList.contains('suggestion-item')) {
        const text = e.target.textContent;
        if (text.startsWith('Did you mean:')) {
            const suggested = text.replace('Did you mean: ', '').split(', ')[0];
            citySearchInput.value = suggested;
            suggestionsDiv.style.display = 'none';
            selectedCity = suggested;
            map.setView(cityCoords[selectedCity] || [52.37, 4.895], 12);
        } else {
            citySearchInput.value = text;
            suggestionsDiv.style.display = 'none';
            selectedCity = text;
            map.setView(cityCoords[selectedCity] || [52.37, 4.895], 12);
        }
    }
});

// Date selection
document.getElementById('date-input').addEventListener('change', function() {
    selectedDate = this.value;
    // In a real app, this would fetch new data for the selected date
});

// Layer toggles
// document.getElementById('cloud-checkbox').addEventListener('change', function() {
//     if (this.checked) {
//         cloudLayer.addTo(map);
//         layersVisible.clouds = true;
//     } else {
//         map.removeLayer(cloudLayer);
//         layersVisible.clouds = false;
//     }
// });

document.getElementById('cloud-checkbox').addEventListener('change', function() {
    if (this.checked) {
        refreshCloudLayer();
        cloudLayer.addTo(map);
        layersVisible.clouds = true;
    } else {
        map.removeLayer(cloudLayer);
        layersVisible.clouds = false;
    }
});

document.getElementById('terrain-checkbox').addEventListener('change', function() {
    if (this.checked) {
        refreshTerrainLayer();
        terrainLayer.addTo(map);
        layersVisible.terrain = true;
    } else {
        map.removeLayer(terrainLayer);
        layersVisible.terrain = false;
    }
});

document.getElementById('greenness-checkbox').addEventListener('change', function() {
    if (this.checked) {
        refreshGreenessLayer();
        greennessLayer.addTo(map);
        layersVisible.greenness = true;
    } else {
        map.removeLayer(greennessLayer);
        layersVisible.greenness = false;
    }
});

// Top search (global)
document.getElementById('search-input').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        const query = this.value.trim();
        if (query.includes(',')) {
            // Coordinates
            const [lat, lng] = query.split(',').map(s => parseFloat(s.trim()));
            if (!isNaN(lat) && !isNaN(lng)) {
                map.setView([lat, lng], 15);
            }
        } else {
            // City name
            const queryLower = query.toLowerCase();
            const cityKey = Object.keys(cityCoords).find(key => key.toLowerCase() === queryLower);
            map.setView(cityCoords[cityKey] || [52.37, 4.895], 12);
        }
    }
});

// Update sidebar with grid cell info
function updateSidebar(cell) {
    const dynamicContent = document.getElementById('dynamic-content');
    if (!cell) {
        dynamicContent.innerHTML = `
            <div class="empty-state" id="empty-state">
                <div class="empty-icon">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/>
                        <circle cx="12" cy="10" r="3"/>
                    </svg>
                </div>
                <p>Draw a rectangle on the map to see grid cell analysis.</p>
            </div>
        `;
        return;
    }

    document.querySelector('.sidebar-title').textContent = 'Area details';

    const congestionLevel = cell.congestion;
    const congestionClass = congestionLevel ? congestionLevel + '-badge' : 'no-data-badge';
    const congestionDisplay = congestionLevel
        ? congestionLevel.charAt(0).toUpperCase() + congestionLevel.slice(1)
        : 'No data';
    const roi = cell.roi;

    const cellId = cell.id.replace('cell-', '');

    const buildingDensity = cell.ndbiPct !== null ? cell.ndbiPct.toFixed(1) : null;
    const pvClustering = cell.pvPct !== null ? cell.pvPct.toFixed(1) : null;
    const landUse = cell.landUse || 'Unknown';
    const consumptionPct = cell.consumptionPct !== null ? cell.consumptionPct.toFixed(1) : null;

    // Build content based on active mode
    if (activeMode === 'congestion') {
        dynamicContent.innerHTML = `
            <div class="area-banner">
                <h3 class="area-name">Cell ${cellId}</h3>
                <p class="area-subtitle">${selectedCity}, Netherlands</p>
            </div>
            <div class="coords-row">
                <div class="coord-chip"><div class="coord-label">Latitude</div><div class="coord-value">${cell.center[0].toFixed(4)}</div></div>
                <div class="coord-chip"><div class="coord-label">Longitude</div><div class="coord-value">${cell.center[1].toFixed(4)}</div></div>
            </div>
            <div class="card">
                <div class="icon-box" style="background: ${congestionLevel === 'high' ? '#FEF2F2' : congestionLevel === 'medium' ? '#FFFBEB' : congestionLevel === 'low' ? '#ECFDF5' : '#F3F4F6'};">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="${congestionLevel === 'high' ? '#F87171' : congestionLevel === 'medium' ? '#FBBF24' : congestionLevel === 'low' ? '#34D399' : '#6B7280'}" stroke-width="2"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>
                </div>
                <div class="card-content">
                    <div class="card-label">Congestion level <button type="button" class="info-button" data-tooltip-key="sidebar-congestion-level" aria-label="Congestion level info">?</button></div>
                    <div class="congestion-badge ${congestionClass}"><div class="badge-dot"></div><span>${congestionDisplay}</span></div>
                </div>
            </div>
            <div class="card">
                <div class="icon-box" style="background: rgba(237,231,113,0.12); border: 1px solid #EDE771;">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#EDE771" stroke-width="2"><rect x="2" y="6" width="20" height="12" rx="2"/><circle cx="10" cy="12" r="2"/><path d="M10 8v8"/><path d="M14 12h6"/></svg>
                </div>
                <div class="card-content">
                    <div class="card-label">Consumption intensity <button type="button" class="info-button" data-tooltip-key="sidebar-capacity-usage" aria-label="Consumption intensity info">?</button></div>
                    <div class="card-value">${consumptionPct !== null ? consumptionPct + '%' : 'No data'}</div>
                    <div class="card-caption">relative to highest-consuming cell</div>
                </div>
            </div>
            <div class="card">
                <div class="icon-box" style="background: rgba(237,231,113,0.12); border: 1px solid #EDE771;">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#EDE771" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M9 3v18"/><path d="M15 3v18"/></svg>
                </div>
                <div class="card-content">
                    <div class="card-label">Building density</div>
                    <div class="card-value">${buildingDensity !== null ? buildingDensity + '%' : 'No data'}</div>
                    <div class="card-caption">built-up density from satellite (NDBI)</div>
                </div>
            </div>
            <div class="card">
                <div class="icon-box" style="background: rgba(248,113,113,0.12); border: 1px solid #F87171;">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#F87171" stroke-width="2"><circle cx="12" cy="12" r="2"/><circle cx="19" cy="12" r="2"/><circle cx="5" cy="12" r="2"/><circle cx="12" cy="5" r="2"/><circle cx="12" cy="19" r="2"/></svg>
                </div>
                <div class="card-content">
                    <div class="card-label">PV penetration <button type="button" class="info-button" data-tooltip-key="sidebar-pv-clustering" aria-label="PV penetration info">?</button></div>
                    <div class="card-value">${pvClustering !== null ? pvClustering + '%' : 'No data'}</div>
                    <div class="card-caption">of connections with solar panels</div>
                </div>
            </div>
            <div class="card">
                <div class="icon-box" style="background: rgba(129,140,248,0.12); border: 1px solid #818CF8;">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#818CF8" stroke-width="2"><path d="M3 3h7v7H3z"/><path d="M14 3h7v7h-7z"/><path d="M14 14h7v7h-7z"/><path d="M3 14h7v7H3z"/></svg>
                </div>
                <div class="card-content">
                    <div class="card-label">Land use type <button type="button" class="info-button" data-tooltip-key="sidebar-land-use" aria-label="Land use type info">?</button></div>
                    <div class="card-value">${landUse}</div>
                    <div class="card-caption">derived from NDVI + NDBI + CBS population</div>
                </div>
            </div>
            <div class="info-row"><span class="info-label">Date:</span><span class="info-value">${selectedDate}</span></div>
        `;
    } else {
        // Radiation mode
        const roiBgColor = roi >= 100 ? 'rgba(226,75,74,0.12)' : 'rgba(55,138,221,0.12)';
        const roiBorderColor = roi >= 100 ? '#E24B4A' : '#378ADD';
        const roiStroke = roi >= 100 ? '#E24B4A' : '#378ADD';
        
        dynamicContent.innerHTML = `
            <div class="area-banner">
                <h3 class="area-name">Cell ${cellId}</h3>
                <p class="area-subtitle">${selectedCity}, Netherlands</p>
            </div>
            <div class="coords-row">
                <div class="coord-chip"><div class="coord-label">Latitude</div><div class="coord-value">${cell.center[0].toFixed(4)}</div></div>
                <div class="coord-chip"><div class="coord-label">Longitude</div><div class="coord-value">${cell.center[1].toFixed(4)}</div></div>
            </div>
            <div class="card">
                <div class="icon-box" style="background: ${roiBgColor}; border: 1px solid ${roiBorderColor};">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="${roiStroke}" stroke-width="2"><circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="M4.93 4.93l1.41 1.41"/><path d="M17.66 17.66l1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="M6.34 6.34L4.93 4.93"/><path d="M19.07 19.07l1.41 1.41"/></svg>
                </div>
                <div class="card-content">
                    <div class="card-label">Radiation ROI <button type="button" class="info-button" data-tooltip-key="sidebar-radiation-roi" aria-label="Radiation ROI info">?</button></div>
                    <div class="card-value">${roi.toFixed(1)}%</div>
                    <div class="card-caption">relative to city average</div>
                </div>
            </div>
            <div class="card">
                <div class="icon-box" style="background: rgba(251,191,36,0.12); border: 1px solid #FBBF24;">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#FBBF24" stroke-width="2"><circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="M4.93 4.93l1.41 1.41"/><path d="M17.66 17.66l1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="M6.34 6.34L4.93 4.93"/><path d="M19.07 19.07l1.41 1.41"/></svg>
                </div>
                <div class="card-content">
                    <div class="card-label">Solar radiation estimate <button type="button" class="info-button" data-tooltip-key="sidebar-solar-radiation" aria-label="Solar radiation estimate info">?</button></div>
                    <div class="card-value">${cell.irradiance.toFixed(1)} kWh/m2</div>
                    <div class="card-caption">daily horizontal irradiance</div>
                </div>
            </div>
            <div class="card">
                <div class="icon-box" style="background: rgba(55,138,221,0.12); border: 1px solid #378ADD;">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#378ADD" stroke-width="2"><path d="M18 10a6 6 0 10-12 0"/><path d="M12 2v4"/><path d="M4.93 4.93l2.83 2.83"/><path d="M19.07 4.93l-2.83 2.83"/></svg>
                </div>
                <div class="card-content">
                    <div class="card-label">Cloud factor <button type="button" class="info-button" data-tooltip-key="sidebar-cloud-factor" aria-label="Cloud factor info">?</button></div>
                    <div class="card-value">${cell.cloudFactor.toFixed(2)}</div>
                    <div class="card-caption">1.0 = clear sky, lower = more cloud</div>
                </div>
            </div>
            <div class="card">
                <div class="icon-box" style="background: ${congestionLevel === 'high' ? '#FEF2F2' : congestionLevel === 'medium' ? '#FFFBEB' : congestionLevel === 'low' ? '#ECFDF5' : '#F3F4F6'};">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="${congestionLevel === 'high' ? '#F87171' : congestionLevel === 'medium' ? '#FBBF24' : congestionLevel === 'low' ? '#34D399' : '#6B7280'}" stroke-width="2"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>
                </div>
                <div class="card-content">
                    <div class="card-label">Congestion in this cell</div>
                    <div class="congestion-badge ${congestionClass}"><div class="badge-dot"></div><span>${congestionDisplay}</span></div>
                </div>
            </div>
            <div class="roi-scale"></div>
            <div class="info-row"><span class="info-label">Date:</span><span class="info-value">${selectedDate}</span></div>
        `;
    }
}