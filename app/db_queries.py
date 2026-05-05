"""
db_queries.py
=============
All Supabase queries for the Streamlit app.
Uses @st.cache_data / @st.cache_resource to minimize round-trips.
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
    ComboComponente, AlertaPedido, Compra, DetalleCompra, Envio, RappiDetalle,
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
        raise ValueError("DATABASE_URL not configured in .env or st.secrets")
    return create_engine(url, pool_pre_ping=True, pool_recycle=3600)


# ---------------------------------------------------------------------------
# KPIs — short TTL so "today" is always fresh
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
            return {
                "count": row[0] or 0,
                "bruto": int(row[1] or 0),
                "neto": int(row[2] or 0),
                "comisiones": int(row[3] or 0),
            }

        base = (
            select(
                func.count(Venta.id),
                func.coalesce(func.sum(Venta.subtotal), 0),
                func.coalesce(func.sum(Venta.total), 0),
                func.coalesce(func.sum(Venta.descuento), 0),
            )
            .where(Venta.estado != EstadoVenta.cancelada)
        )

        today_kpis = _agg(base.where(Venta.fecha >= today_start).where(Venta.fecha <= today_end))
        month_kpis = _agg(base.where(Venta.fecha >= month_start))

    return {"hoy": today_kpis, "mes": month_kpis}


# ---------------------------------------------------------------------------
# Dashboard chart queries
# ---------------------------------------------------------------------------

@st.cache_data(ttl=300)
def get_sales_by_channel(_engine, start: date, end: date) -> pd.DataFrame:
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
def get_daily_trend(_engine, start: date, end: date) -> pd.DataFrame:
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
def get_top_products(_engine, limit: int = 10) -> pd.DataFrame:
    # Group only by (sku, catalog name) so all sales of the same SKU are
    # summed into one row regardless of how the product was named in each message.
    with Session(_engine) as s:
        rows = s.execute(
            select(
                VentaItem.sku,
                Producto.nombre.label("Producto"),
                func.sum(VentaItem.cantidad).label("Unidades"),
                func.coalesce(func.sum(VentaItem.subtotal), 0).label("Ingresos"),
            )
            .join(Producto, VentaItem.sku == Producto.sku)
            .join(Venta, VentaItem.venta_id == Venta.id)
            .where(Venta.estado != EstadoVenta.cancelada)
            .where(VentaItem.sku.isnot(None))
            .group_by(VentaItem.sku, Producto.nombre)
            .order_by(desc("Unidades"))
            .limit(limit)
        ).all()
    return pd.DataFrame(rows, columns=["SKU", "Producto", "Unidades", "Ingresos"])


@st.cache_data(ttl=300)
def get_top_billers(_engine, limit: int = 10) -> pd.DataFrame:
    """Payment methods ranked by total revenue."""
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
def get_recent_sales(_engine, limit: int = 15) -> pd.DataFrame:
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
# Inventory queries
# ---------------------------------------------------------------------------

@st.cache_data(ttl=60)
def get_inventory(_engine, search: str = "") -> pd.DataFrame:
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
def get_stock_alerts(_engine, umbral: int = 3) -> pd.DataFrame:
    """
    umbral=-1 → only negative stock (< 0)
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
def get_combo_virtual_stock(_engine) -> pd.DataFrame:
    """
    Calculates the virtual stock for each combo:
        virtual_stock = min( floor(component.stock_actual / qty_per_combo) )
    The component with the lowest proportional availability is the bottleneck.
    """
    with Session(_engine) as s:
        combo_skus = s.execute(
            select(ComboComponente.combo_sku).distinct()
        ).scalars().all()

        if not combo_skus:
            return pd.DataFrame(columns=["SKU", "Combo", "Stock Virtual", "Cuello de botella"])

        rows = []
        for combo_sku in combo_skus:
            combo_product = s.execute(
                select(Producto).where(Producto.sku == combo_sku)
            ).scalar_one_or_none()
            if not combo_product:
                continue

            components = s.execute(
                select(ComboComponente, Producto)
                .join(Producto, ComboComponente.componente_sku == Producto.sku)
                .where(ComboComponente.combo_sku == combo_sku)
            ).all()

            if not components:
                continue

            virtual_stock = None
            bottleneck = None
            for cc, prod in components:
                sv = prod.stock_actual // cc.cantidad if cc.cantidad > 0 else 0
                if virtual_stock is None or sv < virtual_stock:
                    virtual_stock = sv
                    bottleneck = f"{prod.nombre} (×{cc.cantidad})"

            rows.append({
                "SKU": combo_sku,
                "Combo": combo_product.nombre,
                "Stock Virtual": virtual_stock if virtual_stock is not None else 0,
                "Cuello de botella": bottleneck or "—",
            })

    return pd.DataFrame(rows)


