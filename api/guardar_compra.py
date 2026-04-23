"""
guardar_compra.py
=================
Persiste una compra en la base de datos y suma stock a los productos.

Flujo:
    DataFrame editado por el usuario
        │
        ├─► Insertar fila en 'compras'
        ├─► Insertar filas en 'detalle_compras'
        └─► Sumar cantidad a productos.stock_actual

Todo ocurre en una sola transacción. Si algo falla, nada se guarda.
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


def guardar_compra(
    session: Session,
    proveedor: Optional[str],
    df: pd.DataFrame,
) -> Compra:
    """
    Persiste la compra desde el DataFrame editado por el usuario.

    Columnas esperadas en df:
        - producto_nombre_raw (str)
        - sku                 (str | None)
        - cantidad            (int)
        - precio_costo_unitario (int | None)

    Args:
        session:    Sesión SQLAlchemy activa (sin commit).
        proveedor:  Nombre del proveedor.
        df:         DataFrame con los items revisados por el usuario.

    Returns:
        Objeto Compra recién creado.
    """
    monto_total = int(
        (df["cantidad"] * df["precio_costo_unitario"].fillna(0)).sum()
    )

    compra = Compra(
        proveedor=proveedor or None,
        monto_total=monto_total if monto_total > 0 else None,
    )
    session.add(compra)
    session.flush()

    for _, row in df.iterrows():
        sku = row.get("sku") or None
        if isinstance(sku, str) and sku.strip() == "":
            sku = None

        cantidad = int(row["cantidad"])
        precio = int(row["precio_costo_unitario"]) if pd.notna(row.get("precio_costo_unitario")) else None

        detalle = DetalleCompra(
            compra_id=compra.id,
            producto_sku=sku,
            producto_nombre_raw=str(row["producto_nombre_raw"]),
            cantidad=cantidad,
            precio_costo_unitario=precio,
        )
        session.add(detalle)

        # Sumar stock solo si el SKU existe en el catálogo
        if sku:
            existe = session.execute(
                select(Producto.sku).where(Producto.sku == sku)
            ).scalar_one_or_none()
            if existe:
                session.execute(
                    update(Producto)
                    .where(Producto.sku == sku)
                    .values(stock_actual=Producto.stock_actual + cantidad)
                )

    return compra
