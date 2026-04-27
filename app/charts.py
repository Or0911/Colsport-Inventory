"""
charts.py
=========
High-performance dark-theme analytics charts for Colsports dashboard.
All charts use plotly.graph_objects for full design control.
"""

import plotly.graph_objects as go
import pandas as pd

# ---------------------------------------------------------------------------
# Design tokens — deep dark with blue accent
# ---------------------------------------------------------------------------
D_BG        = "#0d1b2e"
D_SURFACE   = "#111f33"
D_SURFACE2  = "#162a47"
D_BLUE      = "#3498db"
D_BLUE_DIM  = "rgba(52,152,219,0.18)"
D_GREEN     = "#2ecc71"
D_GREEN_DIM = "rgba(46,204,113,0.15)"
D_ORANGE    = "#e67e22"
D_ORANGE_DIM = "rgba(230,126,34,0.15)"
D_RED       = "#e74c3c"
D_PURPLE    = "#a855f7"
D_TEXT      = "#dce8f5"
D_MUTED     = "#6b86a8"
D_GRID      = "rgba(255,255,255,0.06)"

CANAL_PALETTE = {
    "WhatsApp":    "#25D366",
    "Rappi":       "#FF441F",
    "Rappi Pro":   "#FF6B35",
    "Local":       "#3498db",
    "TikTok Live": "#a855f7",
    "Instagram":   "#C13584",
}

_CAT_COLORS = [
    "#3498db", "#2ecc71", "#e67e22", "#a855f7",
    "#1abc9c", "#e74c3c", "#f1c40f", "#e91e63",
]

_FONT = dict(family="Inter, 'Helvetica Neue', Arial, sans-serif", color=D_TEXT, size=12)

_BASE = dict(
    paper_bgcolor=D_SURFACE,
    plot_bgcolor=D_SURFACE,
    font=_FONT,
    margin=dict(l=16, r=16, t=36, b=16),
    hoverlabel=dict(
        bgcolor=D_SURFACE2, bordercolor=D_BLUE,
        font_size=13, font_color=D_TEXT,
        font_family="Inter, Arial",
    ),
)
_XAXIS = dict(showgrid=False, zeroline=False, linecolor=D_GRID, tickcolor=D_GRID, color=D_MUTED)
_YAXIS = dict(gridcolor=D_GRID, zeroline=False, tickcolor="rgba(0,0,0,0)",
              linecolor="rgba(0,0,0,0)", color=D_MUTED)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _empty(msg: str = "Sin datos para el período") -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(text=msg, x=0.5, y=0.5, xref="paper", yref="paper",
                       showarrow=False, font=dict(size=13, color=D_MUTED))
    fig.update_layout(**_BASE, xaxis_visible=False, yaxis_visible=False)
    return fig


def _cop(v) -> str:
    try:
        return f"${int(v):,}".replace(",", ".")
    except Exception:
        return str(v)


def _hex_to_rgb(hex_color: str) -> str:
    h = hex_color.lstrip("#")
    return f"{int(h[0:2], 16)},{int(h[2:4], 16)},{int(h[4:6], 16)}"


# ---------------------------------------------------------------------------
# KPI card — dark premium style
# ---------------------------------------------------------------------------

def kpi_card(label: str, value: str, sub: str = "", color: str = "#555") -> str:
    sub_html = (
        f"<div style='font-size:13px;color:{color};margin-top:4px;"
        f"font-family:Caveat,cursive'>{sub}</div>"
        if sub else ""
    )
    return f"""
    <div style="
        background: #fffef9;
        border: 1.5px solid #d4d0c8;
        border-radius: 2px;
        box-shadow: 3px 4px 0 #e8e4dc;
        border-left: 4px solid {color};
        padding: 16px 18px;
        height: 100%;
        box-sizing: border-box;
        font-family: 'Caveat', cursive;
    ">
        <div style="font-size:13px;color:#999;margin-bottom:6px">{label}</div>
        <div style="font-size:23px;font-weight:700;color:#1a1a1a;line-height:1.2">{value}</div>
        {sub_html}
    </div>"""


# ---------------------------------------------------------------------------
# Donut — Ventas por canal
# ---------------------------------------------------------------------------

