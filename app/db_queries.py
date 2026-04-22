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
    Venta, VentaItem, Producto, Canal, Pago, Cliente, EstadoVenta
)


@st.cache_resource
def get_engine():
    url = os.getenv("DATABASE_URL")
    if not url:
        raise ValueError("DATABASE_URL no configurada en .env")
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
