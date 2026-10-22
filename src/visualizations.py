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
NEG    = "#C2703D"   # negative contributions / declines only
SLATE  = "#5C7682"   # muted labels, neutral series
GRID   = "#DBE7EA"   # chart gridlines
ZERO   = "#9FB6BE"   # zero lines

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
    "East Asia":      "#19A3B8",
    "Southeast Asia": "#0E7C86",
    "South Asia":     "#4C6EA8",
    "Europe":         "#06303C",
    "North America":  "#5C7682",
    "Latin America":  "#D98A2B",
    "Africa":         "#3F8F5F",
    "Middle East":    "#C2703D",
    "Oceania":        "#7FB2A5",
}

# Categorical sequence for cluster scatter — ordered for maximum separation
CLUSTER_SEQUENCE = [
    "#19A3B8", "#06303C", "#D98A2B", "#C2703D",
    "#0E7C86", "#4C6EA8", "#3F8F5F", "#5C7682",
]

# Sequential scale for continuous values (choropleth, importance)
SEQUENTIAL_TEAL = [
    [0.0,  "#EEF5F6"],
    [0.30, "#C2DFE3"],
    [0.55, "#7FC0C9"],
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
    """Apply consistent exhibit typography to any figure. Call before returning."""
    fig.update_layout(
        font=dict(family=FONT_BODY, size=13, color=INK),
        title=dict(
            font=dict(family=FONT_DISPLAY, size=19, color=INK),
            x=0.01, xanchor="left",
        ),
        hoverlabel=dict(
            bgcolor="#FFFFFF",
            bordercolor="#C9DCE0",
            font=dict(family=FONT_BODY, size=12, color=INK),
        ),
    )
    # Let axes grow their own margins so tick labels are never clipped
    fig.update_xaxes(automargin=True)
    fig.update_yaxes(automargin=True)
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
        line_width=2.5, marker_size=6,
        fill="tozeroy", fillcolor="rgba(6, 48, 60, 0.06)",
    )
    fig.update_layout(
        hovermode="x unified",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False),
        yaxis=dict(gridcolor=GRID, range=[0, 105]),
        margin=dict(l=10, r=10, t=44, b=10),
    )
    return _exhibit(fig)


def plot_forecast(historical_df, forecast_df, country_name):
    """
    Historical data plus Prophet forecast and confidence interval.
    Legend anchors top-RIGHT so it never collides with the left-aligned title.
    """
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=historical_df["ds"].dt.year,
        y=historical_df["y"],
        mode="lines+markers",
        name="Historical",
        line=dict(color=INK, width=2.5),
        marker=dict(size=6),
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
            fillcolor="rgba(25, 163, 184, 0.13)",
            line=dict(color="rgba(0,0,0,0)"),
            name="80% confidence",
            hoverinfo="skip",
        ))
        fig.add_trace(go.Scatter(
            x=fc_future["ds"].dt.year,
            y=fc_future["yhat"],
            mode="lines+markers",
            name="Forecast",
            line=dict(color=CYAN, width=2.5, dash="dash"),
            marker=dict(size=7, symbol="diamond"),
        ))

    fig.update_layout(
        title=f"5-Year Forecast — {country_name}",
        xaxis_title="Year",
        yaxis_title="Renewable Energy (%)",
        hovermode="x unified",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False),
        yaxis=dict(gridcolor=GRID, range=[0, 105]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02,
                    xanchor="right", x=1),
        margin=dict(l=10, r=10, t=52, b=10),
    )
    return _exhibit(fig)


