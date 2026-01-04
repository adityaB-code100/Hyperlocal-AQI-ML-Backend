def filter_off(pollutants: dict) -> dict:
    required_keys = {
        "PM2.5": "PM₂.₅",
        "PM10": "PM₁₀",
        "NO2": "NO₂",
        "SO2": "SO₂",
        "Ozone": "O₃",
        "CO (mg/m³)": "CO",   # match your key name
        "NH3": "NH₃",
        "Pb": "Pb"
    }

    # keep only those pollutants which exist in data
    return {required_keys[k]: pollutants[k] for k in required_keys if k in pollutants}


def classify_pollutants(data):
    # CPCB 24-hr / 8-hr standards (µg/m³ except CO in mg/m³)
    standards = {
        "PM2.5": 60,
        "PM10": 100,
        "NO2": 80,
        "SO2": 80,
        "O3": 100,   # 8-hr
        "CO": 2,     # mg/m³ (8-hr)
        "NH3": 400
    }

    # AQI-like classification levels (based on % of standard)
    levels = [
        (50, "Good", "bg-green-500", "bg-green-500"),
        (100, "Satisfactory", "bg-yellow-500", "bg-yellow-500"),
        (200, "Moderate", "bg-orange-500", "bg-orange-500"),
        (300, "Poor", "bg-red-500", "bg-red-500"),
        (400, "Very Poor", "bg-purple-500", "bg-purple-500"),
        (9999, "Severe", "bg-gray-800", "bg-gray-800")
    ]

    results = []
    for pollutant, value in data.items():
        if value is None or value < 0:
            continue  # Skip invalid values

        # Normalize pollutant key (e.g., "PM₂.₅" → "PM2.5")
        key = pollutant.replace("₂", "2").replace("₅", "5").replace("_", ".")
        standard = standards.get(key, None)

        if not standard:  
            continue  # Skip pollutants not in standard list

        # Calculate % of standard
        percentage = (value / standard) * 100

        # Find AQI category
        for limit, status, color, css_class in levels:
            if percentage <= limit:
                results.append({
                    "name": pollutant,
                    "value": round(value, 2),
                    "standard": standard,
                    "percentage": (round(percentage, 1)),
                    "status": status,
                    "color": color,
                    "class": css_class
                })
                break

    # Sort pollutants by % exceedance (worst first)
    #results.sort(key=lambda x: x["percentage"], reverse=True)

    return results

