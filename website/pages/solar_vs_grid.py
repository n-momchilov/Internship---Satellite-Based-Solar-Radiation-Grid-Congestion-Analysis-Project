import streamlit as st
import geopandas as gpd
import pandas as pd
import numpy as np
from pathlib import Path
import json

RISK_LABELS = {0: "Low", 1: "Medium", 2: "High"}
SEASONAL_GHI_COLS = ["GHI_spring", "GHI_summer", "GHI_autumn", "GHI_winter"]


def _find_existing_path(paths):
    return next((p for p in paths if p.exists()), None)


def _ceil_one_decimal(value):
    return np.ceil(value * 10) / 10


def _load_cell_panel_pv():
    """Use the same clipped PV field used by the map cell panel."""
    possible_paths = [
        Path("static/grid/grid_data.geojson"),
        Path("website/static/grid/grid_data.geojson"),
    ]
    path = _find_existing_path(possible_paths)
    if path is None:
        return None

    data = json.loads(path.read_text(encoding="utf-8"))
    features = data.get("features", [])
    rows = []
    for feature in features:
        props = feature.get("properties", {})
        rows.append({
            "cell_id": props.get("cell_id"),
            "pv_penetration_pct": props.get("pv_penetration_pct"),
        })

    pv = pd.DataFrame(rows)
    pv["pv_penetration_pct"] = pd.to_numeric(pv["pv_penetration_pct"], errors="coerce").clip(0, 100)
    return pv


def _build_stats_table(grid):
    stats_cols = ["cell_id", "congestion_class"] + [col for col in SEASONAL_GHI_COLS if col in grid.columns]
    if "GHI_annual_mean" in grid.columns:
        stats_cols.append("GHI_annual_mean")

    stats = grid[stats_cols].copy()
    pv = _load_cell_panel_pv()
    if pv is not None:
        stats = stats.merge(pv, on="cell_id", how="left")
    elif "pv_penetration_pct" in grid.columns:
        stats["pv_penetration_pct"] = pd.to_numeric(grid["pv_penetration_pct"], errors="coerce").clip(0, 100)
    elif "pv_penetration" in grid.columns:
        stats["pv_penetration_pct"] = pd.to_numeric(grid["pv_penetration"], errors="coerce").clip(0, 100)
    else:
        stats["pv_penetration_pct"] = np.nan

    return stats


def _ghi_validation_spread(stats):
    spreads = {}
    for col in SEASONAL_GHI_COLS:
        if col not in stats.columns:
            continue
        valid = stats.dropna(subset=[col, "congestion_class"])
        if valid.empty:
            continue
        means = valid.groupby("congestion_class")[col].mean()
        if len(means) >= 2:
            spreads[col] = means.max() - means.min()

    if not spreads and "GHI_annual_mean" in stats.columns:
        valid = stats.dropna(subset=["GHI_annual_mean", "congestion_class"])
        means = valid.groupby("congestion_class")["GHI_annual_mean"].mean()
        if len(means) >= 2:
            spreads["GHI_annual_mean"] = means.max() - means.min()

    if not spreads:
        return np.nan, {}

    spread = max(spreads.values())
    return spread, spreads


def _pv_summary(stats):
    valid = stats.dropna(subset=["pv_penetration_pct", "congestion_class"])
    if valid.empty:
        return pd.Series(dtype=float), np.nan

    means = valid.groupby("congestion_class")["pv_penetration_pct"].mean()
    low = means.get(0.0, np.nan)
    high = means.get(2.0, np.nan)
    ratio = high / low if pd.notna(low) and pd.notna(high) and low > 0 else np.nan
    return means, ratio


