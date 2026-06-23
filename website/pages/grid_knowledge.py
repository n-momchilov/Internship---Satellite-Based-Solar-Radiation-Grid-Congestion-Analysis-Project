import streamlit as st
from pathlib import Path

def render():
    st.markdown("""
<style>
.gk-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 12px;
    padding: 20px 24px;
    margin-bottom: 18px;
}
.gk-card h2 {
    margin-top: 0;
    margin-bottom: 10px;
    font-size: 1.15rem;
    font-weight: 600;
    color: #ffffff;
}
.gk-card p { margin: 0 0 10px 0; line-height: 1.65; color: rgba(255,255,255,0.85); }
.gk-cards-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 12px;
    margin-top: 12px;
}
.gk-mini-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 10px;
    padding: 14px 16px;
}
.gk-mini-card h3 { margin: 6px 0 6px 0; font-size: 0.92rem; color: #ffffff; }
.gk-mini-card p  { margin: 0; font-size: 0.84rem; color: rgba(255,255,255,0.75); }
.gk-mini-icon { font-size: 1.4rem; }
.gk-step-row {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 10px;
    margin-top: 12px;
}
.gk-step-card {
    background: rgba(237,231,113,0.06);
    border: 1px solid rgba(237,231,113,0.2);
    border-radius: 10px;
    padding: 12px 14px;
    font-size: 0.84rem;
    color: rgba(255,255,255,0.8);
}
.gk-step-card strong { color: #EDE771; display: block; margin-bottom: 4px; }
.gk-table { width: 100%; border-collapse: collapse; margin-top: 12px; font-size: 0.86rem; }
.gk-table th {
    background: rgba(237,231,113,0.1);
    color: #EDE771;
    font-weight: 600;
    padding: 8px 12px;
    text-align: left;
    border-bottom: 1px solid rgba(237,231,113,0.25);
}
.gk-table td {
    padding: 7px 12px;
    border-bottom: 1px solid rgba(255,255,255,0.07);
    color: rgba(255,255,255,0.82);
    vertical-align: top;
}
.gk-table tr:last-child td { border-bottom: none; }
.gk-link { color: #EDE771; text-decoration: none; }
.gk-link:hover { text-decoration: underline; }
.gk-ref-list { list-style: none; padding: 0; margin: 0; }
.gk-ref-list li {
    padding: 7px 0;
    border-bottom: 1px solid rgba(255,255,255,0.07);
    font-size: 0.84rem;
    color: rgba(255,255,255,0.72);
    line-height: 1.55;
}
.gk-ref-list li:last-child { border-bottom: none; }
.gk-hl { color: #EDE771; }
.gk-footer { font-size: 0.82rem; color: rgba(255,255,255,0.45); margin-top: 24px; text-align: center; }
</style>

<h1 style="margin-bottom:20px;">How <span class="gk-hl">satellite imagery</span> reveals grid congestion</h1>

<div class="gk-card">
  <h2>How this analysis works, and how to trust it</h2>
  <p>This tool predicts grid congestion risk across Amsterdam at 1x1 km. Here is where the data comes from and how reliable it is.</p>

  <p><strong style="color:#ffffff;">The data</strong></p>
  <p>The project uses three sources. Sentinel-2 satellite images (Level-2A) give the physical picture of each cell: how built-up it is, how much greenery, what kind of land use. CBS provides neighbourhood statistics like population density and electricity use. Liander provides open energy data: solar feed-in, consumption, and PV penetration per area.</p>

  <p><strong style="color:#ffffff;">The model</strong></p>
  <p>A Random Forest classifier sorts each cell into Low, Medium, or High congestion risk. It learns from 37 features: 28 from satellite imagery and 9 from CBS.</p>

  <p><strong style="color:#ffffff;">How accurate is it</strong></p>
  <p>The model scores an F1-macro of about 0.58 on cross-validation, and 0.55 on a temporal hold-out test. That is not perfect, but it is consistent and honest. An earlier version showed 0.94, but that was wrong: one feature (PV penetration) was accidentally used both as an input and as part of the target, which inflated the score. After fixing that, the real score is 0.58. We kept the honest number.</p>

  <p><strong style="color:#ffffff;">Do the satellites actually matter, or is it just population data?</strong></p>
  <p>Fair question. Population density is the single strongest predictor. But the satellite features together carry most of the model's weight: about 72% of total importance comes from the 28 satellite features, versus 28% from the 9 CBS features. So no single satellite band beats population, but the satellite group does the heavy lifting overall. The satellite data is also what separates a dense residential area from a dense industrial one with the same population, and it is what makes the solar-driven vs consumption-driven classification possible.</p>

  <p><strong style="color:#ffffff;">Why do some cells show an estimated PV value?</strong></p>
  <p>Liander's PV data covers only about 42% of cells. For the rest, the tool uses the city-average PV share so every cell still gets a feed-in stress estimate. This is an approximation, not a measurement for that cell. It may slightly overcount consumption-driven areas and undercount solar-driven ones. Cells using this fallback are clearly labelled.</p>

  <p><strong style="color:#ffffff;">What this tool is and is not</strong></p>
  <p>It is a planning and analysis aid that shows where congestion risk is high and what kind it is. It is not a live grid operator tool and does not use real-time transformer loading. The congestion classes are built from Liander's published energy data, not from official congestion declarations.</p>
</div>

<div class="gk-card">
  <h2>1. The Problem</h2>
  <p>The Dutch electricity grid was designed for one-way power flow: from power plants to homes. Rooftop solar panels reversed this. When too many panels in one area push electricity back into the grid, cables and transformers get overloaded. This is called <span class="gk-hl">grid congestion</span>. In Amsterdam, operator Liander has already declared congestion in several districts. New solar connections are being refused because the local grid cannot handle more feed-in.</p>
</div>

<div class="gk-card">
  <h2>2. Why Satellite Imagery?</h2>
  <p>Grid operators know where congestion happens, but their data is private and hard to access. <span class="gk-hl">Satellite imagery</span> is publicly available and covers entire cities at once. The idea behind this project: can we look at a city from space and predict where the grid is likely congested, without needing access to internal grid data?</p>
</div>

<div class="gk-card">
  <h2>3. What Satellites See That Matters for Congestion</h2>
  <div class="gk-cards-grid">
    <div class="gk-mini-card"><div class="gk-mini-icon">🏢</div><h3>Building density</h3><p><span class="gk-hl">Sentinel-2</span> imagery reveals built-up surface density through the NDBI index. Denser built areas tend to have more connections and higher solar feed-in potential.</p></div>
    <div class="gk-mini-card"><div class="gk-mini-icon">🗂️</div><h3>Land use patterns</h3><p>Satellite indices combined with <span class="gk-hl">CBS</span> neighbourhood statistics show residential, commercial, or industrial character. Each type has a different consumption-to-generation ratio.</p></div>
    <div class="gk-mini-card"><div class="gk-mini-icon">☀️</div><h3>Solar panel penetration</h3><p>Network operator data shows the share of connections with solar panels per cell. Risk is higher when many panels feed one substation.</p></div>
  </div>
</div>

<div class="gk-card">
  <h2>4. The Analysis Pipeline</h2>
  <div class="gk-step-row">
    <div class="gk-step-card"><strong>Step 1</strong>Grid congestion analysis with <span class="gk-hl">Sentinel-2</span> and Dutch public datasets. <span class="gk-hl">Random Forest</span> predicts High / Medium / Low per 1×1 km cell.</div>
    <div class="gk-step-card"><strong>Step 2</strong>Solar radiation estimation from <span class="gk-hl">Meteosat</span> SEVIRI at 15-min resolution. Captures cloud variation that 5-day Sentinel cannot.</div>
    <div class="gk-step-card"><strong>Step 3</strong>Validation and comparison: high radiation + high congestion = solar-grid mismatch. Low radiation + high congestion = load from consumption.</div>
  </div>
</div>

<div class="gk-card">
  <h2>5. What the Map Shows</h2>
  <p>Congestion uses a categorical scale: red is high risk, orange medium, green low. The solar feed-in stress view combines each cell's PV share with seasonal sunlight, so it changes when the date changes. Per-cell overlays show <span class="gk-hl">building density</span> (yellow heat), <span class="gk-hl">PV penetration</span> (red, from network data), and <span class="gk-hl">land use type</span> (colour by residential/commercial/industrial/mixed).</p>
</div>

<div class="gk-card">
  <h2>6. Limitations</h2>
  <p>This prototype uses real spatial and Liander data for the congestion pipeline. The radiation pipeline uses CM SAF SARAH-3 monthly averages. The 1×1 km cell size balances detail and data needs. It does not detect individual rooftop panels, only area-level behaviour.</p>
</div>

<div class="gk-card">
  <h2>7. What is Meteosat SEVIRI?</h2>
  <p>Meteosat is a family of geostationary weather satellites operated by <span class="gk-hl">EUMETSAT</span>. Unlike Sentinel-2 which orbits the Earth every 5 days, Meteosat sits fixed above the equator at 0° longitude, 36,000 km altitude, continuously watching Europe and Africa.</p>
  <p>The main instrument is <span class="gk-hl">SEVIRI</span> (Spinning Enhanced Visible and InfraRed Imager). It captures a full image every 15 minutes in 12 spectral channels. Clouds can cross a city in minutes — a satellite imaging every 5 days misses this completely.</p>
  <p>EUMETSAT Data Store: <a class="gk-link" href="https://data.eumetsat.int" target="_blank">data.eumetsat.int</a></p>
  <table class="gk-table">
    <tr><th>Feature</th><th>Sentinel-2</th><th>Meteosat SEVIRI</th></tr>
    <tr><td>Orbit type</td><td>Polar (circles the Earth)</td><td>Geostationary (fixed above equator)</td></tr>
    <tr><td>Revisit time</td><td>5 days</td><td>15 minutes</td></tr>
    <tr><td>Spatial resolution</td><td>10 m</td><td>~5.5 km at Amsterdam latitude</td></tr>
    <tr><td>Spectral bands</td><td>13</td><td>12</td></tr>
    <tr><td>Best for</td><td>Spatial detail (buildings, vegetation, land use)</td><td>Temporal detail (cloud tracking, radiation)</td></tr>
    <tr><td>Used in this project for</td><td>Pipeline 1: congestion features (NDVI, NDBI)</td><td>Pipeline 2: solar radiation estimation (GHI)</td></tr>
  </table>
</div>

<div class="gk-card">
  <h2>8. What is CM SAF SARAH-3 SIS?</h2>
  <p><span class="gk-hl">CM SAF</span> (Climate Monitoring Satellite Application Facility) is a EUMETSAT division producing climate data records from satellite observations. <span class="gk-hl">SARAH-3</span> (Surface Solar Radiation Data Record, Edition 3) is their flagship solar radiation product.</p>
  <p><span class="gk-hl">SIS</span> (Surface Incoming Shortwave radiation) represents Global Horizontal Irradiance (GHI): total solar energy reaching a horizontal surface on the ground in W/m². GHI includes both direct sunlight and diffuse light scattered by clouds.</p>
  <p>Product page: <a class="gk-link" href="https://data.eumetsat.int" target="_blank">data.eumetsat.int</a> — search for "SARAH"</p>
  <p><strong style="color:#ffffff;">How SIS is produced:</strong></p>
  <div class="gk-step-row">
    <div class="gk-step-card"><strong>1</strong>Meteosat SEVIRI captures cloud images every 15 minutes.</div>
    <div class="gk-step-card"><strong>2</strong>The Heliosat method computes a cloud index per pixel describing how much sunlight is blocked.</div>
    <div class="gk-step-card"><strong>3</strong>A clear-sky model calculates the theoretical maximum radiation based on sun position and atmosphere.</div>
    <div class="gk-step-card"><strong>4</strong>The cloud index reduces the clear-sky value to give estimated actual surface radiation.</div>
    <div class="gk-step-card"><strong>5</strong>15-minute estimates are averaged into daily, monthly, and annual mean products.</div>
  </div>
  <table class="gk-table" style="margin-top:16px;">
    <tr><th>Property</th><th>Value</th></tr>
    <tr><td>Product name</td><td>CM SAF SARAH-3 SIS</td></tr>
    <tr><td>Source satellite</td><td>Meteosat SEVIRI</td></tr>
    <tr><td>Variable</td><td>Surface Incoming Shortwave radiation (GHI)</td></tr>
    <tr><td>Unit</td><td>W/m²</td></tr>
    <tr><td>Temporal resolution</td><td>Monthly mean (also daily and 30-minute)</td></tr>
    <tr><td>Spatial resolution</td><td>0.05 degrees (~5.5 km at Amsterdam)</td></tr>
    <tr><td>Coverage</td><td>Europe, Africa, parts of South America</td></tr>
    <tr><td>Time span</td><td>1983 to present</td></tr>
    <tr><td>Format</td><td>NetCDF (.nc)</td></tr>
    <tr><td>Data policy</td><td>Free and unrestricted</td></tr>
    <tr><td>Validation</td><td>Tested against Dutch ground stations at Cabauw and De Bilt (Cui et al., 2024)</td></tr>
  </table>
</div>

<div class="gk-card">
  <h2>9. How Solar Radiation Estimation Works</h2>
  <p>Solar radiation estimation answers: how much solar energy actually reaches the ground at a specific location and time? The key factor is cloud cover. On a clear day, Amsterdam receives ~800–1000 W/m² at solar noon in summer. On a fully overcast day, this drops to 100–200 W/m².</p>
  <p>The difference between locations <em>within</em> a city is small compared with the seasonal swing between summer and winter. This is why the project treats sunlight as a city-wide seasonal input and keeps the map focused on PV density. Congestion variation comes from how people respond to that radiation, not from the radiation itself.</p>
  <table class="gk-table">
    <tr><th>Metric</th><th>What it measures</th><th>Unit</th><th>Relevance for solar</th></tr>
    <tr><td>GHI</td><td>Total radiation on a horizontal surface</td><td>W/m²</td><td>Main metric for rooftop solar potential</td></tr>
    <tr><td>DNI</td><td>Direct beam from the sun only</td><td>W/m²</td><td>Relevant for tracking/concentrating systems</td></tr>
    <tr><td>DHI</td><td>Diffuse scattered light from the sky</td><td>W/m²</td><td>Important on cloudy days</td></tr>
    <tr><td>kWh/m²/day</td><td>Daily energy total</td><td>kWh/m²</td><td>How much energy a panel receives per day</td></tr>
  </table>
  <p style="margin-top:12px;">For Amsterdam: annual average GHI ≈ 118.5 W/m². Summer average 224 W/m² (~5.4 kWh/m²/day). Winter average 34 W/m² (~0.8 kWh/m²/day). Summer receives approximately 6.5× more solar energy than winter.</p>
</div>

<div class="gk-card">
  <h2>10. The Combined Analysis</h2>
  <p>The project follows a <span class="gk-hl">grid-first methodology</span>. First, analyse where congestion occurs using satellite imagery (Pipeline 1). Then, use solar radiation estimation to understand what drives congestion in each area (Pipeline 2). The comparison uses the same 2,217 grid cells of 1×1 km covering Amsterdam and surrounding municipalities.</p>
  <p>Pipeline 1 identifies 493 high-risk cells. Pipeline 2 classifies each by its dominant driver:</p>
  <table class="gk-table">
    <tr><th>Driver type</th><th>Count</th><th>Description</th><th>Solution</th></tr>
    <tr><td style="color:#FF8C00;">Solar-driven</td><td>163 cells</td><td>High PV adoption creates reverse power flow</td><td>Smart inverters, battery storage, local energy communities</td></tr>
    <tr><td style="color:#DC143C;">Consumption-driven</td><td>223 cells</td><td>High demand exceeds infrastructure capacity</td><td>Cable upgrades, new substations, demand management</td></tr>
    <tr><td style="color:#9B59B6;">Mixed</td><td>107 cells</td><td>Both factors contribute</td><td>Combined approach needed</td></tr>
    <tr><td style="color:#2ECC71;">Low/Medium risk</td><td>937 cells</td><td>No significant grid stress</td><td>Monitor for future growth</td></tr>
  </table>
  <p style="margin-top:12px;">The finding that radiation is spatially uniform across Amsterdam reframes the congestion problem: it is not about <em>where</em> the sun shines, but about <em>where</em> people install panels and how fast adoption outpaces grid capacity.</p>
</div>

<div class="gk-card">
  <h2>11. Links and Resources</h2>
  <table class="gk-table">
    <tr><th>Resource</th><th>URL</th></tr>
    <tr><td>Copernicus Data Space (Sentinel-2 download)</td><td><a class="gk-link" href="https://browser.dataspace.copernicus.eu" target="_blank">browser.dataspace.copernicus.eu</a></td></tr>
    <tr><td>EUMETSAT Data Store (Meteosat / SIS download)</td><td><a class="gk-link" href="https://data.eumetsat.int" target="_blank">data.eumetsat.int</a></td></tr>
    <tr><td>SNAP Desktop (Sentinel-2 processing)</td><td><a class="gk-link" href="https://step.esa.int/main/download/snap-download" target="_blank">step.esa.int</a></td></tr>
    <tr><td>CBS Wijken en Buurten (Dutch statistics)</td><td><a class="gk-link" href="https://www.pdok.nl" target="_blank">pdok.nl</a></td></tr>
    <tr><td>Liander Open Data</td><td><a class="gk-link" href="https://www.liander.nl/over-ons/open-data" target="_blank">liander.nl/over-ons/open-data</a></td></tr>
    <tr><td>Netbeheer Nederland Capacity Map</td><td><a class="gk-link" href="https://capaciteitskaart.netbeheernederland.nl" target="_blank">capaciteitskaart.netbeheernederland.nl</a></td></tr>
    <tr><td>KNMI Solar Atlas</td><td><a class="gk-link" href="https://www.knmi.nl" target="_blank">knmi.nl</a></td></tr>
    <tr><td>scikit-learn (Random Forest)</td><td><a class="gk-link" href="https://scikit-learn.org" target="_blank">scikit-learn.org</a></td></tr>
    <tr><td>xarray (NetCDF processing)</td><td><a class="gk-link" href="https://docs.xarray.dev" target="_blank">docs.xarray.dev</a></td></tr>
  </table>
</div>

<div class="gk-card">
  <h2>References</h2>
  <ul class="gk-ref-list">
    <li>Cui, Y.; Wang, P.; Meirink, J.F.; Ntantis, N.; Wijnands, J.S. Solar radiation nowcasting based on geostationary satellite images and deep learning models. <em>Solar Energy</em>, 2024.</li>
    <li>Suwanwimolkul, S.; Tongamrak, N.; Thungka, N.; et al. Deep learning-based and near real-time solar irradiance map using Himawari-8 satellite imageries. <em>Solar Energy</em>, 2025.</li>
    <li>Rouse, J.W.; Haas, R.H.; Schell, J.A.; Deering, D.W. Monitoring vegetation systems in the Great Plains with ERTS. <em>Third Earth Resources Technology Satellite-1 Symposium</em>, 1974.</li>
    <li>Zha, Y.; Gao, J.; Ni, S. Use of normalized difference built-up index in automatically mapping urban areas from TM imagery. <em>International Journal of Remote Sensing</em>, 2003.</li>
  </ul>
</div>

<p class="gk-footer">Nikola Momchilov &mdash; HBO-ICT Internship 2026 &mdash; Fontys Innovation Lab, Eindhoven</p>
""", unsafe_allow_html=True)