@st.cache_data(ttl=30)
def get_order_alerts(_engine, solo_pendientes: bool = True) -> pd.DataFrame:
    """Missing component alerts generated when selling combos."""
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


def mark_alert_resolved(_engine, alert_id: int) -> None:
    """Marks a purchase alert as resolved (no cache — direct write)."""
    with Session(_engine) as s:
        from sqlalchemy import update as sql_update
        s.execute(
            sql_update(AlertaPedido)
            .where(AlertaPedido.id == alert_id)
            .values(resuelta=True)
        )
        s.commit()


@st.cache_data(ttl=60)
def get_orders_without_stock(_engine) -> pd.DataFrame:
    """Products with negative stock: sold more times than available units."""
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
# Purchase queries
# ---------------------------------------------------------------------------

@st.cache_data(ttl=60)
def get_purchase_kpis(_engine) -> dict:
    today = date.today()
    month_start = datetime.combine(today.replace(day=1), datetime.min.time())
    with Session(_engine) as s:
        def _agg(q):
            row = s.execute(q).one()
            return {"count": row[0] or 0, "total": int(row[1] or 0)}

        base = select(func.count(Compra.id), func.coalesce(func.sum(Compra.monto_total), 0))
        month_kpis = _agg(base.where(Compra.fecha >= month_start))
    return {"mes": month_kpis}


@st.cache_data(ttl=300)
def get_purchase_trend(_engine, start: date, end: date) -> pd.DataFrame:
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
def get_purchases_by_supplier(_engine, start: date, end: date) -> pd.DataFrame:
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
def get_daily_margin(_engine, start: date, end: date) -> pd.DataFrame:
    """Joins daily sales and purchases to compute gross daily margin."""
    with Session(_engine) as s:
        sales_rows = s.execute(
            select(
                func.date(Venta.fecha).label("Fecha"),
                func.coalesce(func.sum(Venta.total), 0).label("Ventas_total"),
            )
            .where(func.date(Venta.fecha) >= start)
            .where(func.date(Venta.fecha) <= end)
            .where(Venta.estado != EstadoVenta.cancelada)
            .group_by(func.date(Venta.fecha))
        ).all()

        purchase_rows = s.execute(
            select(
                func.date(Compra.fecha).label("Fecha"),
                func.coalesce(func.sum(Compra.monto_total), 0).label("Compras_total"),
            )
            .where(func.date(Compra.fecha) >= start)
            .where(func.date(Compra.fecha) <= end)
            .group_by(func.date(Compra.fecha))
        ).all()

    df_sales = pd.DataFrame(sales_rows, columns=["Fecha", "Ventas_total"])
    df_purchases = pd.DataFrame(purchase_rows, columns=["Fecha", "Compras_total"])

    df = pd.merge(df_sales, df_purchases, on="Fecha", how="outer").fillna(0)
    return df.sort_values("Fecha").reset_index(drop=True)


@st.cache_data(ttl=60)
def get_recent_purchases(_engine, limit: int = 20) -> pd.DataFrame:
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
def get_sku_catalog(_engine) -> list[dict]:
    """Returns list of {sku, nombre} to populate the SKU selector in data_editor."""
    with Session(_engine) as s:
        rows = s.execute(
            select(Producto.sku, Producto.nombre).order_by(Producto.nombre)
        ).all()
    return [{"sku": r.sku, "nombre": r.nombre} for r in rows]


# ---------------------------------------------------------------------------
# Sale detail (single sale, all relations loaded)
# ---------------------------------------------------------------------------

