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
# Theme — one dict per tenant; override via env vars for multi-tenancy.
# THEME_PRIMARY      → sidebar background, active accents
# THEME_PRIMARY_DARK → hover/active states on primary surfaces
# THEME_PRIMARY_TEXT → text color on top of primary background
# THEME_SECONDARY    → primary action buttons, strong text
# THEME_CANVAS       → page background
# ---------------------------------------------------------------------------
THEME = {
    "primary":      os.getenv("THEME_PRIMARY",      "#314457"),
    "primary_dark": os.getenv("THEME_PRIMARY_DARK", "#243344"),
    "primary_text": os.getenv("THEME_PRIMARY_TEXT", "#ffffff"),
    "secondary":    os.getenv("THEME_SECONDARY",    "#1a1a1a"),
    "canvas":       os.getenv("THEME_CANVAS",       "#edeae3"),
}

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
# Inject theme tokens as CSS custom properties so every rule can use var(--cs-*)
st.markdown(f"""
<style>
:root {{
    --cs-primary:      {THEME["primary"]};
    --cs-primary-dark: {THEME["primary_dark"]};
    --cs-primary-text: {THEME["primary_text"]};
    --cs-secondary:    {THEME["secondary"]};
    --cs-canvas:       {THEME["canvas"]};
}}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Caveat:wght@400;500;600;700&display=swap');

html, body, [class*="css"], .stApp {
    font-family: 'Caveat', cursive !important;
    background-color: var(--cs-canvas) !important;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: var(--cs-primary) !important;
    border-right: 1px solid var(--cs-primary-dark) !important;
}
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] div {
    color: var(--cs-primary-text) !important;
    font-family: 'Caveat', cursive !important;
}
[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,0.2) !important;
}
[data-testid="stSidebar"] .stButton > button {
    width: 100%;
    background: rgba(255,255,255,0.88) !important;
    color: var(--cs-primary) !important;
    border: none !important;
    border-radius: 2px !important;
    text-align: left !important;
    padding: 10px 14px !important;
    font-size: 15px !important;
    font-family: 'Caveat', cursive !important;
    margin-bottom: 2px !important;
    transition: background 0.15s, color 0.15s;
}
[data-testid="stSidebar"] .stButton > button p,
[data-testid="stSidebar"] .stButton > button span,
[data-testid="stSidebar"] .stButton > button div {
    color: var(--cs-primary) !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: var(--cs-primary-dark) !important;
    color: var(--cs-primary-text) !important;
}
[data-testid="stSidebar"] .stButton > button:hover p,
[data-testid="stSidebar"] .stButton > button:hover span,
[data-testid="stSidebar"] .stButton > button:hover div {
    color: var(--cs-primary-text) !important;
}

/* Sidebar collapse/expand button — keep transparent so icon is visible */
[data-testid="stSidebarCollapseButton"] button {
    background: transparent !important;
    border: none !important;
    color: var(--cs-primary-text) !important;
}
[data-testid="stSidebarCollapseButton"] button:hover {
    background: var(--cs-primary-dark) !important;
}
[data-testid="stSidebarCollapseButton"] svg {
    stroke: var(--cs-primary-text) !important;
    fill: var(--cs-primary-text) !important;
}

/* Primary button */
.stButton > button[kind="primary"],
.stButton > button[data-testid="baseButton-primary"] {
    background-color: var(--cs-primary) !important;
    color: var(--cs-primary-text) !important;
    border: 2px solid var(--cs-primary-dark) !important;
    border-radius: 2px !important;
    font-family: 'Caveat', cursive !important;
    font-size: 16px !important;
    font-weight: 600 !important;
}
.stButton > button[kind="primary"]:hover,
.stButton > button[data-testid="baseButton-primary"]:hover {
    background-color: var(--cs-primary-dark) !important;
    color: var(--cs-primary-text) !important;
}

/* Secondary / default button */
.stButton > button[kind="secondary"],
.stButton > button[data-testid="baseButton-secondary"] {
    background-color: #f0ece4 !important;
    color: #555 !important;
    border: 1.5px solid #999 !important;
    border-radius: 2px !important;
    font-family: 'Caveat', cursive !important;
    font-size: 15px !important;
}

/* Cards */
.cs-card {
    background: #fffef9;
    border: 1.5px solid #d4d0c8;
    border-radius: 2px;
    box-shadow: 3px 4px 0 #e8e4dc;
    padding: 16px 18px;
    margin-bottom: 12px;
}

/* Section titles */
.cs-section-title {
    font-size: 22px;
    font-weight: 700;
    color: #1a1a1a;
    padding-bottom: 8px;
    border-bottom: 2px solid #d4d0c8;
    margin-bottom: 20px;
    font-family: 'Caveat', cursive;
}

/* KPI components */
.cs-kpi-label { font-size: 13px; color: #999; font-family: 'Caveat', cursive; }
.cs-kpi-value { font-size: 23px; font-weight: 700; color: #1a1a1a; font-family: 'Caveat', cursive; line-height: 1.2; }
.cs-kpi-sub   { font-size: 13px; color: #aaa; font-family: 'Caveat', cursive; margin-top: 4px; }

/* Status colors */
.cs-green { color: #5aaa88; }
.cs-amber { color: #aa8844; }
.cs-blue  { color: #4488aa; }
.cs-red   { color: #cc4444; }
.cs-muted { color: #aaa; }

/* Alert card */
.cs-alert {
    background: #fff8f2;
    border: 1.5px solid #c89070;
    border-radius: 2px;
    padding: 8px 14px;
    margin: 4px 0;
    font-family: 'Caveat', cursive;
}
.cs-alert-amber {
    background: #fffaf2;
    border: 1.5px solid #c8a070;
    border-radius: 2px;
    padding: 8px 14px;
    margin: 4px 0;
    font-family: 'Caveat', cursive;
}

/* Canal badge */
.badge {
    display: inline-block;
    padding: 3px 12px;
    border-radius: 2px;
    border: 1.5px solid currentColor;
    font-size: 13px;
    font-weight: 600;
    font-family: 'Caveat', cursive;
    margin-bottom: 12px;
}

/* Inputs */
.stTextInput input, .stTextArea textarea {
    font-family: 'Caveat', cursive !important;
    background: #fffef9 !important;
    border: 1.5px solid #ccc !important;
    border-radius: 2px !important;
    color: #333 !important;
}

/* Tabs */
.stTabs [data-baseweb="tab"] {
    font-family: 'Caveat', cursive !important;
    font-size: 15px !important;
    color: #777 !important;
}
.stTabs [aria-selected="true"] {
    color: #1a1a1a !important;
    border-bottom-color: #1a1a1a !important;
}

/* Dataframe */
.stDataFrame { background: #fffef9 !important; }

/* Hide streamlit chrome */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Imports de la app (después del page_config)
# ---------------------------------------------------------------------------
from app.db_queries import (
    get_engine, get_kpis,
    get_sales_by_channel, get_daily_trend, get_top_products,
    get_top_billers, get_recent_sales,
    get_inventory, get_stock_alerts, get_orders_without_stock,
    get_combo_virtual_stock, get_order_alerts, mark_alert_resolved,
    get_recent_purchases, get_sku_catalog,
    get_purchase_kpis, get_purchase_trend, get_purchases_by_supplier, get_daily_margin,
    get_sale_detail, get_money_by_account, get_all_sales, update_sale,
    # legacy aliases kept for cache-clear calls
    get_ventas_por_canal, get_tendencia_diaria, get_top_productos,
    get_top_facturadores, get_ventas_recientes, get_alertas_stock,
    get_pedidos_sin_stock, get_combos_stock_virtual, get_alertas_pedido,
    get_inventario, get_compras_recientes,
)
from app.charts import (
    chart_ventas_canal, chart_tendencia, chart_top_productos,
    kpi_card,
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
        "sv_detalle_edit": None,
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
    st.markdown("""
    <style>
    .login-feature { font-size: 17px; color: #666; font-family: 'Caveat', cursive; margin: 6px 0; }
    .login-card {
        background: #fffef9;
        border: 1.5px solid #aaa8a0;
        border-radius: 2px;
        box-shadow: 4px 5px 0 #dedad2;
        padding: 36px 32px;
    }
    </style>
    """, unsafe_allow_html=True)

    col_left, col_card, col_right = st.columns([1.1, 1, 0.9])

    with col_left:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.markdown(
            "<div style='font-size:46px;font-weight:700;color:#1a1a1a;"
            "font-family:Caveat,cursive;letter-spacing:-1px'>Colsports</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<div style='font-size:18px;color:#888;font-family:Caveat,cursive;"
            "margin-top:4px'>Sistema de Ventas & Inventario</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<hr style='border:none;border-top:1px solid #d4d0c8;margin:16px 0 20px'>",
            unsafe_allow_html=True,
        )
        features = [
            "✦  Registro de ventas por WhatsApp / Rappi",
            "✦  Parsing con IA — sin cálculos manuales",
            "✦  Inventario con deducción automática",
            "✦  Dashboard de métricas en tiempo real",
            "✦  Control de combos y stock virtual",
        ]
        for f in features:
            st.markdown(f'<div class="login-feature">{f}</div>', unsafe_allow_html=True)

    with col_card:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        st.markdown(
            "<div style='font-size:28px;font-weight:700;color:#1a1a1a;"
            "font-family:Caveat,cursive;text-align:center;margin-bottom:4px'>Bienvenido</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<div style='font-size:15px;color:#999;font-family:Caveat,cursive;"
            "text-align:center;margin-bottom:20px'>Ingresa la contraseña de acceso</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<hr style='border:none;border-top:1px solid #e8e4dc;margin-bottom:20px'>",
            unsafe_allow_html=True,
        )
        pwd = st.text_input("Contraseña", type="password", key="login_pwd",
                            placeholder="Contraseña del sistema",
                            label_visibility="collapsed")
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
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
            "<div style='text-align:center;margin-top:20px'>"
            "<hr style='border:none;border-top:1px solid #e8e4dc;margin-bottom:12px'>"
            "<span style='font-size:12px;color:#bbb;font-family:Caveat,cursive'>"
            "Sistema interno Colsports · acceso restringido</span></div>",
            unsafe_allow_html=True,
        )
        st.markdown('</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------------------------

def render_sidebar():
    p  = THEME["primary"]
    pt = THEME["primary_text"]
    with st.sidebar:
        st.markdown(
            f"<div style='text-align:center;padding:20px 0 12px'>"
            f"<div style='display:inline-flex;align-items:center;justify-content:center;"
            f"width:46px;height:46px;border-radius:50%;background:rgba(255,255,255,0.2);"
            f"border:1.5px solid rgba(255,255,255,0.5);font-size:16px;font-weight:700;"
            f"color:{pt};font-family:Caveat,cursive'>CS</div>"
            f"<div style='font-size:18px;font-weight:700;letter-spacing:0.5px;"
            f"color:{pt};margin-top:8px;font-family:Caveat,cursive'>COLSPORTS</div>"
            f"<div style='font-size:12px;color:rgba(255,255,255,0.6);margin-top:2px;"
            f"font-family:Caveat,cursive'>Sistema de Ventas</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<hr style='border:none;border-top:1px solid rgba(255,255,255,0.2);margin:0 0 8px'>",
            unsafe_allow_html=True,
        )

        icons = {"nueva_venta": "📝", "dashboard": "📊", "inventario": "📦", "compras": "🛒", "ventas": "📋"}
        labels = {
            "nueva_venta": "Nueva Venta",
            "dashboard": "Dashboard",
            "inventario": "Inventario",
            "compras": "Compras",
            "ventas": "Ventas",
        }
        for page, label in labels.items():
            if st.button(f"{icons[page]}  {label}", key=f"nav_{page}",
                         use_container_width=True):
                st.session_state.current_page = page
                st.rerun()

        st.markdown(
            "<hr style='border:none;border-top:1px solid rgba(255,255,255,0.2);margin:8px 0'>",
            unsafe_allow_html=True,
        )

        if st.button("🔒  Cerrar sesión", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.current_page = "nueva_venta"
            st.rerun()

        st.markdown(
            "<div style='position:absolute;bottom:16px;left:0;width:100%;text-align:center;"
            "font-size:11px;color:rgba(255,255,255,0.45);font-family:Caveat,cursive'>"
            "v1.0 · Colsports 2025</div>",
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# PÁGINA: NUEVA VENTA
# ---------------------------------------------------------------------------

def page_new_sale(engine):
    st.markdown('<div class="cs-section-title">📝 Nueva Venta</div>', unsafe_allow_html=True)

    if "sale_msg_v" not in st.session_state:
        st.session_state["sale_msg_v"] = 0
    sale_key = f"sale_msg_{st.session_state['sale_msg_v']}"

    col_left, col_right = st.columns([1, 1], gap="large")

    # ── Left column: form ──
    with col_left:
        st.markdown(
            '<div class="cs-card">',
            unsafe_allow_html=True,
        )
        st.markdown(
            "<div style='font-size:14px;color:#777;margin-bottom:8px;"
            "font-family:Caveat,cursive'>Pega aquí el mensaje de WhatsApp, Rappi o Instagram</div>",
            unsafe_allow_html=True,
        )
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

        st.markdown('</div>', unsafe_allow_html=True)

        if parsear_btn:
            msg = st.session_state.get(sale_key, "").strip()
            if not msg:
                st.warning("Pega un mensaje antes de parsear.")
            else:
                with st.spinner("Procesando con IA..."):
                    try:
                        from api.motor_ia import parse_sale_message, calculate_amounts
                        venta = parse_sale_message(msg)
                        montos = calculate_amounts(venta)
                        st.session_state.parsed_sale = venta
                        st.session_state.sale_montos = montos
                        st.session_state.sale_saved = False
                        st.session_state.last_venta_id = None
                    except Exception as e:
                        st.error(f"Error al parsear: {e}")

    # ── Right column: preview ──
    with col_right:

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
                "<div style='background:#f5f2eb;border:1.5px dashed #d4d0c8;border-radius:2px;"
                "padding:40px;text-align:center;color:#aaa;font-family:Caveat,cursive'>"
                "<div style='font-size:36px'>👈</div>"
                "<div style='margin-top:8px;font-size:15px'>La vista previa aparecerá aquí<br>"
                "después de procesar el mensaje</div>"
                "</div>",
                unsafe_allow_html=True,
            )
            return

        st.markdown('<div class="cs-card">', unsafe_allow_html=True)

        # Canal badge
        canal_color = CANAL_COLORS.get(venta.canal, "#555")
        st.markdown(
            f'<span class="badge" style="color:{canal_color};border-color:{canal_color}">'
            f'{venta.canal}</span>',
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
        st.markdown(
            "<div style='font-size:14px;font-weight:600;color:#555;"
            "font-family:Caveat,cursive;margin-bottom:6px'>🛒 Productos</div>",
            unsafe_allow_html=True,
        )
        for item in venta.items:
            precio = fmt_cop(item.precio_unitario) if item.precio_unitario else "—"
            st.markdown(
                f"<div style='background:#f5f2eb;border:1.5px solid #e0ddd8;border-radius:2px;"
                f"padding:7px 12px;margin:3px 0;font-size:14px;font-family:Caveat,cursive'>"
                f"<b>{item.cantidad}×</b> {item.producto_nombre_raw} "
                f"<span style='float:right;color:#1a1a1a;font-weight:700'>{precio}</span></div>",
                unsafe_allow_html=True,
            )

        # Totals
        st.markdown(
            "<hr style='border:none;border-top:1px solid #e0ddd8;margin:12px 0'>",
            unsafe_allow_html=True,
        )
        mc1, mc2, mc3 = st.columns(3)
        mc1.metric("Bruto", fmt_cop(montos["subtotal"]))
        if montos["costo_envio"]:
            mc2.metric("Envío", fmt_cop(montos["costo_envio"]))
        if montos["comision_monto"]:
            pct = venta.rappi_detalle.comision_porcentaje if venta.rappi_detalle else 0
            mc2.metric("Comisión", fmt_cop(montos["comision_monto"]),
                       delta=f"-{pct:.0f}%", delta_color="inverse")
        mc3.metric("**Neto**", fmt_cop(montos["total"]))

        # Payment
        pago_str = venta.pago.metodo
        if venta.pago.cuenta_destino:
            pago_str += f" › {venta.pago.cuenta_destino}"
        st.markdown(
            f"<div style='font-size:14px;color:#555;font-family:Caveat,cursive;margin-top:4px'>"
            f"💳 <b>Pago:</b> {pago_str}</div>",
            unsafe_allow_html=True,
        )

        # Shipping
        if venta.envio and (venta.envio.ciudad or venta.envio.direccion):
            with st.expander("📦 Dirección de envío"):
                e = venta.envio
                if e.direccion:    st.text(f"Dirección : {e.direccion}")
                if e.ciudad:       st.text(f"Ciudad    : {e.ciudad}")
                if e.departamento: st.text(f"Dpto      : {e.departamento}")

        if venta.notas:
            st.info(f"📝 {venta.notas}")
        if venta.fuente_referido:
            st.markdown(
                f"<div style='font-size:14px;color:#777;font-family:Caveat,cursive'>"
                f"📣 <b>Referido:</b> {venta.fuente_referido}</div>",
                unsafe_allow_html=True,
            )

        st.markdown(
            "<hr style='border:none;border-top:1px solid #e0ddd8;margin:12px 0'>",
            unsafe_allow_html=True,
        )

        # Confirm / cancel buttons
        b1, b2 = st.columns([3, 1])
        with b1:
            if st.button("✅ Confirmar y Guardar", type="primary",
                         use_container_width=True, key="btn_guardar"):
                msg = st.session_state.get(sale_key, "")
                with st.spinner("Guardando en base de datos..."):
                    try:
                        from sqlalchemy.orm import Session as DBSession
                        from api.guardar_venta import save_sale
                        with DBSession(engine) as session:
                            v_guardada = save_sale(session, venta, msg)
                            session.commit()
                            venta_id = v_guardada.id

                        st.session_state.sale_saved = True
                        st.session_state.last_venta_id = venta_id
                        st.session_state["sale_msg_v"] = st.session_state["sale_msg_v"] + 1

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

        st.markdown('</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Shared helper: render a sale detail dict (used in Dashboard and Ventas page)
# ---------------------------------------------------------------------------

def _render_sale_detail(detalle: dict):
    canal_color = CANAL_COLORS.get(detalle["canal"], "#555")
    st.markdown(
        f'<span class="badge" style="color:{canal_color};border-color:{canal_color}">'
        f'{detalle["canal"]}</span>'
        f'&nbsp;<span style="font-size:13px;color:#aaa;font-family:Caveat,cursive">'
        f'#{detalle["id"]} · {detalle["fecha"].strftime("%d/%m/%Y %H:%M") if detalle["fecha"] else "—"}'
        f' · <b>{detalle["estado"]}</b></span>',
        unsafe_allow_html=True,
    )

    # Client
    nombre = detalle["cliente_nombre"] or "—"
    cedula = detalle["cliente_cedula"] or ""
    telefono = detalle["cliente_telefono"] or ""
    st.markdown(
        f'<div style="font-size:13px;color:#777;font-family:Caveat,cursive;margin:4px 0 10px">'
        f'👤 <b>{nombre}</b>'
        f'{" · CC " + cedula if cedula else ""}'
        f'{" · " + telefono if telefono else ""}'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Items
    st.markdown(
        "<div style='font-size:14px;font-weight:600;color:#555;"
        "font-family:Caveat,cursive;margin-bottom:4px'>🛒 Productos</div>",
        unsafe_allow_html=True,
    )
    for it in detalle["items"]:
        nombre_prod = it["nombre_catalogo"] or it["nombre_raw"]
        sku_txt = f' <span style="color:#bbb;font-size:12px">[{it["sku"]}]</span>' if it["sku"] else ""
        precio = fmt_cop(it["precio_unitario"])
        subtotal = fmt_cop(it["subtotal"])
        st.markdown(
            f'<div style="background:#f5f2eb;border:1.5px solid #e0ddd8;border-radius:2px;'
            f'padding:6px 12px;margin:2px 0;font-size:13px;font-family:Caveat,cursive">'
            f'<b>{it["cantidad"]}×</b> {nombre_prod}{sku_txt}'
            f' <span style="float:right;color:#555">{precio} c/u = <b>{subtotal}</b></span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # Totals
    st.markdown(
        "<hr style='border:none;border-top:1px solid #e0ddd8;margin:10px 0'>",
        unsafe_allow_html=True,
    )
    tc1, tc2, tc3 = st.columns(3)
    tc1.metric("Bruto", fmt_cop(detalle["subtotal"]))
    if detalle["costo_envio"]:
        tc2.metric("Envío", fmt_cop(detalle["costo_envio"]))
    if detalle["descuento"]:
        tc2.metric("Descuento", fmt_cop(detalle["descuento"]))
    tc3.metric("Neto", fmt_cop(detalle["total"]))

    # Payment
    for pago in detalle["pagos"]:
        cuenta = f" › {pago['cuenta_destino']}" if pago["cuenta_destino"] else ""
        ref = f" · Ref: {pago['referencia']}" if pago["referencia"] else ""
        st.markdown(
            f'<div style="font-size:13px;color:#555;font-family:Caveat,cursive;margin-top:4px">'
            f'💳 <b>{pago["metodo"]}</b>{cuenta}{ref}</div>',
            unsafe_allow_html=True,
        )

    # Shipping
    if detalle["envio"]:
        e = detalle["envio"]
        partes = [x for x in [e.get("direccion"), e.get("ciudad"), e.get("departamento")] if x]
        if partes:
            st.markdown(
                f'<div style="font-size:13px;color:#555;font-family:Caveat,cursive;margin-top:4px">'
                f'📦 {" · ".join(partes)}</div>',
                unsafe_allow_html=True,
            )

    # Rappi
    if detalle["rappi"]:
        r = detalle["rappi"]
        st.markdown(
            f'<div style="font-size:13px;color:#FF441F;font-family:Caveat,cursive;margin-top:4px">'
            f'🛵 Rappi {r["tipo"]} · Orden {r["order_id"]} · '
            f'Comisión {r["comision_porcentaje"]}% = {fmt_cop(r["comision_monto"] or 0)}</div>',
            unsafe_allow_html=True,
        )

    if detalle["notas"]:
        st.info(f"📝 {detalle['notas']}")

    if detalle["fuente_referido"]:
        st.markdown(
            f'<div style="font-size:13px;color:#777;font-family:Caveat,cursive">📣 Referido: {detalle["fuente_referido"]}</div>',
            unsafe_allow_html=True,
        )

    if detalle["mensaje_original"]:
        with st.expander("📄 Mensaje original"):
            st.text(detalle["mensaje_original"])


# ---------------------------------------------------------------------------
# PÁGINA: DASHBOARD
# ---------------------------------------------------------------------------

def page_dashboard(engine):
    st.markdown(
        '<div class="cs-section-title">📊 Dashboard</div>',
        unsafe_allow_html=True,
    )

    # ── Period selector ──
    st.markdown('<div class="cs-card">', unsafe_allow_html=True)
    if "_dash_start" not in st.session_state:
        st.session_state["_dash_start"] = date.today() - timedelta(days=29)
    if "_dash_end" not in st.session_state:
        st.session_state["_dash_end"] = date.today()

    pd1, pd2 = st.columns(2)
    with pd1:
        start_date = st.date_input("Desde", value=st.session_state["_dash_start"])
        st.session_state["_dash_start"] = start_date
    with pd2:
        end_date = st.date_input("Hasta", value=st.session_state["_dash_end"])
        st.session_state["_dash_end"] = end_date

    qc = st.columns(4)
    for i, (lbl, delta) in enumerate([("Hoy", 0), ("7 días", 6), ("30 días", 29), ("90 días", 89)]):
        if qc[i].button(lbl, key=f"period_{delta}"):
            st.session_state["_dash_start"] = date.today() - timedelta(days=delta)
            st.session_state["_dash_end"] = date.today()
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # ── Load data ──
    kpis      = get_kpis(engine)
    kpis_comp = get_purchase_kpis(engine)
    df_canal  = get_sales_by_channel(engine, start_date, end_date)
    df_tend   = get_daily_trend(engine, start_date, end_date)
    df_top    = get_top_products(engine)
    df_alerr  = get_stock_alerts(engine)

    ventas_neto = kpis["mes"]["neto"]
    costo_mes   = kpis_comp["mes"]["total"]
    margen_mes  = ventas_neto - costo_mes
    pct_margen  = round(margen_mes / ventas_neto * 100, 1) if ventas_neto > 0 else 0.0
    n_alertas   = len(df_alerr)

    # ── KPI row — 4 columns ──
    k1, k2, k3, k4 = st.columns(4)
    k1.markdown(kpi_card(
        "Ventas del Mes", fmt_cop(ventas_neto),
        f"{kpis['mes']['count']} órdenes este mes", "#555",
    ), unsafe_allow_html=True)
    k2.markdown(kpi_card(
        "Inversión en Compras", fmt_cop(costo_mes),
        f"{kpis_comp['mes']['count']} órdenes de compra", "#aaa",
    ), unsafe_allow_html=True)
    k3.markdown(kpi_card(
        "Margen Estimado", f"{pct_margen}%",
        fmt_cop(margen_mes),
        "#5aaa88" if pct_margen >= 0 else "#cc4444",
    ), unsafe_allow_html=True)
    k4.markdown(kpi_card(
        "Alertas de Stock", str(n_alertas),
        "productos por reabastecer",
        "#cc4444" if n_alertas > 0 else "#5aaa88",
    ), unsafe_allow_html=True)

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    # ── Daily trend ──
    st.markdown(
        '<div class="cs-section-title" style="font-size:15px;border-bottom:1px solid #e0ddd8;'
        'margin-bottom:8px">Tendencia Diaria de Ingresos</div>',
        unsafe_allow_html=True,
    )
    st.plotly_chart(chart_tendencia(df_tend), use_container_width=True)

    # ── Channel + Top products ──
    r2a, r2b = st.columns(2, gap="medium")
    with r2a:
        st.markdown(
            '<div class="cs-section-title" style="font-size:15px;border-bottom:1px solid #e0ddd8;'
            'margin-bottom:8px">Distribución por Canal</div>',
            unsafe_allow_html=True,
        )
        st.plotly_chart(chart_ventas_canal(df_canal), use_container_width=True)
    with r2b:
        st.markdown(
            '<div class="cs-section-title" style="font-size:15px;border-bottom:1px solid #e0ddd8;'
            'margin-bottom:8px">Top 10 Productos Más Vendidos</div>',
            unsafe_allow_html=True,
        )
        st.plotly_chart(chart_top_productos(df_top), use_container_width=True)

    # ── Money by account (discreet) ──
    df_cuentas = get_money_by_account(engine, start_date, end_date)
    if not df_cuentas.empty:
        with st.expander("💳 Dinero por cuenta / método de pago", expanded=False):
            st.markdown(
                '<div style="font-size:13px;color:#aaa;font-family:Caveat,cursive;margin-bottom:10px">'
                'Total recibido por método y cuenta destino en el período seleccionado</div>',
                unsafe_allow_html=True,
            )
            cols_cnt = st.columns(min(len(df_cuentas), 4))
            for i, (_, row) in enumerate(df_cuentas.iterrows()):
                col = cols_cnt[i % 4]
                cuenta_label = row["Cuenta"] if row["Cuenta"] else row["Método"]
                metodo_label = row["Método"] if row["Cuenta"] else ""
                total_fmt = f"${int(row['Total']):,}".replace(",", ".")
                col.markdown(
                    f'<div class="cs-card" style="padding:10px 14px;margin-bottom:6px">'
                    f'<div style="font-size:11px;color:#999;font-family:Caveat,cursive">'
                    f'{metodo_label}</div>'
                    f'<div style="font-size:14px;font-weight:700;color:#1a1a1a;font-family:Caveat,cursive">'
                    f'{cuenta_label}</div>'
                    f'<div style="font-size:20px;font-weight:700;color:#5aaa88;font-family:Caveat,cursive">'
                    f'{total_fmt}</div>'
                    f'<div style="font-size:11px;color:#bbb;font-family:Caveat,cursive">'
                    f'{int(row["Ventas"])} ventas</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

    # ── Recent sales ──
    st.markdown(
        '<div class="cs-section-title" style="font-size:15px;border-bottom:1px solid #e0ddd8;'
        'margin-bottom:8px">Últimas Ventas</div>',
        unsafe_allow_html=True,
    )
    df_rec = get_recent_sales(engine, limit=15)
    if df_rec.empty:
        st.markdown(
            '<div style="background:#f5f2eb;border:1.5px dashed #d4d0c8;border-radius:2px;'
            'padding:20px;text-align:center;color:#aaa;font-family:Caveat,cursive">'
            'No hay ventas registradas aún.</div>',
            unsafe_allow_html=True,
        )
    else:
        st.dataframe(df_rec, use_container_width=True, hide_index=True)

    # ── Sale detail viewer ──
    st.markdown(
        '<div class="cs-section-title" style="font-size:15px;border-bottom:1px solid #e0ddd8;'
        'margin-top:16px;margin-bottom:8px">🔍 Ver venta completa</div>',
        unsafe_allow_html=True,
    )
    col_id, col_btn = st.columns([2, 1])
    with col_id:
        venta_id_input = st.number_input(
            "ID de venta", min_value=1, step=1,
            key="dash_venta_id", label_visibility="collapsed",
            placeholder="Ingresa el ID de la venta…",
        )
    with col_btn:
        ver_btn = st.button("Ver detalle", key="dash_ver_venta", use_container_width=True)

    if ver_btn and venta_id_input:
        detalle = get_sale_detail(engine, int(venta_id_input))
        if detalle is None:
            st.warning(f"No existe ninguna venta con ID #{int(venta_id_input)}")
        else:
            _render_sale_detail(detalle)


# ---------------------------------------------------------------------------
# PÁGINA: INVENTARIO Y ALERTAS
# ---------------------------------------------------------------------------

def page_inventory(engine):
    st.markdown('<div class="cs-section-title">📦 Inventario y Alertas</div>', unsafe_allow_html=True)

    tab_inv, tab_alertas, tab_combos, tab_hot = st.tabs(
        ["📋 Catálogo", "🚨 Alertas de stock", "🧩 Combos", "🔥 Hot Products"]
    )

    # ── Tab 1: Catálogo ──
    with tab_inv:
        search = st.text_input("🔍 Buscar producto (nombre, SKU, marca, categoría)",
                               key="inv_search", placeholder="Ej: creatina, 1013, IMN…")
        df_inv = get_inventory(engine, search)

        if df_inv.empty:
            st.markdown(
                '<div style="background:#f5f2eb;border:1.5px dashed #d4d0c8;border-radius:2px;'
                'padding:20px;text-align:center;color:#aaa;font-family:Caveat,cursive">'
                'No se encontraron productos.</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div style="font-size:13px;color:#aaa;font-family:Caveat,cursive;'
                f'margin-bottom:8px">{len(df_inv)} productos encontrados</div>',
                unsafe_allow_html=True,
            )

            def _style_stock(val):
                if val < 0:
                    return "background-color:#fff0ee;color:#cc4444;font-weight:700"
                if val <= 3:
                    return "background-color:#fff8f2;color:#aa8844;font-weight:600"
                if val > 10:
                    return "background-color:#f0f9f4;color:#5aaa88"
                return ""

            styled = df_inv.style.applymap(_style_stock, subset=["Stock"])
            st.dataframe(styled, use_container_width=True, hide_index=True)

    # ── Tab 2: Alertas ──
    with tab_alertas:
        df_negativos = get_stock_alerts(engine, umbral=-1)

        st.markdown(
            '<div class="cs-section-title" style="font-size:17px;border-bottom:1px solid #e0ddd8;'
            'margin-bottom:12px">🔴 Stock negativo</div>',
            unsafe_allow_html=True,
        )
        if df_negativos.empty:
            st.markdown(
                '<div style="background:#f0f9f4;border:1.5px solid #5aaa88;border-radius:2px;'
                'padding:10px 16px;font-family:Caveat,cursive;color:#3a7a58">'
                '✓ No hay productos con stock negativo.</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div style="background:#fff0ee;border:1.5px solid #cc4444;border-radius:2px;'
                f'padding:10px 16px;font-family:Caveat,cursive;color:#cc4444;margin-bottom:8px">'
                f'❗ {len(df_negativos)} productos con stock negativo — reposición urgente</div>',
                unsafe_allow_html=True,
            )
            for _, row in df_negativos.iterrows():
                st.markdown(
                    f'<div class="cs-alert">'
                    f'🔴 <b>[{row["SKU"]}]</b> {row["Nombre"]} '
                    f'— <span style="color:#cc4444;font-weight:700">Stock: {row["Stock"]}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

        st.markdown(
            "<hr style='border:none;border-top:1px solid #e0ddd8;margin:16px 0'>",
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="cs-section-title" style="font-size:17px;border-bottom:1px solid #e0ddd8;'
            'margin-bottom:12px">🟡 Stock bajo</div>',
            unsafe_allow_html=True,
        )
        umbral = st.slider("Mostrar productos con stock entre 0 y:", 1, 10, 5,
                           key="umbral_alerta")
        df_bajo = get_stock_alerts(engine, umbral=umbral)
        df_bajo = df_bajo[df_bajo["Stock"] >= 0]

        if df_bajo.empty:
            st.markdown(
                f'<div style="background:#f0f9f4;border:1.5px solid #5aaa88;border-radius:2px;'
                f'padding:10px 16px;font-family:Caveat,cursive;color:#3a7a58">'
                f'✓ No hay productos con stock entre 0 y {umbral}.</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div style="background:#fffaf2;border:1.5px solid #c8a070;border-radius:2px;'
                f'padding:10px 16px;font-family:Caveat,cursive;color:#aa8844;margin-bottom:8px">'
                f'⚠️ {len(df_bajo)} productos con stock entre 0 y {umbral}</div>',
                unsafe_allow_html=True,
            )
            for _, row in df_bajo.iterrows():
                st.markdown(
                    f'<div class="cs-alert-amber">'
                    f'🟡 <b>[{row["SKU"]}]</b> {row["Nombre"]} '
                    f'— <span style="color:#aa8844;font-weight:700">Stock: {row["Stock"]}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

        st.markdown(
            "<hr style='border:none;border-top:1px solid #e0ddd8;margin:16px 0'>",
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="cs-section-title" style="font-size:17px;border-bottom:1px solid #e0ddd8;'
            'margin-bottom:12px">📋 Pedidos sin stock</div>',
            unsafe_allow_html=True,
        )
        df_sin = get_orders_without_stock(engine)
        if df_sin.empty:
            st.markdown(
                '<div style="background:#f0f9f4;border:1.5px solid #5aaa88;border-radius:2px;'
                'padding:10px 16px;font-family:Caveat,cursive;color:#3a7a58">'
                '✓ No hay pedidos pendientes por reponer.</div>',
                unsafe_allow_html=True,
            )
        else:
            st.dataframe(df_sin, use_container_width=True, hide_index=True)

    # ── Tab 3: Combos ──
    with tab_combos:
        st.markdown(
            '<div class="cs-section-title" style="font-size:17px;border-bottom:1px solid #e0ddd8;'
            'margin-bottom:8px">🧩 Stock Virtual de Combos</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div style="font-size:13px;color:#aaa;font-family:Caveat,cursive;margin-bottom:12px">'
            'Stock virtual = cuántas unidades del combo se pueden armar con el stock actual '
            'de cada componente. El cuello de botella es el componente más escaso.</div>',
            unsafe_allow_html=True,
        )
        df_combos = get_combo_virtual_stock(engine)
        if df_combos.empty:
            st.markdown(
                '<div style="background:#f5f2eb;border:1.5px dashed #d4d0c8;border-radius:2px;'
                'padding:20px;text-align:center;color:#aaa;font-family:Caveat,cursive">'
                'No hay combos registrados aún. Agrega filas en combo_componentes para que '
                'aparezcan aquí.</div>',
                unsafe_allow_html=True,
            )
        else:
            def _style_combo_stock(val):
                if val <= 0:
                    return "background-color:#fff0ee;color:#cc4444;font-weight:700"
                if val <= 3:
                    return "background-color:#fff8f2;color:#aa8844;font-weight:600"
                return "background-color:#f0f9f4;color:#5aaa88"

            styled_combos = df_combos.style.applymap(_style_combo_stock, subset=["Stock Virtual"])
            st.dataframe(styled_combos, use_container_width=True, hide_index=True)

        st.markdown(
            "<hr style='border:none;border-top:1px solid #e0ddd8;margin:16px 0'>",
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="cs-section-title" style="font-size:17px;border-bottom:1px solid #e0ddd8;'
            'margin-bottom:12px">⚠️ Alertas de componentes faltantes</div>',
            unsafe_allow_html=True,
        )
        mostrar_resueltas = st.checkbox("Incluir alertas ya resueltas", key="chk_resueltas")
        df_alertas = get_order_alerts(engine, solo_pendientes=not mostrar_resueltas)

        if df_alertas.empty:
            st.markdown(
                '<div style="background:#f0f9f4;border:1.5px solid #5aaa88;border-radius:2px;'
                'padding:10px 16px;font-family:Caveat,cursive;color:#3a7a58">'
                '✓ No hay alertas de componentes pendientes.</div>',
                unsafe_allow_html=True,
            )
        else:
            for _, row in df_alertas.iterrows():
                resuelta = bool(row["Resuelta"])
                if resuelta:
                    card_style = ('background:#f0f9f4;border:1.5px solid #5aaa88;'
                                  'border-radius:2px;padding:8px 14px;margin:4px 0;'
                                  'font-family:Caveat,cursive')
                else:
                    card_style = ('background:#fff8f2;border:1.5px solid #c89070;'
                                  'border-radius:2px;padding:8px 14px;margin:4px 0;'
                                  'font-family:Caveat,cursive')
                estado_txt = "✅ Resuelta" if resuelta else "🔴 Pendiente"
                col_info, col_btn = st.columns([5, 1])
                with col_info:
                    st.markdown(
                        f'<div style="{card_style}">'
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
                            mark_alert_resolved(engine, int(row["ID"]))
                            get_alertas_pedido.clear()
                            st.rerun()

    # ── Tab 4: Hot Products ──
    with tab_hot:
        st.markdown(
            '<div class="cs-section-title" style="font-size:17px;border-bottom:1px solid #e0ddd8;'
            'margin-bottom:12px">🔥 Top 5 productos más vendidos</div>',
            unsafe_allow_html=True,
        )
        df_hot = get_top_products(engine, limit=5)
        if df_hot.empty:
            st.markdown(
                '<div style="background:#f5f2eb;border:1.5px dashed #d4d0c8;border-radius:2px;'
                'padding:20px;text-align:center;color:#aaa;font-family:Caveat,cursive">'
                'No hay datos de ventas aún.</div>',
                unsafe_allow_html=True,
            )
        else:
            medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
            for i, (_, row) in enumerate(df_hot.iterrows(), 1):
                medal = medals[i - 1]
                st.markdown(
                    f'<div style="background:#fffef9;border:1.5px solid #d4d0c8;border-radius:2px;'
                    f'box-shadow:2px 3px 0 #e8e4dc;padding:10px 16px;margin:6px 0;'
                    f'display:flex;align-items:center;justify-content:space-between;'
                    f'font-family:Caveat,cursive">'
                    f'<span style="font-size:16px">{medal} <b>{row["Producto"][:50]}</b></span>'
                    f'<span style="color:#aaa;font-size:13px">{int(row["Unidades"])} uds</span>'
                    f'<span style="color:#5aaa88;font-weight:700;font-size:15px">'
                    f'{fmt_cop(row["Ingresos"])}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )


# ---------------------------------------------------------------------------
# PÁGINA: COMPRAS E INGRESO DE MERCANCÍA
# ---------------------------------------------------------------------------

def page_purchases(engine):
    st.markdown('<div class="cs-section-title">🛒 Compras e Ingreso de Mercancía</div>',
                unsafe_allow_html=True)

    if "purchase_msg_v" not in st.session_state:
        st.session_state["purchase_msg_v"] = 0
    purchase_key = f"purchase_msg_{st.session_state['purchase_msg_v']}"

    tab_nueva, tab_historial = st.tabs(["📥 Nueva Compra", "📋 Historial"])

    # ── Tab 1: Nueva compra ──
    with tab_nueva:
        col_left, col_right = st.columns([1, 1.3], gap="large")

        with col_left:
            st.markdown('<div class="cs-card">', unsafe_allow_html=True)
            st.markdown(
                "<div style='font-size:14px;color:#777;margin-bottom:8px;"
                "font-family:Caveat,cursive'>Pega aquí el mensaje del proveedor o lista de productos</div>",
                unsafe_allow_html=True,
            )
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

            st.markdown('</div>', unsafe_allow_html=True)

            if analizar_btn:
                msg = st.session_state.get(purchase_key, "").strip()
                if not msg:
                    st.warning("Pega un mensaje antes de analizar.")
                else:
                    with st.spinner("Procesando con IA..."):
                        try:
                            from api.purchase_parser import parse_purchase
                            compra_parsed = parse_purchase(msg)
                            st.session_state["parsed_compra"] = compra_parsed
                            st.session_state.pop("compra_guardada", None)
                            st.session_state.pop("last_compra_id", None)
                        except Exception as e:
                            st.error(f"Error al analizar: {e}")

        with col_right:
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
                    "<div style='background:#f5f2eb;border:1.5px dashed #d4d0c8;border-radius:2px;"
                    "padding:40px;text-align:center;color:#aaa;font-family:Caveat,cursive'>"
                    "<div style='font-size:36px'>👈</div>"
                    "<div style='margin-top:8px;font-size:15px'>La tabla de revisión aparecerá aquí<br>"
                    "después de analizar el mensaje</div></div>",
                    unsafe_allow_html=True,
                )

            else:
                compra_parsed = st.session_state["parsed_compra"]

                proveedor = st.text_input(
                    "Proveedor", value=compra_parsed.proveedor or "",
                    key="compra_proveedor", placeholder="Nombre del proveedor"
                )

                catalogo = get_sku_catalog(engine)
                skus_disponibles = [""] + [f"{p['sku']} — {p['nombre']}" for p in catalogo]
                sku_map = {"": None}
                for p in catalogo:
                    sku_map[f"{p['sku']} — {p['nombre']}"] = p["sku"]

                from api.guardar_venta import _match_sku as _buscar_sku
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

                st.markdown(
                    '<div class="cs-section-title" style="font-size:16px;'
                    'border-bottom:1px solid #e0ddd8;margin-bottom:6px">'
                    'Revisar y ajustar productos detectados</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    '<div style="font-size:13px;color:#aaa;font-family:Caveat,cursive;'
                    'margin-bottom:8px">Edita el SKU, cantidad o costo antes de confirmar. '
                    'Solo se suma stock a los productos con SKU asignado.</div>',
                    unsafe_allow_html=True,
                )

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

                try:
                    total_est = int(
                        (df_resultado["Cantidad"] * df_resultado["Costo unitario (COP)"].fillna(0)).sum()
                    )
                    total_fmt = f"${total_est:,}".replace(",", ".")
                    st.markdown(
                        f"<div style='text-align:right;font-size:16px;color:#555;"
                        f"font-family:Caveat,cursive;margin-top:8px'>"
                        f"<b>Total estimado:</b> "
                        f"<span style='color:#1a1a1a;font-weight:700'>{total_fmt}</span>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
                except Exception:
                    pass

                st.markdown(
                    "<hr style='border:none;border-top:1px solid #e0ddd8;margin:12px 0'>",
                    unsafe_allow_html=True,
                )

                if st.button(
                    "✅ Confirmar e Ingresar a Inventario",
                    type="primary",
                    use_container_width=True,
                    key="btn_confirmar_compra",
                ):
                    with st.spinner("Guardando compra y actualizando stock..."):
                        try:
                            df_save = df_resultado.copy()

                            # Normalise SKU column — replace None/NaN with ""
                            df_save["SKU en catálogo"] = df_save["SKU en catálogo"].fillna("")

                            df_save["sku"] = df_save["SKU en catálogo"].map(
                                lambda v: sku_map.get(str(v).strip(), None) if str(v).strip() else None
                            )
                            df_save = df_save.rename(columns={
                                "Producto (del proveedor)": "producto_nombre_raw",
                                "Cantidad": "cantidad",
                                "Costo unitario (COP)": "precio_costo_unitario",
                            })[["producto_nombre_raw", "sku", "cantidad", "precio_costo_unitario"]]

                            # Drop rows that are empty or came from accidental selection
                            df_save = df_save.dropna(subset=["producto_nombre_raw"])
                            df_save = df_save[df_save["producto_nombre_raw"].astype(str).str.strip() != ""]
                            df_save = df_save.dropna(subset=["cantidad"])
                            df_save["cantidad"] = pd.to_numeric(df_save["cantidad"], errors="coerce")
                            df_save = df_save[df_save["cantidad"].notna() & (df_save["cantidad"] > 0)]
                            df_save["cantidad"] = df_save["cantidad"].astype(int)

                            if df_save.empty:
                                st.warning("No hay filas válidas. Revisa que cada producto tenga nombre y cantidad > 0.")
                            else:
                                from sqlalchemy.orm import Session as DBSession2
                                from api.guardar_compra import save_purchase
                                with DBSession2(engine) as session:
                                    compra_obj = save_purchase(
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

    # ── Tab 2: Historial ──
    with tab_historial:
        st.markdown(
            '<div class="cs-section-title" style="font-size:17px;border-bottom:1px solid #e0ddd8;'
            'margin-bottom:12px">Últimas 20 compras registradas</div>',
            unsafe_allow_html=True,
        )
        df_hist = get_recent_purchases(engine)
        if df_hist.empty:
            st.markdown(
                '<div style="background:#f5f2eb;border:1.5px dashed #d4d0c8;border-radius:2px;'
                'padding:20px;text-align:center;color:#aaa;font-family:Caveat,cursive">'
                'No hay compras registradas aún.</div>',
                unsafe_allow_html=True,
            )
        else:
            st.dataframe(df_hist, use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------------
# PÁGINA: VENTAS (Historial + Auditador/Corrector)
# ---------------------------------------------------------------------------

def page_sales(engine):
    st.markdown('<div class="cs-section-title">📋 Ventas</div>', unsafe_allow_html=True)

    tab_hist, tab_editor = st.tabs(["📜 Historial", "✏️ Editar venta"])

    # ── Tab 1: Historial filtrable ──
    with tab_hist:
        st.markdown('<div class="cs-card">', unsafe_allow_html=True)
        fc1, fc2, fc3, fc4 = st.columns([1, 1, 1, 1])
        with fc1:
            f_start = st.date_input("Desde", value=date.today() - timedelta(days=29), key="sv_start")
        with fc2:
            f_end = st.date_input("Hasta", value=date.today(), key="sv_end")
        with fc3:
            estados_opts = ["Todos"] + [e.value for e in __import__("models", fromlist=["EstadoVenta"]).EstadoVenta]
            f_estado = st.selectbox("Estado", estados_opts, key="sv_estado")
        with fc4:
            canales_opts = ["Todos"] + list(CANAL_COLORS.keys())
            f_canal = st.selectbox("Canal", canales_opts, key="sv_canal")
        st.markdown('</div>', unsafe_allow_html=True)

        df_ventas = get_all_sales(
            engine,
            f_start, f_end,
            estado=None if f_estado == "Todos" else f_estado,
            canal_nombre=None if f_canal == "Todos" else f_canal,
        )

        if df_ventas.empty:
            st.markdown(
                '<div style="background:#f5f2eb;border:1.5px dashed #d4d0c8;border-radius:2px;'
                'padding:20px;text-align:center;color:#aaa;font-family:Caveat,cursive">'
                'No hay ventas con esos filtros.</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div style="font-size:13px;color:#aaa;font-family:Caveat,cursive;margin-bottom:8px">'
                f'{len(df_ventas)} ventas encontradas</div>',
                unsafe_allow_html=True,
            )
            cols_show = ["ID", "Fecha", "Canal", "Cliente", "Bruto", "Total", "Estado", "Pago", "Cuenta"]
            st.dataframe(df_ventas[cols_show], use_container_width=True, hide_index=True)

            # Quick detail viewer inline
            st.markdown(
                "<div style='font-size:13px;color:#aaa;font-family:Caveat,cursive;margin-top:12px'>"
                "Ingresa un ID de la lista para ver el detalle completo:</div>",
                unsafe_allow_html=True,
            )
            sv_id = st.number_input("ID venta (historial)", min_value=1, step=1, key="sv_hist_id",
                                    label_visibility="collapsed")
            if st.button("Ver detalle", key="sv_hist_ver"):
                detalle = get_sale_detail(engine, int(sv_id))
                if detalle is None:
                    st.warning(f"No existe venta #{int(sv_id)}")
                else:
                    with st.container():
                        st.markdown('<div class="cs-card">', unsafe_allow_html=True)
                        _render_sale_detail(detalle)
                        st.markdown('</div>', unsafe_allow_html=True)

    # ── Tab 2: Editar / corregir venta ──
    with tab_editor:
        st.markdown(
            '<div style="font-size:14px;color:#777;font-family:Caveat,cursive;margin-bottom:12px">'
            'Busca una venta por ID para corregir su estado o agregar/editar notas.</div>',
            unsafe_allow_html=True,
        )

        ec1, ec2 = st.columns([1, 2])
        with ec1:
            edit_id = st.number_input("ID de la venta a editar", min_value=1, step=1,
                                      key="sv_edit_id", label_visibility="visible")
            buscar_btn = st.button("🔍 Buscar", key="sv_buscar_btn", use_container_width=True)

        if buscar_btn:
            st.session_state["sv_detalle_edit"] = get_sale_detail(engine, int(edit_id))

        detalle_edit = st.session_state.get("sv_detalle_edit")

        if detalle_edit is None and buscar_btn:
            st.warning(f"No existe venta #{int(edit_id)}")
        elif detalle_edit:
            st.markdown('<div class="cs-card">', unsafe_allow_html=True)
            _render_sale_detail(detalle_edit)
            st.markdown("<hr style='border:none;border-top:1px solid #e0ddd8;margin:14px 0'>", unsafe_allow_html=True)

            st.markdown(
                "<div style='font-size:16px;font-weight:700;color:#1a1a1a;"
                "font-family:Caveat,cursive;margin-bottom:10px'>✏️ Editar</div>",
                unsafe_allow_html=True,
            )
            from models import EstadoVenta as _EstadoVenta
            estados_list = [e.value for e in _EstadoVenta]
            current_estado = detalle_edit["estado"].value if hasattr(detalle_edit["estado"], "value") else str(detalle_edit["estado"])
            new_estado = st.selectbox(
                "Estado de la venta",
                estados_list,
                index=estados_list.index(current_estado) if current_estado in estados_list else 0,
                key="sv_new_estado",
            )
            new_notas = st.text_area(
                "Notas",
                value=detalle_edit["notas"] or "",
                key="sv_new_notas",
                placeholder="Observaciones, correcciones, motivo del cambio…",
                height=90,
            )

            if st.button("💾 Guardar cambios", type="primary", key="sv_guardar_edit"):
                update_sale(engine, detalle_edit["id"], new_estado, new_notas or None)
                get_sale_detail.clear()
                get_all_sales.clear()
                get_ventas_recientes.clear()
                get_kpis.clear()
                st.session_state.pop("sv_detalle_edit", None)
                st.success(f"✅ Venta #{detalle_edit['id']} actualizada: estado → {new_estado}")
                st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)


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
        page_new_sale(engine)
    elif page == "dashboard":
        page_dashboard(engine)
    elif page == "inventario":
        page_inventory(engine)
    elif page == "compras":
        page_purchases(engine)
    elif page == "ventas":
        page_sales(engine)


if __name__ == "__main__":
    main()
