"""
db_queries.py
=============
Todas las consultas a Supabase para la app Streamlit.
Usa @st.cache_data / @st.cache_resource para minimizar round-trips.
"""

import os
import sys
from datetime import date, datetime
from typing import Optional

import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, select, func, desc
from sqlalchemy.orm import Session

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _root)

from models import (
    Venta, VentaItem, Producto, Canal, Pago, Cliente, EstadoVenta,
    ComboComponente, AlertaPedido, Compra, DetalleCompra,
)


@st.cache_resource
def get_engine():
    url = os.getenv("DATABASE_URL")
    if not url:
        try:
            url = st.secrets["DATABASE_URL"]
        except Exception:
            pass
    if not url:
        raise ValueError("DATABASE_URL no configurada en .env ni en st.secrets")
    return create_engine(url, pool_pre_ping=True, pool_recycle=3600)


# ---------------------------------------------------------------------------
# KPIs — TTL corto para que "hoy" siempre esté fresco
# ---------------------------------------------------------------------------

@st.cache_data(ttl=60)
def get_kpis(_engine) -> dict:
    today = date.today()
    month_start = datetime.combine(today.replace(day=1), datetime.min.time())
    today_start = datetime.combine(today, datetime.min.time())
    today_end   = datetime.combine(today, datetime.max.time())

    with Session(_engine) as s:
        def _agg(q):
            row = s.execute(q).one()
            return {"count": row[0] or 0, "bruto": int(row[1] or 0), "neto": int(row[2] or 0), "comisiones": int(row[3] or 0)}

        base = (
            select(
                func.count(Venta.id),
                func.coalesce(func.sum(Venta.subtotal), 0),
                func.coalesce(func.sum(Venta.total), 0),
                func.coalesce(func.sum(Venta.descuento), 0),
            )
            .where(Venta.estado != EstadoVenta.cancelada)
        )

        hoy = _agg(base.where(Venta.fecha >= today_start).where(Venta.fecha <= today_end))
        mes = _agg(base.where(Venta.fecha >= month_start))

    return {"hoy": hoy, "mes": mes}


# ---------------------------------------------------------------------------
# Dashboard charts
# ---------------------------------------------------------------------------

@st.cache_data(ttl=300)
def get_ventas_por_canal(_engine, start: date, end: date) -> pd.DataFrame:
    with Session(_engine) as s:
        rows = s.execute(
            select(
                Canal.nombre.label("Canal"),
                func.count(Venta.id).label("Ventas"),
                func.coalesce(func.sum(Venta.total), 0).label("Total"),
            )
            .join(Canal, Venta.canal_id == Canal.id)
            .where(func.date(Venta.fecha) >= start)
            .where(func.date(Venta.fecha) <= end)
            .where(Venta.estado != EstadoVenta.cancelada)
            .group_by(Canal.nombre)
            .order_by(desc("Total"))
        ).all()
    return pd.DataFrame(rows, columns=["Canal", "Ventas", "Total"])


@st.cache_data(ttl=300)
def get_tendencia_diaria(_engine, start: date, end: date) -> pd.DataFrame:
    with Session(_engine) as s:
        rows = s.execute(
            select(
                func.date(Venta.fecha).label("Fecha"),
                func.count(Venta.id).label("Ventas"),
                func.coalesce(func.sum(Venta.total), 0).label("Total"),
            )
            .where(func.date(Venta.fecha) >= start)
            .where(func.date(Venta.fecha) <= end)
            .where(Venta.estado != EstadoVenta.cancelada)
            .group_by(func.date(Venta.fecha))
            .order_by(func.date(Venta.fecha))
        ).all()
    return pd.DataFrame(rows, columns=["Fecha", "Ventas", "Total"])


@st.cache_data(ttl=300)
def get_top_productos(_engine, limit: int = 10) -> pd.DataFrame:
    with Session(_engine) as s:
        rows = s.execute(
            select(
                VentaItem.sku,
                func.coalesce(Producto.nombre, VentaItem.producto_nombre_raw).label("Producto"),
                func.sum(VentaItem.cantidad).label("Unidades"),
                func.coalesce(func.sum(VentaItem.subtotal), 0).label("Ingresos"),
            )
            .outerjoin(Producto, VentaItem.sku == Producto.sku)
            .join(Venta, VentaItem.venta_id == Venta.id)
            .where(Venta.estado != EstadoVenta.cancelada)
            .where(VentaItem.sku.isnot(None))
            .group_by(VentaItem.sku, Producto.nombre, VentaItem.producto_nombre_raw)
            .order_by(desc("Unidades"))
            .limit(limit)
        ).all()
    return pd.DataFrame(rows, columns=["SKU", "Producto", "Unidades", "Ingresos"])