def plot_shap_waterfall(shap_result, country_name, base_value):
    """
    SHAP contributions for one country.
    Cyan = pushes adoption up. Terracotta = pushes adoption down.
    X-range padded both sides so outside labels never touch the feature names.
    """
    if shap_result is None or shap_result.empty:
        return go.Figure()

    top = shap_result.head(8).sort_values("shap_value")
    colors = [CYAN if v >= 0 else NEG for v in top["shap_value"]]

    vals = top["shap_value"].astype(float)
    vmax, vmin = float(vals.max()), float(vals.min())
    span = max(abs(vmax), abs(vmin), 1e-9)
    x_lo = vmin - span * 0.35 if vmin < 0 else -span * 0.04
    x_hi = vmax + span * 0.35 if vmax > 0 else span * 0.04

    fig = go.Figure(go.Bar(
        x=top["shap_value"],
        y=top["feature"],
        orientation="h",
        marker_color=colors,
        text=[f"{v:+.2f}" for v in top["shap_value"]],
        textposition="outside",
        textfont=dict(family=FONT_MONO, size=11),
        cliponaxis=False,
    ))

    fig.update_layout(
        title=f"What drives adoption in {country_name}?<br>"
              f"<sup>Base prediction: {base_value:.1f}%</sup>",
        xaxis_title="SHAP value (impact on prediction)",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=True, gridcolor=GRID,
                   zeroline=True, zerolinecolor=ZERO, zerolinewidth=1.5,
                   range=[x_lo, x_hi]),
        yaxis=dict(showgrid=False),
        margin=dict(l=10, r=30, t=74, b=10),
        height=370,
    )
    return _exhibit(fig)


def plot_global_feature_importance(importance_df):
    """Global mean |SHAP| per feature, with data labels."""
    top = importance_df.head(10).sort_values("mean_abs_shap")
    x_hi = float(top["mean_abs_shap"].max()) * 1.22

    fig = px.bar(
        top,
        x="mean_abs_shap", y="feature",
        orientation="h",
        title="Global Feature Importance (mean |SHAP|)",
        labels={"mean_abs_shap": "Mean |SHAP value|", "feature": ""},
        color="mean_abs_shap",
        color_continuous_scale=[[0, "#CFE6EA"], [1, INK]],
        text_auto=".2f",
    )
    fig.update_traces(
        textposition="outside",
        textfont=dict(family=FONT_MONO, size=11),
        cliponaxis=False,
    )
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        coloraxis_showscale=False,
        xaxis=dict(showgrid=True, gridcolor=GRID, range=[0, x_hi]),
        yaxis=dict(showgrid=False),
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
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        geo=dict(
            showframe=False,
            showcoastlines=True, coastlinecolor="#C9DCE0",
            showland=True, landcolor="#F0F5F6",
            showocean=True, oceancolor="#F8FBFC",
        ),
        margin=dict(l=0, r=0, t=44, b=0),
        height=440,
        coloraxis_colorbar=dict(
            title="Renewable %", thickness=12,
            tickfont=dict(family=FONT_MONO, size=11),
        ),
    )
    return _exhibit(fig)


def plot_cluster_scatter(cluster_df):
    """2D PCA scatter of country clusters, sized by renewable %."""
    if "cluster" not in cluster_df.columns:
        return go.Figure()

    cluster_df = cluster_df.copy()
    cluster_df["cluster_label"] = "Cluster " + cluster_df["cluster"].astype(str)

    if TARGET_COL in cluster_df.columns:
        cluster_df["size"] = cluster_df[TARGET_COL].clip(1, 100) ** 0.5 * 3 + 6
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
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=True, gridcolor=GRID, zeroline=False),
        yaxis=dict(showgrid=True, gridcolor=GRID, zeroline=False),
        legend_title="Cluster",
        margin=dict(l=10, r=10, t=44, b=10),
        height=420,
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
        marker_color=["#C3D6DA", CYAN],
        text=[f"{baseline:.1f}%", f"{modified:.1f}%"],
        textposition="outside",
        textfont=dict(family=FONT_MONO, size=13),
        cliponaxis=False,
        width=0.4,
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
    Horizontal orientation gives every region name full room.
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
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(gridcolor=GRID, range=[-2, 105]),
        yaxis=dict(showgrid=False),
        showlegend=False,
        margin=dict(l=10, r=10, t=44, b=10),
        height=400,
    )
    return _exhibit(fig)
