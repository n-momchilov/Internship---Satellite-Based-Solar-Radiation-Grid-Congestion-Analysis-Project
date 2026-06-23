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
let selectedDate = document.getElementById('date-input')?.value || new Date().toISOString().split('T')[0];
const SEASONAL_GHI = { winter: 34.3, spring: 178.4, summer: 223.9, autumn: 79.5 };
const SEASONAL_GHI_BY_CELL = typeof SEASONAL_GHI_BY_CELL_INLINE !== 'undefined' ? SEASONAL_GHI_BY_CELL_INLINE : {};
const GHI_SEASONS = ['spring', 'summer', 'autumn', 'winter'];
let GHI_SEASON_STATS = {};
let GHI_CELL_SPREADS = {};

function getSeasonLabel(dateStr) {
    const d = new Date(dateStr);
    const month = d.getMonth() + 1; // 1-12
    const year = d.getFullYear();
    if (month >= 6 && month <= 8)  return 'Summer ' + year;
    if (month >= 9 && month <= 11) return 'Autumn ' + year;
    if (month <= 2)                return 'Winter ' + (year - 1) + '–' + year;
    if (month === 12)              return 'Winter ' + year + '–' + (year + 1);
    return 'Spring ' + year; // March, April, May
}
let activeMode = 'congestion';
let selectedCell = null;
let activeMarker = null;
let CITY_MEDIAN_PV = null;
let ignoreMapClickUntil = 0;
let showEstimatedStressCells = true;

const tooltipTexts = {
    'layer-congestion': 'The congestion layer shows predicted grid overload risk per 1×1 km cell. <span class="tooltip-highlight">Red</span> = high risk, <span class="tooltip-highlight">orange</span> = medium, <span class="tooltip-highlight">green</span> = low, <span class="tooltip-highlight">grey</span> = no prediction available. Predictions are based on satellite-derived features like NDBI, PV penetration, and land use.',
    'layer-radiation': 'Solar feed-in stress combines each cell\'s PV share with seasonal <span class="tooltip-highlight">GHI</span>. It changes with the selected date: summer is hotter, winter is calmer.',
    'intro-ghi': 'GHI (Global Horizontal Irradiance): the total solar energy hitting a flat surface, measured in watts per square metre (W/m2). Higher means more sunlight.',
    'tier-ndbi': 'NDBI (Normalized Difference Built-up Index): a satellite measure of how built-up a cell is. Higher means more buildings and paved surface, less greenery.',
    'tier-confidence': 'How is this accurate? The model scores about F1 0.58 on held-out data, not perfect but consistent. See the Knowledge page for how it\'s validated.',
    'city-median-pv': 'Why an estimate? This cell has no local PV data, so the city-median PV share is used. It\'s an approximation, not a measurement for this cell.',
    'sidebar-congestion-level': 'Congestion happens when too much electricity is pushed back into the grid from solar panels, overloading cables and transformers. The level (<span class="tooltip-highlight">High/Medium/Low</span>) is predicted by a <span class="tooltip-highlight">Random Forest classifier</span> trained on Amsterdam grid cells.',
    'sidebar-capacity-usage': `This cell's electricity consumption as a percentage of the highest-consuming cell in the dataset. A high value means this area draws a lot from the grid relative to others — relevant because high consumption can mask or amplify solar feed-in congestion.`,
    'sidebar-solar-radiation': `Average daily solar energy reaching a horizontal surface during summer months. Derived from Meteosat SEVIRI satellite observations (CM SAF SARAH-3 product). Higher values mean more solar energy available for PV generation.`,
    'sidebar-seasonal-variation': `How many times more solar energy summer receives compared to winter. Higher values mean solar output drops more dramatically in winter, creating larger seasonal swings in grid feed-in. For Amsterdam this is typically 6-7x.`,
    'sidebar-congestion-driver': `Classification of what drives congestion in this cell. Solar-driven areas need smart inverters and batteries. Consumption-driven areas need cable upgrades and new substations.`,
    'sidebar-investment-priority': `Combined priority score based on congestion risk (50%), solar radiation potential (25%), and PV installation density (25%). High priority cells need grid investment most urgently.`,
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

document.body.addEventListener('mouseover', function(e) {
    const infoButton = e.target.closest('.info-button');
    if (infoButton) showTooltip(infoButton, infoButton.dataset.tooltipKey);
});

document.body.addEventListener('mouseout', function(e) {
    const infoButton = e.target.closest('.info-button');
    if (infoButton && !infoButton.contains(e.relatedTarget)) hideTooltip();
});

document.body.addEventListener('focusin', function(e) {
    const infoButton = e.target.closest('.info-button');
    if (infoButton) showTooltip(infoButton, infoButton.dataset.tooltipKey);
});

document.body.addEventListener('focusout', function(e) {
    const infoButton = e.target.closest('.info-button');
    if (infoButton) hideTooltip();
});

document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        hideTooltip();
    }
});

function formatGhiSpread(spread) {
    if (spread === null || spread === undefined || Number.isNaN(spread)) return '...';
    const roundedUp = Math.ceil((spread + 0.000001) * 10) / 10;
    return roundedUp.toFixed(1);
}

function ghiInfoButton() {
    return '<button type="button" class="info-button intro-info-button" data-tooltip-key="intro-ghi" aria-label="GHI definition">?</button>';
}

function ndbiInfoButton() {
    return '<button type="button" class="info-button intro-info-button" data-tooltip-key="tier-ndbi" aria-label="NDBI definition">?</button>';
}

function confidenceInfoButton() {
    return '<button type="button" class="info-button intro-info-button" data-tooltip-key="tier-confidence" aria-label="Model confidence definition">?</button>';
}

