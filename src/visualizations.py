"""
visualizations.py
All Plotly chart functions for the Technology Adoption Analyzer.
Each function returns a plotly Figure object — call st.plotly_chart(fig) in app.py.

Visual language: energy-agency report style, matched to the public showcase site.
Deep teal-navy = historical / primary data. Cyan = forecast, emphasis, positive
contribution. Terracotta = negative contribution only.
"""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

TARGET_COL = "renewable_energy_pct"

# ── Design tokens (mirrored in app.py CSS and .streamlit/config.toml) ─────────
INK    = "#06303C"   # deep teal-navy — text, primary data series
INK2   = "#0C4657"
TEAL   = "#0E7C86"   # secondary data, positive values
CYAN   = "#19A3B8"   # emphasis, forecasts, interaction
AMBER  = "#D98A2B"
NEG    = "#B45A2B"   # negative contributions / declines only
SLATE  = "#4A6673"   # muted labels (dark enough to read)
GRID   = "#D3E2E6"   # chart gridlines
ZERO   = "#8DA8B1"   # zero lines

FONT_BODY    = "Barlow, Segoe UI, sans-serif"
FONT_DISPLAY = "Barlow Condensed, Barlow, sans-serif"
FONT_MONO    = "IBM Plex Mono, Menlo, monospace"

COLORS = {
    "primary":   INK,
    "secondary": CYAN,
    "accent":    TEAL,
    "warning":   AMBER,
    "danger":    NEG,
    "grey":      SLATE,
}

REGION_COLORS = {
    "East Asia":      "#1793A8",
    "Southeast Asia": "#0E7C86",
    "South Asia":     "#3F5F99",
    "Europe":         "#06303C",
    "North America":  "#4A6673",
    "Latin America":  "#C4801F",
    "Africa":         "#2F7A4C",
    "Middle East":    "#B45A2B",
    "Oceania":        "#5A9E8E",
}

CLUSTER_SEQUENCE = [
    "#19A3B8", "#06303C", "#C4801F", "#B45A2B",
    "#0E7C86", "#3F5F99", "#2F7A4C", "#4A6673",
]

# Rank shades for bar charts — every bar stays legible regardless of value spread
RANK_SHADES = [
    "#8CC6CF", "#6FB8C3", "#52AAB7", "#2EA0B2", "#19A3B8",
    "#15899A", "#117181", "#0D5A66", "#09424B", "#06303C",
]

SEQUENTIAL_TEAL = [
    [0.0,  "#D3E6E9"],
    [0.30, "#9DCBD4"],
    [0.55, "#55AEBE"],
    [0.80, "#19A3B8"],
    [1.0,  "#06303C"],
]

# ISO-2 to ISO-3 mapping for choropleth
ISO2_TO_ISO3 = {
    "IN":"IND","CN":"CHN","JP":"JPN","KR":"KOR","SG":"SGP",
    "MY":"MYS","TH":"THA","VN":"VNM","ID":"IDN","PH":"PHL",
    "DE":"DEU","FR":"FRA","GB":"GBR","ES":"ESP","IT":"ITA",
    "SE":"SWE","NO":"NOR","DK":"DNK","NL":"NLD","PL":"POL",
    "US":"USA","BR":"BRA","MX":"MEX","CA":"CAN","AR":"ARG",
    "CL":"CHL","CO":"COL","ZA":"ZAF","NG":"NGA","KE":"KEN",
    "ET":"ETH","MA":"MAR","EG":"EGY","SA":"SAU","AE":"ARE",
    "QA":"QAT","KW":"KWT","BH":"BHR","OM":"OMN",
    "AU":"AUS","NZ":"NZL","TR":"TUR","PK":"PAK","BD":"BGD",
}