@st.cache_data(ttl=300)
def get_top_facturadores(_engine, limit: int = 10) -> pd.DataFrame:
    """Canales o métodos de pago que más facturan."""
    with Session(_engine) as s:
        rows = s.execute(
            select(
                Pago.metodo.label("Metodo"),
                func.count(Venta.id).label("Ventas"),
                func.coalesce(func.sum(Venta.total), 0).label("Total"),
            )
            .join(Pago, Pago.venta_id == Venta.id)
            .where(Venta.estado != EstadoVenta.cancelada)
            .group_by(Pago.metodo)
            .order_by(desc("Total"))
            .limit(limit)
        ).all()
    return pd.DataFrame(rows, columns=["Método de pago", "Ventas", "Total"])


@st.cache_data(ttl=60)
def get_ventas_recientes(_engine, limit: int = 15) -> pd.DataFrame:
    with Session(_engine) as s:
        rows = s.execute(
            select(
                Venta.id,
                Venta.fecha,
                Canal.nombre.label("Canal"),
                func.coalesce(Venta.cliente_nombre_raw, "—").label("Cliente"),
                Venta.total,
                Venta.estado,
                Pago.metodo.label("Pago"),
            )
            .join(Canal, Venta.canal_id == Canal.id)
            .outerjoin(Pago, Pago.venta_id == Venta.id)
            .order_by(desc(Venta.fecha))
            .limit(limit)
        ).all()
    df = pd.DataFrame(rows, columns=["ID", "Fecha", "Canal", "Cliente", "Total", "Estado", "Pago"])
    if not df.empty:
        df["Fecha"] = pd.to_datetime(df["Fecha"]).dt.strftime("%d/%m %H:%M")
        df["Total"] = df["Total"].apply(lambda x: f"${x:,.0f}".replace(",", "."))
    return df


# ---------------------------------------------------------------------------
# Inventario
# ---------------------------------------------------------------------------

@st.cache_data(ttl=60)
def get_inventario(_engine, search: str = "") -> pd.DataFrame:
    with Session(_engine) as s:
        rows = s.execute(
            select(
                Producto.sku,
                Producto.nombre,
                Producto.marca,
                Producto.categoria,
                Producto.stock_actual,
            ).order_by(Producto.stock_actual)
        ).all()
    df = pd.DataFrame(rows, columns=["SKU", "Nombre", "Marca", "Categoría", "Stock"])
    if search:
        mask = df.apply(lambda row: search.lower() in str(row).lower(), axis=1)
        df = df[mask]
    return df


@st.cache_data(ttl=60)
def get_alertas_stock(_engine, umbral: int = 3) -> pd.DataFrame:
    """
    umbral=-1 → solo stock negativo (< 0)
    umbral>=0 → stock <= umbral
    """
    with Session(_engine) as s:
        q = select(Producto.sku, Producto.nombre, Producto.marca, Producto.stock_actual)
        if umbral < 0:
            q = q.where(Producto.stock_actual < 0)
        else:
            q = q.where(Producto.stock_actual <= umbral)
        rows = s.execute(q.order_by(Producto.stock_actual)).all()
    return pd.DataFrame(rows, columns=["SKU", "Nombre", "Marca", "Stock"])


@st.cache_data(ttl=60)
def get_combos_stock_virtual(_engine) -> pd.DataFrame:
    """
    Calcula el stock virtual de cada combo:
        stock_virtual = min( floor(componente.stock_actual / cantidad_por_combo) )
    El componente con menos disponibilidad proporcional es el cuello de botella.
    """
    with Session(_engine) as s:
        combo_skus = s.execute(
            select(ComboComponente.combo_sku).distinct()
        ).scalars().all()

        if not combo_skus:
            return pd.DataFrame(columns=["SKU", "Combo", "Stock Virtual", "Cuello de botella"])

        rows = []
        for combo_sku in combo_skus:
            combo_prod = s.execute(
                select(Producto).where(Producto.sku == combo_sku)
            ).scalar_one_or_none()
            if not combo_prod:
                continue

            componentes = s.execute(
                select(ComboComponente, Producto)
                .join(Producto, ComboComponente.componente_sku == Producto.sku)
                .where(ComboComponente.combo_sku == combo_sku)
            ).all()

            if not componentes:
                continue

            stock_virtual = None
            cuello = None
            for cc, prod in componentes:
                sv = prod.stock_actual // cc.cantidad if cc.cantidad > 0 else 0
                if stock_virtual is None or sv < stock_virtual:
                    stock_virtual = sv
                    cuello = f"{prod.nombre} (×{cc.cantidad})"

            rows.append({
                "SKU": combo_sku,
                "Combo": combo_prod.nombre,
                "Stock Virtual": stock_virtual if stock_virtual is not None else 0,
                "Cuello de botella": cuello or "—",
            })

    return pd.DataFrame(rows)


