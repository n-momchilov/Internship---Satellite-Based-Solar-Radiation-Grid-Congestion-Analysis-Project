import streamlit as st

def render():
    # ---------- Page styles & layout wrapper ----------
    st.markdown(
        """
<style>
/* Tighter top padding and centered content column */
.block-container { padding-top: 1.1rem !important; }
.content-wrap { max-width: 980px; margin: 0 auto; }

/* Typography */
h1, h2, h3 { margin-top: 0.2rem; }
.lead { opacity: .95; font-size: 1.02rem; line-height: 1.6; }

/* Subsection spacing */
.section { margin: 1.2rem 0 0.5rem; }

/* Callout (if you need to add any quick notes) */
.callout {
  background: rgba(33,150,243,.08);
  border: 1px solid rgba(33,150,243,.35);
  padding: 10px 12px;
  border-radius: 10px;
  font-size: .95rem;
  margin: .5rem 0 1rem;
}

/* Clean, sharp tables (force white bg so text stays crisp on dark themes) */
.clean-table {
  width: 100%;
  border-collapse: collapse;
  margin: .5rem 0 1.1rem;
  background: #ffffff;
  color: #111;
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 6px 14px rgba(0,0,0,.12);
}
.clean-table thead tr {
  background: #f5f7fb;
  font-weight: 700;
}
.clean-table th, .clean-table td {
  padding: 12px 14px;
  border-bottom: 1px solid #e9eef5;
  vertical-align: top;
  text-align: left;
  font-size: .95rem;
}
.clean-table tr:last-child td { border-bottom: none; }

.ref-list { line-height: 1.55; }
.ref-list li { margin-bottom: .4rem; }
.caption { display:block; font-size:.85rem; opacity:.85; margin-top:.25rem; }
</style>
<div class="content-wrap">
""",
        unsafe_allow_html=True,
    )

    # ---------- Title & intro ----------
    st.title("Satellite Imagery for Solar Energy Analysis")
    st.markdown(
        '<p class="lead">'
        "Satellite imagery is central to solar research and planning. It shows how sunlight interacts with land, clouds, "
        "and atmosphere, helping select locations, estimate potential, and monitor conditions over time. "
        "Below is a concise knowledge overview from research, written for general readers and students, with references."
        "</p>",
        unsafe_allow_html=True,
    )

    # ---------- 1. What are satellite images? ----------
    st.markdown('<h3 class="section">1. What Are Satellite Images?</h3>', unsafe_allow_html=True)
    st.markdown(
        "- Satellite images are pictures of Earth taken from orbit. They’re used to **map land**, **monitor weather**, "
        "and **analyze sunlight** across regions for solar planning.\n"
        "- Satellites carry **sensors** that are either **passive** (measure reflected sunlight) or **active** (emit microwaves and measure the return)."
    )
    st.markdown(
        """
**Passive sensors** (e.g., Landsat-8, Sentinel-2) capture visible/infrared light with resolutions down to **10 m**, great for land, vegetation, and **albedo** studies; limited by daytime and clouds (Ahuja & Biday, 2018).  
**Active sensors / SAR** (e.g., Sentinel-1, TerraSAR-X) emit microwaves, work **day/night** and **through clouds**, with resolutions down to **1 m**—ideal for continuous terrain and surface monitoring (Ablin et al., 2020).
        """
    )

    st.markdown(
        """
<table class="clean-table">
  <thead>
    <tr>
      <th>Feature</th>
      <th>Passive Sensors</th>
      <th>Active Sensors (SAR)</th>
    </tr>
  </thead>
  <tbody>
    <tr><td>Energy source</td><td>Sunlight (reflected)</td><td>Own microwaves</td></tr>
    <tr><td>Operating time</td><td>Daytime</td><td>Day or night</td></tr>
    <tr><td>Weather impact</td><td>Blocked by clouds</td><td>Sees through clouds/rain</td></tr>
    <tr><td>Wavelengths</td><td>Visible, NIR, SWIR, TIR</td><td>Microwave (C/X-band, etc.)</td></tr>
    <tr><td>Example satellites</td><td>Landsat-8, Sentinel-2</td><td>Sentinel-1, TerraSAR-X</td></tr>
    <tr><td>Typical uses</td><td>Land cover, albedo</td><td>Terrain, flood, stability</td></tr>
  </tbody>
</table>
""",
        unsafe_allow_html=True,
    )

    # ---------- 2. How acquired ----------
    st.markdown('<h3 class="section">2. How Are Satellite Images Acquired?</h3>', unsafe_allow_html=True)
    st.markdown(
        """
**Optical satellites** (passive) capture visible and infrared light. Examples: **Landsat-8 (30 m)**, **Sentinel-2 (10 m)**.  
Open data portal: Copernicus Data Space → https://browser.dataspace.copernicus.eu/  (Bajpai & Soni, 2017).

**SAR satellites** (active) send microwave pulses and record reflections. Examples: **Sentinel-1 (C-band, ~5 m)**, **TerraSAR-X (X-band, ~1 m)**.  
Cloud/lighting independent—useful for terrain and infrastructure assessment (Ablin et al., 2020).
        """
    )
    st.markdown(
        """
**Image acquisition steps**
- **Capture:** Polar orbits (e.g., Sentinel-2, ~5-day revisit) or geostationary (e.g., Meteosat).  
- **Transmission:** Downlink to ground stations for preprocessing/calibration.  
- **Access:** Download/query via portals (e.g., Copernicus Data Space).
        """
    )

    # ---------- 3. Processing ----------
    st.markdown('<h3 class="section">3. Image Processing for Satellite Images</h3>', unsafe_allow_html=True)
    st.markdown(
        "Raw images need correction and analysis to be useful for solar studies—adjusting pixel values for atmosphere, "
        "sensor noise, and geometry (Kaur et al., 2021). Tooling includes ESA **SNAP** → https://earth.esa.int/eogateway/tools/snap"
    )
    st.markdown(
        """
**Why it’s needed**
- Clouds/haze reduce optical clarity.  
- Terrain and view angles distort geometry.  
- Sensors/atmosphere bias brightness and color.

**Main processing types**
- **Radiometric correction:** Removes haze/sensor effects (e.g., **Sen2Cor** for Sentinel-2).  
- **Geometric correction:** Aligns to true map coordinates using DEM/orthorectification.  
- **Enhancement:** Improves contrast/sharpness for interpretation.  
- **Classification:** Groups pixels (e.g., forest/urban) to find solar-suitable areas.  
- **Change detection:** Compares dates to track land/seasonal change.
        """
    )

    # ---------- 4. Enhancement ----------
    st.markdown('<h3 class="section">4. Image Enhancement for Satellite Images</h3>', unsafe_allow_html=True)
    st.markdown(
        "Enhancement boosts visibility and interpretability without altering the underlying data (Ahuja & Biday, 2018). "
        "Common tools: **ENVI** → https://www.nv5geospatialsoftware.com/Products/ENVI and **SNAP**."
    )
    st.markdown(
        """
- **Spatial enhancement:** Pan-sharpening, high-pass filtering → pinpoint solar sites.  
- **Spectral enhancement:** Color composites, contrast stretching → distinguish land types.  
- **Temporal enhancement:** Time-series analysis → seasonal sunlight patterns (Kaur et al., 2021).  
- **Radiometric enhancement:** Histogram equalization/linear stretching → highlight faint clouds/dust.
        """
    )
    st.markdown(
        """
<table class="clean-table">
  <thead>
    <tr>
      <th>Type</th><th>Examples</th><th>Purpose for Solar</th>
    </tr>
  </thead>
  <tbody>
    <tr><td>Spatial</td><td>Pan-sharpening, high-pass</td><td>Precise siting of panels/arrays</td></tr>
    <tr><td>Spectral</td><td>Composites, stretching</td><td>Identify suitable land cover</td></tr>
    <tr><td>Temporal</td><td>Time-series</td><td>Understand seasonal radiation patterns</td></tr>
    <tr><td>Radiometric</td><td>Histogram eq., linear stretch</td><td>Reveal clouds/dust affecting sunlight</td></tr>
  </tbody>
</table>
""",
        unsafe_allow_html=True,
    )

    # ---------- 5. Challenges ----------
    st.markdown('<h3 class="section">5. Challenges with Satellite Imagery</h3>', unsafe_allow_html=True)
    st.markdown(
        """
<table class="clean-table">
  <thead>
    <tr>
      <th>Problem</th><th>Why it happens</th><th>How to fix it</th><th>Reference</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Clouds & haze (optical)</td>
      <td>Scatter light; obscure surface</td>
      <td>Atmospheric correction (e.g., 6S, Sen2Cor)</td>
      <td>Kaur et al., 2021</td>
    </tr>
    <tr>
      <td>Geometric distortions</td>
      <td>Terrain, viewing angle, orbit</td>
      <td>Orthorectification with DEM</td>
      <td>Bajpai & Soni, 2017</td>
    </tr>
    <tr>
      <td>Radiometric errors</td>
      <td>Sensor/atmospheric bias</td>
      <td>Calibration & color correction</td>
      <td>Ahuja & Biday, 2018</td>
    </tr>
    <tr>
      <td>Speckle noise (SAR)</td>
      <td>Coherent microwave interference</td>
      <td>Lee filter / speckle reduction</td>
      <td>Ablin et al., 2020</td>
    </tr>
    <tr>
      <td>Large data volume</td>
      <td>High resolution & frequent revisits</td>
      <td>Cloud platforms (Google Earth Engine; Copernicus)</td>
      <td>Kaur et al., 2021</td>
    </tr>
    <tr>
      <td>Resolution trade-offs</td>
      <td>Spatial vs spectral vs temporal limits</td>
      <td>Fuse optical + SAR for complementary strengths</td>
      <td>Bajpai & Soni, 2017</td>
    </tr>
  </tbody>
</table>
""",
        unsafe_allow_html=True,
    )

    # ---------- 6. Conclusion ----------
    st.markdown('<h3 class="section">6. Conclusion</h3>', unsafe_allow_html=True)
    st.markdown(
        "Satellite data (optical + SAR) enables mapping of sunlight distribution, evaluating terrain, and understanding "
        "seasonal patterns for solar planning. Tools like **SNAP**, **ENVI**, and **ArcGIS** "
        "(https://www.arcgis.com/index.html) make processing and enhancement accessible, while "
        "**Copernicus Data Space** (https://browser.dataspace.copernicus.eu/) provides open Sentinel data. "
        "Despite clouds, geometry, and data-scale challenges, modern correction, fusion, and cloud computing deliver "
        "reliable analysis. Combined with **AI**, these inputs improve solar estimation and forecasting for "
        "smarter, sustainable energy systems."
    )

    # ---------- 7. References (plain URLs) ----------
    st.markdown('<h3 class="section">7. References</h3>', unsafe_allow_html=True)
    st.markdown(
        """
<ol class="ref-list">
  <li>Ablin, R., Sulochana, C. H., & Prabin, G. S. J. (2020). <i>An investigation in satellite images based on image enhancement techniques.</i> European Journal of Remote Sensing, 53(1), 317–329. https://doi.org/10.1080/22797254.2019.1673216</li>
  <li>Ahuja, S., & Biday, S. (2018). <i>A survey of satellite image enhancement techniques.</i> International Journal of Advanced Intelligence and Research, 2(8), 2278–7844. https://www.researchgate.net/publication/322695750_A_Survey_of_Satellite_Image_Enhancement_Techniques</li>
  <li>Bajpai, S., & Soni, S. K. (2017). <i>Analysis of image enhancement techniques used in remote sensing satellite images.</i> International Journal of Computer Applications, 171(8), 30–34. https://doi.org/10.5120/ijca2017914884</li>
  <li>Kaur, H., Koundal, D., & Kadyan, V. (2021). <i>Image fusion techniques: A survey.</i> Archives of Computational Methods in Engineering, 28, 1–23. https://doi.org/10.1007/s11831-021-09540-7</li>
  <li>Suvitha, N. (2018). <i>Image fusion techniques—A survey.</i> International Journal of Research in Applied Science & Engineering Technology, 6(1), 288–291. https://www.ijraset.com/fileserve.php?FID=16955</li>
</ol>
""",
        unsafe_allow_html=True,
    )

    # ---------- Close wrapper ----------
    st.markdown("</div>", unsafe_allow_html=True)