@st.cache_data(ttl=30)
def get_sale_detail(_engine, sale_id: int) -> Optional[dict]:
    """Returns all fields of a single sale: items, client, payments, shipping, rappi."""
    with Session(_engine) as s:
        sale = s.execute(select(Venta).where(Venta.id == sale_id)).scalar_one_or_none()
        if not sale:
            return None

        canal = s.execute(select(Canal).where(Canal.id == sale.canal_id)).scalar_one_or_none()
        cliente = None
        if sale.cliente_id:
            cliente = s.execute(select(Cliente).where(Cliente.id == sale.cliente_id)).scalar_one_or_none()

        item_rows = s.execute(
            select(VentaItem, Producto)
            .outerjoin(Producto, VentaItem.sku == Producto.sku)
            .where(VentaItem.venta_id == sale_id)
        ).all()

        pagos = s.execute(select(Pago).where(Pago.venta_id == sale_id)).scalars().all()
        envio = s.execute(select(Envio).where(Envio.venta_id == sale_id)).scalar_one_or_none()
        rappi = s.execute(select(RappiDetalle).where(RappiDetalle.venta_id == sale_id)).scalar_one_or_none()

        return {
            "id": sale.id,
            "fecha": sale.fecha,
            "canal": canal.nombre if canal else "—",
            "estado": sale.estado,
            "cliente_nombre": sale.cliente_nombre_raw or (cliente.nombre if cliente else None),
            "cliente_cedula": cliente.cedula if cliente else None,
            "cliente_telefono": cliente.telefono if cliente else None,
            "subtotal": sale.subtotal,
            "costo_envio": sale.costo_envio,
            "descuento": sale.descuento,
            "total": sale.total,
            "notas": sale.notas,
            "fuente_referido": sale.fuente_referido,
            "mensaje_original": sale.mensaje_original,
            "items": [
                {
                    "nombre_raw": it.producto_nombre_raw,
                    "sku": it.sku,
                    "nombre_catalogo": prod.nombre if prod else None,
                    "cantidad": it.cantidad,
                    "precio_unitario": it.precio_unitario,
                    "subtotal": it.subtotal,
                }
                for it, prod in item_rows
            ],
            "pagos": [
                {
                    "metodo": p.metodo,
                    "cuenta_destino": p.cuenta_destino,
                    "monto": p.monto,
                    "referencia": p.referencia,
                }
                for p in pagos
            ],
            "envio": {
                "direccion": envio.direccion,
                "ciudad": envio.ciudad,
                "departamento": envio.departamento,
            } if envio else None,
            "rappi": {
                "order_id": rappi.order_id,
                "tipo": rappi.tipo,
                "comision_porcentaje": rappi.comision_porcentaje,
                "comision_monto": rappi.comision_monto,
            } if rappi else None,
        }


# ---------------------------------------------------------------------------
# Money by payment account — for dashboard
# ---------------------------------------------------------------------------

@st.cache_data(ttl=120)
def get_money_by_account(_engine, start: date, end: date) -> pd.DataFrame:
    """Totals per payment method + account within the given date range."""
    with Session(_engine) as s:
        rows = s.execute(
            select(
                Pago.metodo.label("Método"),
                Pago.cuenta_destino.label("Cuenta"),
                func.count(Venta.id).label("Ventas"),
                func.coalesce(func.sum(Venta.total), 0).label("Total"),
            )
            .join(Venta, Pago.venta_id == Venta.id)
            .where(func.date(Venta.fecha) >= start)
            .where(func.date(Venta.fecha) <= end)
            .where(Venta.estado != EstadoVenta.cancelada)
            .group_by(Pago.metodo, Pago.cuenta_destino)
            .order_by(desc("Total"))
        ).all()
    return pd.DataFrame(rows, columns=["Método", "Cuenta", "Ventas", "Total"])


# ---------------------------------------------------------------------------
# Sales list for the auditor page
# ---------------------------------------------------------------------------

@st.cache_data(ttl=30)
def get_all_sales(
    _engine,
    start: date,
    end: date,
    estado: Optional[str] = None,
    canal_nombre: Optional[str] = None,
    limit: int = 100,
) -> pd.DataFrame:
    """Filterable sales list used by the auditor/editor page."""
    with Session(_engine) as s:
        q = (
            select(
                Venta.id,
                Venta.fecha,
                Canal.nombre.label("Canal"),
                func.coalesce(Venta.cliente_nombre_raw, "—").label("Cliente"),
                Venta.subtotal,
                Venta.total,
                Venta.estado,
                Pago.metodo.label("Pago"),
                Pago.cuenta_destino.label("Cuenta"),
                Venta.notas,
            )
            .join(Canal, Venta.canal_id == Canal.id)
            .outerjoin(Pago, Pago.venta_id == Venta.id)
            .where(func.date(Venta.fecha) >= start)
            .where(func.date(Venta.fecha) <= end)
        )
        if estado:
            q = q.where(Venta.estado == estado)
        if canal_nombre:
            q = q.where(Canal.nombre == canal_nombre)
        q = q.order_by(desc(Venta.fecha)).limit(limit)
        rows = s.execute(q).all()

    df = pd.DataFrame(rows, columns=["ID", "Fecha", "Canal", "Cliente", "Bruto", "Total", "Estado", "Pago", "Cuenta", "Notas"])
    if not df.empty:
        df["Fecha"] = pd.to_datetime(df["Fecha"]).dt.strftime("%d/%m/%Y %H:%M")
        df["Total_num"] = df["Total"]
        df["Total"] = df["Total"].apply(lambda x: f"${int(x):,}".replace(",", "."))
        df["Bruto"] = df["Bruto"].apply(lambda x: f"${int(x):,}".replace(",", "."))
    return df


