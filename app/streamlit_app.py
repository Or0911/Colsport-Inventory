"""
streamlit_app.py
================
Interfaz web de Colsports — Sistema de Ventas y Métricas.

Ejecutar desde la raíz del proyecto:
    streamlit run app/streamlit_app.py
"""

import os
import sys
from datetime import date, timedelta

import streamlit as st

# ---------------------------------------------------------------------------
# Rutas
# ---------------------------------------------------------------------------
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _root)

from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(_root, ".env"), override=True)

# ---------------------------------------------------------------------------
# Configuración de página — debe ser el primer comando Streamlit
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Colsports | Sistema de Ventas",
    page_icon="🏋️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# CSS global
# ---------------------------------------------------------------------------
st.markdown("""
<style>
/* Sidebar oscuro */
[data-testid="stSidebar"] {
    background-color: #2c3e50 !important;
}
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] div {
    color: #ecf0f1 !important;
}
[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,0.15) !important;
}
/* Botones de nav en sidebar */
[data-testid="stSidebar"] .stButton > button {
    width: 100%;
    background: rgba(255,255,255,0.06) !important;
    color: #ecf0f1 !important;
    border: none !important;
    border-radius: 8px !important;
    text-align: left !important;
    padding: 10px 14px !important;
    font-size: 14px !important;
    margin-bottom: 4px !important;
    transition: background 0.15s;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(52,152,219,0.35) !important;
}
/* Botón primario */
.stButton > button[kind="primary"] {
    background-color: #3498db !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
}
.stButton > button[kind="primary"]:hover {
    background-color: #2980b9 !important;
}
/* Encabezados de sección */
.section-title {
    font-size: 22px;
    font-weight: 700;
    color: #2c3e50;
    padding-bottom: 8px;
    border-bottom: 3px solid #3498db;
    margin-bottom: 20px;
}
/* Canal badge */
.badge {
    display: inline-block;
    padding: 3px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
    color: white;
    margin-bottom: 12px;
}
/* Alert row */
.alert-item {
    background: #fde8e8;
    border-left: 4px solid #e74c3c;
    padding: 8px 14px;
    border-radius: 6px;
    margin: 5px 0;
    font-size: 13px;
    color: #2c3e50;
}
/* Ocultar el hamburger menu y footer de Streamlit */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Imports de la app (después del page_config)
# ---------------------------------------------------------------------------
from app.db_queries import (
    get_engine, get_kpis, get_ventas_por_canal, get_tendencia_diaria,
    get_top_productos, get_top_facturadores, get_ventas_recientes,
    get_inventario, get_alertas_stock, get_pedidos_sin_stock,
    get_combos_stock_virtual, get_alertas_pedido, marcar_alerta_resuelta,
    get_compras_recientes, get_catalogo_skus,
    get_kpis_compras, get_tendencia_compras, get_compras_por_proveedor, get_margen_diario,
    get_ventas_hora_canal, get_inventario_sunburst,
)
from app.charts import (
    chart_ventas_canal, chart_tendencia, chart_top_productos,
    kpi_card,
    chart_sankey, chart_waterfall, chart_heatmap, chart_sunburst,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def fmt_cop(v) -> str:
    try:
        return f"${int(v):,}".replace(",", ".")
    except Exception:
        return str(v)


def init_session():
    defaults = {
        "authenticated": False,
        "current_page": "nueva_venta",
        "sale_saved": False,
        "parsed_sale": None,
        "sale_montos": None,
        "last_venta_id": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


CANAL_COLORS = {
    "WhatsApp":    "#25D366",
    "Rappi":       "#FF441F",
    "Rappi Pro":   "#FF6B35",
    "Local":       "#3498db",
    "TikTok Live": "#010101",
    "Instagram":   "#C13584",
}


# ---------------------------------------------------------------------------
# LOGIN
# ---------------------------------------------------------------------------

def page_login():
    col_c, col_form, col_r = st.columns([1, 1.2, 1])
    with col_form:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.image("https://via.placeholder.com/220x70/2c3e50/ffffff?text=COLSPORTS", width=220)
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### Acceso al sistema")
        pwd = st.text_input("Contraseña", type="password", key="login_pwd",
                            placeholder="Ingresa la contraseña")
        if st.button("Ingresar", type="primary", use_container_width=True):
            expected = os.getenv("APP_PASSWORD")
            if not expected:
                st.error("APP_PASSWORD no está configurada en el archivo .env")
                st.stop()
            if pwd == expected:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Contraseña incorrecta")
        st.markdown(
            "<p style='color:#95a5a6;font-size:12px;margin-top:16px'>"
            "Sistema interno Colsports — acceso restringido</p>",
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------------------------

def render_sidebar():
    with st.sidebar:
        st.markdown(
            "<div style='text-align:center;padding:16px 0 8px'>"
            "<span style='font-size:28px'>🏋️</span>"
            "<div style='font-size:18px;font-weight:700;letter-spacing:1px;margin-top:4px'>COLSPORTS</div>"
            "<div style='font-size:11px;color:#95a5a6;margin-top:2px'>Sistema de Ventas</div>"
            "</div>",
            unsafe_allow_html=True,
        )
        st.divider()

        icons = {"nueva_venta": "📝", "dashboard": "📊", "inventario": "📦", "compras": "🛒"}
        labels = {"nueva_venta": "Nueva Venta", "dashboard": "Dashboard", "inventario": "Inventario", "compras": "Compras"}
        for page, label in labels.items():
            if st.button(f"{icons[page]}  {label}", key=f"nav_{page}"):
                st.session_state.current_page = page
                st.rerun()

        st.divider()

        if st.button("🔒  Cerrar sesión"):
            st.session_state.authenticated = False
            st.session_state.current_page = "nueva_venta"
            st.rerun()

        st.markdown(
            "<div style='position:absolute;bottom:20px;width:80%;text-align:center;"
            "font-size:10px;color:#7f8c8d'>v1.0 · Colsports 2025</div>",
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# PÁGINA: NUEVA VENTA
# ---------------------------------------------------------------------------

def page_nueva_venta(engine):
    st.markdown('<div class="section-title">📝 Nueva Venta</div>', unsafe_allow_html=True)

    # Versión del textarea: incrementar para forzar widget vacío (método garantizado en Streamlit)
    if "sale_msg_v" not in st.session_state:
        st.session_state["sale_msg_v"] = 0
    sale_key = f"sale_msg_{st.session_state['sale_msg_v']}"

    col_left, col_right = st.columns([1, 1], gap="large")

    # ── Columna izquierda: formulario ──
    with col_left:
        st.markdown("**Pega aquí el mensaje de WhatsApp o Rappi**")
        st.text_area(
            "",
            placeholder=(
                "VENTA WHATSAPP\nJuan García\n1028000000\n3100000000\n"
                "1 und Creatina IMN 133 serv\n$139.000\nTransferencia bancolombia"
            ),
            height=260,
            key=sale_key,
            label_visibility="collapsed",
        )

        c1, c2 = st.columns([3, 1])
        with c1:
            parsear_btn = st.button("⬆️ Procesar Venta", type="primary",
                                    use_container_width=True, key="btn_parsear")
        with c2:
            if st.button("🗑️", use_container_width=True, key="btn_limpiar",
                         help="Limpiar formulario"):
                for k in ["parsed_sale", "sale_montos", "sale_saved", "last_venta_id"]:
                    st.session_state[k] = None if k != "sale_saved" else False
                st.session_state["sale_msg_v"] = st.session_state["sale_msg_v"] + 1
                st.rerun()

        if parsear_btn:
            msg = st.session_state.get(sale_key, "").strip()
            if not msg:
                st.warning("Pega un mensaje antes de parsear.")
            else:
                with st.spinner("Procesando con IA..."):
                    try:
                        from api.motor_ia import parsear_mensaje, calcular_montos
                        venta = parsear_mensaje(msg)
                        montos = calcular_montos(venta)
                        st.session_state.parsed_sale = venta
                        st.session_state.sale_montos = montos
                        st.session_state.sale_saved = False
                        st.session_state.last_venta_id = None
                    except Exception as e:
                        st.error(f"Error al parsear: {e}")

    # ── Columna derecha: vista previa ──
    with col_right:

        # Estado: venta ya guardada
        if st.session_state.get("sale_saved") and st.session_state.get("last_venta_id"):
            st.success(f"✅ Venta **#{st.session_state.last_venta_id}** guardada correctamente.")
            if st.button("➕ Registrar otra venta", type="primary", use_container_width=True):
                for k in ["parsed_sale", "sale_montos", "last_venta_id"]:
                    st.session_state[k] = None
                st.session_state["sale_saved"] = False
                st.session_state["sale_msg_v"] = st.session_state["sale_msg_v"] + 1
                st.rerun()
            return

        venta = st.session_state.get("parsed_sale")
        montos = st.session_state.get("sale_montos")

        if venta is None:
            st.markdown(
                "<div style='background:#f8f9fa;border-radius:10px;padding:40px;text-align:center;color:#95a5a6'>"
                "<div style='font-size:36px'>👈</div>"
                "<div style='margin-top:8px'>La vista previa aparecerá aquí<br>después de parsear el mensaje</div>"
                "</div>",
                unsafe_allow_html=True,
            )
            return

        # Badge de canal
        canal_color = CANAL_COLORS.get(venta.canal, "#3498db")
        st.markdown(
            f'<span class="badge" style="background:{canal_color}">{venta.canal}</span>',
            unsafe_allow_html=True,
        )

        # Cliente
        if venta.cliente:
            c = venta.cliente
            with st.expander("👤 Cliente", expanded=True):
                cols = st.columns(2)
                if c.nombre:   cols[0].markdown(f"**Nombre:** {c.nombre}")
                if c.cedula:   cols[1].markdown(f"**CC:** {c.cedula}")
                if c.telefono: cols[0].markdown(f"**Tel:** {c.telefono}")
                if c.email:    cols[1].markdown(f"**Email:** {c.email}")

        # Productos
        st.markdown("**🛒 Productos**")
        for item in venta.items:
            precio = fmt_cop(item.precio_unitario) if item.precio_unitario else "—"
            st.markdown(
                f"<div style='background:#f0f4f8;border-radius:6px;padding:7px 12px;"
                f"margin:3px 0;font-size:13px'>"
                f"<b>{item.cantidad}×</b> {item.producto_nombre_raw} "
                f"<span style='float:right;color:#3498db;font-weight:600'>{precio}</span></div>",
                unsafe_allow_html=True,
            )

        # Montos
        st.divider()
        mc1, mc2, mc3 = st.columns(3)
        mc1.metric("Bruto", fmt_cop(montos["subtotal"]))
        if montos["costo_envio"]:
            mc2.metric("Envío", fmt_cop(montos["costo_envio"]))
        if montos["comision_monto"]:
            pct = venta.rappi_detalle.comision_porcentaje if venta.rappi_detalle else 0
            mc2.metric("Comisión", fmt_cop(montos["comision_monto"]),
                       delta=f"-{pct:.0f}%", delta_color="inverse")
        mc3.metric("**Neto**", fmt_cop(montos["total"]))

        # Pago
        pago_str = venta.pago.metodo
        if venta.pago.cuenta_destino:
            pago_str += f" › {venta.pago.cuenta_destino}"
        st.markdown(f"💳 **Pago:** {pago_str}")

        # Envío / dirección
        if venta.envio and (venta.envio.ciudad or venta.envio.direccion):
            with st.expander("📦 Dirección de envío"):
                e = venta.envio
                if e.direccion:    st.text(f"Dirección : {e.direccion}")
                if e.ciudad:       st.text(f"Ciudad    : {e.ciudad}")
                if e.departamento: st.text(f"Dpto      : {e.departamento}")

        # Notas
        if venta.notas:
            st.info(f"📝 {venta.notas}")
        if venta.fuente_referido:
            st.markdown(f"📣 **Referido:** {venta.fuente_referido}")

        st.divider()

        # Botones confirmar / cancelar
        b1, b2 = st.columns([3, 1])
        with b1:
            if st.button("✅ Confirmar y Guardar", type="primary",
                         use_container_width=True, key="btn_guardar"):
                msg = st.session_state.get(sale_key, "")
                with st.spinner("Guardando en base de datos..."):
                    try:
                        from sqlalchemy.orm import Session as DBSession
                        from api.guardar_venta import guardar_venta
                        with DBSession(engine) as session:
                            v_guardada = guardar_venta(session, venta, msg)
                            session.commit()
                            venta_id = v_guardada.id

                        st.session_state.sale_saved = True
                        st.session_state.last_venta_id = venta_id
                        st.session_state["sale_msg_v"] = st.session_state["sale_msg_v"] + 1

                        # Invalidar cachés del dashboard
                        get_ventas_por_canal.clear()
                        get_tendencia_diaria.clear()
                        get_top_productos.clear()
                        get_top_facturadores.clear()
                        get_ventas_recientes.clear()
                        get_alertas_stock.clear()
                        get_pedidos_sin_stock.clear()
                        get_combos_stock_virtual.clear()
                        get_alertas_pedido.clear()
                        get_kpis.clear()

                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al guardar: {e}")
        with b2:
            if st.button("❌", use_container_width=True, key="btn_cancelar",
                         help="Cancelar"):
                st.session_state.parsed_sale = None
                st.session_state.sale_montos = None
                st.rerun()


# ---------------------------------------------------------------------------
# PÁGINA: DASHBOARD
# ---------------------------------------------------------------------------

def page_dashboard(engine):
    # ── Dark theme CSS (solo activo cuando esta página renderiza) ──
    st.markdown("""
    <style>
    .main .block-container { background-color: #0d1b2e !important; }
    .dash-label {
        font-size: 10px; color: #6b86a8;
        text-transform: uppercase; letter-spacing: 1.5px;
        font-weight: 700; margin-bottom: 6px; margin-top: 2px;
    }
    </style>
    """, unsafe_allow_html=True)

    # ── Header ──
    st.markdown("""
    <div style="display:flex;align-items:center;gap:18px;margin-bottom:20px;padding-bottom:14px;
                border-bottom:1px solid #162a47">
        <div style="font-size:28px;font-weight:900;color:#3498db;letter-spacing:-1px">COL SPORTS</div>
        <div style="font-size:10px;color:#6b86a8;text-transform:uppercase;letter-spacing:2.5px;
                    border-left:2px solid #162a47;padding-left:16px">ANALYTICS DASHBOARD</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Selector de período ──
    if "_dash_start" not in st.session_state:
        st.session_state["_dash_start"] = date.today() - timedelta(days=29)
    if "_dash_end" not in st.session_state:
        st.session_state["_dash_end"] = date.today()

    col_d1, col_d2, col_d3 = st.columns([1, 1, 3])
    with col_d1:
        start_date = st.date_input("Desde", value=st.session_state["_dash_start"])
        st.session_state["_dash_start"] = start_date
    with col_d2:
        end_date = st.date_input("Hasta", value=st.session_state["_dash_end"])
        st.session_state["_dash_end"] = end_date
    with col_d3:
        qc = st.columns(4)
        for i, (lbl, delta) in enumerate([("Hoy", 0), ("7 días", 6), ("30 días", 29), ("90 días", 89)]):
            if qc[i].button(lbl, key=f"period_{delta}"):
                st.session_state["_dash_start"] = date.today() - timedelta(days=delta)
                st.session_state["_dash_end"] = date.today()
                st.rerun()

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # ── Carga de datos ──
    kpis       = get_kpis(engine)
    kpis_comp  = get_kpis_compras(engine)
    df_canal   = get_ventas_por_canal(engine, start_date, end_date)
    df_tend    = get_tendencia_diaria(engine, start_date, end_date)
    df_top     = get_top_productos(engine)
    df_horas   = get_ventas_hora_canal(engine, start_date, end_date)
    df_sun     = get_inventario_sunburst(engine)
    df_alertas = get_alertas_stock(engine)

    ventas_neto  = kpis["mes"]["neto"]
    costo_mes    = kpis_comp["mes"]["total"]
    comisiones   = kpis["mes"]["comisiones"]
    margen_mes   = ventas_neto - costo_mes
    pct_margen   = round(margen_mes / ventas_neto * 100, 1) if ventas_neto > 0 else 0.0
    n_alertas    = len(df_alertas)
    alert_color  = "#e74c3c" if n_alertas > 0 else "#607d8b"

    # ── 4 KPI cards ──
    k1, k2, k3, k4 = st.columns(4)
    k1.markdown(kpi_card(
        "Ventas del Mes", fmt_cop(ventas_neto),
        f"{kpis['mes']['count']} órdenes este mes", "#3498db",
    ), unsafe_allow_html=True)
    k2.markdown(kpi_card(
        "Inversión en Compras", fmt_cop(costo_mes),
        f"{kpis_comp['mes']['count']} órdenes de compra", "#607d8b",
    ), unsafe_allow_html=True)
    k3.markdown(kpi_card(
        "Margen Estimado", f"{pct_margen}%",
        fmt_cop(margen_mes), "#2ecc71" if pct_margen >= 0 else "#e74c3c",
    ), unsafe_allow_html=True)
    k4.markdown(kpi_card(
        "Alertas de Stock", str(n_alertas),
        "productos por reabastecer", alert_color,
    ), unsafe_allow_html=True)

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    def _label(text: str):
        st.markdown(f"<div class='dash-label'>{text}</div>", unsafe_allow_html=True)

    # ── Fila 1: Sankey | Waterfall ──
    r1a, r1b = st.columns([55, 45], gap="medium")
    with r1a:
        _label("Flujo de Capital — Período Seleccionado")
        st.plotly_chart(
            chart_sankey(df_canal, ventas_neto, costo_mes, comisiones),
            use_container_width=True,
        )
    with r1b:
        _label("Cierre del Mes Actual")
        st.plotly_chart(
            chart_waterfall(ventas_neto, costo_mes, comisiones),
            use_container_width=True,
        )

    # ── Fila 2: Heatmap full width ──
    _label("Actividad de Ventas — Hora y Día de la Semana")
    st.plotly_chart(chart_heatmap(df_horas), use_container_width=True)

    # ── Fila 3: Canal donut | Top productos ──
    r3a, r3b = st.columns([2, 3], gap="medium")
    with r3a:
        _label("Distribución por Canal")
        st.plotly_chart(chart_ventas_canal(df_canal), use_container_width=True)
    with r3b:
        _label("Top 10 Productos Más Vendidos")
        st.plotly_chart(chart_top_productos(df_top), use_container_width=True)

    # ── Fila 4: Sunburst | Tendencia diaria ──
    r4a, r4b = st.columns([2, 3], gap="medium")
    with r4a:
        _label("Distribución de Inventario Activo")
        st.plotly_chart(chart_sunburst(df_sun), use_container_width=True)
    with r4b:
        _label("Tendencia Diaria de Ingresos")
        st.plotly_chart(chart_tendencia(df_tend), use_container_width=True)

    # ── Ventas recientes ──
    _label("Últimas Ventas")
    df_rec = get_ventas_recientes(engine, limit=10)
    if df_rec.empty:
        st.info("No hay ventas registradas aún.")
    else:
        st.dataframe(df_rec, use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------------
# PÁGINA: INVENTARIO Y ALERTAS
# ---------------------------------------------------------------------------

def page_inventario(engine):
    st.markdown('<div class="section-title">📦 Inventario y Alertas</div>',
                unsafe_allow_html=True)

    tab_inv, tab_alertas, tab_combos, tab_hot = st.tabs(
        ["📋 Catálogo", "🚨 Alertas de stock", "🧩 Combos", "🔥 Hot Products"]
    )

    # ── Tab 1: Catálogo completo ──
    with tab_inv:
        search = st.text_input("🔍 Buscar producto (nombre, SKU, marca, categoría)",
                               key="inv_search", placeholder="Ej: creatina, 1013, IMN…")
        df_inv = get_inventario(engine, search)

        if df_inv.empty:
            st.info("No se encontraron productos.")
        else:
            st.caption(f"{len(df_inv)} productos encontrados")

            def _style_stock(val):
                if val < 0:
                    return "background-color:#fde8e8;color:#c0392b;font-weight:700"
                if val <= 3:
                    return "background-color:#fef9e7;color:#d35400;font-weight:600"
                if val > 10:
                    return "background-color:#eafaf1;color:#1e8449"
                return ""

            styled = df_inv.style.applymap(_style_stock, subset=["Stock"])
            st.dataframe(styled, use_container_width=True, hide_index=True)

    # ── Tab 2: Alertas ──
    with tab_alertas:
        # Sección 1: stock negativo — siempre visible
        df_negativos = get_alertas_stock(engine, umbral=-1)
        st.markdown("#### 🔴 Stock negativo (vendidos sin stock)")
        if df_negativos.empty:
            st.success("No hay productos con stock negativo.")
        else:
            st.error(f"❗ {len(df_negativos)} productos con stock negativo — requieren reposición urgente")
            for _, row in df_negativos.iterrows():
                st.markdown(
                    f'<div class="alert-item">'
                    f'🔴 <b>[{row["SKU"]}]</b> {row["Nombre"]} '
                    f'— <span style="color:#e74c3c;font-weight:700">Stock: {row["Stock"]}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

        st.markdown("---")

        # Sección 2: stock bajo — controlado por slider
        st.markdown("#### 🟡 Stock bajo")
        umbral = st.slider("Mostrar productos con stock entre 0 y:", 1, 10, 5,
                           key="umbral_alerta")
        df_bajo = get_alertas_stock(engine, umbral=umbral)
        df_bajo = df_bajo[df_bajo["Stock"] >= 0]  # excluir los negativos ya mostrados arriba

        if df_bajo.empty:
            st.success(f"✅ No hay productos con stock entre 0 y {umbral}.")
        else:
            st.warning(f"⚠️ {len(df_bajo)} productos con stock entre 0 y {umbral}")
            for _, row in df_bajo.iterrows():
                st.markdown(
                    f'<div class="alert-item" style="background:#fef9e7;border-color:#e67e22">'
                    f'🟡 <b>[{row["SKU"]}]</b> {row["Nombre"]} '
                    f'— <span style="color:#d35400;font-weight:700">Stock: {row["Stock"]}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

        st.markdown("---")
        st.markdown("#### 📋 Detalle: pedidos sin stock")
        df_sin = get_pedidos_sin_stock(engine)
        if df_sin.empty:
            st.success("No hay pedidos pendientes por reponer.")
        else:
            st.dataframe(df_sin, use_container_width=True, hide_index=True)

    # ── Tab 3: Combos ──
    with tab_combos:
        st.markdown("#### 🧩 Stock Virtual de Combos")
        st.caption(
            "El stock virtual es cuántas unidades del combo se podrían armar "
            "con el stock actual de cada componente. El cuello de botella es el "
            "componente más escaso."
        )
        df_combos = get_combos_stock_virtual(engine)
        if df_combos.empty:
            st.info(
                "No hay combos registrados aún. "
                "Agrega filas en la tabla **combo_componentes** para que aparezcan aquí."
            )
        else:
            def _style_combo_stock(val):
                if val <= 0:
                    return "background-color:#fde8e8;color:#c0392b;font-weight:700"
                if val <= 3:
                    return "background-color:#fef9e7;color:#d35400;font-weight:600"
                return "background-color:#eafaf1;color:#1e8449"

            styled_combos = df_combos.style.applymap(_style_combo_stock, subset=["Stock Virtual"])
            st.dataframe(styled_combos, use_container_width=True, hide_index=True)

        st.markdown("---")
        st.markdown("#### ⚠️ Alertas de componentes faltantes en combos")
        mostrar_resueltas = st.checkbox("Incluir alertas ya resueltas", key="chk_resueltas")
        df_alertas = get_alertas_pedido(engine, solo_pendientes=not mostrar_resueltas)

        if df_alertas.empty:
            st.success("No hay alertas de componentes pendientes.")
        else:
            for _, row in df_alertas.iterrows():
                resuelta = bool(row["Resuelta"])
                color = "#eafaf1" if resuelta else "#fde8e8"
                borde = "#27ae60" if resuelta else "#e74c3c"
                estado_txt = "✅ Resuelta" if resuelta else "🔴 Pendiente"
                col_info, col_btn = st.columns([5, 1])
                with col_info:
                    st.markdown(
                        f'<div class="alert-item" style="background:{color};border-color:{borde}">'
                        f'<b>Combo:</b> {row["Combo SKU"]} &nbsp;|&nbsp; '
                        f'<b>Faltante:</b> {row["Componente"]} × {row["Faltante"]} und '
                        f'&nbsp;|&nbsp; <b>Venta:</b> #{row["Venta ID"]} '
                        f'&nbsp;|&nbsp; {estado_txt}'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                with col_btn:
                    if not resuelta:
                        if st.button("Resolver", key=f"resolve_{row['ID']}"):
                            marcar_alerta_resuelta(engine, int(row["ID"]))
                            get_alertas_pedido.clear()
                            st.rerun()

    # ── Tab 4: Hot Products ──
    with tab_hot:
        st.markdown("**Top 5 productos más vendidos (todas las ventas)**")
        df_hot = get_top_productos(engine, limit=5)
        if df_hot.empty:
            st.info("No hay datos de ventas aún.")
        else:
            for i, (_, row) in enumerate(df_hot.iterrows(), 1):
                medal = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"][i - 1]
                c1, c2, c3 = st.columns([3, 1, 1])
                c1.markdown(f"{medal} **{row['Producto'][:50]}**")
                c2.metric("Unidades", int(row["Unidades"]))
                c3.metric("Ingresos", fmt_cop(row["Ingresos"]))


# ---------------------------------------------------------------------------
# PÁGINA: COMPRAS E INGRESO DE MERCANCÍA
# ---------------------------------------------------------------------------

def page_compras(engine):
    st.markdown('<div class="section-title">🛒 Compras e Ingreso de Mercancía</div>',
                unsafe_allow_html=True)

    # Versión del textarea: incrementar limpia el campo de forma garantizada
    if "purchase_msg_v" not in st.session_state:
        st.session_state["purchase_msg_v"] = 0
    purchase_key = f"purchase_msg_{st.session_state['purchase_msg_v']}"

    tab_nueva, tab_historial = st.tabs(["📥 Nueva Compra", "📋 Historial"])

    # ── Tab 1: Nueva compra ──
    with tab_nueva:
        col_left, col_right = st.columns([1, 1.3], gap="large")

        with col_left:
            st.markdown("**Pega aquí el mensaje del proveedor o lista de productos**")
            st.text_area(
                "",
                placeholder=(
                    "Ejemplo:\n"
                    "IMN Colombia\n"
                    "12 Creatina 133 serv 550g - $75.000 c/u\n"
                    "6 Whey Protein 2lb vainilla - $95.000\n"
                    "4 Pre-entreno 30 serv - $58.000"
                ),
                height=240,
                key=purchase_key,
                label_visibility="collapsed",
            )

            c1, c2 = st.columns([3, 1])
            with c1:
                analizar_btn = st.button(
                    "🔍 Analizar Compra", type="primary",
                    use_container_width=True, key="btn_analizar_compra"
                )
            with c2:
                if st.button("🗑️", use_container_width=True, key="btn_limpiar_compra",
                             help="Limpiar"):
                    for k in ["parsed_compra", "compra_guardada", "last_compra_id"]:
                        st.session_state.pop(k, None)
                    st.session_state["purchase_msg_v"] += 1
                    st.rerun()

            if analizar_btn:
                msg = st.session_state.get(purchase_key, "").strip()
                if not msg:
                    st.warning("Pega un mensaje antes de analizar.")
                else:
                    with st.spinner("Procesando con IA..."):
                        try:
                            from api.purchase_parser import parsear_compra
                            compra_parsed = parsear_compra(msg)
                            st.session_state["parsed_compra"] = compra_parsed
                            st.session_state.pop("compra_guardada", None)
                            st.session_state.pop("last_compra_id", None)
                        except Exception as e:
                            st.error(f"Error al analizar: {e}")

        with col_right:
            # Estado: compra ya guardada — sin return, usando if/elif/else
            if st.session_state.get("compra_guardada") and st.session_state.get("last_compra_id"):
                st.success(
                    f"✅ Compra **#{st.session_state['last_compra_id']}** "
                    "ingresada y stock actualizado."
                )
                if st.button("➕ Registrar otra compra", type="primary",
                             use_container_width=True):
                    for k in ["parsed_compra", "compra_guardada", "last_compra_id"]:
                        st.session_state.pop(k, None)
                    st.session_state["purchase_msg_v"] += 1
                    st.rerun()

            elif st.session_state.get("parsed_compra") is None:
                st.markdown(
                    "<div style='background:#f8f9fa;border-radius:10px;padding:40px;"
                    "text-align:center;color:#95a5a6'>"
                    "<div style='font-size:36px'>👈</div>"
                    "<div style='margin-top:8px'>La tabla de revisión aparecerá aquí<br>"
                    "después de analizar el mensaje</div></div>",
                    unsafe_allow_html=True,
                )

            else:
                compra_parsed = st.session_state["parsed_compra"]

                # Proveedor editable
                proveedor = st.text_input(
                    "Proveedor", value=compra_parsed.proveedor or "",
                    key="compra_proveedor", placeholder="Nombre del proveedor"
                )

                # Catálogo para sugerir SKUs
                catalogo = get_catalogo_skus(engine)
                skus_disponibles = [""] + [f"{p['sku']} — {p['nombre']}" for p in catalogo]
                sku_map = {"": None}
                for p in catalogo:
                    sku_map[f"{p['sku']} — {p['nombre']}"] = p["sku"]

                # DataFrame inicial con SKU sugerido por F1-score
                from api.guardar_venta import _buscar_sku
                from sqlalchemy.orm import Session as DBSession
                from models import Producto as ProdModel
                from sqlalchemy import select as sql_select

                with DBSession(engine) as s:
                    productos_catalogo = s.execute(sql_select(ProdModel)).scalars().all()

                rows_editor = []
                for item in compra_parsed.items:
                    sku_sugerido = _buscar_sku(productos_catalogo, item.producto_nombre_raw)
                    sku_display = ""
                    if sku_sugerido:
                        match = next((p for p in catalogo if p["sku"] == sku_sugerido), None)
                        if match:
                            sku_display = f"{match['sku']} — {match['nombre']}"
                    rows_editor.append({
                        "Producto (del proveedor)": item.producto_nombre_raw,
                        "SKU en catálogo": sku_display,
                        "Cantidad": item.cantidad,
                        "Costo unitario (COP)": item.precio_costo_unitario,
                    })

                import pandas as pd
                df_edit = pd.DataFrame(rows_editor)

                st.markdown("**Revisar y ajustar productos detectados**")
                st.caption("Edita el SKU, cantidad o costo antes de confirmar. "
                           "Solo se suma stock a los productos con SKU asignado.")

                df_resultado = st.data_editor(
                    df_edit,
                    use_container_width=True,
                    hide_index=True,
                    num_rows="dynamic",
                    key="editor_compra",
                    column_config={
                        "Producto (del proveedor)": st.column_config.TextColumn(
                            "Producto (del proveedor)", width="large"
                        ),
                        "SKU en catálogo": st.column_config.SelectboxColumn(
                            "SKU en catálogo",
                            options=skus_disponibles,
                            width="large",
                        ),
                        "Cantidad": st.column_config.NumberColumn(
                            "Cantidad", min_value=1, step=1, width="small"
                        ),
                        "Costo unitario (COP)": st.column_config.NumberColumn(
                            "Costo unitario (COP)", min_value=0, step=1000, width="medium",
                            format="$ %d"
                        ),
                    },
                )

                # Total estimado
                try:
                    total_est = int(
                        (df_resultado["Cantidad"] * df_resultado["Costo unitario (COP)"].fillna(0)).sum()
                    )
                    total_fmt = f"${total_est:,}".replace(",", ".")
                    st.markdown(
                        f"<div style='text-align:right;font-size:15px;color:#2c3e50'>"
                        f"<b>Total estimado:</b> "
                        f"<span style='color:#3498db;font-weight:700'>{total_fmt}</span>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
                except Exception:
                    pass

                st.divider()

                if st.button(
                    "✅ Confirmar e Ingresar a Inventario",
                    type="primary",
                    use_container_width=True,
                    key="btn_confirmar_compra",
                ):
                    with st.spinner("Guardando compra y actualizando stock..."):
                        try:
                            df_save = df_resultado.copy()
                            df_save["sku"] = df_save["SKU en catálogo"].map(
                                lambda v: sku_map.get(v, None)
                            )
                            df_save = df_save.rename(columns={
                                "Producto (del proveedor)": "producto_nombre_raw",
                                "Cantidad": "cantidad",
                                "Costo unitario (COP)": "precio_costo_unitario",
                            })[["producto_nombre_raw", "sku", "cantidad", "precio_costo_unitario"]]

                            from sqlalchemy.orm import Session as DBSession2
                            from api.guardar_compra import guardar_compra
                            with DBSession2(engine) as session:
                                compra_obj = guardar_compra(
                                    session, proveedor or None, df_save
                                )
                                session.commit()
                                compra_id = compra_obj.id

                            st.session_state["compra_guardada"] = True
                            st.session_state["last_compra_id"] = compra_id
                            st.session_state["purchase_msg_v"] += 1

                            get_inventario.clear()
                            get_alertas_stock.clear()
                            get_pedidos_sin_stock.clear()
                            get_combos_stock_virtual.clear()
                            get_compras_recientes.clear()
                            get_kpis.clear()

                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al guardar: {e}")

    # ── Tab 2: Historial ── (siempre se renderiza, sin return previo)
    with tab_historial:
        st.markdown("**Últimas 20 compras registradas**")
        df_hist = get_compras_recientes(engine)
        if df_hist.empty:
            st.info("No hay compras registradas aún.")
        else:
            st.dataframe(df_hist, use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    init_session()

    if not st.session_state.authenticated:
        page_login()
        st.stop()

    engine = get_engine()
    render_sidebar()

    page = st.session_state.current_page
    if page == "nueva_venta":
        page_nueva_venta(engine)
    elif page == "dashboard":
        page_dashboard(engine)
    elif page == "inventario":
        page_inventario(engine)
    elif page == "compras":
        page_compras(engine)


if __name__ == "__main__":
    main()