@st.cache_data(ttl=30)
def get_alertas_pedido(_engine, solo_pendientes: bool = True) -> pd.DataFrame:
    """Alertas de componentes faltantes generadas al vender combos."""
    with Session(_engine) as s:
        q = (
            select(
                AlertaPedido.id,
                AlertaPedido.fecha_creada,
                AlertaPedido.combo_sku,
                AlertaPedido.componente_sku,
                AlertaPedido.componente_nombre,
                AlertaPedido.cantidad_faltante,
                AlertaPedido.resuelta,
                AlertaPedido.venta_id,
            )
            .order_by(AlertaPedido.resuelta, AlertaPedido.fecha_creada.desc())
        )
        if solo_pendientes:
            q = q.where(AlertaPedido.resuelta == False)  # noqa: E712
        rows = s.execute(q).all()
    return pd.DataFrame(
        rows,
        columns=[
            "ID", "Fecha", "Combo SKU", "Componente SKU",
            "Componente", "Faltante", "Resuelta", "Venta ID",
        ],
    )


def marcar_alerta_resuelta(_engine, alerta_id: int) -> None:
    """Marca una alerta de pedido como resuelta (sin caché — escritura directa)."""
    with Session(_engine) as s:
        s.execute(
            select(AlertaPedido).where(AlertaPedido.id == alerta_id)
        )  # pre-check
        from sqlalchemy import update as sql_update
        s.execute(
            sql_update(AlertaPedido)
            .where(AlertaPedido.id == alerta_id)
            .values(resuelta=True)
        )
        s.commit()


@st.cache_data(ttl=60)
def get_pedidos_sin_stock(_engine) -> pd.DataFrame:
    """Productos con stock negativo: vendidos más veces de las que había."""
    with Session(_engine) as s:
        rows = s.execute(
            select(
                Producto.sku,
                Producto.nombre,
                Producto.stock_actual,
                func.count(VentaItem.id).label("Veces vendido"),
                func.sum(VentaItem.cantidad).label("Unidades vendidas"),
            )
            .join(VentaItem, VentaItem.sku == Producto.sku)
            .join(Venta, VentaItem.venta_id == Venta.id)
            .where(Producto.stock_actual < 0)
            .where(Venta.estado != EstadoVenta.cancelada)
            .group_by(Producto.sku, Producto.nombre, Producto.stock_actual)
            .order_by(Producto.stock_actual)
        ).all()
    return pd.DataFrame(rows, columns=["SKU", "Nombre", "Stock actual", "Veces vendido", "Unidades vendidas"])


# ---------------------------------------------------------------------------
# Compras
# ---------------------------------------------------------------------------

@st.cache_data(ttl=60)
def get_kpis_compras(_engine) -> dict:
    today = date.today()
    month_start = datetime.combine(today.replace(day=1), datetime.min.time())
    with Session(_engine) as s:
        def _agg(q):
            row = s.execute(q).one()
            return {"count": row[0] or 0, "total": int(row[1] or 0)}

        base = select(func.count(Compra.id), func.coalesce(func.sum(Compra.monto_total), 0))
        mes = _agg(base.where(Compra.fecha >= month_start))
    return {"mes": mes}


@st.cache_data(ttl=300)
def get_tendencia_compras(_engine, start: date, end: date) -> pd.DataFrame:
    with Session(_engine) as s:
        rows = s.execute(
            select(
                func.date(Compra.fecha).label("Fecha"),
                func.coalesce(func.sum(Compra.monto_total), 0).label("Total"),
                func.count(Compra.id).label("Compras"),
            )
            .where(func.date(Compra.fecha) >= start)
            .where(func.date(Compra.fecha) <= end)
            .group_by(func.date(Compra.fecha))
            .order_by(func.date(Compra.fecha))
        ).all()
    return pd.DataFrame(rows, columns=["Fecha", "Total", "Compras"])


@st.cache_data(ttl=300)
def get_compras_por_proveedor(_engine, start: date, end: date) -> pd.DataFrame:
    with Session(_engine) as s:
        rows = s.execute(
            select(
                Compra.proveedor.label("Proveedor"),
                func.count(Compra.id).label("Compras"),
                func.coalesce(func.sum(Compra.monto_total), 0).label("Total"),
            )
            .where(func.date(Compra.fecha) >= start)
            .where(func.date(Compra.fecha) <= end)
            .group_by(Compra.proveedor)
            .order_by(desc("Total"))
        ).all()
    return pd.DataFrame(rows, columns=["Proveedor", "Compras", "Total"])


