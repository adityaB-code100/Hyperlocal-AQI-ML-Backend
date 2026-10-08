import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import folium
import geopandas as gpd
from app.config import Config
from app.services.aqi_service import get_aqi_color

logger = logging.getLogger(__name__)

CITY_COORDINATES = [
    {"name": "Nanded", "lat": 18.916670, "lon": 77.500000},
    {"name": "Pune", "lat": 18.520430, "lon": 73.856743},
    {"name": "Mumbai", "lat": 19.076090, "lon": 72.877426},
    {"name": "Nagpur", "lat": 21.145800, "lon": 79.088200},
    {"name": "Nashik", "lat": 20.011000, "lon": 73.790000}
]

def mapgenerator(date: str, aqi_by_village: Optional[Dict[str, Any]] = None,
                 output_dir: Optional[Path] = None) -> Optional[folium.Map]:
    """
    Generate an interactive Folium AQI map for Maharashtra districts.
    
    Robustness:
    - Safely handles missing cities without KeyError.
    - Gracefully handles None, negative, or non-numeric AQI.
    - Explicit 'No Data' visual state for missing cities.
    - Gracefully falls back if GeoJSON file is missing.
    - Saves output to generated/maps/ without crashing.
    """
    aqi_input = aqi_by_village or {}
    
    # Create case-insensitive lookup
    normalized_aqi = {}
    for k, v in aqi_input.items():
        if k:
            normalized_aqi[str(k).strip().lower()] = v

    # Build location markers
    markers = []
    bounds = []
    for city in CITY_COORDINATES:
        c_name = city["name"]
        val = normalized_aqi.get(c_name.lower())
        
        # Validate numeric AQI
        aqi_val = None
        if val is not None:
            try:
                aqi_val = float(val)
            except (ValueError, TypeError):
                aqi_val = None

        markers.append({
            "name": c_name,
            "lat": city["lat"],
            "lon": city["lon"],
            "aqi": aqi_val
        })
        bounds.append([city["lat"], city["lon"]])

    # Initialize Folium Map
    m = folium.Map(location=[19.5, 76.0], zoom_start=6)

    # Load GeoJSON if available
    geojson_path = Config.GEOJSON_PATH
    if geojson_path.exists():
        try:
            gdf = gpd.read_file(geojson_path)
            
            # Match districts
            village_map = {m_item["name"].lower(): m_item["aqi"] for m_item in markers if m_item["aqi"] is not None}
            district_aqi = {}
            for _, row in gdf.iterrows():
                if "DISTRICT" in row and pd_not_na(row["DISTRICT"]):
                    dist = str(row["DISTRICT"]).lower()
                    for v_name, v_aqi in village_map.items():
                        if v_name in dist:
                            district_aqi[dist] = max(district_aqi.get(dist, 0), v_aqi)

            def style_func(feature):
                props = feature.get("properties", {})
                d_name = str(props.get("DISTRICT", "")).lower()
                if d_name in district_aqi:
                    c = get_aqi_color(district_aqi[d_name])
                    return {"fillColor": c, "color": "transparent", "weight": 0, "fillOpacity": 0.55}
                return {"fillColor": "transparent", "color": "#D1D5DB", "weight": 0.5, "fillOpacity": 0.05}

            folium.GeoJson(
                str(geojson_path),
                style_function=style_func,
                name="Districts"
            ).add_to(m)
        except Exception as e:
            logger.warning("GeoJSON overlay could not be loaded: %s", e)
    else:
        logger.warning("GeoJSON file not found at %s. Rendering markers only.", geojson_path)

    # Add markers
    for loc in markers:
        val = loc["aqi"]
        color = get_aqi_color(val)
        popup_text = f"<b>{loc['name']}</b>: AQI {val:.0f}" if val is not None else f"<b>{loc['name']}</b>: No Data"
        
        folium.CircleMarker(
            location=[loc["lat"], loc["lon"]],
            radius=9,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.8,
            popup=popup_text,
            tooltip=popup_text
        ).add_to(m)

    if bounds:
        m.fit_bounds(bounds)

    # Click event JavaScript for external API callback
    map_id = m.get_name()
    api_endpoint = "/p"
    click_js = f"""
    <script>
        {map_id}.on('click', function(e) {{
            var lat = e.latlng.lat.toFixed(6);
            var lng = e.latlng.lng.toFixed(6);
            fetch('{api_endpoint}', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify({{ latitude: lat, longitude: lng }})
            }})
            .then(res => res.json())
            .then(data => console.log('Coordinate response:', data))
            .catch(err => console.error('Error posting coordinates:', err));
        }});
    </script>
    """
    m.get_root().html.add_child(folium.Element(click_js))

    # Save to generated maps directory
    target_dir = output_dir or Config.GENERATED_MAPS_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    out_file = target_dir / f"map{date}.html"
    try:
        m.save(str(out_file))
        logger.info("Saved map to %s", out_file)
    except Exception as e:
        logger.error("Failed to save map HTML to %s: %s", out_file, e)

    return m

def pd_not_na(val):
    return val is not None and str(val).lower() != "nan"