function cityMedianInfoButton() {
    return '<button type="button" class="info-button intro-info-button" data-tooltip-key="city-median-pv" aria-label="City-median PV estimate definition">?</button>';
}

function renderIntro() {
    const introBox = document.getElementById('intro-box');
    if (!introBox) return;

    if (activeMode === 'stress') {
        introBox.innerHTML = `
            <h2 class="intro-heading">Solar Feed-in Stress</h2>
            <p class="intro-text">
                This view shows where solar panels create the most feed-in pressure on the grid, combining each cell's PV share with seasonal sunlight (<span class="intro-term">GHI</span>${ghiInfoButton()}).
                It changes with the date you pick: high in summer, low in winter.
                Sunlight itself is uniform across the city, so the pattern here is driven by where panels are concentrated, not by sunlight.
            </p>
        `;
        return;
    }

    introBox.innerHTML = `
        <h2 class="intro-heading">Amsterdam Grid Congestion Analysis</h2>
        <p class="intro-text">
            This map predicts grid congestion risk across Amsterdam at 1&times;1 km using Sentinel-2 satellite imagery and a Random Forest model.
            Sunlight is nearly uniform across the city, so congestion comes from where power is consumed and where solar is installed.
        </p>
        <ol class="intro-steps">
            <li><strong>Search and pick a location in the sidebar</strong> to center the map on the area you want.</li>
            <li><strong>Select a date</strong> to choose which season&#39;s satellite imagery the map uses.</li>
            <li><strong>Click Run Analysis</strong> to load and classify all ~2,200 grid cells into Low / Medium / High congestion risk.</li>
            <li><strong>Toggle the layers</strong> (Building density, PV penetration, Land use) to see what drives congestion in each area.</li>
            <li><strong>Click any cell on the map</strong> to see its full breakdown below, including the model prediction, the energy data, and the solar feed-in stress for the selected date.</li>
            <li><strong>Switch to the Solar feed-in stress view</strong> to see how seasonal sunlight and local PV adoption combine into feed-in pressure.</li>
        </ol>
    `;
}

renderIntro();

// Initialize map
const map = L.map('map').setView([52.37, 4.895], 12);

// Base layers
const osmLayer = L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; CartoDB',
    className: 'standard-tiles'
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
            color: 'none', fillColor: '#FACC15', fillOpacity: opacity, weight: 0,
            interactive: false
        }).addTo(cloudLayer);
    });
}