@st.cache_data(ttl=300)
def get_margen_diario(_engine, start: date, end: date) -> pd.DataFrame:
    """Une tendencia de ventas y compras por fecha para calcular margen bruto diario."""
    with Session(_engine) as s:
        v_rows = s.execute(
            select(
                func.date(Venta.fecha).label("Fecha"),
                func.coalesce(func.sum(Venta.total), 0).label("Ventas_total"),
            )
            .where(func.date(Venta.fecha) >= start)
            .where(func.date(Venta.fecha) <= end)
            .where(Venta.estado != EstadoVenta.cancelada)
            .group_by(func.date(Venta.fecha))
        ).all()

        c_rows = s.execute(
            select(
                func.date(Compra.fecha).label("Fecha"),
                func.coalesce(func.sum(Compra.monto_total), 0).label("Compras_total"),
            )
            .where(func.date(Compra.fecha) >= start)
            .where(func.date(Compra.fecha) <= end)
            .group_by(func.date(Compra.fecha))
        ).all()

    df_v = pd.DataFrame(v_rows, columns=["Fecha", "Ventas_total"])
    df_c = pd.DataFrame(c_rows, columns=["Fecha", "Compras_total"])

    df = pd.merge(df_v, df_c, on="Fecha", how="outer").fillna(0)
    df = df.sort_values("Fecha").reset_index(drop=True)
    return df


@st.cache_data(ttl=60)
def get_compras_recientes(_engine, limit: int = 20) -> pd.DataFrame:
    with Session(_engine) as s:
        rows = s.execute(
            select(
                Compra.id,
                Compra.fecha,
                Compra.proveedor,
                Compra.monto_total,
                func.count(DetalleCompra.id).label("Items"),
            )
            .outerjoin(DetalleCompra, DetalleCompra.compra_id == Compra.id)
            .group_by(Compra.id, Compra.fecha, Compra.proveedor, Compra.monto_total)
            .order_by(desc(Compra.fecha))
            .limit(limit)
        ).all()
    df = pd.DataFrame(rows, columns=["ID", "Fecha", "Proveedor", "Monto total", "Items"])
    if not df.empty:
        df["Fecha"] = pd.to_datetime(df["Fecha"]).dt.strftime("%d/%m/%Y %H:%M")
        df["Monto total"] = df["Monto total"].apply(
            lambda x: f"${int(x):,}".replace(",", ".") if pd.notna(x) and x else "—"
        )
    return df


@st.cache_data(ttl=60)
def get_catalogo_skus(_engine) -> list[dict]:
    """Retorna lista de {sku, nombre} para poblar el selector de SKU en data_editor."""
    with Session(_engine) as s:
        rows = s.execute(
            select(Producto.sku, Producto.nombre).order_by(Producto.nombre)
        ).all()
    return [{"sku": r.sku, "nombre": r.nombre} for r in rows]


@st.cache_data(ttl=300)
def get_ventas_hora_canal(_engine, start: date, end: date) -> pd.DataFrame:
    """Distribución de ventas por hora del día y día de semana (heatmap de actividad)."""
    with Session(_engine) as s:
        rows = s.execute(
            select(
                func.extract("dow", Venta.fecha).label("DiaSemana"),
                func.extract("hour", Venta.fecha).label("Hora"),
                func.count(Venta.id).label("Ventas"),
            )
            .where(func.date(Venta.fecha) >= start)
            .where(func.date(Venta.fecha) <= end)
            .where(Venta.estado != EstadoVenta.cancelada)
            .group_by(func.extract("dow", Venta.fecha), func.extract("hour", Venta.fecha))
            .order_by(func.extract("dow", Venta.fecha), func.extract("hour", Venta.fecha))
        ).all()
    return pd.DataFrame(rows, columns=["DiaSemana", "Hora", "Ventas"])


@st.cache_data(ttl=300)
def get_inventario_sunburst(_engine) -> pd.DataFrame:
    """Distribución de inventario por categoría y producto (sunburst)."""
    with Session(_engine) as s:
        rows = s.execute(
            select(
                func.coalesce(Producto.categoria, "Sin categoría").label("Categoría"),
                Producto.nombre,
                Producto.stock_actual,
            )
            .where(Producto.stock_actual > 0)
            .order_by(Producto.categoria, Producto.nombre)
        ).all()
    return pd.DataFrame(rows, columns=["Categoría", "Producto", "Stock"])