def chart_ventas_canal(df: pd.DataFrame) -> go.Figure:
    if df.empty or df["Ventas"].sum() == 0:
        return _empty()

    colors = [CANAL_PALETTE.get(c, D_BLUE) for c in df["Canal"]]

    fig = go.Figure(go.Pie(
        labels=df["Canal"], values=df["Ventas"],
        hole=0.62,
        marker=dict(colors=colors, line=dict(color=D_SURFACE, width=3)),
        textinfo="percent",
        textfont=dict(size=11, color=D_TEXT),
        hovertemplate="<b>%{label}</b><br>%{value} ventas · %{percent}<extra></extra>",
        sort=True, direction="clockwise",
    ))

    total = int(df["Ventas"].sum())
    fig.add_annotation(
        text=f"<b>{total}</b><br><span style='font-size:10px'>ventas</span>",
        x=0.5, y=0.5, xref="paper", yref="paper",
        showarrow=False, font=dict(size=20, color=D_TEXT), align="center",
    )
    fig.update_layout(
        **_BASE,
        showlegend=True,
        legend=dict(orientation="h", y=-0.18, x=0.5, xanchor="center", font=dict(size=11)),
    )
    return fig


# ---------------------------------------------------------------------------
# Área + barras — Tendencia diaria de ventas
# ---------------------------------------------------------------------------

def chart_tendencia(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return _empty()

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df["Fecha"], y=df["Ventas"], name="# Ventas", yaxis="y2",
        marker=dict(color=D_BLUE_DIM, line=dict(width=0)),
        hovertemplate="%{y} ventas<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=df["Fecha"], y=df["Total"], mode="lines+markers", name="Ingreso neto",
        line=dict(color=D_BLUE, width=2.5, shape="spline", smoothing=0.8),
        marker=dict(size=5, color=D_SURFACE, line=dict(color=D_BLUE, width=2)),
        fill="tozeroy", fillcolor=D_BLUE_DIM,
        hovertemplate="<b>%{x}</b><br>%{y:,.0f} COP<extra></extra>",
    ))
    fig.update_layout(
        **_BASE,
        yaxis=dict(**_YAXIS, title="COP"),
        yaxis2=dict(overlaying="y", side="right", showgrid=False, zeroline=False,
                    title="# Ventas", tickcolor=D_GRID, color=D_MUTED),
        xaxis=dict(**_XAXIS),
        hovermode="x unified", bargap=0.3,
        legend=dict(orientation="h", y=1.12, x=0, font=dict(size=11)),
    )
    return fig


# ---------------------------------------------------------------------------
# Barras horizontales — Top productos
# ---------------------------------------------------------------------------