@st.cache_data(ttl=60)
def get_kpis_period(_engine, start: date, end: date) -> dict:
    """Sales + purchase KPIs aggregated for an arbitrary date range (dashboard filter)."""
    start_dt = datetime.combine(start, datetime.min.time())
    end_dt   = datetime.combine(end,   datetime.max.time())
    with Session(_engine) as s:
        v = s.execute(
            select(
                func.count(Venta.id),
                func.coalesce(func.sum(Venta.subtotal), 0),
                func.coalesce(func.sum(Venta.total), 0),
            )
            .where(Venta.estado != EstadoVenta.cancelada)
            .where(Venta.fecha >= start_dt)
            .where(Venta.fecha <= end_dt)
        ).one()
        c = s.execute(
            select(
                func.count(Compra.id),
                func.coalesce(func.sum(Compra.monto_total), 0),
            )
            .where(Compra.fecha >= start_dt)
            .where(Compra.fecha <= end_dt)
        ).one()
    return {
        "ventas":  {"count": v[0] or 0, "bruto": int(v[1] or 0), "neto": int(v[2] or 0)},
        "compras": {"count": c[0] or 0, "total": int(c[1] or 0)},
    }


def update_sale(engine, sale_id: int, new_estado: str, new_notas: Optional[str]) -> None:
    """Updates estado and notas of a sale. Direct write, no cache."""
    from sqlalchemy import update as sql_update
    with Session(engine) as s:
        s.execute(
            sql_update(Venta)
            .where(Venta.id == sale_id)
            .values(estado=new_estado, notas=new_notas)
        )
        s.commit()


def update_sale_items(
    engine,
    sale_id: int,
    items: list[dict],
    new_estado: str,
    new_notas: Optional[str],
) -> None:
    """
    Replaces all venta_items of a sale and recalculates subtotal/total.

    Keeps existing costo_envio and descuento; total = subtotal + envio - descuento.
    Does NOT adjust stock — stock corrections must be done manually or via a compra.

    Each item dict must have:
        nombre_raw      str
        sku             str | None
        cantidad        int
        precio_unitario int
    """
    from sqlalchemy import update as sql_update, delete as sql_delete
    with Session(engine) as s:
        sale = s.execute(select(Venta).where(Venta.id == sale_id)).scalar_one()

        s.execute(sql_delete(VentaItem).where(VentaItem.venta_id == sale_id))

        new_subtotal = 0
        for item in items:
            qty = max(int(item.get("cantidad") or 1), 1)
            precio = max(int(item.get("precio_unitario") or 0), 0)
            item_sub = qty * precio
            new_subtotal += item_sub
            s.add(VentaItem(
                venta_id=sale_id,
                sku=item.get("sku") or None,
                producto_nombre_raw=str(item["nombre_raw"]).strip() or "—",
                cantidad=qty,
                precio_unitario=precio,
                subtotal=item_sub,
            ))

        new_total = max(new_subtotal + (sale.costo_envio or 0) - (sale.descuento or 0), 0)

        s.execute(
            sql_update(Venta)
            .where(Venta.id == sale_id)
            .values(
                subtotal=new_subtotal,
                total=new_total,
                estado=new_estado,
                notas=new_notas,
            )
        )
        s.commit()


# ---------------------------------------------------------------------------
# Purchase detail (single purchase, all line items loaded)
# ---------------------------------------------------------------------------

