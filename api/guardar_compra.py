"""
guardar_compra.py
=================
Persists a purchase to the database and adds stock to products.

Flow:
    User-edited DataFrame
        │
        ├─► Insert row into 'compras'
        ├─► Insert rows into 'detalle_compras'
        └─► Add quantity to productos.stock_actual

Everything happens in a single transaction. If anything fails, nothing is saved.
"""

import os
import sys
from typing import Optional

import pandas as pd
from sqlalchemy import select, update
from sqlalchemy.orm import Session

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _root)

from models import Compra, DetalleCompra, Producto
from api.rappi_client import sync_after_purchase


def save_purchase(
    session: Session,
    supplier: Optional[str],
    df: pd.DataFrame,
) -> Compra:
    """
    Persists the purchase from the user-reviewed DataFrame.

    Expected columns in df:
        - producto_nombre_raw     (str)
        - sku                     (str | None)
        - cantidad                (int)
        - precio_costo_unitario   (int | None)

    Args:
        session:   Active SQLAlchemy session (without commit).
        supplier:  Supplier name.
        df:        DataFrame with items reviewed by the user.

    Returns:
        Newly created Compra object.
    """
    total_amount = int(
        (df["cantidad"] * df["precio_costo_unitario"].fillna(0)).sum()
    )

    purchase = Compra(
        proveedor=supplier or None,
        monto_total=total_amount if total_amount > 0 else None,
    )
    session.add(purchase)
    session.flush()

    for _, row in df.iterrows():
        sku = row.get("sku") or None
        if isinstance(sku, str) and sku.strip() == "":
            sku = None

        quantity = int(row["cantidad"])
        cost = int(row["precio_costo_unitario"]) if pd.notna(row.get("precio_costo_unitario")) else None

        detail = DetalleCompra(
            compra_id=purchase.id,
            producto_sku=sku,
            producto_nombre_raw=str(row["producto_nombre_raw"]),
            cantidad=quantity,
            precio_costo_unitario=cost,
        )
        session.add(detail)

        # Add stock only if the SKU exists in the catalog
        if sku:
            product = session.execute(
                select(Producto).where(Producto.sku == sku)
            ).scalar_one_or_none()
            if product:
                new_stock = product.stock_actual + quantity
                session.execute(
                    update(Producto)
                    .where(Producto.sku == sku)
                    .values(stock_actual=new_stock)
                )
                # Sync Rappi: if stock went above 0, re-enable the product
                if product.rappi_product_id:
                    sync_after_purchase(sku, product.rappi_product_id, new_stock)

    return purchase


# Backward-compatible alias
guardar_compra = save_purchase