def _exhibit(fig):
    """
    Apply consistent exhibit typography. Call before returning any figure.
    Axis ticks, axis titles, legends and colorbars are coloured EXPLICITLY —
    Plotly's default template renders them in a pale grey that is close to
    unreadable against a white page.
    """
    fig.update_layout(
        font=dict(family=FONT_BODY, size=13, color=INK),
        title=dict(
            font=dict(family=FONT_DISPLAY, size=19, color=INK),
            x=0.01, xanchor="left",
        ),
        legend=dict(
            font=dict(family=FONT_BODY, size=12, color=INK),
            title=dict(font=dict(family=FONT_BODY, size=12, color=SLATE)),
            bgcolor="rgba(255,255,255,0.9)",
            bordercolor=GRID,
            borderwidth=1,
        ),
        hoverlabel=dict(
            bgcolor="#FFFFFF",
            bordercolor="#9DBBC2",
            font=dict(family=FONT_BODY, size=12, color=INK),
        ),
    )
    axis_style = dict(
        automargin=True,
        tickfont=dict(family=FONT_BODY, size=12, color=INK),
        title_font=dict(family=FONT_BODY, size=13, color=SLATE),
    )
    fig.update_xaxes(**axis_style)
    fig.update_yaxes(**axis_style)

    # Colorbar text (choropleth and any continuous scale)
    try:
        fig.update_coloraxes(
            colorbar_tickfont=dict(family=FONT_MONO, size=11, color=INK),
            colorbar_title_font=dict(family=FONT_BODY, size=12, color=SLATE),
        )
    except Exception:
        pass
    return fig


def plot_historical_trend(df, country_code, country_name):
    """Line chart of historical renewable energy % over time for one country."""
    cdf = df[df["country_code"] == country_code].sort_values("year")

    if cdf.empty:
        return go.Figure()

    fig = px.line(
        cdf, x="year", y=TARGET_COL,
        markers=True,
        title=f"Renewable Energy — {country_name}",
        labels={"year": "Year", TARGET_COL: "Renewable Energy (%)"},
        color_discrete_sequence=[INK],
    )
    fig.update_traces(
        line_width=3, marker_size=7,
        marker=dict(line=dict(width=0)),
        fill="tozeroy", fillcolor="rgba(14, 124, 134, 0.22)",
    )
    fig.update_layout(
        hovermode="x unified",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False, linecolor=GRID),
        yaxis=dict(gridcolor=GRID, range=[0, 105]),
        margin=dict(l=10, r=10, t=44, b=10),
    )
    return _exhibit(fig)


def plot_forecast(historical_df, forecast_df, country_name):
    """
    Historical data plus Prophet forecast and confidence interval.
    Legend sits BELOW the plot so it cannot collide with the title.
    """
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=historical_df["ds"].dt.year,
        y=historical_df["y"],
        mode="lines+markers",
        name="Historical",
        line=dict(color=INK, width=3),
        marker=dict(size=7),
        fill="tozeroy",
        fillcolor="rgba(14, 124, 134, 0.18)",
    ))

    future_mask = forecast_df["ds"].dt.year > historical_df["ds"].dt.year.max()
    fc_future = forecast_df[future_mask]

    if not fc_future.empty:
        fig.add_trace(go.Scatter(
            x=pd.concat([fc_future["ds"].dt.year,
                         fc_future["ds"].dt.year[::-1]]),
            y=pd.concat([fc_future["yhat_upper"],
                         fc_future["yhat_lower"][::-1]]),
            fill="toself",
            fillcolor="rgba(25, 163, 184, 0.26)",
            line=dict(color="rgba(0,0,0,0)"),
            name="80% confidence",
            hoverinfo="skip",
        ))
        fig.add_trace(go.Scatter(
            x=fc_future["ds"].dt.year,
            y=fc_future["yhat"],
            mode="lines+markers",
            name="Forecast",
            line=dict(color=CYAN, width=3, dash="dash"),
            marker=dict(size=8, symbol="diamond"),
        ))

    fig.update_layout(
        title=f"5-Year Forecast — {country_name}",
        xaxis_title="Year",
        yaxis_title="Renewable Energy (%)",
        hovermode="x unified",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False, linecolor=GRID),
        yaxis=dict(gridcolor=GRID, range=[0, 105]),
        legend=dict(orientation="h", yanchor="top", y=-0.16,
                    xanchor="left", x=0),
        margin=dict(l=10, r=10, t=48, b=70),
    )
    return _exhibit(fig)