@st.cache_data(ttl=30)
def get_purchase_detail(_engine, purchase_id: int) -> Optional[dict]:
    """Returns all fields of a single purchase: header + line items with catalog names."""
    with Session(_engine) as s:
        compra = s.execute(select(Compra).where(Compra.id == purchase_id)).scalar_one_or_none()
        if not compra:
            return None

        item_rows = s.execute(
            select(DetalleCompra, Producto)
            .outerjoin(Producto, DetalleCompra.producto_sku == Producto.sku)
            .where(DetalleCompra.compra_id == purchase_id)
        ).all()

        return {
            "id": compra.id,
            "fecha": compra.fecha,
            "proveedor": compra.proveedor or "—",
            "monto_total": compra.monto_total,
            "items": [
                {
                    "nombre_raw": dc.producto_nombre_raw,
                    "sku": dc.producto_sku,
                    "nombre_catalogo": prod.nombre if prod else None,
                    "cantidad": dc.cantidad,
                    "precio_costo_unitario": dc.precio_costo_unitario,
                    "subtotal": (dc.cantidad * dc.precio_costo_unitario)
                                if dc.precio_costo_unitario else None,
                }
                for dc, prod in item_rows
            ],
        }


# ---------------------------------------------------------------------------
# Purchase editing — reverses old stock, applies new stock, updates header
# ---------------------------------------------------------------------------

def update_purchase_items(
    engine,
    purchase_id: int,
    items: list[dict],
    new_proveedor: Optional[str],
) -> None:
    """
    Replaces all detalle_compras of a purchase and adjusts stock accordingly.

    Procedure (single transaction):
        1. Reverse stock additions from old items (subtract old quantities).
        2. Delete old detalle_compras rows.
        3. Insert new detalle_compras rows and add new quantities to stock.
        4. Recalculate and update compra.monto_total and proveedor.

    Each item dict must have:
        nombre_raw              str
        sku                     str | None
        cantidad                int
        precio_costo_unitario   int | None
    """
    from sqlalchemy import update as sql_update, delete as sql_delete
    with Session(engine) as s:
        # 1. Reverse old stock additions using a column expression so the DB
        #    does the arithmetic — avoids ORM staleness if the same SKU appears
        #    in multiple old rows or in both the reverse and apply phases.
        old_items = s.execute(
            select(DetalleCompra).where(DetalleCompra.compra_id == purchase_id)
        ).scalars().all()

        for old_item in old_items:
            if old_item.producto_sku:
                s.execute(
                    sql_update(Producto)
                    .where(Producto.sku == old_item.producto_sku)
                    .values(stock_actual=Producto.stock_actual - old_item.cantidad)
                )

        # 2. Delete old items
        s.execute(sql_delete(DetalleCompra).where(DetalleCompra.compra_id == purchase_id))

        # 3. Insert new items and apply stock additions (same atomic pattern)
        new_total = 0
        for item in items:
            sku = item.get("sku") or None
            if isinstance(sku, str) and not sku.strip():
                sku = None
            quantity = max(int(item.get("cantidad") or 1), 1)
            cost = int(item["precio_costo_unitario"]) if item.get("precio_costo_unitario") else None
            if cost:
                new_total += quantity * cost

            s.add(DetalleCompra(
                compra_id=purchase_id,
                producto_sku=sku,
                producto_nombre_raw=str(item["nombre_raw"]).strip() or "—",
                cantidad=quantity,
                precio_costo_unitario=cost,
            ))

            if sku:
                s.execute(
                    sql_update(Producto)
                    .where(Producto.sku == sku)
                    .values(stock_actual=Producto.stock_actual + quantity)
                )

        # 4. Update purchase header
        s.execute(
            sql_update(Compra)
            .where(Compra.id == purchase_id)
            .values(
                proveedor=new_proveedor or None,
                monto_total=new_total if new_total > 0 else None,
            )
        )
        s.commit()


# ---------------------------------------------------------------------------
# Backward-compatible aliases (used by streamlit_app and legacy scripts)
# ---------------------------------------------------------------------------
get_ventas_por_canal = get_sales_by_channel
get_tendencia_diaria = get_daily_trend
get_top_productos = get_top_products
get_top_facturadores = get_top_billers
get_ventas_recientes = get_recent_sales
get_inventario = get_inventory
get_alertas_stock = get_stock_alerts
get_combos_stock_virtual = get_combo_virtual_stock
get_alertas_pedido = get_order_alerts
marcar_alerta_resuelta = mark_alert_resolved
get_pedidos_sin_stock = get_orders_without_stock
get_kpis_compras = get_purchase_kpis
get_tendencia_compras = get_purchase_trend
get_compras_por_proveedor = get_purchases_by_supplier
get_margen_diario = get_daily_margin
get_compras_recientes = get_recent_purchases
get_catalogo_skus = get_sku_catalog
