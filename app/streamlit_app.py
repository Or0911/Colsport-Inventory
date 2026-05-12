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
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');

html, body, [class*="css"], .stApp {
    font-family: 'Poppins', sans-serif !important;
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
    font-family: 'Poppins', sans-serif !important;
}
[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,0.2) !important;
}
[data-testid="stSidebar"] .stButton > button {
    width: 100%;
    background: rgba(255,255,255,0.88) !important;
    color: var(--cs-primary) !important;
    border: none !important;
    border-radius: 6px !important;
    text-align: left !important;
    padding: 10px 14px !important;
    font-size: 14px !important;
    font-family: 'Poppins', sans-serif !important;
    font-weight: 500 !important;
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

/* Hide keyboard shortcut label that Streamlit 1.35+ injects inside the toggle button */
[data-testid="stSidebarCollapseButton"] p,
[data-testid="stSidebarCollapseButton"] span {
    display: none !important;
}

/* Collapse button INSIDE the open sidebar — icon must be white over dark bg */
[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] button {
    background: transparent !important;
    border: none !important;
}
[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] button:hover {
    background: var(--cs-primary-dark) !important;
}
[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] svg {
    stroke: var(--cs-primary-text) !important;
    fill: var(--cs-primary-text) !important;
}

/* Expand button that appears in the header when sidebar is COLLAPSED.
   No pointer-events manipulation: Streamlit's layout already places the header
   above (not overlapping) the main content, so clicks reach content normally. */
[data-testid="stHeader"] [data-testid="stSidebarCollapseButton"] button {
    background: var(--cs-primary) !important;
    border: none !important;
    border-radius: 6px !important;
    padding: 6px !important;
    opacity: 1 !important;
    visibility: visible !important;
    display: flex !important;
}
[data-testid="stHeader"] [data-testid="stSidebarCollapseButton"] button:hover {
    background: var(--cs-primary-dark) !important;
}
[data-testid="stHeader"] [data-testid="stSidebarCollapseButton"] svg {
    stroke: var(--cs-primary-text) !important;
    fill: var(--cs-primary-text) !important;
}

/* Primary button */
.stButton > button[kind="primary"],
.stButton > button[data-testid="baseButton-primary"] {
    background-color: var(--cs-primary) !important;
    color: var(--cs-primary-text) !important;
    border: 2px solid var(--cs-primary-dark) !important;
    border-radius: 6px !important;
    font-family: 'Poppins', sans-serif !important;
    font-size: 14px !important;
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
    border-radius: 6px !important;
    font-family: 'Poppins', sans-serif !important;
    font-size: 13px !important;
}

/* Cards */
.cs-card {
    background: #fffef9;
    border: 1.5px solid #d4d0c8;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    padding: 16px 18px;
    margin-bottom: 12px;
}

/* Section titles */
.cs-section-title {
    font-size: 18px;
    font-weight: 700;
    color: #1a1a1a;
    padding-bottom: 8px;
    border-bottom: 2px solid #d4d0c8;
    margin-bottom: 20px;
    font-family: 'Poppins', sans-serif;
}

/* KPI components */
.cs-kpi-label { font-size: 12px; color: #999; font-family: 'Poppins', sans-serif; }
.cs-kpi-value { font-size: 22px; font-weight: 700; color: #1a1a1a; font-family: 'Poppins', sans-serif; line-height: 1.2; }
.cs-kpi-sub   { font-size: 12px; color: #aaa; font-family: 'Poppins', sans-serif; margin-top: 4px; }

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
    border-radius: 6px;
    padding: 8px 14px;
    margin: 4px 0;
    font-family: 'Poppins', sans-serif;
}
.cs-alert-amber {
    background: #fffaf2;
    border: 1.5px solid #c8a070;
    border-radius: 6px;
    padding: 8px 14px;
    margin: 4px 0;
    font-family: 'Poppins', sans-serif;
}

/* Canal badge */
.badge {
    display: inline-block;
    padding: 3px 12px;
    border-radius: 20px;
    border: 1.5px solid currentColor;
    font-size: 12px;
    font-weight: 600;
    font-family: 'Poppins', sans-serif;
    margin-bottom: 12px;
}

/* Inputs */
.stTextInput input, .stTextArea textarea {
    font-family: 'Poppins', sans-serif !important;
    background: #fffef9 !important;
    border: 1.5px solid #ccc !important;
    border-radius: 6px !important;
    color: #333 !important;
}

/* Tabs */
.stTabs [data-baseweb="tab"] {
    font-family: 'Poppins', sans-serif !important;
    font-size: 14px !important;
    color: #777 !important;
}
.stTabs [aria-selected="true"] {
    color: #1a1a1a !important;
    border-bottom-color: #1a1a1a !important;
}

/* Dataframe */
.stDataFrame { background: #fffef9 !important; }

/* Header: transparent so it doesn't show Streamlit branding.
   Kept in the DOM (not display:none) so the sidebar expand button remains accessible. */
[data-testid="stHeader"] {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}
/* Hide Streamlit chrome elements */
[data-testid="stToolbar"] { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }
#MainMenu { display: none !important; }
footer { display: none !important; }
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
    get_sale_detail, get_money_by_account, get_all_sales, update_sale_items,
    get_kpis_period, get_purchase_detail, update_purchase_items,
    # client analysis
    get_shipping_departments, get_client_stats, get_client_category_breakdown,
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
EDIT_WINDOW_HOURS = 24


def fmt_cop(v) -> str:
    try:
        return f"${int(v):,}".replace(",", ".")
    except Exception:
        return str(v)


def _is_editable(fecha) -> bool:
    """Returns True if the record is within the allowed edit window."""
    if fecha is None:
        return False
    from datetime import datetime, timedelta
    if not isinstance(fecha, datetime):
        fecha = datetime.combine(fecha, datetime.min.time())
    return datetime.now() - fecha < timedelta(hours=EDIT_WINDOW_HOURS)


def init_session():
    defaults = {
        "authenticated": False,
        "current_page": "ventas",
        "sale_saved": False,
        "parsed_sale": None,
        "sale_montos": None,
        "last_venta_id": None,
        "sale_parse_v": 0,   # increments each time a new sale is parsed → resets the items editor
        "sv_detalle_edit": None,
        "sv_editing_id": None,
        "ep_detalle_edit": None,
        "ep_editing_id": None,
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
    "Página Web":  "#e67e22",
}


# ---------------------------------------------------------------------------
# LOGIN
# ---------------------------------------------------------------------------

def page_login():
    st.markdown("""
    <style>
    .login-feature { font-size: 17px; color: #666; font-family: 'Poppins', sans-serif; margin: 6px 0; }
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
        st.markdown("<br><br>", unsafe_allow_html=True)
        _logo_login = os.path.join(_root, "assets", "logo.png")
        if os.path.exists(_logo_login):
            st.image(_logo_login, width=220)
        else:
            st.markdown(
                "<div style='font-size:40px;font-weight:700;color:#1a1a1a;"
                "font-family:Poppins,sans-serif;letter-spacing:-1px'>Colsports</div>",
                unsafe_allow_html=True,
            )
        st.markdown(
            "<div style='font-size:16px;color:#888;font-family:Poppins,sans-serif;"
            "margin-top:6px'>Sistema de Ventas & Inventario</div>",
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

        # Embed logo as base64 so it renders inside the HTML card block
        import base64 as _b64
        _logo_login = os.path.join(_root, "assets", "logo.png")
        if os.path.exists(_logo_login):
            with open(_logo_login, "rb") as _lf:
                _logo_b64 = _b64.b64encode(_lf.read()).decode()
            _logo_img_html = (
                f"<img src='data:image/png;base64,{_logo_b64}' "
                "style='width:160px;display:block;margin:0 auto 20px;'>"
            )
        else:
            _logo_img_html = (
                "<div style='font-size:24px;font-weight:700;color:#1a3a5c;"
                "font-family:Poppins,sans-serif;text-align:center;margin-bottom:16px'>"
                "COL SPORTS</div>"
            )

        st.markdown(
            f"<div class='login-card'>"
            f"{_logo_img_html}"
            "<div style='font-size:28px;font-weight:700;color:#1a1a1a;"
            "font-family:Poppins,sans-serif;text-align:center;margin-bottom:4px'>Bienvenido</div>"
            "<div style='font-size:15px;color:#999;font-family:Poppins,sans-serif;"
            "text-align:center;margin-bottom:20px'>Ingresa la contraseña de acceso</div>"
            "<hr style='border:none;border-top:1px solid #e8e4dc;margin-bottom:0'>"
            "</div>",
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
            "<span style='font-size:12px;color:#bbb;font-family:Poppins,sans-serif'>"
            "Sistema interno Colsports · acceso restringido</span></div>",
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------------------------

def render_sidebar():
    p  = THEME["primary"]
    pt = THEME["primary_text"]
    with st.sidebar:
        _logo = os.path.join(_root, "assets", "logo.png")
        st.markdown("<div style='text-align:center;padding:16px 0 8px'>", unsafe_allow_html=True)
        if os.path.exists(_logo):
            st.image(_logo, width=150)
        else:
            st.markdown(
                f"<div style='font-size:20px;font-weight:700;letter-spacing:0.5px;"
                f"color:{pt};font-family:Poppins,sans-serif'>COLSPORTS</div>",
                unsafe_allow_html=True,
            )
        st.markdown(
            f"<div style='font-size:11px;color:rgba(255,255,255,0.6);margin-top:2px;"
            f"font-family:Poppins,sans-serif;padding-bottom:8px'>Sistema de Ventas</div>",
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown(
            "<hr style='border:none;border-top:1px solid rgba(255,255,255,0.2);margin:0 0 8px'>",
            unsafe_allow_html=True,
        )

        icons = {
            "dashboard":  "📊",
            "inventario": "📦",
            "compras":    "🛒",
            "ventas":     "📋",
            "clientes":   "👥",
            "busqueda":   "🔍",
            "admin":      "⚙️",
        }
        labels = {
            "dashboard":  "Dashboard",
            "inventario": "Inventario",
            "compras":    "Compras",
            "ventas":     "Ventas",
            "clientes":   "Análisis Clientes",
            "busqueda":   "Búsqueda Producto",
            "admin":      "Admin / Logs",
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
            st.session_state.current_page = "ventas"
            st.rerun()

        st.markdown(
            "<div style='position:absolute;bottom:16px;left:0;width:100%;text-align:center;"
            "font-size:11px;color:rgba(255,255,255,0.45);font-family:Poppins,sans-serif'>"
            "v1.0 · Colsports 2025</div>",
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# PÁGINA: NUEVA VENTA
# ---------------------------------------------------------------------------

def _render_new_sale_content(engine):
    """Renders the new-sale form. Called from within the Ventas page tabs."""
    if "sale_msg_v" not in st.session_state:
        st.session_state["sale_msg_v"] = 0
    sale_key = f"sale_msg_{st.session_state['sale_msg_v']}"

    col_left, col_right = st.columns([1, 1], gap="large")

    # ── Left column: form ──
    with col_left:
        st.markdown(
            "<div style='font-size:13px;color:#777;margin-bottom:6px;"
            "font-family:Poppins,sans-serif'>Pega aquí el mensaje de WhatsApp, Rappi o Instagram</div>",
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
                        # Increment to reset the items editor for the new parsed sale
                        st.session_state["sale_parse_v"] = st.session_state.get("sale_parse_v", 0) + 1
                    except Exception as e:
                        st.error(f"Error al parsear: {e}")

    # ── Right column: editable preview ──
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

        if venta is None:
            st.markdown(
                "<div style='background:#f5f2eb;border:1.5px dashed #d4d0c8;border-radius:2px;"
                "padding:40px;text-align:center;color:#aaa;font-family:Poppins,sans-serif'>"
                "<div style='font-size:36px'>👈</div>"
                "<div style='margin-top:8px;font-size:15px'>La vista previa aparecerá aquí<br>"
                "después de procesar el mensaje</div>"
                "</div>",
                unsafe_allow_html=True,
            )
            return

        parse_v = st.session_state.get("sale_parse_v", 0)

        # ── Canal (editable) ──
        all_canales = list(CANAL_COLORS.keys())
        if venta.canal not in all_canales:
            all_canales = [venta.canal] + all_canales
        edited_canal = st.selectbox(
            "Canal",
            all_canales,
            index=all_canales.index(venta.canal),
            key=f"nv_canal_{parse_v}",
        )
        canal_color = CANAL_COLORS.get(edited_canal, "#555")
        st.markdown(
            f'<span class="badge" style="color:{canal_color};border-color:{canal_color};'
            f'margin-bottom:4px">{edited_canal}</span>',
            unsafe_allow_html=True,
        )

        # ── Cliente (editable) ──
        with st.expander("👤 Cliente", expanded=bool(venta.cliente)):
            c = venta.cliente
            cli_c1, cli_c2 = st.columns(2)
            c_nombre = cli_c1.text_input("Nombre", value=c.nombre if c else "",
                                          key=f"nv_c_nom_{parse_v}")
            c_cedula = cli_c2.text_input("CC", value=(c.cedula or "") if c else "",
                                          key=f"nv_c_cc_{parse_v}")
            c_tel = cli_c1.text_input("Teléfono", value=(c.telefono or "") if c else "",
                                       key=f"nv_c_tel_{parse_v}")
            c_email = cli_c2.text_input("Email", value=(c.email or "") if c else "",
                                         key=f"nv_c_email_{parse_v}")

        # ── Productos (editable con SKU matching) ──
        st.markdown(
            "<div style='font-size:13px;font-weight:600;color:#555;"
            "font-family:Poppins,sans-serif;margin:6px 0 2px'>🛒 Productos</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<div style='font-size:12px;color:#aaa;font-family:Poppins,sans-serif;margin-bottom:6px'>"
            "Edita SKU, cantidad o precio antes de confirmar. Solo descuenta stock a los ítems con SKU.</div>",
            unsafe_allow_html=True,
        )

        import pandas as _pd_nv
        from api.guardar_venta import _match_sku as _nv_match
        from sqlalchemy.orm import Session as _NVSess
        from models import Producto as _NVProd
        from sqlalchemy import select as _nv_sel

        catalogo_nv = get_sku_catalog(engine)
        skus_nv = [""] + [f"{p['sku']} — {p['nombre']}" for p in catalogo_nv]
        sku_map_nv = {"": None}
        for p in catalogo_nv:
            sku_map_nv[f"{p['sku']} — {p['nombre']}"] = p["sku"]
        sku_display_nv = {p["sku"]: f"{p['sku']} — {p['nombre']}" for p in catalogo_nv}

        with _NVSess(engine) as _nv_s:
            _nv_catalog = _nv_s.execute(_nv_sel(_NVProd)).scalars().all()

        rows_nv = []
        suggested_skus_nv = {}
        for item in venta.items:
            sku_sug = _nv_match(_nv_catalog, item.producto_nombre_raw)
            suggested_skus_nv[item.producto_nombre_raw] = sku_sug
            rows_nv.append({
                "Producto": item.producto_nombre_raw,
                "SKU": sku_display_nv.get(sku_sug, "") if sku_sug else "",
                "Cantidad": item.cantidad,
                "Precio unit. (COP)": item.precio_unitario,
            })

        df_nv_result = st.data_editor(
            _pd_nv.DataFrame(rows_nv) if rows_nv else _pd_nv.DataFrame(
                columns=["Producto", "SKU", "Cantidad", "Precio unit. (COP)"]
            ),
            use_container_width=True,
            hide_index=True,
            num_rows="dynamic",
            key=f"nv_editor_{parse_v}",
            column_config={
                "Producto": st.column_config.TextColumn("Producto", width="large"),
                "SKU": st.column_config.SelectboxColumn("SKU en catálogo", options=skus_nv, width="large"),
                "Cantidad": st.column_config.NumberColumn("Cantidad", min_value=1, step=1, width="small"),
                "Precio unit. (COP)": st.column_config.NumberColumn(
                    "Precio unit. (COP)", min_value=0, step=1000, format="$ %d", width="medium"
                ),
            },
        )

        # ── Totales (calculados en tiempo real) ──
        try:
            nv_sub = int(
                (df_nv_result["Cantidad"].fillna(1) * df_nv_result["Precio unit. (COP)"].fillna(0)).sum()
            )
        except Exception:
            nv_sub = st.session_state.get("sale_montos", {}).get("subtotal", 0) or 0
        nv_env = venta.costo_envio or 0
        nv_com_pct = venta.rappi_detalle.comision_porcentaje if venta.rappi_detalle else 0
        nv_com = round(nv_sub * nv_com_pct / 100) if nv_com_pct else 0
        nv_total = nv_sub + nv_env - nv_com

        st.markdown(
            "<hr style='border:none;border-top:1px solid #e0ddd8;margin:8px 0'>",
            unsafe_allow_html=True,
        )
        mc1, mc2, mc3 = st.columns(3)
        mc1.metric("Bruto", fmt_cop(nv_sub))
        if nv_env:
            mc2.metric("Envío", fmt_cop(nv_env))
        if nv_com:
            mc2.metric("Comisión", fmt_cop(nv_com),
                       delta=f"-{nv_com_pct:.0f}%", delta_color="inverse")
        mc3.metric("Total", fmt_cop(nv_total))

        # ── Pago (editable) ──
        st.markdown(
            "<hr style='border:none;border-top:1px solid #e0ddd8;margin:8px 0'>",
            unsafe_allow_html=True,
        )
        _pago_opts = [
            "Sin especificar", "Transferencia Bancolombia", "Nequi", "Efectivo",
            "Pago contraentrega", "Contra entrega Rappi", "Tarjeta de crédito",
        ]
        _cur_pago = venta.pago.metodo or "Sin especificar"
        if _cur_pago not in _pago_opts:
            _pago_opts = [_cur_pago] + _pago_opts
        p_c1, p_c2 = st.columns(2)
        e_pago = p_c1.selectbox(
            "💳 Método de pago", _pago_opts,
            index=_pago_opts.index(_cur_pago),
            key=f"nv_pago_{parse_v}",
        )
        e_cuenta = p_c2.text_input(
            "Cuenta destino", value=venta.pago.cuenta_destino or "",
            key=f"nv_cuenta_{parse_v}",
        )

        # ── Dirección (solo lectura) ──
        if venta.envio and (venta.envio.ciudad or venta.envio.direccion):
            with st.expander("📦 Dirección de envío"):
                e = venta.envio
                if e.direccion:    st.text(f"Dirección : {e.direccion}")
                if e.ciudad:       st.text(f"Ciudad    : {e.ciudad}")
                if e.departamento: st.text(f"Dpto      : {e.departamento}")

        if venta.fuente_referido:
            st.markdown(
                f"<div style='font-size:13px;color:#777;font-family:Poppins,sans-serif;margin-top:2px'>"
                f"📣 <b>Referido:</b> {venta.fuente_referido}</div>",
                unsafe_allow_html=True,
            )

        # ── Notas (editable) ──
        e_notas = st.text_area(
            "Notas", value=venta.notas or "",
            key=f"nv_notas_{parse_v}",
            height=60,
            placeholder="Observaciones, correcciones…",
            label_visibility="collapsed",
        )

        st.markdown(
            "<hr style='border:none;border-top:1px solid #e0ddd8;margin:8px 0'>",
            unsafe_allow_html=True,
        )

        # ── Confirmar / Cancelar ──
        b1, b2 = st.columns([3, 1])
        with b1:
            if st.button("✅ Confirmar y Guardar", type="primary",
                         use_container_width=True, key="btn_guardar"):
                msg = st.session_state.get(sale_key, "")

                # Build items list from the editor — defensive against None/NaN/pd.NA
                pre_items = []
                for _, row in df_nv_result.iterrows():
                    # Nombre: skip empty or all-None rows (e.g. phantom rows from data_editor)
                    try:
                        nombre_raw = row.get("Producto")
                        nombre = (
                            str(nombre_raw).strip()
                            if nombre_raw is not None and not _pd_nv.isna(nombre_raw)
                            else ""
                        )
                    except (TypeError, ValueError):
                        nombre = ""
                    if not nombre:
                        continue

                    qty = row.get("Cantidad")
                    precio = row.get("Precio unit. (COP)")
                    try:
                        qty = int(qty) if qty is not None and not _pd_nv.isna(qty) else 1
                        precio = int(precio) if precio is not None and not _pd_nv.isna(precio) else 0
                    except (ValueError, TypeError):
                        qty, precio = 1, 0
                    if qty <= 0:
                        continue

                    try:
                        sku_raw = row.get("SKU")
                        sku_str = (
                            str(sku_raw).strip()
                            if sku_raw is not None and not _pd_nv.isna(sku_raw)
                            else ""
                        )
                    except (TypeError, ValueError):
                        sku_str = ""
                    sku_val = sku_map_nv.get(sku_str, None)

                    pre_items.append({
                        "nombre_raw": nombre, "sku": sku_val,
                        "cantidad": qty, "precio_unitario": precio,
                    })

                if not pre_items:
                    st.warning("Debe haber al menos un producto con nombre válido.")
                else:
                    # Reconstruct ParsedSale with all edits applied
                    from api.motor_ia import (
                        ParsedSale as _PS, SaleItemData as _SID,
                        CustomerData as _CD, PaymentData as _PD,
                    )

                    edited_cliente = None
                    if c_nombre.strip():
                        edited_cliente = _CD(
                            nombre=c_nombre,
                            cedula=c_cedula or None,
                            telefono=c_tel or None,
                            email=c_email or None,
                        )

                    # SaleItemData with pre-resolved sku → _create_sale_items skips re-matching
                    edited_items_ps = [
                        _SID(
                            producto_nombre_raw=it["nombre_raw"],
                            cantidad=it["cantidad"],
                            precio_unitario=it["precio_unitario"] or None,
                            sku=it["sku"],
                        )
                        for it in pre_items
                    ]

                    edited_sale = _PS(
                        canal=edited_canal,
                        cliente=edited_cliente,
                        items=edited_items_ps,
                        costo_envio=venta.costo_envio,
                        total_declarado=venta.total_declarado,
                        pago=_PD(
                            metodo=e_pago,
                            cuenta_destino=e_cuenta or None,
                            referencia=venta.pago.referencia,
                        ),
                        envio=venta.envio,
                        rappi_detalle=venta.rappi_detalle,
                        fuente_referido=venta.fuente_referido,
                        notas=e_notas or None,
                    )

                    with st.spinner("Guardando en base de datos..."):
                        try:
                            from sqlalchemy.orm import Session as DBSession
                            from api.guardar_venta import save_sale, DuplicateRappiOrderError
                            with DBSession(engine) as session:
                                v_guardada = save_sale(session, edited_sale, msg)
                                session.commit()
                                venta_id = v_guardada.id

                            # Log SKU corrections (suggested ≠ confirmed) — fire-and-forget
                            from app.db_queries import log_sku_correction as _log_sku_v
                            for it in pre_items:
                                _sug = suggested_skus_nv.get(it["nombre_raw"])
                                if it["sku"] != _sug:
                                    try:
                                        _log_sku_v(engine, it["nombre_raw"], _sug, it["sku"], "venta")
                                    except Exception:
                                        pass

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
                            get_kpis_period.clear()

                            st.rerun()
                        except DuplicateRappiOrderError as e:
                            st.warning(
                                f"⚠️ **Orden Rappi duplicada — no se guardó.**\n\n"
                                f"La orden **{e.order_id}** ya fue registrada anteriormente. "
                                f"El stock **no fue descontado**. "
                                f"Si la orden es nueva, verifica el Order ID antes de continuar."
                            )
                        except Exception as e:
                            st.error(f"Error al guardar: {e}")
        with b2:
            if st.button("❌", use_container_width=True, key="btn_cancelar",
                         help="Cancelar"):
                st.session_state.parsed_sale = None
                st.session_state.sale_montos = None
                st.rerun()


# ---------------------------------------------------------------------------
# Shared helper: render a sale detail dict (used in Dashboard and Ventas page)
# ---------------------------------------------------------------------------

def _render_sale_detail(detalle: dict):
    canal_color = CANAL_COLORS.get(detalle["canal"], "#555")
    st.markdown(
        f'<span class="badge" style="color:{canal_color};border-color:{canal_color}">'
        f'{detalle["canal"]}</span>'
        f'&nbsp;<span style="font-size:13px;color:#aaa;font-family:Poppins,sans-serif">'
        f'#{detalle["id"]} · {detalle["fecha"].strftime("%d/%m/%Y %H:%M") if detalle["fecha"] else "—"}'
        f' · <b>{detalle["estado"]}</b></span>',
        unsafe_allow_html=True,
    )

    # Client
    nombre = detalle["cliente_nombre"] or "—"
    cedula = detalle["cliente_cedula"] or ""
    telefono = detalle["cliente_telefono"] or ""
    st.markdown(
        f'<div style="font-size:13px;color:#777;font-family:Poppins,sans-serif;margin:4px 0 10px">'
        f'👤 <b>{nombre}</b>'
        f'{" · CC " + cedula if cedula else ""}'
        f'{" · " + telefono if telefono else ""}'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Items
    st.markdown(
        "<div style='font-size:14px;font-weight:600;color:#555;"
        "font-family:Poppins,sans-serif;margin-bottom:4px'>🛒 Productos</div>",
        unsafe_allow_html=True,
    )
    for it in detalle["items"]:
        nombre_prod = it["nombre_catalogo"] or it["nombre_raw"]
        sku_txt = f' <span style="color:#bbb;font-size:12px">[{it["sku"]}]</span>' if it["sku"] else ""
        precio = fmt_cop(it["precio_unitario"])
        subtotal = fmt_cop(it["subtotal"])
        st.markdown(
            f'<div style="background:#f5f2eb;border:1.5px solid #e0ddd8;border-radius:2px;'
            f'padding:6px 12px;margin:2px 0;font-size:13px;font-family:Poppins,sans-serif">'
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
            f'<div style="font-size:13px;color:#555;font-family:Poppins,sans-serif;margin-top:4px">'
            f'💳 <b>{pago["metodo"]}</b>{cuenta}{ref}</div>',
            unsafe_allow_html=True,
        )

    # Shipping
    if detalle["envio"]:
        e = detalle["envio"]
        partes = [x for x in [e.get("direccion"), e.get("ciudad"), e.get("departamento")] if x]
        if partes:
            st.markdown(
                f'<div style="font-size:13px;color:#555;font-family:Poppins,sans-serif;margin-top:4px">'
                f'📦 {" · ".join(partes)}</div>',
                unsafe_allow_html=True,
            )

    # Rappi
    if detalle["rappi"]:
        r = detalle["rappi"]
        st.markdown(
            f'<div style="font-size:13px;color:#FF441F;font-family:Poppins,sans-serif;margin-top:4px">'
            f'🛵 Rappi {r["tipo"]} · Orden {r["order_id"]} · '
            f'Comisión {r["comision_porcentaje"]}% = {fmt_cop(r["comision_monto"] or 0)}</div>',
            unsafe_allow_html=True,
        )

    if detalle["notas"]:
        st.info(f"📝 {detalle['notas']}")

    if detalle["fuente_referido"]:
        st.markdown(
            f'<div style="font-size:13px;color:#777;font-family:Poppins,sans-serif">📣 Referido: {detalle["fuente_referido"]}</div>',
            unsafe_allow_html=True,
        )

    if detalle["mensaje_original"]:
        with st.expander("📄 Mensaje original"):
            st.text(detalle["mensaje_original"])


# ---------------------------------------------------------------------------
# Shared helper: render a purchase detail dict
# ---------------------------------------------------------------------------

def _render_purchase_detail(detalle: dict):
    fecha_txt = detalle["fecha"].strftime("%d/%m/%Y %H:%M") if detalle["fecha"] else "—"
    st.markdown(
        f'<div style="font-size:14px;font-family:Poppins,sans-serif;margin-bottom:10px">'
        f'🗓️ <b>{fecha_txt}</b> &nbsp;·&nbsp; '
        f'Proveedor: <b>{detalle["proveedor"]}</b>'
        f'</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        "<div style='font-size:14px;font-weight:600;color:#555;"
        "font-family:Poppins,sans-serif;margin-bottom:4px'>📦 Productos comprados</div>",
        unsafe_allow_html=True,
    )

    total_calculado = 0
    for it in detalle["items"]:
        nombre = it["nombre_catalogo"] or it["nombre_raw"]
        sku_txt = (
            f' <span style="color:#bbb;font-size:12px">[{it["sku"]}]</span>'
            if it["sku"] else ""
        )
        costo_txt = fmt_cop(it["precio_costo_unitario"]) if it["precio_costo_unitario"] else "—"
        sub_txt   = fmt_cop(it["subtotal"]) if it["subtotal"] else "—"
        if it["subtotal"]:
            total_calculado += it["subtotal"]
        st.markdown(
            f'<div style="background:#f5f2eb;border:1.5px solid #e0ddd8;border-radius:2px;'
            f'padding:6px 12px;margin:2px 0;font-size:13px;font-family:Poppins,sans-serif">'
            f'<b>{it["cantidad"]}×</b> {nombre}{sku_txt}'
            f'<span style="float:right;color:#555">{costo_txt} c/u = <b>{sub_txt}</b></span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown(
        "<hr style='border:none;border-top:1px solid #e0ddd8;margin:10px 0'>",
        unsafe_allow_html=True,
    )
    tc1, tc2 = st.columns(2)
    tc1.metric("Total calculado", fmt_cop(total_calculado))
    if detalle["monto_total"]:
        tc2.metric("Total registrado", fmt_cop(detalle["monto_total"]))


# ---------------------------------------------------------------------------
# PÁGINA: DASHBOARD
# ---------------------------------------------------------------------------

def page_dashboard(engine):
    st.markdown(
        '<div class="cs-section-title">📊 Dashboard</div>',
        unsafe_allow_html=True,
    )

    # ── Period selector ──
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

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # ── Load data — KPIs follow the selected period ──
    kpis_periodo = get_kpis_period(engine, start_date, end_date)
    df_canal  = get_sales_by_channel(engine, start_date, end_date)
    df_tend   = get_daily_trend(engine, start_date, end_date)
    df_top    = get_top_products(engine)
    df_alerr  = get_stock_alerts(engine, umbral=-1)   # only negative stock

    ventas_neto  = kpis_periodo["ventas"]["neto"]
    costo_period = kpis_periodo["compras"]["total"]
    margen       = ventas_neto - costo_period
    pct_margen   = round(margen / ventas_neto * 100, 1) if ventas_neto > 0 else 0.0
    n_alertas    = len(df_alerr)

    # ── KPI row — 4 columns ──
    k1, k2, k3, k4 = st.columns(4)
    k1.markdown(kpi_card(
        "Ventas del Período", fmt_cop(ventas_neto),
        f"{kpis_periodo['ventas']['count']} órdenes", "#555",
    ), unsafe_allow_html=True)
    k2.markdown(kpi_card(
        "Inversión en Compras", fmt_cop(costo_period),
        f"{kpis_periodo['compras']['count']} órdenes de compra", "#aaa",
    ), unsafe_allow_html=True)
    k3.markdown(kpi_card(
        "Margen Estimado", f"{pct_margen}%",
        fmt_cop(margen),
        "#5aaa88" if pct_margen >= 0 else "#cc4444",
    ), unsafe_allow_html=True)
    k4.markdown(kpi_card(
        "Stock Negativo", str(n_alertas),
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
                '<div style="font-size:13px;color:#aaa;font-family:Poppins,sans-serif;margin-bottom:10px">'
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
                    f'<div style="font-size:11px;color:#999;font-family:Poppins,sans-serif">'
                    f'{metodo_label}</div>'
                    f'<div style="font-size:14px;font-weight:700;color:#1a1a1a;font-family:Poppins,sans-serif">'
                    f'{cuenta_label}</div>'
                    f'<div style="font-size:20px;font-weight:700;color:#5aaa88;font-family:Poppins,sans-serif">'
                    f'{total_fmt}</div>'
                    f'<div style="font-size:11px;color:#bbb;font-family:Poppins,sans-serif">'
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
            'padding:20px;text-align:center;color:#aaa;font-family:Poppins,sans-serif">'
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

    tab_inv, tab_alertas, tab_combos, tab_hot, tab_ajuste = st.tabs(
        ["📋 Catálogo", "🚨 Alertas de stock", "🧩 Combos", "🔥 Hot Products", "⚙️ Ajuste Stock"]
    )

    # ── Tab 1: Catálogo ──
    with tab_inv:
        search = st.text_input("🔍 Buscar producto (nombre, SKU, marca, categoría)",
                               key="inv_search", placeholder="Ej: creatina, 1013, IMN…")
        df_inv = get_inventory(engine, search)

        if df_inv.empty:
            st.markdown(
                '<div style="background:#f5f2eb;border:1.5px dashed #d4d0c8;border-radius:2px;'
                'padding:20px;text-align:center;color:#aaa;font-family:Poppins,sans-serif">'
                'No se encontraron productos.</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div style="font-size:13px;color:#aaa;font-family:Poppins,sans-serif;'
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
                'padding:10px 16px;font-family:Poppins,sans-serif;color:#3a7a58">'
                '✓ No hay productos con stock negativo.</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div style="background:#fff0ee;border:1.5px solid #cc4444;border-radius:2px;'
                f'padding:10px 16px;font-family:Poppins,sans-serif;color:#cc4444;margin-bottom:8px">'
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
            'margin-bottom:12px">📋 Pedidos sin stock</div>',
            unsafe_allow_html=True,
        )
        df_sin = get_orders_without_stock(engine)
        if df_sin.empty:
            st.markdown(
                '<div style="background:#f0f9f4;border:1.5px solid #5aaa88;border-radius:2px;'
                'padding:10px 16px;font-family:Poppins,sans-serif;color:#3a7a58">'
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
            '<div style="font-size:13px;color:#aaa;font-family:Poppins,sans-serif;margin-bottom:12px">'
            'Stock virtual = cuántas unidades del combo se pueden armar con el stock actual '
            'de cada componente. El cuello de botella es el componente más escaso.</div>',
            unsafe_allow_html=True,
        )
        df_combos = get_combo_virtual_stock(engine)
        if df_combos.empty:
            st.markdown(
                '<div style="background:#f5f2eb;border:1.5px dashed #d4d0c8;border-radius:2px;'
                'padding:20px;text-align:center;color:#aaa;font-family:Poppins,sans-serif">'
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
                'padding:10px 16px;font-family:Poppins,sans-serif;color:#3a7a58">'
                '✓ No hay alertas de componentes pendientes.</div>',
                unsafe_allow_html=True,
            )
        else:
            for _, row in df_alertas.iterrows():
                resuelta = bool(row["Resuelta"])
                if resuelta:
                    card_style = ('background:#f0f9f4;border:1.5px solid #5aaa88;'
                                  'border-radius:2px;padding:8px 14px;margin:4px 0;'
                                  'font-family:Poppins,sans-serif')
                else:
                    card_style = ('background:#fff8f2;border:1.5px solid #c89070;'
                                  'border-radius:2px;padding:8px 14px;margin:4px 0;'
                                  'font-family:Poppins,sans-serif')
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
                'padding:20px;text-align:center;color:#aaa;font-family:Poppins,sans-serif">'
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
                    f'font-family:Poppins,sans-serif">'
                    f'<span style="font-size:16px">{medal} <b>{row["Producto"][:50]}</b></span>'
                    f'<span style="color:#aaa;font-size:13px">{int(row["Unidades"])} uds</span>'
                    f'<span style="color:#5aaa88;font-weight:700;font-size:15px">'
                    f'{fmt_cop(row["Ingresos"])}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

    # ── Tab 5: Ajuste de Stock ──
    with tab_ajuste:
        from app.db_queries import adjust_stock_with_log

        st.markdown(
            '<div class="cs-section-title" style="font-size:17px;border-bottom:1px solid #e0ddd8;'
            'margin-bottom:12px">⚙️ Ajuste manual de stock</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            "<div style='font-size:13px;color:#888;font-family:Poppins,sans-serif;margin-bottom:16px'>"
            "Usa este panel para corregir el stock de un producto sin crear una compra. "
            "Cada ajuste queda registrado en el log de Admin con fecha, producto y motivo.</div>",
            unsafe_allow_html=True,
        )

        catalogo_aj = get_sku_catalog(engine)
        opciones_aj = [f"{p['sku']} — {p['nombre']}" for p in catalogo_aj]
        sku_map_aj = {f"{p['sku']} — {p['nombre']}": p["sku"] for p in catalogo_aj}

        q_aj = st.text_input("Filtrar producto", placeholder="Nombre o SKU…",
                             key="aj_filter", label_visibility="collapsed")
        filtered_aj = [o for o in opciones_aj if q_aj.lower() in o.lower()] if q_aj else opciones_aj

        if not filtered_aj:
            st.warning("Sin resultados para ese filtro.")
        else:
            sel_aj = st.selectbox("Producto a ajustar", filtered_aj,
                                  key="aj_producto", label_visibility="collapsed")
            sku_aj = sku_map_aj.get(sel_aj)

            if sku_aj:
                prod_aj = next((p for p in catalogo_aj if p["sku"] == sku_aj), None)
                stock_aj = prod_aj.get("stock_actual", 0) if prod_aj else 0
                nombre_aj = prod_aj.get("nombre", sku_aj) if prod_aj else sku_aj

                st.markdown(
                    f"<div style='font-size:13px;font-family:Poppins,sans-serif;margin:8px 0'>"
                    f"Stock actual: <b>{stock_aj}</b></div>",
                    unsafe_allow_html=True,
                )

                aj_c1, aj_c2 = st.columns([1, 2])
                with aj_c1:
                    delta_aj = st.number_input("Unidades a ajustar (+/-)", value=0, step=1,
                                               key="aj_delta",
                                               help="Positivo = sumar unidades. Negativo = quitar unidades.")
                with aj_c2:
                    motivo_aj = st.text_input("Motivo (opcional)",
                                              placeholder="Ej: corrección inventario físico",
                                              key="aj_motivo")

                if delta_aj != 0:
                    nuevo_stock_preview = stock_aj + delta_aj
                    color_delta = "#3a7a58" if delta_aj > 0 else "#cc4444"
                    signo = "+" if delta_aj > 0 else "−"
                    motivo_line = (
                        f"<div style='margin-top:5px;color:#777'>"
                        f"Motivo: {motivo_aj.strip()}</div>"
                        if motivo_aj.strip() else ""
                    )
                    st.markdown(
                        f"<div style='font-size:13px;font-family:Poppins,sans-serif;"
                        f"background:#f5f2eb;border:1.5px solid #d4d0c8;border-radius:6px;"
                        f"padding:12px 16px;margin:10px 0'>"
                        f"<div style='font-weight:600;margin-bottom:6px;color:#1a1a1a'>"
                        f"Resumen del ajuste</div>"
                        f"<div><b>{sku_aj}</b> — {nombre_aj}</div>"
                        f"<div style='margin-top:4px'>Stock: <b>{stock_aj}</b> → "
                        f"<b style='color:{color_delta}'>{nuevo_stock_preview}</b>"
                        f"&nbsp;&nbsp;<span style='color:{color_delta};font-weight:600'>"
                        f"({signo}{abs(delta_aj)} unidades)</span></div>"
                        f"{motivo_line}"
                        f"</div>",
                        unsafe_allow_html=True,
                    )

                    st.markdown(
                        "<div style='font-size:13px;color:#888;font-family:Poppins,sans-serif;"
                        "margin:10px 0 4px'>Escribe <b>CONFIRMAR</b> para aplicar el ajuste:</div>",
                        unsafe_allow_html=True,
                    )
                    confirm_text = st.text_input("Confirmación", key="aj_confirm",
                                                 label_visibility="collapsed",
                                                 placeholder="CONFIRMAR")

                    if st.button("Aplicar ajuste", key="aj_aplicar", type="primary"):
                        if confirm_text.strip().upper() != "CONFIRMAR":
                            st.error("Escribe exactamente CONFIRMAR para proceder.")
                        else:
                            try:
                                nuevo_stock = adjust_stock_with_log(
                                    engine, sku_aj, int(delta_aj),
                                    motivo_aj.strip() or None
                                )
                                get_inventario.clear()
                                get_alertas_stock.clear()
                                get_kpis.clear()
                                st.success(
                                    f"Stock de **{sku_aj}** ajustado: "
                                    f"{stock_aj} → {nuevo_stock}. Registrado en log."
                                )
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")
                else:
                    st.info("Ingresa un delta distinto de 0 para aplicar un ajuste.")


# ---------------------------------------------------------------------------
# PÁGINA: COMPRAS E INGRESO DE MERCANCÍA
# ---------------------------------------------------------------------------

def _render_purchase_edit_form(engine, detalle_compra: dict) -> None:
    """Inline edit form for a single purchase. Called from the history section."""
    import pandas as _pd_ep

    catalogo_ep = get_sku_catalog(engine)
    skus_ep = [""] + [f"{p['sku']} — {p['nombre']}" for p in catalogo_ep]
    sku_map_ep = {"": None}
    for p in catalogo_ep:
        sku_map_ep[f"{p['sku']} — {p['nombre']}"] = p["sku"]
    sku_display_ep = {p["sku"]: f"{p['sku']} — {p['nombre']}" for p in catalogo_ep}

    ep_proveedor = st.text_input(
        "Proveedor",
        value=detalle_compra.get("proveedor") or "",
        key=f"ep_prov_{detalle_compra['id']}",
        placeholder="Nombre del proveedor",
    )

    st.markdown(
        '<div style="font-size:12px;color:#aaa;font-family:Poppins,sans-serif;margin-bottom:6px">'
        'El stock <b>se ajusta automáticamente</b>: se revierte el stock anterior y se aplica el nuevo.</div>',
        unsafe_allow_html=True,
    )

    rows_ep = []
    for it in detalle_compra["items"]:
        sku_disp = sku_display_ep.get(it["sku"], "") if it["sku"] else ""
        rows_ep.append({
            "Producto": it["nombre_catalogo"] or it["nombre_raw"],
            "SKU": sku_disp,
            "Cantidad": it["cantidad"],
            "Costo unitario (COP)": it["precio_costo_unitario"],
        })
    df_ep_edit = _pd_ep.DataFrame(rows_ep) if rows_ep else _pd_ep.DataFrame(
        columns=["Producto", "SKU", "Cantidad", "Costo unitario (COP)"]
    )

    df_ep_result = st.data_editor(
        df_ep_edit,
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
        key=f"ep_editor_{detalle_compra['id']}",
        column_config={
            "Producto": st.column_config.TextColumn("Producto", width="large"),
            "SKU": st.column_config.SelectboxColumn("SKU en catálogo", options=skus_ep, width="large"),
            "Cantidad": st.column_config.NumberColumn("Cantidad", min_value=1, step=1, width="small"),
            "Costo unitario (COP)": st.column_config.NumberColumn(
                "Costo unitario (COP)", min_value=0, step=1000, format="$ %d", width="medium"
            ),
        },
    )

    try:
        ep_total = int(
            (df_ep_result["Cantidad"].fillna(1) * df_ep_result["Costo unitario (COP)"].fillna(0)).sum()
        )
        st.markdown(
            f"<div style='text-align:right;font-size:15px;color:#555;"
            f"font-family:Poppins,sans-serif;margin:6px 0 12px'>"
            f"<b>Total estimado:</b> <span style='color:#1a1a1a;font-weight:700;font-size:18px'>"
            f"{fmt_cop(ep_total)}</span></div>",
            unsafe_allow_html=True,
        )
    except Exception:
        ep_total = 0

    st.markdown("<hr style='border:none;border-top:1px solid #e0ddd8;margin:4px 0 12px'>",
                unsafe_allow_html=True)

    btn_cols = st.columns([3, 1])
    with btn_cols[0]:
        if st.button("💾 Guardar cambios", type="primary",
                     key=f"ep_guardar_{detalle_compra['id']}", use_container_width=True):
            items_ep_save = []
            for _, row in df_ep_result.iterrows():
                nombre = str(row.get("Producto") or "").strip()
                if not nombre:
                    continue
                qty = row.get("Cantidad")
                costo = row.get("Costo unitario (COP)")
                try:
                    qty = int(qty) if qty is not None and not _pd_ep.isna(qty) else 1
                    costo = int(costo) if costo is not None and not _pd_ep.isna(costo) else None
                except (ValueError, TypeError):
                    qty, costo = 1, None
                if qty <= 0:
                    continue
                sku_val = sku_map_ep.get(str(row.get("SKU") or "").strip(), None)
                items_ep_save.append({
                    "nombre_raw": nombre, "sku": sku_val,
                    "cantidad": qty, "precio_costo_unitario": costo,
                })
            if not items_ep_save:
                st.warning("Debe haber al menos un producto con nombre válido.")
            else:
                try:
                    update_purchase_items(engine, detalle_compra["id"],
                                         items_ep_save, ep_proveedor or None)
                    get_purchase_detail.clear()
                    get_compras_recientes.clear()
                    get_inventario.clear()
                    get_alertas_stock.clear()
                    get_kpis.clear()
                    get_kpis_period.clear()
                    st.session_state.pop("ep_editing_id", None)
                    st.session_state.pop("ep_detalle_edit", None)
                    st.success(
                        f"✅ Compra #{detalle_compra['id']} actualizada — "
                        f"{len(items_ep_save)} producto(s). Stock ajustado."
                    )
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al guardar: {e}")
    with btn_cols[1]:
        if st.button("✕ Cancelar", key=f"ep_cancelar_{detalle_compra['id']}",
                     use_container_width=True):
            st.session_state.pop("ep_editing_id", None)
            st.session_state.pop("ep_detalle_edit", None)
            st.rerun()


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
            st.markdown(
                "<div style='font-size:13px;color:#777;margin-bottom:6px;"
                "font-family:Poppins,sans-serif'>Pega aquí el mensaje del proveedor o lista de productos</div>",
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
                    "padding:40px;text-align:center;color:#aaa;font-family:Poppins,sans-serif'>"
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

                # Track suggested SKUs for correction logging
                suggested_skus_compra = {
                    r["Producto (del proveedor)"]: sku_map.get(r["SKU en catálogo"]) or None
                    for r in rows_editor
                }

                import pandas as pd
                df_edit = pd.DataFrame(rows_editor)

                st.markdown(
                    '<div class="cs-section-title" style="font-size:16px;'
                    'border-bottom:1px solid #e0ddd8;margin-bottom:6px">'
                    'Revisar y ajustar productos detectados</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    '<div style="font-size:13px;color:#aaa;font-family:Poppins,sans-serif;'
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
                        f"font-family:Poppins,sans-serif;margin-top:8px'>"
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
                                # Log SKU corrections (suggested ≠ confirmed)
                                from app.db_queries import log_sku_correction as _log_sku
                                for _, _row in df_save.iterrows():
                                    _confirmed = _row["sku"]
                                    _suggested = suggested_skus_compra.get(
                                        str(_row["producto_nombre_raw"]).strip()
                                    )
                                    if _confirmed != _suggested:
                                        try:
                                            _log_sku(engine, str(_row["producto_nombre_raw"]),
                                                     _suggested, _confirmed, "compra")
                                        except Exception:
                                            pass  # logging failure must not block the save

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
                'padding:20px;text-align:center;color:#aaa;font-family:Poppins,sans-serif">'
                'No hay compras registradas aún.</div>',
                unsafe_allow_html=True,
            )
        else:
            st.dataframe(df_hist, use_container_width=True, hide_index=True)

            st.markdown(
                "<div style='font-size:13px;color:#aaa;font-family:Poppins,sans-serif;margin-top:12px'>"
                "Ingresa un ID de la lista para ver el detalle completo:</div>",
                unsafe_allow_html=True,
            )
            ch1, ch2 = st.columns([2, 1])
            with ch1:
                compra_id_input = st.number_input(
                    "ID compra", min_value=1, step=1, key="ch_hist_id",
                    label_visibility="collapsed",
                )
            with ch2:
                ver_compra_btn = st.button("Ver detalle", key="ch_hist_ver",
                                           use_container_width=True)

            if ver_compra_btn and compra_id_input:
                detalle_c = get_purchase_detail(engine, int(compra_id_input))
                if detalle_c is None:
                    st.warning(f"No existe ninguna compra con ID #{int(compra_id_input)}")
                else:
                    st.markdown('<div class="cs-card">', unsafe_allow_html=True)
                    _render_purchase_detail(detalle_c)
                    st.markdown('</div>', unsafe_allow_html=True)

        # ── Editable records (within 24h window) ──
        import pandas as _pd_ep2
        if "fecha_dt" not in df_hist.columns:
            return

        cutoff_ep = _pd_ep2.Timestamp.now() - _pd_ep2.Timedelta(hours=EDIT_WINDOW_HOURS)
        df_ep_editable = df_hist[df_hist["fecha_dt"] > cutoff_ep]

        if df_ep_editable.empty:
            return

        st.markdown(
            '<div class="cs-section-title" style="font-size:15px;border-bottom:1px solid #e0ddd8;'
            'margin-top:20px;margin-bottom:8px">✏️ Registros editables (últimas 24 h)</div>',
            unsafe_allow_html=True,
        )

        ep_editing_id = st.session_state.get("ep_editing_id")

        for _, row in df_ep_editable.iterrows():
            compra_id = int(row["ID"])
            is_ep_open = ep_editing_id == compra_id
            proveedor_txt = row["Proveedor"] or "Sin proveedor"

            ep_card_cols = st.columns([5, 1])
            with ep_card_cols[0]:
                st.markdown(
                    f'<div style="background:#fffef9;border:1.5px solid #d4d0c8;border-radius:6px;'
                    f'padding:8px 14px;font-family:Poppins,sans-serif;font-size:13px">'
                    f'<b>#{compra_id}</b> &nbsp;'
                    f'<span style="color:#555;font-weight:600">{proveedor_txt}</span>'
                    f' &nbsp;·&nbsp; <b>{row["Monto total"]}</b>'
                    f' &nbsp;·&nbsp; {row["Items"]} ítem(s)'
                    f' &nbsp;·&nbsp; <span style="color:#aaa">{row["Fecha"]}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            with ep_card_cols[1]:
                ep_btn_label = "✕ Cerrar" if is_ep_open else "✏️ Editar"
                if st.button(ep_btn_label, key=f"ep_open_{compra_id}", use_container_width=True):
                    if is_ep_open:
                        st.session_state.pop("ep_editing_id", None)
                        st.session_state.pop("ep_detalle_edit", None)
                    else:
                        st.session_state["ep_editing_id"] = compra_id
                        st.session_state["ep_detalle_edit"] = get_purchase_detail(engine, compra_id)
                    st.rerun()

            if is_ep_open:
                ep_detalle = st.session_state.get("ep_detalle_edit")
                if ep_detalle and ep_detalle["id"] == compra_id:
                    with st.expander(f"✏️ Editando compra #{compra_id}", expanded=True):
                        with st.expander("📄 Referencia actual", expanded=False):
                            _render_purchase_detail(ep_detalle)
                        _render_purchase_edit_form(engine, ep_detalle)


# ---------------------------------------------------------------------------
# PÁGINA: VENTAS (Historial + Auditador/Corrector)
# ---------------------------------------------------------------------------

def _render_sale_edit_form(engine, detalle_edit: dict) -> None:
    """Inline edit form for a single sale. Called from the history section."""
    import pandas as _pd_sv

    catalogo_ed = get_sku_catalog(engine)
    skus_ed = [""] + [f"{p['sku']} — {p['nombre']}" for p in catalogo_ed]
    sku_map_ed = {"": None}
    for p in catalogo_ed:
        sku_map_ed[f"{p['sku']} — {p['nombre']}"] = p["sku"]
    sku_display_ed = {p["sku"]: f"{p['sku']} — {p['nombre']}" for p in catalogo_ed}

    rows_items = []
    for it in detalle_edit["items"]:
        sku_disp = sku_display_ed.get(it["sku"], "") if it["sku"] else ""
        rows_items.append({
            "Producto": it["nombre_catalogo"] or it["nombre_raw"],
            "SKU": sku_disp,
            "Cantidad": it["cantidad"],
            "Precio unit.": it["precio_unitario"],
        })
    df_items_edit = _pd_sv.DataFrame(rows_items) if rows_items else _pd_sv.DataFrame(
        columns=["Producto", "SKU", "Cantidad", "Precio unit."]
    )

    df_items_result = st.data_editor(
        df_items_edit,
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
        key=f"sv_items_editor_{detalle_edit['id']}",
        column_config={
            "Producto": st.column_config.TextColumn("Producto", width="large"),
            "SKU": st.column_config.SelectboxColumn("SKU en catálogo", options=skus_ed, width="large"),
            "Cantidad": st.column_config.NumberColumn("Cantidad", min_value=1, step=1, width="small"),
            "Precio unit.": st.column_config.NumberColumn(
                "Precio unit. (COP)", min_value=0, step=1000, format="$ %d", width="medium"
            ),
        },
    )

    try:
        nuevo_subtotal = int(
            (df_items_result["Cantidad"].fillna(1) * df_items_result["Precio unit."].fillna(0)).sum()
        )
        envi_actual = detalle_edit.get("costo_envio") or 0
        desc_actual = detalle_edit.get("descuento") or 0
        nuevo_total = max(nuevo_subtotal + envi_actual - desc_actual, 0)
        st.markdown(
            f"<div style='text-align:right;font-size:15px;color:#555;"
            f"font-family:Poppins,sans-serif;margin:6px 0 12px'>"
            f"Subtotal: <b>{fmt_cop(nuevo_subtotal)}</b>"
            f"{f'  +  Envío: {fmt_cop(envi_actual)}' if envi_actual else ''}"
            f"{f'  −  Descuento: {fmt_cop(desc_actual)}' if desc_actual else ''}"
            f" &nbsp;→&nbsp; <span style='color:#1a1a1a;font-weight:700;font-size:18px'>"
            f"Total: {fmt_cop(nuevo_total)}</span></div>",
            unsafe_allow_html=True,
        )
    except Exception:
        nuevo_total = 0

    st.markdown("<hr style='border:none;border-top:1px solid #e0ddd8;margin:4px 0 12px'>",
                unsafe_allow_html=True)

    from models import EstadoVenta as _EstadoVenta
    estados_list = [e.value for e in _EstadoVenta]
    current_estado = (
        detalle_edit["estado"].value if hasattr(detalle_edit["estado"], "value")
        else str(detalle_edit["estado"])
    )
    ea1, ea2 = st.columns([1, 2])
    with ea1:
        new_estado = st.selectbox(
            "Estado", estados_list,
            index=estados_list.index(current_estado) if current_estado in estados_list else 0,
            key=f"sv_estado_{detalle_edit['id']}",
        )
    with ea2:
        new_notas = st.text_area(
            "Notas", value=detalle_edit["notas"] or "",
            key=f"sv_notas_{detalle_edit['id']}",
            placeholder="Observaciones, correcciones, motivo del cambio…",
            height=80,
        )

    btn_cols = st.columns([3, 1])
    with btn_cols[0]:
        if st.button("💾 Guardar cambios", type="primary",
                     key=f"sv_guardar_{detalle_edit['id']}", use_container_width=True):
            items_to_save = []
            for _, row in df_items_result.iterrows():
                nombre = str(row.get("Producto") or "").strip()
                if not nombre:
                    continue
                qty = row.get("Cantidad")
                precio = row.get("Precio unit.")
                try:
                    qty = int(qty) if qty is not None and not _pd_sv.isna(qty) else 1
                    precio = int(precio) if precio is not None and not _pd_sv.isna(precio) else 0
                except (ValueError, TypeError):
                    qty, precio = 1, 0
                if qty <= 0:
                    continue
                sku_val = sku_map_ed.get(str(row.get("SKU") or "").strip(), None)
                items_to_save.append({
                    "nombre_raw": nombre, "sku": sku_val,
                    "cantidad": qty, "precio_unitario": precio,
                })
            if not items_to_save:
                st.warning("Debe haber al menos un producto con nombre válido.")
            else:
                try:
                    update_sale_items(engine, detalle_edit["id"],
                                      items_to_save, new_estado, new_notas or None)
                    get_sale_detail.clear()
                    get_all_sales.clear()
                    get_ventas_recientes.clear()
                    get_kpis.clear()
                    get_top_productos.clear()
                    st.session_state.pop("sv_editing_id", None)
                    st.session_state.pop("sv_detalle_edit", None)
                    st.success(
                        f"✅ Venta #{detalle_edit['id']} actualizada — "
                        f"{len(items_to_save)} producto(s), total {fmt_cop(nuevo_total)}, "
                        f"estado → {new_estado}"
                    )
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al guardar: {e}")
    with btn_cols[1]:
        if st.button("✕ Cancelar", key=f"sv_cancelar_{detalle_edit['id']}",
                     use_container_width=True):
            st.session_state.pop("sv_editing_id", None)
            st.session_state.pop("sv_detalle_edit", None)
            st.rerun()


def _render_sales_history(engine):
    """Renders the sales history table, detail viewer, and 24h inline editor."""
    import pandas as _pd_sv2

    # ── Filters ──
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

    df_ventas = get_all_sales(
        engine, f_start, f_end,
        estado=None if f_estado == "Todos" else f_estado,
        canal_nombre=None if f_canal == "Todos" else f_canal,
    )

    if df_ventas.empty:
        st.markdown(
            '<div style="background:#f5f2eb;border:1.5px dashed #d4d0c8;border-radius:2px;'
            'padding:20px;text-align:center;color:#aaa;font-family:Poppins,sans-serif">'
            'No hay ventas con esos filtros.</div>',
            unsafe_allow_html=True,
        )
        return

    st.markdown(
        f'<div style="font-size:13px;color:#aaa;font-family:Poppins,sans-serif;margin-bottom:8px">'
        f'{len(df_ventas)} ventas encontradas</div>',
        unsafe_allow_html=True,
    )
    cols_show = ["ID", "Fecha", "Canal", "Cliente", "Bruto", "Total", "Estado", "Pago", "Cuenta"]
    st.dataframe(df_ventas[cols_show], use_container_width=True, hide_index=True)

    # ── Quick detail viewer ──
    st.markdown(
        "<div style='font-size:13px;color:#aaa;font-family:Poppins,sans-serif;margin-top:12px'>"
        "Ver detalle de cualquier venta:</div>",
        unsafe_allow_html=True,
    )
    dv1, dv2 = st.columns([2, 1])
    with dv1:
        sv_id = st.number_input("ID venta", min_value=1, step=1, key="sv_hist_id",
                                label_visibility="collapsed")
    with dv2:
        if st.button("Ver detalle", key="sv_hist_ver", use_container_width=True):
            detalle = get_sale_detail(engine, int(sv_id))
            if detalle is None:
                st.warning(f"No existe venta #{int(sv_id)}")
            else:
                st.markdown('<div class="cs-card">', unsafe_allow_html=True)
                _render_sale_detail(detalle)
                st.markdown('</div>', unsafe_allow_html=True)

    # ── Editable records (within 24h window) ──
    if "fecha_dt" not in df_ventas.columns:
        return

    cutoff = _pd_sv2.Timestamp.now() - _pd_sv2.Timedelta(hours=EDIT_WINDOW_HOURS)
    df_editable = df_ventas[df_ventas["fecha_dt"] > cutoff]

    if df_editable.empty:
        return

    st.markdown(
        '<div class="cs-section-title" style="font-size:15px;border-bottom:1px solid #e0ddd8;'
        'margin-top:20px;margin-bottom:8px">✏️ Registros editables (últimas 24 h)</div>',
        unsafe_allow_html=True,
    )

    editing_id = st.session_state.get("sv_editing_id")

    for _, row in df_editable.iterrows():
        sale_id = int(row["ID"])
        is_this_open = editing_id == sale_id
        canal_color = CANAL_COLORS.get(row["Canal"], "#555")

        card_cols = st.columns([5, 1])
        with card_cols[0]:
            st.markdown(
                f'<div style="background:#fffef9;border:1.5px solid #d4d0c8;border-radius:6px;'
                f'padding:8px 14px;font-family:Poppins,sans-serif;font-size:13px">'
                f'<b>#{sale_id}</b> &nbsp;'
                f'<span style="color:{canal_color};font-weight:600">{row["Canal"]}</span>'
                f' &nbsp;·&nbsp; {row["Cliente"]}'
                f' &nbsp;·&nbsp; <b>{row["Total"]}</b>'
                f' &nbsp;·&nbsp; <span style="color:#aaa">{row["Fecha"]}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
        with card_cols[1]:
            btn_label = "✕ Cerrar" if is_this_open else "✏️ Editar"
            if st.button(btn_label, key=f"sv_open_{sale_id}", use_container_width=True):
                if is_this_open:
                    st.session_state.pop("sv_editing_id", None)
                    st.session_state.pop("sv_detalle_edit", None)
                else:
                    st.session_state["sv_editing_id"] = sale_id
                    st.session_state["sv_detalle_edit"] = get_sale_detail(engine, sale_id)
                st.rerun()

        if is_this_open:
            detalle_edit = st.session_state.get("sv_detalle_edit")
            if detalle_edit and detalle_edit["id"] == sale_id:
                with st.expander(f"✏️ Editando venta #{sale_id}", expanded=True):
                    with st.expander("📄 Referencia actual", expanded=False):
                        _render_sale_detail(detalle_edit)
                    st.markdown(
                        "<div style='font-size:12px;color:#aaa;font-family:Poppins,sans-serif;"
                        "margin-bottom:8px'>El stock <b>no se ajusta</b> al editar una venta "
                        "&#8212; usa una compra o ajuste manual si cambiaste cantidades.</div>",
                        unsafe_allow_html=True,
                    )
                    _render_sale_edit_form(engine, detalle_edit)


def page_sales(engine):
    st.markdown('<div class="cs-section-title">📋 Ventas</div>', unsafe_allow_html=True)

    tab_nueva, tab_historial = st.tabs(["📝 Nueva Venta", "📋 Historial"])

    with tab_nueva:
        _render_new_sale_content(engine)

    with tab_historial:
        _render_sales_history(engine)


# ---------------------------------------------------------------------------
# PÁGINA: ANÁLISIS POR CLIENTES
# ---------------------------------------------------------------------------

# Default category grouping — can be updated via multiselect in the UI.
# Categories whose name contains any of these substrings (case-insensitive)
# are classified as "Suplementos"; the rest as "Implementos".
_SUPLEMENTO_KEYWORDS = [
    "suplemento", "proteina", "proteína", "whey", "creatina", "pre-entreno",
    "preentreno", "aminoacid", "bcaa", "quemador", "vitamina", "colageno",
    "colágeno", "omega", "ganador", "mass", "hipercalorico", "hipercalórico",
    "recovery", "recuperacion", "recuperación", "energizante", "barra proteica",
    "nutri",
]


def _classify_category(cat: str, suplemento_cats: set[str]) -> str:
    """Returns 'Suplementos' if cat is in suplemento_cats, else 'Implementos'."""
    return "Suplementos" if cat in suplemento_cats else "Implementos"


def page_clientes(engine):
    from app.db_queries import (
        get_shipping_departments,
        get_client_stats,
        get_client_category_breakdown,
    )
    import pandas as _pd_cl
    import plotly.express as _px

    st.markdown('<div class="cs-section-title">👥 Análisis por Clientes</div>',
                unsafe_allow_html=True)

    # ── Period + department filters (shared across all tabs) ──
    f1, f2, f3 = st.columns([1, 1, 2])
    with f1:
        cl_start = st.date_input("Desde", value=date.today() - timedelta(days=89),
                                 key="cl_start")
    with f2:
        cl_end = st.date_input("Hasta", value=date.today(), key="cl_end")
    with f3:
        deptos = get_shipping_departments(engine)
        depto_opts = ["Todos los departamentos"] + deptos
        cl_depto = st.selectbox("Departamento", depto_opts, key="cl_depto",
                                label_visibility="collapsed")
    depto_filter = None if cl_depto == "Todos los departamentos" else cl_depto

    # ── Quick-period shortcuts ──
    qc = st.columns(4)
    for i, (lbl, delta) in enumerate([("30 días", 29), ("90 días", 89),
                                       ("6 meses", 179), ("Este año", 364)]):
        if qc[i].button(lbl, key=f"cl_period_{delta}"):
            st.session_state["cl_start"] = date.today() - timedelta(days=delta)
            st.session_state["cl_end"] = date.today()
            st.rerun()

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # ── Load main data ──
    df_stats = get_client_stats(engine, cl_start, cl_end, departamento=depto_filter)
    df_cat   = get_client_category_breakdown(engine, cl_start, cl_end, departamento=depto_filter)

    # ── Summary KPIs ──
    if not df_stats.empty:
        n_clientes  = len(df_stats)
        total_rev   = int(df_stats["Total"].sum())
        ticket_prom = int(total_rev / df_stats["Compras"].sum()) if df_stats["Compras"].sum() > 0 else 0
        top_cliente = df_stats.iloc[0]["Cliente"]

        k1, k2, k3, k4 = st.columns(4)
        from app.charts import kpi_card
        k1.markdown(kpi_card("Clientes únicos", str(n_clientes),
                             f"en el período", "#555"), unsafe_allow_html=True)
        k2.markdown(kpi_card("Ingresos totales", fmt_cop(total_rev),
                             f"{int(df_stats['Compras'].sum())} ventas", "#555"),
                    unsafe_allow_html=True)
        k3.markdown(kpi_card("Ticket promedio", fmt_cop(ticket_prom),
                             "por transacción", "#5aaa88"), unsafe_allow_html=True)
        k4.markdown(kpi_card("Cliente top", top_cliente[:28] + "…"
                             if len(top_cliente) > 28 else top_cliente,
                             fmt_cop(int(df_stats.iloc[0]["Total"])), "#4488aa"),
                    unsafe_allow_html=True)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    tab_valor, tab_items, tab_categoria = st.tabs(
        ["💰 Por Valor", "📦 Por Unidades", "🏷️ Por Categoría"]
    )

    # ── Tab 1: ranking by total spent ──
    with tab_valor:
        st.markdown(
            '<div class="cs-section-title" style="font-size:16px;'
            'border-bottom:1px solid #e0ddd8;margin-bottom:12px">'
            'Clientes que más han gastado</div>',
            unsafe_allow_html=True,
        )

        if df_stats.empty:
            st.markdown(
                '<div style="background:#f5f2eb;border:1.5px dashed #d4d0c8;border-radius:2px;'
                'padding:20px;text-align:center;color:#aaa;font-family:Poppins,sans-serif">'
                'No hay datos de clientes en el período seleccionado.</div>',
                unsafe_allow_html=True,
            )
        else:
            top_n = st.slider("Top N clientes", min_value=5, max_value=50,
                              value=15, step=5, key="cl_top_n_valor")
            df_top_v = df_stats.head(top_n).copy()

            # Bar chart
            fig_v = _px.bar(
                df_top_v.sort_values("Total"),
                x="Total", y="Cliente",
                orientation="h",
                text=df_top_v.sort_values("Total")["Total"].apply(fmt_cop),
                color="Total",
                color_continuous_scale=["#d4d0c8", "#314457"],
                labels={"Total": "Total gastado (COP)", "Cliente": ""},
            )
            fig_v.update_traces(textposition="outside", textfont_size=11)
            fig_v.update_layout(
                height=max(300, top_n * 28),
                margin=dict(l=0, r=40, t=20, b=20),
                coloraxis_showscale=False,
                plot_bgcolor="#fffef9",
                paper_bgcolor="#fffef9",
                font_family="Poppins",
            )
            st.plotly_chart(fig_v, use_container_width=True)

            # Detail table
            with st.expander("Ver tabla completa", expanded=False):
                display_v = df_top_v.copy()
                display_v["Total"] = display_v["Total"].apply(fmt_cop)
                display_v["Ticket Prom."] = display_v["Ticket Prom."].apply(fmt_cop)
                st.dataframe(display_v, use_container_width=True, hide_index=True)

    # ── Tab 2: ranking by units ──
    with tab_items:
        st.markdown(
            '<div class="cs-section-title" style="font-size:16px;'
            'border-bottom:1px solid #e0ddd8;margin-bottom:12px">'
            'Clientes que más unidades han comprado</div>',
            unsafe_allow_html=True,
        )

        if df_stats.empty:
            st.markdown(
                '<div style="background:#f5f2eb;border:1.5px dashed #d4d0c8;border-radius:2px;'
                'padding:20px;text-align:center;color:#aaa;font-family:Poppins,sans-serif">'
                'No hay datos en el período seleccionado.</div>',
                unsafe_allow_html=True,
            )
        else:
            df_top_u = df_stats.sort_values("Unidades", ascending=False).copy()
            top_nu = st.slider("Top N clientes", min_value=5, max_value=50,
                               value=15, step=5, key="cl_top_n_items")
            df_top_u = df_top_u.head(top_nu)

            fig_u = _px.bar(
                df_top_u.sort_values("Unidades"),
                x="Unidades", y="Cliente",
                orientation="h",
                text="Unidades",
                color="Unidades",
                color_continuous_scale=["#d4d0c8", "#5aaa88"],
                labels={"Unidades": "Unidades compradas", "Cliente": ""},
            )
            fig_u.update_traces(textposition="outside", textfont_size=11)
            fig_u.update_layout(
                height=max(300, top_nu * 28),
                margin=dict(l=0, r=40, t=20, b=20),
                coloraxis_showscale=False,
                plot_bgcolor="#fffef9",
                paper_bgcolor="#fffef9",
                font_family="Poppins",
            )
            st.plotly_chart(fig_u, use_container_width=True)

            with st.expander("Ver tabla completa", expanded=False):
                display_u = df_top_u[["Cliente", "Unidades", "Compras", "Total"]].copy()
                display_u["Total"] = display_u["Total"].apply(fmt_cop)
                st.dataframe(display_u, use_container_width=True, hide_index=True)

    # ── Tab 3: by product category ──
    with tab_categoria:
        st.markdown(
            '<div class="cs-section-title" style="font-size:16px;'
            'border-bottom:1px solid #e0ddd8;margin-bottom:12px">'
            'Qué tipo de productos compra cada cliente</div>',
            unsafe_allow_html=True,
        )

        if df_cat.empty:
            st.markdown(
                '<div style="background:#f5f2eb;border:1.5px dashed #d4d0c8;border-radius:2px;'
                'padding:20px;text-align:center;color:#aaa;font-family:Poppins,sans-serif">'
                'No hay datos de categorías para el período seleccionado. '
                'Solo se cuentan ítems con SKU asignado.</div>',
                unsafe_allow_html=True,
            )
        else:
            # ── Category classifier ──
            all_cats = sorted(df_cat["Categoría"].unique().tolist())
            default_suplementos = [
                c for c in all_cats
                if any(kw in c.lower() for kw in _SUPLEMENTO_KEYWORDS)
            ]
            default_implementos = [c for c in all_cats if c not in default_suplementos]

            st.markdown(
                "<div style='font-size:13px;color:#888;font-family:Poppins,sans-serif;"
                "margin-bottom:10px'>Clasifica las categorías de tu catálogo para calcular"
                " el resumen Suplementos / Implementos.</div>",
                unsafe_allow_html=True,
            )

            col_sup, col_imp = st.columns(2)
            with col_sup:
                cats_suplementos = st.multiselect(
                    "🟢 Categorías → Suplementos",
                    options=all_cats,
                    default=default_suplementos,
                    key="cl_cats_sup",
                )
            with col_imp:
                st.markdown(
                    "<div style='font-size:12px;color:#aaa;font-family:Poppins,sans-serif;"
                    "margin-top:28px'>Las categorías no seleccionadas como Suplementos "
                    "se clasifican automáticamente como <b>Implementos</b>.</div>",
                    unsafe_allow_html=True,
                )

            suplemento_set = set(cats_suplementos)

            # Pivot: cliente × tipo (Suplementos | Implementos)
            df_cat_copy = df_cat.copy()
            df_cat_copy["Tipo"] = df_cat_copy["Categoría"].apply(
                lambda c: _classify_category(c, suplemento_set)
            )
            df_pivot = (
                df_cat_copy
                .groupby(["Cliente", "Tipo"])["Total"]
                .sum()
                .unstack(fill_value=0)
                .reset_index()
            )
            # Ensure both columns exist even if one group has no data
            for col in ["Suplementos", "Implementos"]:
                if col not in df_pivot.columns:
                    df_pivot[col] = 0
            df_pivot["Total"] = df_pivot["Suplementos"] + df_pivot["Implementos"]
            df_pivot = df_pivot.sort_values("Total", ascending=False)

            # ── KPI split ──
            only_sup = (df_pivot["Implementos"] == 0) & (df_pivot["Suplementos"] > 0)
            only_imp = (df_pivot["Suplementos"] == 0) & (df_pivot["Implementos"] > 0)
            both     = (df_pivot["Suplementos"] > 0) & (df_pivot["Implementos"] > 0)

            ck1, ck2, ck3 = st.columns(3)
            ck1.metric("Solo Suplementos", int(only_sup.sum()),
                       help="Clientes que únicamente compraron suplementos")
            ck2.metric("Solo Implementos", int(only_imp.sum()),
                       help="Clientes que únicamente compraron implementos")
            ck3.metric("Compraron ambos", int(both.sum()),
                       help="Clientes que compraron suplementos e implementos")

            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

            # ── Stacked bar chart ──
            top_nc = st.slider("Top N clientes", min_value=5, max_value=40,
                               value=15, step=5, key="cl_top_n_cat")
            df_chart_cat = df_pivot.head(top_nc).copy()
            df_melt = df_chart_cat[["Cliente", "Suplementos", "Implementos"]].melt(
                id_vars="Cliente", var_name="Tipo", value_name="Total"
            )

            fig_cat = _px.bar(
                df_melt.sort_values("Total"),
                x="Total", y="Cliente",
                color="Tipo",
                orientation="h",
                barmode="stack",
                color_discrete_map={
                    "Suplementos": "#314457",
                    "Implementos": "#5aaa88",
                },
                labels={"Total": "Total (COP)", "Cliente": ""},
                text=df_melt["Total"].apply(
                    lambda v: fmt_cop(v) if v > 0 else ""
                ),
            )
            fig_cat.update_traces(textposition="inside", textfont_size=10)
            fig_cat.update_layout(
                height=max(320, top_nc * 30),
                margin=dict(l=0, r=20, t=20, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=1.02,
                            xanchor="right", x=1),
                plot_bgcolor="#fffef9",
                paper_bgcolor="#fffef9",
                font_family="Poppins",
            )
            st.plotly_chart(fig_cat, use_container_width=True)

            # ── Explicit client lists per type ──
            st.markdown(
                "<hr style='border:none;border-top:1px solid #e0ddd8;margin:16px 0'>",
                unsafe_allow_html=True,
            )
            list_sup, list_imp = st.columns(2)

            clients_sup = (
                df_pivot[df_pivot["Suplementos"] > 0]
                .sort_values("Suplementos", ascending=False)[["Cliente", "Suplementos"]]
                .rename(columns={"Suplementos": "Total (COP)"})
                .copy()
            )
            clients_imp = (
                df_pivot[df_pivot["Implementos"] > 0]
                .sort_values("Implementos", ascending=False)[["Cliente", "Implementos"]]
                .rename(columns={"Implementos": "Total (COP)"})
                .copy()
            )

            with list_sup:
                st.markdown(
                    f'<div style="font-size:14px;font-weight:600;color:#314457;'
                    f'font-family:Poppins,sans-serif;margin-bottom:6px">'
                    f'🟢 Clientes de Suplementos ({len(clients_sup)})</div>',
                    unsafe_allow_html=True,
                )
                if clients_sup.empty:
                    st.caption("Sin datos")
                else:
                    disp_sup = clients_sup.copy()
                    disp_sup["Total (COP)"] = disp_sup["Total (COP)"].apply(fmt_cop)
                    st.dataframe(disp_sup, use_container_width=True, hide_index=True,
                                 height=min(400, (len(disp_sup) + 1) * 36))

            with list_imp:
                st.markdown(
                    f'<div style="font-size:14px;font-weight:600;color:#5aaa88;'
                    f'font-family:Poppins,sans-serif;margin-bottom:6px">'
                    f'🔵 Clientes de Implementos ({len(clients_imp)})</div>',
                    unsafe_allow_html=True,
                )
                if clients_imp.empty:
                    st.caption("Sin datos")
                else:
                    disp_imp = clients_imp.copy()
                    disp_imp["Total (COP)"] = disp_imp["Total (COP)"].apply(fmt_cop)
                    st.dataframe(disp_imp, use_container_width=True, hide_index=True,
                                 height=min(400, (len(disp_imp) + 1) * 36))

            # ── Detail table ──
            with st.expander("Ver desglose exacto por categoría", expanded=False):
                display_cat = df_cat.copy()
                display_cat["Total"] = display_cat["Total"].apply(fmt_cop)
                st.dataframe(display_cat, use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------------
# PÁGINA: CATÁLOGO Y GESTIÓN DE ALIASES
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# PÁGINA: BÚSQUEDA DE PRODUCTO
# ---------------------------------------------------------------------------

def page_product_search(engine):
    from app.db_queries import get_product_transactions

    st.markdown('<div class="cs-section-title">🔍 Búsqueda por Producto</div>',
                unsafe_allow_html=True)
    st.markdown(
        "<div style='font-size:13px;color:#888;font-family:Poppins,sans-serif;margin-bottom:16px'>"
        "Selecciona un producto para ver todas las ventas y compras que lo involucran.</div>",
        unsafe_allow_html=True,
    )

    catalogo = get_sku_catalog(engine)
    if not catalogo:
        st.info("No hay productos en el catálogo.")
        return

    # ── Filtro de búsqueda + selectbox ──
    q_prod = st.text_input("Filtrar catálogo", placeholder="Nombre, SKU o marca…",
                           key="bs_filter", label_visibility="collapsed")
    filtered = catalogo
    if q_prod:
        q_lower = q_prod.lower()
        filtered = [p for p in catalogo
                    if q_lower in p["nombre"].lower() or q_lower in p["sku"].lower()
                    or q_lower in (p.get("marca") or "").lower()]

    if not filtered:
        st.warning("Sin resultados para ese filtro.")
        return

    opciones = [f"{p['sku']} — {p['nombre']}" for p in filtered]
    seleccion = st.selectbox("Producto", opciones, key="bs_producto",
                             label_visibility="collapsed")

    if not seleccion:
        return

    sku_sel = seleccion.split(" — ")[0].strip()

    # ── Stock actual ──
    prod_info = next((p for p in catalogo if p["sku"] == sku_sel), None)
    if prod_info:
        stock_val = prod_info.get("stock_actual", "—")
        stock_color = "#cc4444" if isinstance(stock_val, int) and stock_val < 0 else (
            "#5aaa88" if isinstance(stock_val, int) and stock_val > 5 else "#1a1a1a"
        )
        st.markdown(
            f"<div style='font-size:13px;font-family:Poppins,sans-serif;margin:8px 0 16px'>"
            f"Stock actual: <b style='color:{stock_color}'>{stock_val}</b></div>",
            unsafe_allow_html=True,
        )

    # ── Transacciones ──
    df_tx = get_product_transactions(engine, sku_sel)

    if df_tx.empty:
        st.markdown(
            "<div style='background:#f5f2eb;border:1.5px dashed #d4d0c8;border-radius:2px;"
            "padding:20px;text-align:center;color:#aaa;font-family:Poppins,sans-serif'>"
            "No hay transacciones registradas para este producto.</div>",
            unsafe_allow_html=True,
        )
        return

    n_ventas = (df_tx["Tipo"] == "Venta").sum()
    n_compras = (df_tx["Tipo"] == "Compra").sum()
    st.markdown(
        f"<div style='font-size:13px;color:#aaa;font-family:Poppins,sans-serif;margin-bottom:8px'>"
        f"{len(df_tx)} transacciones · {n_ventas} ventas · {n_compras} compras</div>",
        unsafe_allow_html=True,
    )

    def _style_tipo(val):
        if val == "Venta":
            return "background-color:#f0f9f4;color:#3a7a58;font-weight:600"
        return "background-color:#f5f2eb;color:#8a6a3a;font-weight:600"

    display = df_tx[["Fecha", "Tipo", "Canal/Proveedor", "Cantidad",
                      "Precio/Costo unit.", "Subtotal", "Referencia"]].copy()
    display["Fecha"] = display["Fecha"].dt.strftime("%Y-%m-%d %H:%M")
    for col in ["Precio/Costo unit.", "Subtotal"]:
        display[col] = display[col].apply(
            lambda v: f"${int(v):,}".replace(",", ".") if v and not (
                isinstance(v, float) and __import__("math").isnan(v)) else "—"
        )

    styled = display.style.applymap(_style_tipo, subset=["Tipo"])
    st.dataframe(styled, use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------------
# PÁGINA: ADMIN / LOGS
# ---------------------------------------------------------------------------

def page_admin(engine):
    from app.db_queries import get_sku_match_logs, get_stock_adjustment_logs

    st.markdown('<div class="cs-section-title">⚙️ Admin / Logs del Sistema</div>',
                unsafe_allow_html=True)

    tab_sku, tab_stock = st.tabs(["🔀 Correcciones de SKU", "📦 Ajustes de Stock"])

    # ── Tab SKU corrections ──
    with tab_sku:
        st.markdown(
            "<div style='font-size:13px;color:#888;font-family:Poppins,sans-serif;margin-bottom:12px'>"
            "Registro de casos donde el SKU sugerido por el matcher fue corregido manualmente "
            "antes de guardar. Útil para identificar qué aliases agregar en la BD.</div>",
            unsafe_allow_html=True,
        )
        if st.button("🔄 Actualizar", key="admin_sku_refresh"):
            get_sku_match_logs.clear()

        df_sku = get_sku_match_logs(engine)

        if df_sku.empty:
            st.markdown(
                "<div style='background:#f5f2eb;border:1.5px dashed #d4d0c8;border-radius:2px;"
                "padding:20px;text-align:center;color:#aaa;font-family:Poppins,sans-serif'>"
                "Sin correcciones registradas aún.</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"<div style='font-size:12px;color:#aaa;font-family:Poppins,sans-serif;margin-bottom:8px'>"
                f"Últimas {len(df_sku)} correcciones</div>",
                unsafe_allow_html=True,
            )
            display_sku = df_sku.copy()
            display_sku["Fecha"] = display_sku["Fecha"].dt.strftime("%Y-%m-%d %H:%M")
            display_sku["SKU sugerido"] = display_sku["SKU sugerido"].fillna("(ninguno)")
            display_sku["SKU confirmado"] = display_sku["SKU confirmado"].fillna("(ninguno)")
            display_sku["Nombre sugerido"] = display_sku["Nombre sugerido"].fillna("—")
            st.dataframe(display_sku, use_container_width=True, hide_index=True)

    # ── Tab stock adjustments ──
    with tab_stock:
        st.markdown(
            "<div style='font-size:13px;color:#888;font-family:Poppins,sans-serif;margin-bottom:12px'>"
            "Historial de ajustes manuales de stock realizados desde la aplicación.</div>",
            unsafe_allow_html=True,
        )
        if st.button("🔄 Actualizar", key="admin_stock_refresh"):
            get_stock_adjustment_logs.clear()

        df_adj = get_stock_adjustment_logs(engine)

        if df_adj.empty:
            st.markdown(
                "<div style='background:#f5f2eb;border:1.5px dashed #d4d0c8;border-radius:2px;"
                "padding:20px;text-align:center;color:#aaa;font-family:Poppins,sans-serif'>"
                "Sin ajustes registrados aún.</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"<div style='font-size:12px;color:#aaa;font-family:Poppins,sans-serif;margin-bottom:8px'>"
                f"Últimos {len(df_adj)} ajustes</div>",
                unsafe_allow_html=True,
            )

            def _style_delta(val):
                if isinstance(val, (int, float)):
                    return "color:#3a7a58;font-weight:700" if val > 0 else (
                        "color:#cc4444;font-weight:700" if val < 0 else ""
                    )
                return ""

            display_adj = df_adj.copy()
            display_adj["Fecha"] = display_adj["Fecha"].dt.strftime("%Y-%m-%d %H:%M")
            display_adj["Motivo"] = display_adj["Motivo"].fillna("—")
            styled_adj = display_adj.style.applymap(_style_delta, subset=["Delta"])
            st.dataframe(styled_adj, use_container_width=True, hide_index=True)


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
    # Legacy redirect: "nueva_venta" no longer exists as a separate page.
    if page == "nueva_venta":
        st.session_state.current_page = "ventas"
        st.rerun()
    elif page == "dashboard":
        page_dashboard(engine)
    elif page == "inventario":
        page_inventory(engine)
    elif page == "compras":
        page_purchases(engine)
    elif page == "ventas":
        page_sales(engine)
    elif page == "clientes":
        page_clientes(engine)
    elif page == "busqueda":
        page_product_search(engine)
    elif page == "admin":
        page_admin(engine)


if __name__ == "__main__":
    main()
