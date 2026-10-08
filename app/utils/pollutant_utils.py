import re
from typing import Dict, Any, List

# Unicode subscript translation table
SUBSCRIPT_MAP = {
    '₀': '0', '₁': '1', '₂': '2', '₃': '3', '₄': '4',
    '₅': '5', '₆': '6', '₇': '7', '₈': '8', '₉': '9'
}

# Canonical name aliases
POLLUTANT_ALIASES = {
    "pm2.5": "PM2.5",
    "pm25": "PM2.5",
    "pm10": "PM10",
    "no2": "NO2",
    "so2": "SO2",
    "co": "CO",
    "o3": "O3",
    "ozone": "O3",
    "nh3": "NH3",
    "pb": "Pb",
    "lead": "Pb"
}

# CPCB standards (µg/m³ except CO in mg/m³)
POLLUTANT_STANDARDS = {
    "PM2.5": 60.0,
    "PM10": 100.0,
    "NO2": 80.0,
    "SO2": 80.0,
    "O3": 100.0,
    "CO": 2.0,
    "NH3": 400.0,
    "Pb": 1.0
}

# Classification levels based on percentage of standard
CLASSIFICATION_LEVELS = [
    (50, "Good", "bg-green-500"),
    (100, "Satisfactory", "bg-yellow-500"),
    (200, "Moderate", "bg-orange-500"),
    (300, "Poor", "bg-red-500"),
    (400, "Very Poor", "bg-purple-500"),
    (float("inf"), "Severe", "bg-gray-800")
]

def normalize_pollutant_name(name: str) -> str:
    """
    Convert any pollutant string variant into canonical ASCII representation.
    Handles Unicode subscripts (e.g., PM₂.₅ -> PM2.5, NO₂ -> NO2, SO₂ -> SO2, O₃ -> O3),
    units in parentheses, underscores, and case differences.
    """
    if not name:
        return ""
    
    clean = str(name).strip()
    # Replace subscripts
    for sub, normal in SUBSCRIPT_MAP.items():
        clean = clean.replace(sub, normal)
    
    # Remove unit annotations like (ug/m3), (mg/m3), etc.
    clean = re.sub(r"\(.*?\)", "", clean).strip()
    
    # Replace underscores with periods if representing PM2.5
    clean = clean.replace("_", ".")
    
    # Check lowercased alias mapping
    alias_key = clean.lower().replace(" ", "").replace(".", "")
    # Check with dot
    key_with_dot = clean.lower().replace(" ", "")
    
    if key_with_dot in POLLUTANT_ALIASES:
        return POLLUTANT_ALIASES[key_with_dot]
    if alias_key in POLLUTANT_ALIASES:
        return POLLUTANT_ALIASES[alias_key]
        
    return clean

def filter_off(pollutants: Dict[str, Any]) -> Dict[str, Any]:
    """
    Filter and normalize input pollutant dictionary to canonical names.
    Preserves valid pollutant keys and values.
    """
    filtered = {}
    for key, value in pollutants.items():
        canonical = normalize_pollutant_name(key)
        if canonical in POLLUTANT_STANDARDS:
            filtered[canonical] = value
    return filtered

def classify_pollutants(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Classify pollutants according to CPCB standards.
    Safely ignores None or negative values. Unknown pollutants are handled safely.
    """
    results = []
    if not isinstance(data, dict):
        return results

    for pollutant_raw, value in data.items():
        if value is None:
            continue
        try:
            val_float = float(value)
        except (ValueError, TypeError):
            continue

        if val_float < 0:
            continue

        canonical_key = normalize_pollutant_name(pollutant_raw)
        standard = POLLUTANT_STANDARDS.get(canonical_key)

        if standard is None:
            continue

        percentage = (val_float / standard) * 100.0

        for limit, status, css_class in CLASSIFICATION_LEVELS:
            if percentage <= limit:
                results.append({
                    "name": canonical_key,
                    "value": round(val_float, 2),
                    "standard": standard,
                    "percentage": round(percentage, 1),
                    "status": status,
                    "color": css_class,
                    "class": css_class
                })
                break

    return results