def plot_shap_waterfall(shap_result, country_name, base_value):
    """
    SHAP contributions for one country.
    Teal = pushes adoption up. Terracotta = pushes adoption down.
    X-range padded both sides so outside labels never touch the feature names.
    """
    if shap_result is None or shap_result.empty:
        return go.Figure()

    top = shap_result.head(8).sort_values("shap_value")
    colors = [TEAL if v >= 0 else NEG for v in top["shap_value"]]

    vals = top["shap_value"].astype(float)
    vmax, vmin = float(vals.max()), float(vals.min())
    span = max(abs(vmax), abs(vmin), 1e-9)
    x_lo = vmin - span * 0.35 if vmin < 0 else -span * 0.04
    x_hi = vmax + span * 0.35 if vmax > 0 else span * 0.04

    fig = go.Figure(go.Bar(
        x=top["shap_value"],
        y=top["feature"],
        orientation="h",
        marker=dict(color=colors, line=dict(color=INK, width=0.8)),
        text=[f"{v:+.2f}" for v in top["shap_value"]],
        textposition="outside",
        textfont=dict(family=FONT_MONO, size=11, color=INK),
        cliponaxis=False,
    ))

    fig.update_layout(
        title=f"What drives adoption in {country_name}?<br>"
              f"<sup>Base prediction: {base_value:.1f}%</sup>",
        xaxis_title="SHAP value (impact on prediction)",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=True, gridcolor=GRID,
                   zeroline=True, zerolinecolor=ZERO, zerolinewidth=2,
                   range=[x_lo, x_hi]),
        yaxis=dict(showgrid=False),
        margin=dict(l=10, r=30, t=74, b=10),
        height=370,
    )
    return _exhibit(fig)


def plot_global_feature_importance(importance_df):
    """
    Global mean |SHAP| per feature.
    Bars are shaded by RANK, not by value — with one dominant feature a
    value-scaled gradient renders every other bar almost white.
    """
    top = importance_df.head(10).sort_values("mean_abs_shap")
    n = len(top)
    x_hi = float(top["mean_abs_shap"].max()) * 1.22

    shades = [RANK_SHADES[int(round(i * (len(RANK_SHADES) - 1) / max(n - 1, 1)))]
              for i in range(n)]

    fig = go.Figure(go.Bar(
        x=top["mean_abs_shap"],
        y=top["feature"],
        orientation="h",
        marker=dict(color=shades, line=dict(color=INK, width=0.8)),
        text=[f"{v:.2f}" for v in top["mean_abs_shap"]],
        textposition="outside",
        textfont=dict(family=FONT_MONO, size=11, color=INK),
        cliponaxis=False,
    ))
    fig.update_layout(
        title="Global Feature Importance (mean |SHAP|)",
        xaxis_title="Mean |SHAP value|",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=True, gridcolor=GRID, range=[0, x_hi]),
        yaxis=dict(showgrid=False, title=""),
        margin=dict(l=10, r=20, t=44, b=10),
    )
    return _exhibit(fig)


def plot_choropleth(df, year=None):
    """World map of renewable energy % by country. Uses ISO-3 codes."""
    name_col = "country_name_x" if "country_name_x" in df.columns else "country_name"

    if year is not None:
        plot_df = df[df["year"] == year][
            ["country_code", TARGET_COL, name_col]
        ].dropna().copy()
    else:
        plot_df = (
            df.sort_values("year")
            .groupby("country_code").last().reset_index()
            [["country_code", TARGET_COL, name_col]].dropna().copy()
        )

    plot_df = plot_df.rename(columns={name_col: "country_name"})
    plot_df["iso3"] = plot_df["country_code"].map(ISO2_TO_ISO3)
    plot_df = plot_df.dropna(subset=["iso3"])

    fig = px.choropleth(
        plot_df,
        locations="iso3",
        locationmode="ISO-3",
        color=TARGET_COL,
        hover_name="country_name",
        hover_data={TARGET_COL: ":.1f", "iso3": False},
        color_continuous_scale=SEQUENTIAL_TEAL,
        range_color=[0, 100],
        title="Renewable Energy by Country"
              + (f" — {year}" if year else " (most recent)"),
        labels={TARGET_COL: "Renewable %"},
    )
    fig.update_traces(marker_line_color=INK, marker_line_width=0.6)
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        geo=dict(
            showframe=False,
            showcoastlines=True, coastlinecolor="#A9C4CB",
            showland=True, landcolor="#E7EEF0",
            showocean=True, oceancolor="#F5F9FA",
        ),
        margin=dict(l=0, r=0, t=44, b=0),
        height=460,
        coloraxis_colorbar=dict(
            title=dict(text="Renewable %",
                       font=dict(family=FONT_BODY, size=12, color=SLATE)),
            thickness=14,
            outlinecolor=GRID, outlinewidth=1,
            tickfont=dict(family=FONT_MONO, size=11, color=INK),
        ),
    )
    return _exhibit(fig)


