import logging
from typing import List, Dict, Optional
import plotly.graph_objs as go
import plotly.offline as pyo
from app.database.repositories import get_city_monthly_aqi

logger = logging.getLogger(__name__)

def get_aqi_color(aqi: Optional[float]) -> str:
    """Return standard CPCB color hex for given AQI value."""
    if aqi is None:
        return "#9CA3AF"  # Gray for missing/unknown
    try:
        val = float(aqi)
    except (ValueError, TypeError):
        return "#9CA3AF"

    if val <= 50:
        return "#22C55E"   # Good - Green
    elif val <= 100:
        return "#FACC15"   # Satisfactory - Yellow
    elif val <= 200:
        return "#F97316"   # Moderate - Orange
    elif val <= 300:
        return "#EF4444"   # Poor - Red
    elif val <= 400:
        return "#9333EA"   # Very Poor - Purple
    else:
        return "#111827"   # Severe - Dark/Maroon

def create_aqi_forecast_chart(dates: List[str], aqi_values: List[Optional[float]],
                              title: str = "7 days Graphical AQI Forecast") -> str:
    """
    Create an AQI forecast chart (time vs AQI) using Plotly.
    Returns an embeddable HTML <div> string.
    """
    if not dates or not aqi_values:
        return "<div class='text-gray-500 italic'>No forecast data available</div>"

    fig = go.Figure()

    # Main AQI line
    fig.add_trace(go.Scatter(
        x=dates,
        y=aqi_values,
        mode="lines+markers",
        name="AQI",
        line=dict(color="#2563EB", width=3),
        marker=dict(size=7, color="white", line=dict(color="#2563EB", width=2)),
        hovertemplate="Date: %{x}<br>AQI: %{y}<extra></extra>"
    ))

    # Fill under curve
    fig.add_trace(go.Scatter(
        x=dates,
        y=aqi_values,
        fill='tozeroy',
        mode='none',
        fillcolor="rgba(37, 99, 235, 0.15)",
        showlegend=False
    ))

    # Layout styling
    fig.update_layout(
        title=dict(
            text=f"🌍 {title}",
            x=0.5,
            xanchor="center",
            font=dict(size=20, family="Arial, sans-serif", color="#111827")
        ),
        xaxis=dict(
            title="Date",
            showgrid=False,
            tickfont=dict(size=12, color="#374151"),
            tickangle=-90
        ),
        yaxis=dict(
            title="AQI",
            gridcolor="rgba(0,0,0,0.05)",
            zeroline=False,
            tickfont=dict(size=12, color="#374151")
        ),
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=40, r=20, t=50, b=80),
        height=300,
        hoverlabel=dict(
            bgcolor="white",
            font_size=13,
            font_family="Arial"
        )
    )

    return pyo.plot(
        fig,
        include_plotlyjs=False,
        output_type="div",
        config={"displayModeBar": False, "responsive": True}
    )

def plot_monthly_aqi(city: str) -> str:
    """
    Generate responsive monthly average AQI bar chart for a city.
    Returns an embeddable HTML <div> string.
    """
    monthly_aqi = get_city_monthly_aqi(city)
    if not monthly_aqi:
        return f"<div class='text-gray-500 italic'>No monthly AQI data available for {city}</div>"

    sorted_data = dict(sorted(monthly_aqi.items(), key=lambda x: x[0]))
    months = list(sorted_data.keys())
    values = list(sorted_data.values())

    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    month_labels = []
    for m in months:
        try:
            m_num = int(m.split("-")[1])
            month_labels.append(month_names[m_num - 1])
        except (IndexError, ValueError):
            month_labels.append(m)

    bar_colors = [get_aqi_color(v) for v in values]

    fig = go.Figure(
        data=[go.Bar(
            x=month_labels,
            y=values,
            marker=dict(color=bar_colors, line=dict(color="rgba(0,0,0,0.3)", width=1)),
            text=[f"{v:.0f}" if v is not None else "N/A" for v in values],
            texttemplate="%{text}",
            textposition="auto",
            insidetextanchor="end",
            textfont=dict(color="black"),
            hovertemplate="Month: %{x}<br>AQI: %{y}<extra></extra>"
        )]
    )

    fig.update_layout(
        title=dict(
            text=f"📊 Monthly Average AQI - {city}",
            x=0.5,
            font=dict(size=20, family="Arial, sans-serif", color="#111827")
        ),
        xaxis=dict(
            title="Month",
            tickfont=dict(size=12, color="#374151"),
            showgrid=False,
            zeroline=False
        ),
        yaxis=dict(
            title="AQI",
            gridcolor="rgba(0,0,0,0.05)",
            tickfont=dict(size=12, color="#374151"),
            zeroline=False
        ),
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=40, r=20, t=80, b=60),
        height=300,
        bargap=0.25,
        hoverlabel=dict(
            bgcolor="lavender",
            bordercolor="#000000",
            font_size=13,
            font_family="Arial"
        )
    )

    return pyo.plot(
        fig,
        include_plotlyjs=False,
        output_type="div",
        config={"displayModeBar": False, "responsive": True}
    )