def render():
    st.markdown("## Solar vs Grid: What Drives Congestion?")
    st.markdown(
        "This page presents the combined analysis from both research pipelines. "
        "Pipeline 1 uses Sentinel-2 satellite imagery and machine learning to predict "
        "WHERE congestion risk is highest. Pipeline 2 uses Meteosat SEVIRI radiation data "
        "to understand WHY those areas face congestion. Together, they answer the main "
        "research question: how can satellite imagery and AI techniques analyse grid "
        "congestion in Amsterdam, and how can solar radiation estimation support those findings?"
    )
    st.markdown(
        "*This analysis was conducted by Nikola Momchilov as part of the HBO-ICT internship "
        "at Fontys Innovation Lab (2026), within the Sustainable Data and AI Applications department.*"
    )
    
    # Try to load the combined GeoPackage
    possible_paths = [
        Path("../congestion_radiation_grid.gpkg"),
        Path("congestion_radiation_grid.gpkg"),
        Path("static/grid/congestion_radiation_grid.gpkg"),
    ]
    
    grid = None
    for p in possible_paths:
        if p.exists():
            grid = gpd.read_file(p)
            break
    
    if grid is None:
        st.warning("Combined data file (congestion_radiation_grid.gpkg) not found.")
        st.info("Run both notebooks (congestion_analysis.ipynb and radiation_estimation.ipynb) first to generate this file.")
        return

    stats = _build_stats_table(grid)
    ghi_spread, ghi_spreads_by_season = _ghi_validation_spread(stats)
    ghi_spread_display = _ceil_one_decimal(ghi_spread) if pd.notna(ghi_spread) else np.nan
    pv_means, pv_ratio = _pv_summary(stats)
    summer_col = "GHI_summer" if "GHI_summer" in stats.columns else "GHI_annual_mean"
    
    # ---- SECTION 1: THE CORE FINDING ----
    st.markdown("---")
    st.markdown("### The Core Finding")
    st.markdown(
        "The most important result from combining both pipelines is this: "
        "**solar radiation is effectively the same everywhere in Amsterdam.** "
        f"The largest seasonal GHI difference between congestion classes is only "
        f"{ghi_spread_display:.1f} W/m2, which is negligible at city scale."
    )
    st.markdown(
        "This means the spatial pattern of congestion risk CANNOT be explained by natural "
        "differences in solar resource. All areas receive nearly the same sunlight. The remaining variation "
        "comes mainly from human factors: how many solar panels have been installed, "
        "and how much electricity the area consumes."
    )
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric(
            label="GHI variation across congestion classes",
            value=f"< {ghi_spread_display:.1f} W/m2",
            delta="Negligible",
            delta_color="off"
        )
        st.caption(
            f"The maximum seasonal class-mean spread is {ghi_spread:.2f} W/m2, "
            f"reported consistently as under {ghi_spread_display:.1f} W/m2. "
            "Solar resource does not explain congestion."
        )
    with col2:
        low_pv = pv_means.get(0.0, np.nan)
        high_pv = pv_means.get(2.0, np.nan)
        if pd.notna(low_pv) and pd.notna(high_pv) and pd.notna(pv_ratio):
            st.metric(
                label="PV penetration: High vs Low risk",
                value=f"{pv_ratio:.2f}x difference",
                delta="Higher PV adoption in high-risk cells"
            )
            st.caption(
                f"Using pv_penetration_pct clipped to 0-100: low-risk cells average "
                f"{low_pv:.1f}% PV penetration, while high-risk cells average "
                f"{high_pv:.1f}%. Two neighbourhoods with nearly identical sunlight "
                "can have different congestion risk depending on how many panels are installed."
            )
        else:
            st.metric(label="PV penetration", value="Data incomplete")
    
    st.info(
        "In simple terms: the sun does not care whether an area has 5 or 500 solar panels. "
        "It shines equally everywhere in Amsterdam. But the grid does care. An area with "
        "500 panels feeding electricity back into cables that were designed for 50 "
        "is more likely to face congestion. An area with 5 panels is less likely to. Congestion is a human "
        "infrastructure problem, not a natural resource problem."
    )
    
    # ---- SECTION 2: RADIATION BY CONGESTION CLASS ----
    st.markdown("---")
    st.markdown("### Radiation by Congestion Class")
    st.markdown(
        "This table shows the average solar radiation and PV penetration for each "
        f"congestion risk level. Notice that the GHI column changes by under "
        f"{ghi_spread_display:.1f} W/m2 across classes, while PV penetration changes more visibly. "
        "This confirms that congestion patterns "
        "are driven by adoption rates, not by solar resource availability."
    )
    
    if summer_col in stats.columns and 'congestion_class' in stats.columns:
        valid = stats.dropna(subset=[summer_col, 'congestion_class'])
        if len(valid) > 0:
            summary = valid.groupby('congestion_class').agg(
                cells=('cell_id', 'count'),
                mean_ghi=(summer_col, 'mean'),
                mean_pv=('pv_penetration_pct', 'mean'),
            ).reset_index()
            summary['congestion_class'] = summary['congestion_class'].map(
                {0: 'Low', 1: 'Medium', 2: 'High'})
            ghi_label = 'Mean Summer GHI (W/m2)' if summer_col == 'GHI_summer' else 'Mean GHI (W/m2)'
            summary.columns = ['Risk Level', 'Cells', ghi_label, 'Mean PV Penetration (%)']
            st.dataframe(summary.style.format({
                ghi_label: '{:.1f}',
                'Mean PV Penetration (%)': '{:.1f}',
            }), use_container_width=True)
    
    # ---- SECTION 3: CONGESTION DRIVER CLASSIFICATION ----
    st.markdown("---")
    st.markdown("### What Drives Congestion in Each Area?")
    st.markdown(
        "Based on the combined analysis, each high-risk cell is classified into one "
        "of three categories. This classification is the primary applied contribution "
        "of the project: it turns a generic 'high risk' label into actionable information "
        "about WHAT KIND of congestion each area faces."
    )
    
    if 'congestion_driver' in grid.columns:
        drivers = grid['congestion_driver'].value_counts()
        
        col1, col2, col3, col4 = st.columns(4)
        driver_items = [
            ("Consumption-driven congestion", "Consumption-driven", col1, "#DC143C"),
            ("Solar-driven congestion", "Solar-driven", col2, "#FF8C00"),
            ("Mixed drivers", "Mixed", col3, "#8B008B"),
            ("Low/Medium risk", "Low risk", col4, "#32CD32"),
        ]
        for full_name, short_name, col, color in driver_items:
            count = drivers.get(full_name, 0)
            with col:
                st.markdown(
                    f"<div style='text-align:center; padding:16px; "
                    f"border-radius:12px; border:2px solid {color}; margin-bottom:8px;'>"
                    f"<div style='font-size:32px; font-weight:bold; color:{color};'>{count}</div>"
                    f"<div style='font-size:14px; color:gray;'>{short_name}</div>"
                    f"</div>",
                    unsafe_allow_html=True
                )
    
    # ---- SECTION 4: WHAT EACH TYPE MEANS ----
    st.markdown("---")
    st.markdown("### What Does Each Type Mean for Grid Planning?")
    st.markdown(
        "This is where the research becomes practically useful. A grid planner looking "
        "at the congestion map sees red cells, but does not know what to do about them. "
        "The driver classification tells them which solution to apply where."
    )
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            "<div style='padding:16px; border-radius:12px; border-left:4px solid #DC143C; "
            "background-color:rgba(220,20,60,0.05);'>"
            "<h4 style='color:#DC143C; margin-top:0;'>Consumption-driven (223 cells)</h4>"
            "<p>These areas face congestion because electricity demand exceeds what the "
            "cables and transformers can handle. The infrastructure is old and was not "
            "designed for current load levels (data centres, EV charging, heat pumps).</p>"
            "<p><strong>Solutions:</strong> Cable upgrades, new substations, "
            "demand-side management programs that shift peak consumption.</p>"
            "<p><strong>Cost:</strong> Expensive, long-term infrastructure investments.</p>"
            "</div>",
            unsafe_allow_html=True
        )
    with col2:
        st.markdown(
            "<div style='padding:16px; border-radius:12px; border-left:4px solid #FF8C00; "
            "background-color:rgba(255,140,0,0.05);'>"
            "<h4 style='color:#FF8C00; margin-top:0;'>Solar-driven (163 cells)</h4>"
            "<p>These areas face congestion because many solar panels feed electricity "
            "back into the grid, creating reverse power flow that overloads cables "
            "designed for one-directional delivery.</p>"
            "<p><strong>Solutions:</strong> Smart inverters, battery storage, "
            "local energy communities that match generation with nearby consumption.</p>"
            "<p><strong>Cost:</strong> Relatively lower cost, faster to implement.</p>"
            "</div>",
            unsafe_allow_html=True
        )
    
    st.markdown(
        "Without the combined analysis from both pipelines, all high-risk cells look the same. "
        "The radiation comparison provides the distinction that makes the analysis actionable."
    )
    
    # ---- SECTION 5: SEASONAL PATTERN ----
    st.markdown("---")
    st.markdown("### Seasonal Radiation Pattern")
    st.markdown(
        "Solar radiation in the Netherlands varies strongly by season. "
        "Summer receives approximately 6.5 times more solar energy than winter. "
        "This means solar-driven congestion is a seasonal problem: "
        "grid stress from PV feed-in peaks in summer and nearly disappears in winter. "
        "Consumption-driven congestion follows the opposite pattern: "
        "electricity demand peaks in winter (heating, lighting) and drops in summer."
    )
    
    seasonal_data = {}
    for season in ['spring', 'summer', 'autumn', 'winter']:
        col_name = f'GHI_{season}'
        if col_name in grid.columns:
            val = grid[col_name].mean()
            if not np.isnan(val):
                seasonal_data[season.capitalize()] = round(val, 1)
    
    if seasonal_data:
        season_df = pd.DataFrame({
            'Season': list(seasonal_data.keys()),
            'Mean GHI (W/m2)': list(seasonal_data.values())
        })
        st.bar_chart(season_df.set_index('Season'))
        
        if 'GHI_summer' in grid.columns and 'GHI_winter' in grid.columns:
            summer_mean = grid['GHI_summer'].mean()
            winter_mean = grid['GHI_winter'].mean()
            if winter_mean > 0:
                ratio = summer_mean / winter_mean
                st.caption(
                    f"Summer average: {summer_mean:.1f} W/m2 | "
                    f"Winter average: {winter_mean:.1f} W/m2 | "
                    f"Ratio: {ratio:.1f}x"
                )
    
    # ---- SECTION 6: CONNECTION TO RESEARCH ----
    st.markdown("---")
    st.markdown("### Connection to the Research")
    st.markdown(
        "This combined analysis answers **SQ6** of the research: "
        "*Why is it important to analyse the combined grid congestion with solar radiation "
        "estimation, and what practical insights does this combined approach give?*"
    )
    st.markdown(
        "The answer: radiation estimation reveals that Amsterdam's solar resource is spatially uniform. "
        f"The largest seasonal GHI spread across congestion classes is under {ghi_spread_display:.1f} W/m2, "
        "so congestion risk is better explained by human factors (PV adoption density and "
        "consumption levels) than by natural solar resource variation. The combined approach produces "
        "a congestion driver classification that distinguishes solar-driven from consumption-driven "
        "congestion zones, which neither pipeline can produce alone. "
        "This distinction directly informs grid investment decisions."
    )
    st.markdown(
        "The literature gap identified in the research paper states that no existing study "
        "combines satellite-based spatial data with grid congestion analysis in one workflow for "
        "a specific city. This page demonstrates exactly that combination and the insights it produces."
    )
    
    # ---- SECTION 7: LIMITATIONS ----
    st.markdown("---")
    st.markdown("### Limitations")
    st.markdown(
        "**Proxy target:** The congestion risk classes are constructed from Liander's published "
        "energy data, not from actual grid operator congestion declarations. The STORM substation "
        "dataset from Liander contains real transformer loading data but is fully anonymized "
        "without geographic coordinates, making it unusable for spatial analysis."
    )
    st.markdown(
        "**PV data coverage:** Liander PV penetration data covers only 42% of grid cells. "
        "Cells without PV data are treated as having zero PV adoption, which may overcount "
        "consumption-driven congestion and undercount solar-driven congestion."
    )
    st.markdown(
        "**Radiation resolution:** The CM SAF SIS product has 0.05 degree resolution "
        "(approximately 5.5 km per pixel). Multiple 1 km grid cells share the same radiation "
        "value. At this resolution, very local effects like building shadows cannot be captured."
    )
    
    st.markdown(
        "<div style='text-align:center; margin-top:40px; padding:16px; color:gray; font-size:13px;'>"
        "Nikola Momchilov | HBO-ICT Internship 2026 | Fontys Innovation Lab<br>"
        "Supervisor: Priyanka Darbari | Sustainable Data and AI Applications"
        "</div>",
        unsafe_allow_html=True
    )