def plot_cluster_scatter(cluster_df):
    """2D PCA scatter of country clusters, sized by renewable %."""
    if "cluster" not in cluster_df.columns:
        return go.Figure()

    cluster_df = cluster_df.copy()
    cluster_df["cluster_label"] = "Cluster " + cluster_df["cluster"].astype(str)
    cluster_df = cluster_df.sort_values("cluster")

    if TARGET_COL in cluster_df.columns:
        cluster_df["size"] = cluster_df[TARGET_COL].clip(1, 100) ** 0.5 * 3 + 7
        size_col = "size"
        hover_data = {TARGET_COL: ":.1f", "size": False}
    else:
        size_col = None
        hover_data = {}

    fig = px.scatter(
        cluster_df,
        x="pc1", y="pc2",
        color="cluster_label",
        size=size_col,
        hover_name="country_code",
        hover_data=hover_data,
        title="Country Clusters by Adoption Profile",
        labels={"pc1": "Principal Component 1", "pc2": "Principal Component 2"},
        color_discrete_sequence=CLUSTER_SEQUENCE,
    )
    fig.update_traces(marker=dict(opacity=0.92, line=dict(color=INK, width=1)))
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=True, gridcolor=GRID, zeroline=False, linecolor=GRID),
        yaxis=dict(showgrid=True, gridcolor=GRID, zeroline=False, linecolor=GRID),
        # Legend below the plot — avoids being clipped at the container edge
        legend=dict(orientation="h", yanchor="top", y=-0.14,
                    xanchor="left", x=0, title=dict(text="")),
        margin=dict(l=10, r=10, t=44, b=70),
        height=470,
    )
    return _exhibit(fig)


def plot_policy_simulation(baseline, modified, country_name,
                           scenario_label="Modified scenario"):
    """
    Baseline vs scenario bars.
    Delta annotation is paper-anchored top-right so it cannot collide
    with the bar value labels.
    """
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=["Baseline", scenario_label],
        y=[baseline, modified],
        marker=dict(color=["#9FB7BE", TEAL], line=dict(color=INK, width=1)),
        text=[f"{baseline:.1f}%", f"{modified:.1f}%"],
        textposition="outside",
        textfont=dict(family=FONT_MONO, size=13, color=INK),
        cliponaxis=False,
        width=0.42,
    ))

    change = modified - baseline
    arrow_color = TEAL if change >= 0 else NEG

    fig.add_annotation(
        xref="paper", yref="paper",
        x=0.99, y=0.97, xanchor="right", yanchor="top",
        text=f"{'↑' if change >= 0 else '↓'} {abs(change):.1f} pp",
        font=dict(family=FONT_MONO, size=15, color=arrow_color),
        showarrow=False,
    )

    fig.update_layout(
        title=f"Structural Benchmark — {country_name}",
        yaxis=dict(title="Renewable Energy (%)",
                   range=[0, max(baseline, modified) * 1.3 + 10],
                   gridcolor=GRID),
        xaxis=dict(linecolor=GRID),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        margin=dict(l=10, r=10, t=52, b=10),
        height=320,
    )
    return _exhibit(fig)


def plot_region_comparison(df, year=None):
    """
    Horizontal box plot of renewable % by region, sorted by median.
    Fills rendered solid rather than washed, with ink outlines.
    """
    if year is None:
        plot_df = (df.sort_values("year")
                     .groupby("country_code").last().reset_index())
    else:
        plot_df = df[df["year"] == year].copy()

    if "region" not in plot_df.columns:
        return go.Figure()

    plot_df = plot_df.dropna(subset=[TARGET_COL, "region"])

    region_order = (
        plot_df.groupby("region")[TARGET_COL].median()
        .sort_values(ascending=False).index.tolist()
    )

    fig = px.box(
        plot_df,
        x=TARGET_COL, y="region",
        color="region",
        points="all",
        hover_name="country_code",
        title="Renewable Energy Distribution by Region",
        labels={"region": "", TARGET_COL: "Renewable Energy (%)"},
        color_discrete_map=REGION_COLORS,
        category_orders={"region": region_order},
    )
    fig.update_traces(
        marker=dict(opacity=0.95, size=7, line=dict(color=INK, width=0.8)),
        line=dict(width=1.6),
        fillcolor=None,
        opacity=0.95,
    )
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(gridcolor=GRID, range=[-2, 105], linecolor=GRID),
        yaxis=dict(showgrid=False),
        showlegend=False,
        margin=dict(l=10, r=10, t=44, b=10),
        height=420,
    )
    return _exhibit(fig)