def chart_top_productos(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return _empty()

    df_plot = df.sort_values("Unidades", ascending=True).tail(10).copy()
    df_plot["Etiqueta"] = df_plot["Producto"].str[:36]
    n = len(df_plot)
    colors = [f"rgba(52,152,219,{0.40 + 0.60 * (i / max(n - 1, 1))})" for i in range(n)]

    fig = go.Figure(go.Bar(
        x=df_plot["Unidades"], y=df_plot["Etiqueta"],
        orientation="h",
        marker=dict(color=colors, line=dict(width=0)),
        text=df_plot["Unidades"].astype(int),
        textposition="outside",
        textfont=dict(size=11, color=D_TEXT),
        hovertemplate="<b>%{y}</b><br>%{x} unidades<extra></extra>",
    ))
    fig.update_layout(
        **_BASE,
        xaxis=dict(**_XAXIS, title="Unidades vendidas"),
        yaxis=dict(**_YAXIS, tickfont=dict(size=10)),
        bargap=0.32,
    )
    return fig


# ---------------------------------------------------------------------------
# Sankey — Flujo de capital: Canales → Ingresos → Destinos
# ---------------------------------------------------------------------------

def chart_sankey(
    df_canal: pd.DataFrame,
    ventas_neto: int,
    costo: int,
    comisiones: int,
) -> go.Figure:
    df_c = df_canal[df_canal["Total"] > 0].copy() if not df_canal.empty else pd.DataFrame()

    if df_c.empty and ventas_neto == 0:
        return _empty("Sin datos suficientes para el flujo de capital")

    canal_names = df_c["Canal"].tolist() if not df_c.empty else []
    n = len(canal_names)

    IDX_ING  = n
    IDX_COST = n + 1
    IDX_COM  = n + 2
    IDX_UTIL = n + 3

    node_labels = canal_names + ["Ingresos\nNetos", "Costo\nMercancía", "Comisiones", "Utilidad\nNeta"]
    canal_colors = [CANAL_PALETTE.get(c, D_BLUE) for c in canal_names]
    node_colors  = canal_colors + [D_BLUE, D_ORANGE, D_RED, D_GREEN]

    sources, targets, vals, link_colors = [], [], [], []

    # Canal → Ingresos
    total_canal = int(df_c["Total"].sum()) if not df_c.empty else ventas_neto
    for i, row in enumerate(df_c.itertuples()):
        v = max(1, int(row.Total))
        c = CANAL_PALETTE.get(row.Canal, D_BLUE)
        sources.append(i); targets.append(IDX_ING)
        vals.append(v)
        link_colors.append(f"rgba({_hex_to_rgb(c)},0.22)")

    # If no canal breakdown, use a single source node
    if not canal_names:
        node_labels = ["Ventas"] + node_labels[n:]
        node_colors = [D_BLUE] + node_colors[n:]
        sources.append(0); targets.append(1)
        vals.append(max(1, ventas_neto))
        link_colors.append(f"rgba({_hex_to_rgb(D_BLUE)},0.22)")
        IDX_ING, IDX_COST, IDX_COM, IDX_UTIL = 1, 2, 3, 4

    base = max(total_canal, ventas_neto, 1)
    util = max(0, base - costo - comisiones)

    if costo > 0:
        sources.append(IDX_ING); targets.append(IDX_COST)
        vals.append(min(costo, base))
        link_colors.append(f"rgba({_hex_to_rgb(D_ORANGE)},0.22)")

    if comisiones > 0:
        sources.append(IDX_ING); targets.append(IDX_COM)
        vals.append(min(comisiones, base))
        link_colors.append(f"rgba({_hex_to_rgb(D_RED)},0.22)")

    if util > 0:
        sources.append(IDX_ING); targets.append(IDX_UTIL)
        vals.append(util)
        link_colors.append(f"rgba({_hex_to_rgb(D_GREEN)},0.22)")
    elif costo == 0 and comisiones == 0:
        sources.append(IDX_ING); targets.append(IDX_UTIL)
        vals.append(max(1, base))
        link_colors.append(f"rgba({_hex_to_rgb(D_GREEN)},0.22)")

    fig = go.Figure(go.Sankey(
        arrangement="snap",
        node=dict(
            pad=20, thickness=22,
            line=dict(color=D_BG, width=0),
            label=node_labels,
            color=node_colors,
            hovertemplate="<b>%{label}</b><br>%{value:,.0f} COP<extra></extra>",
        ),
        link=dict(
            source=sources, target=targets, value=vals,
            color=link_colors,
            hovertemplate="%{value:,.0f} COP<extra></extra>",
        ),
    ))
    fig.update_layout(**{**_BASE, "margin": dict(l=12, r=12, t=24, b=12)})
    return fig


# ---------------------------------------------------------------------------
# Waterfall — Cierre mensual
# ---------------------------------------------------------------------------

def chart_waterfall(ventas_neto: int, costo: int, comisiones: int) -> go.Figure:
    if ventas_neto == 0 and costo == 0:
        return _empty("Sin datos del mes")

    utilidad = ventas_neto - costo - comisiones
    util_color = D_GREEN if utilidad >= 0 else D_RED

    fig = go.Figure(go.Waterfall(
        orientation="v",
        measure=["absolute", "relative", "relative", "total"],
        x=["Ventas\nNetas", "− Costo\nMercancía", "− Comisiones", "Utilidad"],
        y=[ventas_neto, -costo, -comisiones, 0],
        text=[_cop(ventas_neto), f"−{_cop(costo)}", f"−{_cop(comisiones)}", _cop(utilidad)],
        textposition="outside",
        textfont=dict(color=D_TEXT, size=10),
        connector=dict(line=dict(color=D_GRID, width=1.5, dash="dot")),
        increasing=dict(marker=dict(color=D_GREEN, line=dict(width=0))),
        decreasing=dict(marker=dict(color=D_RED, line=dict(width=0))),
        totals=dict(marker=dict(color=util_color, line=dict(width=0))),
        hovertemplate="<b>%{x}</b><br>%{y:,.0f} COP<extra></extra>",
    ))
    fig.update_layout(**{
        **_BASE,
        "yaxis": dict(**_YAXIS, title="COP"),
        "xaxis": dict(**_XAXIS, showline=False),
        "showlegend": False,
        "margin": dict(l=16, r=16, t=40, b=48),
    })
    return fig


# ---------------------------------------------------------------------------
# Heatmap — Actividad de ventas por hora × día de semana
# ---------------------------------------------------------------------------

def chart_heatmap(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return _empty("Sin datos de actividad en el período")

    DIAS = {0: "Dom", 1: "Lun", 2: "Mar", 3: "Mié", 4: "Jue", 5: "Vie", 6: "Sáb"}
    HORAS = list(range(7, 23))

    df = df.copy()
    df["DiaSemana"] = df["DiaSemana"].astype(int)
    df["Hora"] = df["Hora"].astype(int)

    pivot = df.pivot_table(index="DiaSemana", columns="Hora", values="Ventas",
                           aggfunc="sum", fill_value=0)
    pivot = pivot.reindex(index=range(7), columns=HORAS, fill_value=0)

    z = pivot.values.tolist()
    y_labels = [DIAS.get(i, str(i)) for i in pivot.index]
    x_labels = [f"{h}:00" for h in pivot.columns]

    colorscale = [
        [0.00, D_SURFACE],
        [0.01, "rgba(52,152,219,0.08)"],
        [0.30, "rgba(52,152,219,0.40)"],
        [0.70, "rgba(52,152,219,0.72)"],
        [1.00, D_BLUE],
    ]

    fig = go.Figure(go.Heatmap(
        z=z, x=x_labels, y=y_labels,
        colorscale=colorscale,
        showscale=True,
        colorbar=dict(
            title=dict(text="Ventas", side="right"),
            tickcolor=D_MUTED, outlinecolor="rgba(0,0,0,0)",
            tickfont=dict(color=D_MUTED), len=0.9,
        ),
        hovertemplate="<b>%{y} · %{x}</b><br>%{z} ventas<extra></extra>",
        xgap=4, ygap=4,
    ))
    fig.update_layout(
    **{
        **_BASE,
        "xaxis": dict(**_XAXIS, side="bottom"),
        "yaxis": dict(**_YAXIS, autorange="reversed"),
        "margin": dict(l=16, r=16, t=16, b=16),
    })
    return fig


# ---------------------------------------------------------------------------
# Sunburst — Distribución de inventario por categoría
# ---------------------------------------------------------------------------

def chart_sunburst(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return _empty("Sin datos de inventario activo")

    labels      = ["Inventario"]
    parents     = [""]
    values      = [int(df["Stock"].sum())]
    node_colors = [D_SURFACE2]

    for ci, (cat, grp) in enumerate(df.groupby("Categoría")):
        cat_color = _CAT_COLORS[ci % len(_CAT_COLORS)]
        labels.append(str(cat))
        parents.append("Inventario")
        values.append(int(grp["Stock"].sum()))
        node_colors.append(cat_color)

        for _, row in grp.iterrows():
            labels.append(str(row["Producto"])[:26])
            parents.append(str(cat))
            values.append(max(1, int(row["Stock"])))
            node_colors.append(f"rgba({_hex_to_rgb(cat_color)},0.55)")

    fig = go.Figure(go.Sunburst(
        labels=labels, parents=parents, values=values,
        branchvalues="total",
        marker=dict(colors=node_colors, line=dict(color=D_BG, width=1.5)),
        hovertemplate="<b>%{label}</b><br>%{value} uds · %{percentParent:.0%} de la cat.<extra></extra>",
        textfont=dict(size=10, color=D_TEXT),
        insidetextorientation="radial",
        maxdepth=2,
    ))
    fig.update_layout(**{**_BASE, "margin": dict(l=8, r=8, t=12, b=8)})
    return fig


# ---------------------------------------------------------------------------
# Legacy charts — kept for compras page compatibility
# ---------------------------------------------------------------------------

def chart_ventas_vs_compras(df_ventas: pd.DataFrame, df_compras: pd.DataFrame) -> go.Figure:
    if df_ventas.empty and df_compras.empty:
        return _empty()
    fig = go.Figure()
    if not df_compras.empty:
        fig.add_trace(go.Scatter(
            x=df_compras["Fecha"], y=df_compras["Total"], mode="lines", name="Compras",
            line=dict(color=D_ORANGE, width=2, shape="spline", smoothing=0.8),
            fill="tozeroy", fillcolor=D_ORANGE_DIM,
            hovertemplate="<b>%{x}</b><br>Compras: %{y:,.0f} COP<extra></extra>",
        ))
    if not df_ventas.empty:
        fig.add_trace(go.Scatter(
            x=df_ventas["Fecha"], y=df_ventas["Total"], mode="lines", name="Ventas",
            line=dict(color=D_BLUE, width=2.5, shape="spline", smoothing=0.8),
            fill="tozeroy", fillcolor=D_BLUE_DIM,
            hovertemplate="<b>%{x}</b><br>Ventas: %{y:,.0f} COP<extra></extra>",
        ))
    fig.update_layout(**_BASE, yaxis=dict(**_YAXIS, title="COP"), xaxis=dict(**_XAXIS),
                      hovermode="x unified",
                      legend=dict(orientation="h", y=1.12, x=0, font=dict(size=11)))
    return fig


def chart_compras_proveedor(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return _empty("Sin compras en el período")
    df_plot = df.sort_values("Total", ascending=True).copy()
    df_plot["Proveedor"] = df_plot["Proveedor"].fillna("Sin especificar").str[:30]
    n = len(df_plot)
    colors = [f"rgba(230,126,34,{0.40 + 0.60 * (i / max(n - 1, 1))})" for i in range(n)]
    fig = go.Figure(go.Bar(
        x=df_plot["Total"], y=df_plot["Proveedor"], orientation="h",
        marker=dict(color=colors, line=dict(width=0)),
        text=df_plot["Total"].apply(_cop), textposition="outside",
        textfont=dict(size=11, color=D_TEXT),
        hovertemplate="<b>%{y}</b><br>%{text}<extra></extra>",
    ))
    fig.update_layout(**_BASE, xaxis=dict(**_XAXIS, title="Total (COP)"),
                      yaxis=dict(**_YAXIS, tickfont=dict(size=10)), bargap=0.32)
    return fig


def chart_margen_barras(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return _empty("Sin datos")
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df["Fecha"], y=df["Ventas_total"], name="Ventas",
                         marker=dict(color=D_BLUE, line=dict(width=0)),
                         hovertemplate="Ventas: %{y:,.0f} COP<extra></extra>"))
    fig.add_trace(go.Bar(x=df["Fecha"], y=df["Compras_total"], name="Compras",
                         marker=dict(color=D_ORANGE, line=dict(width=0)),
                         hovertemplate="Compras: %{y:,.0f} COP<extra></extra>"))
    margen = df["Ventas_total"] - df["Compras_total"]
    fig.add_trace(go.Scatter(x=df["Fecha"], y=margen, name="Margen",
                             mode="lines+markers",
                             line=dict(color=D_GREEN, width=2.5, shape="spline", smoothing=0.7),
                             marker=dict(size=5, color=D_SURFACE, line=dict(color=D_GREEN, width=2)),
                             hovertemplate="Margen: %{y:,.0f} COP<extra></extra>"))
    fig.update_layout(**_BASE, barmode="group", bargap=0.25, bargroupgap=0.08,
                      yaxis=dict(**_YAXIS, title="COP"), xaxis=dict(**_XAXIS),
                      hovermode="x unified",
                      legend=dict(orientation="h", y=1.12, x=0, font=dict(size=11)))
    return fig
