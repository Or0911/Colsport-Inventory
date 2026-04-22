"""
charts.py
=========
Funciones que devuelven figuras Plotly para la app Streamlit.
"""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# ---------------------------------------------------------------------------
# Paleta
# ---------------------------------------------------------------------------
PRIMARY   = "#3498db"
DARK      = "#2c3e50"
GREEN     = "#27ae60"
ORANGE    = "#e67e22"
RED       = "#e74c3c"
LIGHT_BG  = "rgba(0,0,0,0)"

CANAL_COLORS = {
    "WhatsApp":    "#25D366",
    "Rappi":       "#FF441F",
    "Rappi Pro":   "#FF6B35",
    "Local":       "#3498db",
    "TikTok Live": "#010101",
    "Instagram":   "#C13584",
}

_LAYOUT_BASE = dict(
    paper_bgcolor=LIGHT_BG,
    plot_bgcolor=LIGHT_BG,
    font=dict(family="Inter, Arial, sans-serif", color=DARK, size=12),
    margin=dict(l=16, r=16, t=32, b=16),
)


def _empty_fig(msg="Sin datos para el período seleccionado") -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(
        text=msg, x=0.5, y=0.5, xref="paper", yref="paper",
        showarrow=False, font=dict(size=14, color="#95a5a6"),
    )
    fig.update_layout(**_LAYOUT_BASE, xaxis_visible=False, yaxis_visible=False)
    return fig


# ---------------------------------------------------------------------------
# Pie — ventas por canal
# ---------------------------------------------------------------------------

def chart_ventas_canal(df: pd.DataFrame) -> go.Figure:
    if df.empty or df["Ventas"].sum() == 0:
        return _empty_fig()

    colors = [CANAL_COLORS.get(c, PRIMARY) for c in df["Canal"]]
    fig = px.pie(
        df, values="Ventas", names="Canal",
        color_discrete_sequence=colors,
        hole=0.42,
    )
    fig.update_traces(
        textposition="inside",
        textinfo="percent+label",
        hovertemplate="<b>%{label}</b><br>Ventas: %{value}<br>%{percent}<extra></extra>",
    )
    fig.update_layout(**_LAYOUT_BASE, showlegend=True,
                      legend=dict(orientation="h", y=-0.15))
    return fig


# ---------------------------------------------------------------------------
# Line — tendencia diaria
# ---------------------------------------------------------------------------

def chart_tendencia(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return _empty_fig()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["Fecha"], y=df["Total"],
        mode="lines+markers",
        name="Ingreso neto",
        line=dict(color=PRIMARY, width=2.5),
        marker=dict(size=7, color=PRIMARY),
        fill="tozeroy",
        fillcolor="rgba(52,152,219,0.10)",
        hovertemplate="<b>%{x}</b><br>$%{y:,.0f} COP<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        x=df["Fecha"], y=df["Ventas"],
        name="# Ventas",
        yaxis="y2",
        marker_color="rgba(52,152,219,0.25)",
        hovertemplate="%{y} ventas<extra></extra>",
    ))
    fig.update_layout(
        **_LAYOUT_BASE,
        yaxis=dict(title="COP", gridcolor="#ecf0f1", zeroline=False),
        yaxis2=dict(title="Ventas", overlaying="y", side="right", showgrid=False),
        xaxis=dict(showgrid=False),
        hovermode="x unified",
        legend=dict(orientation="h", y=1.08),
    )
    return fig


# ---------------------------------------------------------------------------
# Bar — top productos
# ---------------------------------------------------------------------------

def chart_top_productos(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return _empty_fig()

    df_plot = df.sort_values("Unidades", ascending=True).tail(10).copy()
    # Acortar nombres largos
    df_plot["Producto"] = df_plot["Producto"].str[:45]

    fig = px.bar(
        df_plot, x="Unidades", y="Producto",
        orientation="h",
        text="Unidades",
        color="Unidades",
        color_continuous_scale=[[0, "#a8d8f0"], [1, PRIMARY]],
        hover_data={"Ingresos": ":,.0f"},
    )
    fig.update_traces(textposition="outside", textfont_size=11)
    fig.update_layout(
        **_LAYOUT_BASE,
        xaxis_title="Unidades vendidas",
        yaxis_title="",
        coloraxis_showscale=False,
        yaxis=dict(tickfont=dict(size=11)),
    )
    return fig


# ---------------------------------------------------------------------------
# Bar — top facturadores (métodos de pago)
# ---------------------------------------------------------------------------

def chart_top_facturadores(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return _empty_fig()

    df_plot = df.sort_values("Total", ascending=True).copy()
    fig = px.bar(
        df_plot, x="Total", y="Método de pago",
        orientation="h",
        text=df_plot["Total"].apply(lambda v: f"${v:,.0f}".replace(",", ".")),
        color="Total",
        color_continuous_scale=[[0, "#d5eaf7"], [1, DARK]],
    )
    fig.update_traces(textposition="outside", textfont_size=11)
    fig.update_layout(
        **_LAYOUT_BASE,
        xaxis_title="Total facturado (COP)",
        yaxis_title="",
        coloraxis_showscale=False,
    )
    return fig


# ---------------------------------------------------------------------------
# Helpers HTML para KPI cards
# ---------------------------------------------------------------------------

def kpi_card(label: str, value: str, sub: str = "", color: str = PRIMARY) -> str:
    return f"""
    <div style="
        background:white;
        border-radius:12px;
        padding:18px 20px;
        box-shadow:0 2px 8px rgba(0,0,0,0.07);
        border-left:4px solid {color};
        height:100%;
    ">
        <div style="font-size:11px;color:#7f8c8d;text-transform:uppercase;letter-spacing:0.6px;margin-bottom:6px">{label}</div>
        <div style="font-size:26px;font-weight:700;color:{DARK};line-height:1.1">{value}</div>
        {f'<div style="font-size:12px;color:#95a5a6;margin-top:4px">{sub}</div>' if sub else ""}
    </div>
    """