function refreshTerrainLayer() {
    terrainLayer.clearLayers();
    gridCells.forEach(cell => {
        if (cell.pvPct === null) return;
        const opacity = Math.max(0.02, Math.min(0.4, cell.pvPct / 100 * 0.4));
        L.rectangle([cell.sw, cell.ne], {
            color: 'none', fillColor: '#F87171', fillOpacity: opacity, weight: 0,
            interactive: false
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
            color: 'none', fillColor: color, fillOpacity: 0.25, weight: 0,
            interactive: false
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
    if (marker) {
        marker.setStyle({ weight: 3 });
    }
}

function stopMapDeselectFromCellClick(e, preventDefault = false) {
    ignoreMapClickUntil = performance.now() + 600;
    if (e?.originalEvent) {
        L.DomEvent.stopPropagation(e.originalEvent);
        if (preventDefault) L.DomEvent.preventDefault(e.originalEvent);
    }
}

// Add draw and cell layers
const drawnItems = new L.FeatureGroup();
map.addLayer(drawnItems);

const cellLayer = new L.FeatureGroup();
map.addLayer(cellLayer);

// Urban grid state
let gridCells = [];
let analysisComplete = false;


function getCongestionColor(level) {
    if (level === 'high') return '#F87171';
    if (level === 'medium') return '#FBBF24';
    if (level === 'low') return '#34D399';
    return '#6B7280';
}

function seasonalGhiFromSources(cellId, radProps, season) {
    const inline = SEASONAL_GHI_BY_CELL[String(cellId)] || SEASONAL_GHI_BY_CELL[cellId] || {};
    const field = `GHI_${season}`;
    const val = inline[field] ?? radProps[field] ?? null;
    return val === null || val === undefined || Number.isNaN(Number(val)) ? null : Number(val);
}

function getCellSeasonalGhi(cell, season = dateToSeason(selectedDate)) {
    const field = {
        spring: 'ghiSpring',
        summer: 'ghiSummer',
        autumn: 'ghiAutumn',
        winter: 'ghiWinter'
    }[season];
    const val = field ? cell[field] : null;
    return val === null || val === undefined || Number.isNaN(Number(val)) ? null : Number(val);
}

function clipPct(value) {
    if (value === null || value === undefined || Number.isNaN(Number(value))) return null;
    return Math.min(100, Math.max(0, Number(value)));
}

function interpolateColor(startHex, endHex, t) {
    const clean = (hex) => hex.replace('#', '');
    const start = clean(startHex).match(/.{2}/g).map(v => parseInt(v, 16));
    const end = clean(endHex).match(/.{2}/g).map(v => parseInt(v, 16));
    const rgb = start.map((value, index) => Math.round(value + (end[index] - value) * t));
    return `rgb(${rgb[0]}, ${rgb[1]}, ${rgb[2]})`;
}

function parseCssRgb(color) {
    if (!color) return null;
    if (color.startsWith('#')) {
        const clean = color.replace('#', '');
        return clean.match(/.{2}/g).map(v => parseInt(v, 16));
    }
    const match = color.match(/^rgb\((\d+),\s*(\d+),\s*(\d+)\)$/);
    return match ? [Number(match[1]), Number(match[2]), Number(match[3])] : null;
}

function mixColor(color, targetHex, amount) {
    const source = parseCssRgb(color);
    const target = parseCssRgb(targetHex);
    if (!source || !target) return color;
    const rgb = source.map((value, index) => Math.round(value + (target[index] - value) * amount));
    return `rgb(${rgb[0]}, ${rgb[1]}, ${rgb[2]})`;
}

function hasStressEnergyContext(cell) {
    return cell.consumptionKwh !== null
        && cell.consumptionKwh !== undefined
        && !Number.isNaN(Number(cell.consumptionKwh));
}

function getSolarFeedInStress(cell) {
    const season = dateToSeason(selectedDate);
    const hasOwnPV = clipPct(cell.pvPct) !== null;
    const hasEnergyContext = hasStressEnergyContext(cell);
    const canUseFallback = !hasOwnPV && hasEnergyContext;
    const pvPct = hasOwnPV ? clipPct(cell.pvPct) : canUseFallback ? clipPct(CITY_MEDIAN_PV) : null;
    if (pvPct === null) {
        return {
            norm: null,
            level: 'No data',
            pvPct: null,
            hasOwnPV,
            hasEnergyContext,
            usesFallback: false,
            ghi: SEASONAL_GHI[season],
            season
        };
    }

    const ghi = SEASONAL_GHI[season];
    const pvFrac = pvPct / 100;
    const solarIndexNorm = (pvFrac * ghi) / 223.9;
    const level = solarIndexNorm < 0.04 ? 'Low' : solarIndexNorm < 0.12 ? 'Moderate' : 'High';
    return { norm: solarIndexNorm, level, pvPct, hasOwnPV, hasEnergyContext, usesFallback: !hasOwnPV, ghi, season };
}

function getStressColor(norm) {
    if (norm === null || norm === undefined) return '#94A3B8';
    if (norm < 0.04) {
        return interpolateColor('#dbeafe', '#38bdf8', Math.max(0, Math.min(1, norm / 0.04)));
    }
    if (norm < 0.12) {
        return interpolateColor('#fef3c7', '#f59e0b', Math.max(0, Math.min(1, (norm - 0.04) / 0.08)));
    }
    return interpolateColor('#fca5a5', '#dc2626', Math.max(0, Math.min(1, (norm - 0.12) / 0.28)));
}

function getStressDisplayColor(stressInfo) {
    const baseColor = getStressColor(stressInfo.norm);
    if (stressInfo.norm === null || stressInfo.hasOwnPV) return baseColor;
    return mixColor(baseColor, '#94a3b8', 0.62);
}

function formatStressIndex(norm) {
    return Math.round(norm * 100);
}

function getStressTooltip(cell) {
    const stress = getSolarFeedInStress(cell);
    if (stress.norm === null) {
        return `${cell.id} - Solar feed-in stress: No data`;
    }
    const seasonName = stress.season.charAt(0).toUpperCase() + stress.season.slice(1);
    const pvSource = stress.hasOwnPV ? 'local PV' : 'city-median PV';
    return `${cell.id} - ${seasonName} solar feed-in stress: ${stress.level} (stress index ${formatStressIndex(stress.norm)}/100, ${stress.pvPct.toFixed(1)}% ${pvSource})`;
}

function updateGridStyle() {
    cellLayer.clearLayers();

    gridCells.forEach(cell => {
        let color;
        let opacity;
        let strokeColor;
        let dashArray = null;

        if (activeMode === 'congestion') {
            color = getCongestionColor(cell.congestion);
            opacity = 0.35;
            strokeColor = color;
        } else {
            const stressInfo = getSolarFeedInStress(cell);
            if (stressInfo.usesFallback && !showEstimatedStressCells) {
                cell.rect = null;
                return;
            }
            if (stressInfo.norm === null) {
                color = '#6B7280';
                opacity = 0.08;
                strokeColor = '#6B7280';
            } else {
                color = getStressDisplayColor(stressInfo);
                // Only cells with energy context but missing local PV use the city median;
                // muting them keeps estimates from overpowering measured cells.
                opacity = stressInfo.usesFallback ? 0.24 : 0.66;
                strokeColor = stressInfo.usesFallback ? '#94A3B8' : color;
                dashArray = stressInfo.usesFallback ? '4 3' : null;
            }
        }

        const rect = L.rectangle([cell.sw, cell.ne], {
            color: strokeColor,
            fillColor: color,
            fillOpacity: opacity,
            weight: selectedCell === cell ? 3 : 1,
            dashArray: dashArray,
            bubblingMouseEvents: false
        });

        rect.on('mouseover', () => {
            rect.setStyle({ weight: 2.5 });
            const congestionLabel = cell.congestion
                ? cell.congestion.charAt(0).toUpperCase() + cell.congestion.slice(1)
                : 'No data';
            const tooltipText = activeMode === 'congestion'
                ? `${cell.id} - Congestion: ${congestionLabel}`
                : getStressTooltip(cell);
            rect.bindTooltip(tooltipText, { permanent: false }).openTooltip();
        });

        rect.on('mouseout', () => {
            rect.setStyle({ weight: selectedCell === cell ? 3 : 1 });
            rect.closeTooltip();
        });

        rect.on('mousedown', (e) => stopMapDeselectFromCellClick(e));

        rect.on('click', (e) => {
            stopMapDeselectFromCellClick(e, true);
            selectedCell = cell;
            setActiveMarker(rect);
            showCellSummary(cell);
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
        const season = dateToSeason(selectedDate);
        const seasonName = season.charAt(0).toUpperCase() + season.slice(1);
        const spreadLabel = formatGhiSpread(GHI_CELL_SPREADS[season]);
        const estimatedLegend = showEstimatedStressCells
            ? '<div class="legend-item"><div class="legend-color legend-color-estimated"></div><span>Estimated (city-median PV)</span></div>'
            : '';
        const estimateNote = showEstimatedStressCells
            ? 'Cells without local PV data use the city-median share only when consumption data exists.'
            : 'Estimated cells are hidden by default; measured cells use local PV data.';
        legendDiv.innerHTML = `
            <div class="legend-title">${seasonName} solar feed-in stress</div>
            <div class="legend-item"><div class="legend-color" style="background: #38bdf8;"></div><span>Low &lt; 0.04</span></div>
            <div class="legend-item"><div class="legend-color" style="background: #f59e0b;"></div><span>Moderate 0.04-0.12</span></div>
            <div class="legend-item"><div class="legend-color" style="background: #dc2626;"></div><span>High >= 0.12</span></div>
            ${estimatedLegend}
            <div class="legend-item"><div class="legend-color legend-color-no-data"></div><span>No data</span></div>
            <div class="legend-note">Combines each cell's solar panel share with seasonal sunlight to show how much solar feed-in pressure it adds. Changes with the selected date. Relative estimate, not actual megawatts. ${estimateNote}</div>
            <div class="legend-validation">Sunlight itself is nearly uniform across Amsterdam (GHI spread under <b>${spreadLabel} W/m2</b> across all cells). The variation you see here comes from solar panel density, not sunlight, which is why congestion is driven by PV and consumption.</div>
        `;
    }
}

function updateMapOutput(cell) {
    // map-output UI panel removed as per user request; this function is now a no-op.
}

let geojsonData = null;
let radiationData = null;
const radiationLookup = {};

function buildRadiationLookup() {
    if (!radiationData) return;
    radiationData.features.forEach(f => {
        radiationLookup[f.properties.cell_id] = f.properties;
    });
}

function computeGhiStats() {
    GHI_SEASON_STATS = {};
    GHI_CELL_SPREADS = {};
    if (!geojsonData) return;

    GHI_SEASONS.forEach(season => {
        GHI_SEASON_STATS[season] = { min: Infinity, max: -Infinity };
    });

    geojsonData.features.forEach(feature => {
        const props = feature.properties || {};
        const cellId = props.cell_id;
        const radProps = radiationLookup[cellId] || {};
        GHI_SEASONS.forEach(season => {
            const val = seasonalGhiFromSources(cellId, radProps, season);
            if (val === null) return;
            GHI_SEASON_STATS[season].min = Math.min(GHI_SEASON_STATS[season].min, val);
            GHI_SEASON_STATS[season].max = Math.max(GHI_SEASON_STATS[season].max, val);
        });
    });

    GHI_SEASONS.forEach(season => {
        if (GHI_SEASON_STATS[season].min === Infinity) {
            GHI_SEASON_STATS[season] = null;
            GHI_CELL_SPREADS[season] = null;
            return;
        }
        GHI_CELL_SPREADS[season] = GHI_SEASON_STATS[season].max - GHI_SEASON_STATS[season].min;
    });
}

async function loadGridData() {
    if (typeof USE_INLINE_DATA !== 'undefined' && USE_INLINE_DATA) {
        geojsonData = GRID_DATA_INLINE;
        radiationData = RADIATION_DATA_INLINE;
    } else {
        const [congResp, radResp] = await Promise.all([
            fetch(GRID_GEOJSON_URL),
            fetch(RADIATION_GEOJSON_URL)
        ]);
        geojsonData = await congResp.json();
        radiationData = await radResp.json();
    }
    buildRadiationLookup();
    computeGhiStats();
    computeCityMedianPV();
    updateLegend();
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

        const radProps = radiationLookup[props.cell_id] || {};

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
            ghiAnnualMean: radProps.GHI_annual_mean ?? null,
            ghiSpring: seasonalGhiFromSources(props.cell_id, radProps, 'spring'),
            ghiSummer: seasonalGhiFromSources(props.cell_id, radProps, 'summer'),
            ghiAutumn: seasonalGhiFromSources(props.cell_id, radProps, 'autumn'),
            ghiWinter: seasonalGhiFromSources(props.cell_id, radProps, 'winter'),
            solarRadiationDailySummer: radProps.solar_radiation_daily_summer ?? null,
            seasonalVariationRatio: radProps.GHI_seasonal_ratio ?? radProps.seasonal_variation_ratio ?? null,
            congestionDriver: radProps.congestion_driver_short || ({
                'Solar-driven congestion': 'Solar-driven',
                'Consumption-driven congestion': 'Consumption-driven',
                'Mixed drivers': 'Mixed',
                'Low/Medium risk': 'Low risk'
            }[radProps.congestion_driver]) || null,
            combinedPriority: radProps.combined_priority ?? null,
            combinedPriorityLabel: radProps.combined_priority_label || null,
            predClass: props.pred_class ?? null,
            congestionClass: props.congestion_class ?? null,
            cellId: props.cell_id,
            predLabel: props.pred_label ? props.pred_label.toLowerCase() : null,
            congestionLabelRaw: props.congestion_label ? props.congestion_label.toLowerCase() : null,
            predProbHigh: props.pred_proba_high ?? null,
            consumptionKwh: props.consumption_kwh ?? null,
            feedinKwh: props.feedin_kwh ?? null,
            populationDensity: props.bevolkingsdichtheid_inwoners_per_km2 ?? null,
            rect: null
        });
    });

    updateGridStyle();
}

const drawControl = new L.Control.Draw({
    edit: { featureGroup: drawnItems },
    draw: { polygon: false, polyline: false, circle: false, marker: false, circlemarker: false, rectangle: true }
});
map.addControl(drawControl);

// Add click handler to cancel drawing and deselect cell
map.on('click', function(e) {
    if (performance.now() < ignoreMapClickUntil) {
        return;
    }
    if (drawControl._toolbars && drawControl._toolbars.draw && drawControl._toolbars.draw._modes.rectangle) {
        const mode = drawControl._toolbars.draw._modes.rectangle;
        if (mode.handler && mode.handler.enabled()) {
            mode.handler.disable();
        }
    }
    if (selectedCell) {
        selectedCell = null;
        setActiveMarker(null);
        hideCellSummary();
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

// Load data silently on page load; cells stay hidden until Run Analysis is clicked
window.addEventListener('load', function() {
    loadGridData();
});

async function runAnalysis() {
    if (!geojsonData) return;
    const btn = document.getElementById('run-analysis-btn');
    const overlay = document.getElementById('loading-overlay');
    const msgEl  = document.getElementById('loading-message');
    const messages = [
        'Loading grid data...',
        'Running spatial analysis...',
        'Classifying congestion zones...',
        'Calculating solar feed-in stress...',
        'Analysis complete'
    ];

    btn.disabled = true;
    btn.textContent = 'Running...';
    overlay.style.display = 'flex';

    for (let i = 0; i < messages.length - 1; i++) {
        msgEl.textContent = messages[i];
        await new Promise(r => setTimeout(r, 600));
    }
    msgEl.textContent = messages[messages.length - 1];
    await new Promise(r => setTimeout(r, 400));

    overlay.style.display = 'none';
    computeCityMedianPV();
    buildGridCells(52.30, 4.77, 52.43, 5.00);
    analysisComplete = true;
    updateSummary();
    hideCellSummary();

    document.getElementById('summary-bar').style.display = 'flex';

    btn.textContent = 'Re-run Analysis';
    btn.disabled    = false;
}

function updateSummary() {
    let high = 0, med = 0, low = 0;
    gridCells.forEach(cell => {
        const c = cell.congestion;
        if (c === 'high')   high++;
        else if (c === 'medium') med++;
        else if (c === 'low')    low++;
    });
    const highEl  = document.getElementById('summary-high');
    const medEl   = document.getElementById('summary-med');
    const lowEl   = document.getElementById('summary-low');
    const totalEl = document.getElementById('summary-total');
    if (highEl)  highEl.textContent  = high;
    if (medEl)   medEl.textContent   = med;
    if (lowEl)   lowEl.textContent   = low;
    if (totalEl) totalEl.textContent = gridCells.length;
}

// Toggle layers
function syncStressEstimatedToggle() {
    const toggle = document.getElementById('stress-estimated-toggle');
    if (toggle) toggle.hidden = activeMode !== 'stress';
}

function setActiveLayerMode(mode) {
    activeMode = mode;
    document.getElementById('congestion-btn').classList.toggle('active', mode === 'congestion');
    document.getElementById('radiation-btn').classList.toggle('active', mode === 'stress');
    syncStressEstimatedToggle();
    renderIntro();
    updateGridStyle();
    if (selectedCell) {
        updateCellSummary(selectedCell);
    }
}

document.getElementById('congestion-btn').addEventListener('click', () => setActiveLayerMode('congestion'));
document.getElementById('radiation-btn').addEventListener('click', () => setActiveLayerMode('stress'));

const showEstimatedStressCheckbox = document.getElementById('show-estimated-stress-checkbox');
if (showEstimatedStressCheckbox) {
    showEstimatedStressCells = showEstimatedStressCheckbox.checked;
    showEstimatedStressCheckbox.addEventListener('change', function() {
        showEstimatedStressCells = this.checked;
        if (activeMode === 'stress') {
            updateGridStyle();
        } else {
            updateLegend();
        }
    });
}
syncStressEstimatedToggle();

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
function dateToSeason(dateStr) {
    const month = new Date(dateStr).getMonth() + 1;
    if (month >= 3 && month <= 5) return 'spring';
    if (month >= 6 && month <= 8) return 'summer';
    if (month >= 9 && month <= 11) return 'autumn';
    return 'winter';
}

document.getElementById('date-input').addEventListener('change', function() {
    selectedDate = this.value;
    const season = dateToSeason(this.value);
    const year = new Date(this.value).getFullYear();
    const label = document.getElementById('season-label');
    if (label) label.textContent = 'Showing ' + season + ' ' + year + ' satellite data';
    if (activeMode === 'stress') updateGridStyle();
    else updateLegend();
    if (selectedCell) updateCellSummary(selectedCell);
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
    if (!analysisComplete) { this.checked = false; return; }
    if (this.checked) { refreshCloudLayer(); cloudLayer.addTo(map); layersVisible.clouds = true; }
    else { map.removeLayer(cloudLayer); layersVisible.clouds = false; }
});

document.getElementById('terrain-checkbox').addEventListener('change', function() {
    if (!analysisComplete) { this.checked = false; return; }
    if (this.checked) { refreshTerrainLayer(); terrainLayer.addTo(map); layersVisible.terrain = true; }
    else { map.removeLayer(terrainLayer); layersVisible.terrain = false; }
});

document.getElementById('greenness-checkbox').addEventListener('change', function() {
    if (!analysisComplete) { this.checked = false; return; }
    if (this.checked) { refreshGreenessLayer(); greennessLayer.addTo(map); layersVisible.greenness = true; }
    else { map.removeLayer(greennessLayer); layersVisible.greenness = false; }
});

function updateSidebar(cell) { /* no-op: cell details moved to below-map panel */ }

// City-median PV fallback, computed from pv_penetration_pct after clipping to 0-100.
function median(values) {
    if (!values.length) return null;
    const sorted = [...values].sort((a, b) => a - b);
    const mid = Math.floor(sorted.length / 2);
    return sorted.length % 2 === 1
        ? sorted[mid]
        : (sorted[mid - 1] + sorted[mid]) / 2;
}

function computeCityMedianPV() {
    const sourceFeatures = geojsonData?.features || [];
    const vals = sourceFeatures
        .map(f => f.properties?.pv_penetration_pct)
        .map(v => clipPct(v))
        .filter(v => v !== null);
    CITY_MEDIAN_PV = median(vals);
}

// ── Cell summary panel (below map) ───────────────────────────────────────────
function showCellSummary(cell) {
    document.getElementById('intro-box').style.display = 'none';
    document.getElementById('cell-summary-box').style.display = 'block';
    updateCellSummary(cell);
}

function hideCellSummary() {
    document.getElementById('cell-summary-box').style.display = 'none';
    renderIntro();
    document.getElementById('intro-box').style.display = 'block';
}

function getPredictionConfidenceSentence(predLabel, predProbHigh) {
    if (!predLabel || predProbHigh === null || predProbHigh === undefined) return '';

    const highRiskPct = predProbHigh * 100;
    if (predLabel === 'high') {
        const confidence = highRiskPct >= 70 ? 'very' : highRiskPct >= 45 ? 'fairly' : 'not very';
        return `The model is ${confidence} confident this cell is high-congestion, based on its satellite and neighbourhood features.`;
    }

    const confidence = highRiskPct <= 15 ? 'very' : highRiskPct <= 30 ? 'fairly' : 'not very';
    if (predLabel === 'medium') {
        return `The model is ${confidence} confident this is not high-congestion yet, so treat the medium-risk result as a watch item.`;
    }
    return `The model is ${confidence} confident this is not high-congestion, based on its satellite and neighbourhood features.`;
}

function normalizedDriverType(driverLabel) {
    if (!driverLabel) return null;

    const label = String(driverLabel).trim().toLowerCase();
    if (label.includes('solar')) return 'solar';
    if (label.includes('consumption')) return 'consumption';
    if (label.includes('mixed')) return 'mixed';
    if (label.includes('low')) return 'low';
    if (label.includes('no data')) return null;
    return null;
}

function deriveDriverType(cell) {
    const ratioFromKwh = cell.feedinKwh !== null && cell.consumptionKwh !== null && cell.consumptionKwh > 0
        ? cell.feedinKwh / cell.consumptionKwh
        : null;
    const feedinRatio = cell.feedinRatio !== null ? cell.feedinRatio : ratioFromKwh;
    const consumptionPct = cell.consumptionPct;

    if (feedinRatio === null && consumptionPct === null) return null;

    // Fallback only when GeoJSON lacks a driver label: feed-in ratio >= 0.30 marks elevated PV export
    // pressure; consumption_pct >= 40 marks elevated demand pressure in this dataset.
    const highSolar = feedinRatio !== null && feedinRatio >= 0.30;
    const highDemand = consumptionPct !== null && consumptionPct >= 40;

    if (highSolar && highDemand) return 'mixed';
    if (highSolar) return 'solar';
    if (highDemand) return 'consumption';
    return 'low';
}

function getDriverVerdict(cell) {
    const driverType = normalizedDriverType(cell.congestionDriver) || deriveDriverType(cell);

    if (driverType === 'consumption') {
        return 'Driver verdict: <b>Consumption-driven</b>. This cell uses far more power than it feeds back, so its congestion risk comes from demand, not solar; it is the kind that needs cable or substation upgrades.';
    }
    if (driverType === 'solar') {
        return 'Driver verdict: <b>Solar-driven</b>. This cell feeds back a lot of solar relative to what it uses, so its risk comes from PV export overloading the cables; it is the kind that benefits from batteries or smart inverters.';
    }
    if (driverType === 'mixed') {
        return 'Driver verdict: <b>Mixed</b>. This cell has both high demand and high solar feed-in, so it faces mixed congestion pressure.';
    }
    if (driverType === 'low') {
        return 'Driver verdict: <b>No clear driver</b>. The energy data does not show a strong demand or solar feed-in pressure for this cell.';
    }
    return null;
}

function cellSummaryHeaderHtml(cell, cellId) {
    return `
        <div class="csb-header">
            <div class="csb-header-main">
                <span class="csb-cell-id">Cell ${cellId}</span>
                <span class="csb-city">${selectedCity}, Netherlands &nbsp;&middot;&nbsp; ${cell.center[0].toFixed(4)}&deg;N ${cell.center[1].toFixed(4)}&deg;E</span>
            </div>
            <a class="csb-about-link" href="/?page=Knowledge" target="_blank" rel="noopener">About this analysis</a>
        </div>`;
}

function renderStressCellSummary(box, cell, cellId) {
    const seasonLabel = getSeasonLabel(selectedDate);
    const stressInfo = getSolarFeedInStress(cell);
    const hasOwnPV = stressInfo.hasOwnPV;
    const pvSource = stressInfo.pvPct;
    let content = '';

    if (pvSource === null) {
        content = stressInfo.hasEnergyContext
            ? `<p class="csb-para csb-na"><b>No data for this cell.</b> Solar feed-in stress cannot be estimated because local PV data is missing and no fallback value is available.</p>`
            : `<p class="csb-para csb-na"><b>No data for this cell.</b> Solar feed-in stress is not estimated because this cell has no local PV data and no consumption/energy data.</p>`;
    } else {
        const stressIndex = formatStressIndex(stressInfo.norm);
        const stress = stressInfo.level;
        const stressColor = stress === 'Low' ? '#34D399' : stress === 'Moderate' ? '#FBBF24' : '#F87171';

        if (hasOwnPV) {
            content += `<div class="csb-source-note"><b>PV source: cell's own PV data.</b></div>`;
        } else {
            const cityMedianLabel = CITY_MEDIAN_PV !== null ? CITY_MEDIAN_PV.toFixed(1) : pvSource.toFixed(1);
            content += `<div class="csb-avg-notice"><b>Estimated using the city-median PV share (${cityMedianLabel}%).</b> ${cityMedianInfoButton()} This cell has no local PV data.</div>`;
        }
        content += `<p class="csb-para">Seasonal sunlight used: <b>${seasonLabel}</b>, <b>${stressInfo.ghi} W/m2</b> GHI.</p>`;
        content += `<p class="csb-para">PV share used: <b>${pvSource.toFixed(1)}%</b> from ${hasOwnPV ? "the cell's own PV data" : "the city-median estimate"}.</p>`;
        content += `<p class="csb-para">Stress index: <b style="color:${stressColor}">${stressIndex} / 100</b> &mdash; <b style="color:${stressColor}">${stress}</b> solar stress.</p>`;
        content += `<p class="csb-para">This is a compressed 0-100 scale. Real solar feed-in is a small share of the theoretical maximum, so even modest index values count as high stress. Higher means more solar pressure on the grid.</p>`;
        content += `<p class="csb-para">This is how much solar feed-in pressure the cell adds in ${seasonLabel}; it rises in summer and nearly disappears in winter, change the date to see it move.</p>`;
    }

    box.innerHTML = `
        ${cellSummaryHeaderHtml(cell, cellId)}
        <div class="csb-grid csb-grid-single">
            <div class="csb-tier csb-stress-panel">
                <div class="csb-tier-title">Solar feed-in stress &middot; ${seasonLabel}</div>
                ${content}
            </div>
        </div>`;
}

function updateCellSummary(cell) {
    const box = document.getElementById('cell-summary-box');
    if (!cell) { hideCellSummary(); return; }

    const cellId = cell.cellId ?? cell.id.replace('cell-', '');

    if (activeMode === 'stress') {
        renderStressCellSummary(box, cell, cellId);
        return;
    }

    // ── Tier 1 ───────────────────────────────────────────────────────────────
    const predLabel = cell.predLabel;
    const predDisplay = predLabel
        ? predLabel.charAt(0).toUpperCase() + predLabel.slice(1)
        : null;
    const predColor = predLabel === 'high' ? '#F87171'
                    : predLabel === 'medium' ? '#FBBF24'
                    : predLabel === 'low' ? '#34D399' : '#6B7280';
    const highRiskSignal = cell.predProbHigh !== null
        ? `; <span class="intro-term">model confidence</span>${confidenceInfoButton()}: <b>${(cell.predProbHigh * 100).toFixed(1)}%</b> high-risk probability` : '';

    let t1 = '';
    if (predDisplay) {
        t1 += `<p class="csb-para">Model predicts <b style="color:${predColor}">${predDisplay}</b> congestion risk${highRiskSignal}.</p>`;
        const predictionSentence = getPredictionConfidenceSentence(predLabel, cell.predProbHigh);
        if (predictionSentence) t1 += `<p class="csb-para">${predictionSentence}</p>`;
    } else {
        t1 += `<p class="csb-para csb-na">Model prediction: Not available for this cell.</p>`;
    }
    const lu = (cell.landUse && cell.landUse !== 'Unknown') ? cell.landUse : null;
    if (lu) t1 += `<p class="csb-para">Land use: <b>${lu}</b>.</p>`;
    else    t1 += `<p class="csb-para csb-na">Land use: Not available for this cell.</p>`;
    if (cell.ndbiPct !== null) {
        t1 += `<p class="csb-para">Built-up density (<span class="intro-term">NDBI</span>${ndbiInfoButton()}): <b>${cell.ndbiPct.toFixed(1)}%</b> of surface.</p>`;
        t1 += `<p class="csb-para">A higher NDBI means more built surface, which can concentrate demand and rooftop solar in the same cell.</p>`;
    } else {
        t1 += `<p class="csb-para csb-na">Building density: Not available for this cell.</p>`;
    }

    // ── Tier 2 ───────────────────────────────────────────────────────────────
    const hasTier2 = cell.consumptionKwh !== null || cell.feedinKwh !== null || cell.congestionLabelRaw !== null;
    let t2 = '';
    if (!hasTier2) {
        t2 = `<p class="csb-para csb-na">Energy data: Not available for this cell.</p>`;
    } else {
        const clRaw = cell.congestionLabelRaw;
        const clDisplay = clRaw ? (clRaw.charAt(0).toUpperCase() + clRaw.slice(1)) : null;
        const clColor = clRaw === 'high' ? '#F87171' : clRaw === 'medium' ? '#FBBF24' : clRaw === 'low' ? '#34D399' : '#6B7280';
        if (clDisplay)
            t2 += `<p class="csb-para">Constructed risk label (Liander data): <b style="color:${clColor}">${clDisplay}</b>.</p>`;
        else
            t2 += `<p class="csb-para csb-na">Constructed risk label: Not available for this cell.</p>`;
        if (clDisplay)
            t2 += `<p class="csb-para">This label summarizes the energy-data risk signal before the model prediction is considered.</p>`;
        if (cell.congestionScore !== null) {
            t2 += `<p class="csb-para">Congestion score: <b>${cell.congestionScore.toFixed(2)}</b>.</p>`;
            t2 += `<p class="csb-para">The score lets this cell be compared with other cells on the same congestion-risk scale.</p>`;
        } else {
            t2 += `<p class="csb-para csb-na">Congestion score: Not available for this cell.</p>`;
        }
        const cons = cell.consumptionKwh !== null ? `<b>${Math.round(cell.consumptionKwh).toLocaleString()} kWh</b>` : null;
        const feed = cell.feedinKwh !== null ? `<b>${Math.round(cell.feedinKwh).toLocaleString()} kWh</b>` : null;
        const ratio = (cell.feedinKwh !== null && cell.consumptionKwh !== null && cell.consumptionKwh > 0)
            ? ` (ratio <b>${(cell.feedinKwh / cell.consumptionKwh).toFixed(2)}x</b>)` : '';
        if (cons) {
            t2 += `<p class="csb-para">Annual consumption: ${cons}${cell.consumptionPct !== null ? `, at <b>${cell.consumptionPct.toFixed(1)}%</b> of grid capacity` : ''}.</p>`;
            t2 += `<p class="csb-para">High consumption points to demand pressure, the cable or substation side of congestion.</p>`;
        } else {
            t2 += `<p class="csb-para csb-na">Annual consumption: Not available for this cell.</p>`;
        }
        if (feed) {
            t2 += `<p class="csb-para">Annual solar feed-in: ${feed}${ratio}.</p>`;
            t2 += `<p class="csb-para">Feed-in shows how much solar is pushed back into the grid, the PV-export side of congestion.</p>`;
        } else {
            t2 += `<p class="csb-para csb-na">Annual solar feed-in: Not available for this cell.</p>`;
        }
        const driverVerdict = getDriverVerdict(cell);
        if (driverVerdict) t2 += `<p class="csb-para">${driverVerdict}</p>`;
        if (cell.populationDensity !== null) {
            t2 += `<p class="csb-para">Population density: <b>${Math.round(cell.populationDensity).toLocaleString()} /km²</b>.</p>`;
            t2 += `<p class="csb-para">Population density is the single strongest predictor in the model, denser areas concentrate both consumption and rooftop solar.</p>`;
        }
    }

    // ── Tier 3 ───────────────────────────────────────────────────────────────
    const season = dateToSeason(selectedDate);
    const seasonLabel = getSeasonLabel(selectedDate);
    let t3 = '';

    const stressInfo = getSolarFeedInStress(cell);
    const hasOwnPV = stressInfo.hasOwnPV;
    const pvSource = stressInfo.pvPct;

    if (pvSource === null) {
        t3 = stressInfo.hasEnergyContext
            ? `<p class="csb-para csb-na"><b>No data for this cell.</b> Solar feed-in stress cannot be estimated because local PV data is missing and no fallback value is available.</p>`
            : `<p class="csb-para csb-na"><b>No data for this cell.</b> Solar feed-in stress is not estimated because this cell has no local PV data and no consumption/energy data.</p>`;
    } else {
        const stressIndex = formatStressIndex(stressInfo.norm);
        const stress = stressInfo.level;
        const stressColor = stress === 'Low' ? '#34D399' : stress === 'Moderate' ? '#FBBF24' : '#F87171';

        if (!hasOwnPV) {
            const cityMedianLabel = CITY_MEDIAN_PV !== null ? CITY_MEDIAN_PV.toFixed(1) : pvSource.toFixed(1);
            t3 += `<div class="csb-avg-notice"><b>Estimated using the city-median PV share (${cityMedianLabel}%).</b> ${cityMedianInfoButton()} This cell has no local PV data. Many cells share this same estimate, which is expected.</div>`;
        } else {
            t3 += `<div class="csb-source-note"><b>Using cell's own PV data.</b></div>`;
        }
        t3 += `<p class="csb-para">Using <b>${seasonLabel}</b> sunlight (<b>${stressInfo.ghi} W/m²</b> city average) and <b>${pvSource.toFixed(1)}%</b> PV penetration from ${hasOwnPV ? "the cell's own PV data" : "the city-median estimate"}.</p>`;
        t3 += `<p class="csb-para">These inputs show whether this cell has enough panel density and seasonal sunlight to push power back onto local cables.</p>`;
        t3 += `<p class="csb-para">Stress index: <b style="color:${stressColor}">${stressIndex} / 100</b> &mdash; <b style="color:${stressColor}">${stress}</b> solar stress.</p>`;
        t3 += `<p class="csb-para">This is a compressed 0-100 scale. Real solar feed-in is a small share of the theoretical maximum, so even modest index values count as high stress. Higher means more solar pressure on the grid.</p>`;
        t3 += `<p class="csb-para">This is how much solar feed-in pressure the cell adds in ${seasonLabel}, combining its panel share with seasonal sunlight. It rises in summer and nearly disappears in winter; change the date to see it move.</p>`;
        t3 += `<p class="csb-disclaimer">Relative estimate. Scales PV share by city seasonal sunlight to indicate solar feed-in pressure. Uses city seasonal average GHI. Not actual megawatts.</p>`;
    }

    box.innerHTML = `
        ${cellSummaryHeaderHtml(cell, cellId)}
        <div class="csb-grid">
            <div class="csb-tier">
                <div class="csb-tier-title">Tier 1 — Model prediction</div>
                ${t1}
            </div>
            <div class="csb-tier">
                <div class="csb-tier-title">Tier 2 — Energy data</div>
                ${t2}
            </div>
            <div class="csb-tier">
                <div class="csb-tier-title">Tier 3 — Solar feed-in stress · ${seasonLabel}</div>
                ${t3}
            </div>
        </div>`;
}
