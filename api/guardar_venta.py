"""
guardar_venta.py
================
Persists a ParsedSale to the database and deducts stock from products.

Flow:
    ParsedSale
        │
        ├─► calculate_amounts()       → subtotal, commission, total (Python, not AI)
        ├─► _get_or_create_channel()  → row in 'canales' table
        ├─► _get_or_create_customer() → row in 'clientes' table (if data exists)
        ├─► _create_sale()            → row in 'ventas' table
        ├─► _create_sale_items()      → rows in 'venta_items' (catalog loaded once)
        ├─► _create_payment()         → row in 'pagos' table
        ├─► _create_shipping()        → row in 'envios' table (if applicable)
        ├─► _create_rappi_detail()    → row in 'rappi_detalles' (if Rappi order)
        └─► _deduct_stock()           → updates productos.stock_actual

Everything happens in a single transaction. If anything fails, nothing is saved.

SKU Matching:
    The full catalog is loaded ONCE before processing items.
    _match_sku() works on that in-memory list: 0 additional DB queries per item.
"""

import json
import re
import sys
import os
from typing import Optional
from dotenv import load_dotenv
from sqlalchemy import select, update
from sqlalchemy.orm import Session

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _root)
load_dotenv(dotenv_path=os.path.join(_root, ".env"), override=True)

from models import (
    Base, Canal, Cliente, Venta, EstadoVenta,
    VentaItem, Pago, Envio, RappiDetalle, Producto,
    ComboComponente, AlertaPedido,
)
from api.motor_ia import ParsedSale, calculate_amounts


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _normalize(text: str) -> str:
    """Lowercases and strips special characters for comparison."""
    return re.sub(r"[^a-z0-9 ]", "", text.lower().strip())


def _tokenize(text: str) -> set[str]:
    """
    Normalizes and splits into tokens, separating digit-letter boundaries.
    Applies minimal stemming: removes trailing 's' on words longer than 3 chars
    so singular/plural match (e.g. 'mancuernas' → 'mancuerna').
    """
    normalized = _normalize(text)
    separated = re.sub(r"(\d)([a-z])", r"\1 \2", normalized)
    separated = re.sub(r"([a-z])(\d)", r"\1 \2", separated)
    tokens = separated.split()
    tokens = [t[:-1] if t.endswith("s") and len(t) > 3 else t for t in tokens]
    return set(tokens)


def _f1_score(keywords: list, catalog_tokens: set) -> float:
    """Computes F1 between query keywords and a set of catalog tokens."""
    if not keywords or not catalog_tokens:
        return 0.0
    matches = sum(1 for kw in keywords if kw in catalog_tokens)
    recall = matches / len(keywords)
    if recall < 0.6:
        return 0.0
    precision = matches / len(catalog_tokens)
    return 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0


def _match_sku(catalog: list, raw_name: str) -> Optional[str]:
    """
    Finds the SKU of a product in the in-memory catalog.

    Matching strategy (in priority order):
    1. Checks the product's 'nombre' using F1-score with a 60% recall threshold.
    2. If no match found via nombre, checks each comma-separated alias in product.alias.

    Args:
        catalog:  List of Producto objects already fetched from the DB.
        raw_name: Product name as it appeared in the message.

    Returns:
        SKU of the best match, or None if threshold is not met.
    """
    raw_tokens = _tokenize(raw_name)
    keywords = [
        t for t in raw_tokens
        if (len(t) >= 2 or t.isdigit()) and t not in {"und", "unidad", "par", "x2", "x4", "x8"}
    ]

    if not keywords or not catalog:
        return None

    best_sku: Optional[str] = None
    best_score = 0.0

    for product in catalog:
        # 1. Try matching against the canonical nombre
        score = _f1_score(keywords, _tokenize(product.nombre))

        # 2. If nombre didn't reach threshold, try each alias
        if score == 0.0 and product.alias:
            for alias_entry in product.alias.split(","):
                alias_entry = alias_entry.strip()
                if not alias_entry:
                    continue
                alias_score = _f1_score(keywords, _tokenize(alias_entry))
                if alias_score > score:
                    score = alias_score

        if score > best_score:
            best_score = score
            best_sku = product.sku

    return best_sku


def _get_or_create_channel(session: Session, channel_name: str) -> Canal:
    channel = session.execute(
        select(Canal).where(Canal.nombre == channel_name)
    ).scalar_one_or_none()

    if not channel:
        channel = Canal(nombre=channel_name)
        session.add(channel)
        session.flush()

    return channel


def _get_or_create_customer(session: Session, parsed_sale: ParsedSale) -> Optional[Cliente]:
    customer_data = parsed_sale.cliente
    if not customer_data:
        return None

    if customer_data.cedula:
        existing = session.execute(
            select(Cliente).where(Cliente.cedula == customer_data.cedula)
        ).scalar_one_or_none()

        if existing:
            if customer_data.telefono and not existing.telefono:
                existing.telefono = customer_data.telefono
            if customer_data.email and not existing.email:
                existing.email = customer_data.email
            return existing

    customer = Cliente(
        nombre=customer_data.nombre,
        cedula=customer_data.cedula,
        telefono=customer_data.telefono,
        email=customer_data.email,
    )
    session.add(customer)
    session.flush()
    return customer


def _create_sale_items(
    session: Session,
    sale: Venta,
    parsed_sale: ParsedSale,
    catalog: list,
) -> list[tuple[str, int]]:
    """
    Creates VentaItem rows using the pre-loaded catalog (0 extra queries per item).

    Returns:
        List of (sku, quantity) for items where a SKU was matched.
    """
    matched_items: list[tuple[str, int]] = []

    for item_data in parsed_sale.items:
        sku = _match_sku(catalog, item_data.producto_nombre_raw)
        item_subtotal = (item_data.precio_unitario or 0) * item_data.cantidad

        item = VentaItem(
            venta_id=sale.id,
            sku=sku,
            producto_nombre_raw=item_data.producto_nombre_raw,
            cantidad=item_data.cantidad,
            precio_unitario=item_data.precio_unitario or 0,
            subtotal=item_subtotal,
        )
        session.add(item)

        if sku:
            matched_items.append((sku, item_data.cantidad))

    return matched_items


def _deduct_stock(
    session: Session,
    matched_items: list[tuple[str, int]],
    sale_id: int,
) -> None:
    """
    Deducts stock for each sold product.

    - If a SKU is a combo, deducts each individual component (not the combo itself).
    - If a component goes negative after deduction, creates an alertas_pedido row
      for restocking follow-up.
    - Negative stock on regular products is intentional: indicates a sale without stock.
    """
    # Load into memory which SKUs are combos and their components
    combo_map: dict[str, list[tuple[str, int]]] = {}
    sold_skus = [sku for sku, _ in matched_items]
    combo_rows = session.execute(
        select(ComboComponente).where(ComboComponente.combo_sku.in_(sold_skus))
    ).scalars().all()
    for cc in combo_rows:
        combo_map.setdefault(cc.combo_sku, []).append((cc.componente_sku, cc.cantidad))

    for sku, quantity in matched_items:
        if sku in combo_map:
            # Combo: deduct each component × quantity sold of the combo
            for comp_sku, qty_per_combo in combo_map[sku]:
                total_qty = qty_per_combo * quantity
                product = session.execute(
                    select(Producto).where(Producto.sku == comp_sku)
                ).scalar_one_or_none()
                if product is None:
                    continue
                stock_before = product.stock_actual
                session.execute(
                    update(Producto)
                    .where(Producto.sku == comp_sku)
                    .values(stock_actual=Producto.stock_actual - total_qty)
                )
                stock_after = stock_before - total_qty
                if stock_after < 0:
                    session.add(AlertaPedido(
                        venta_id=sale_id,
                        combo_sku=sku,
                        componente_sku=comp_sku,
                        componente_nombre=product.nombre,
                        cantidad_faltante=abs(stock_after),
                    ))
        else:
            # Regular product: direct deduction
            session.execute(
                update(Producto)
                .where(Producto.sku == sku)
                .values(stock_actual=Producto.stock_actual - quantity)
            )


# ---------------------------------------------------------------------------
# Main function
# ---------------------------------------------------------------------------

def save_sale(session: Session, parsed_sale: ParsedSale, original_text: str) -> Venta:
    """
    Persists a complete ParsedSale to the database.

    - Amounts (subtotal, discount, total) are calculated in Python, not from the LLM.
    - The product catalog is loaded once for all items.
    - Saves the structured JSON and original text for auditing.

    Args:
        session:       Active SQLAlchemy session (without commit).
        parsed_sale:   Output of motor_ia.parse_sale_message().
        original_text: Raw WhatsApp message (for audit trail).

    Returns:
        Newly created Venta object with assigned id.
    """
    amounts = calculate_amounts(parsed_sale)

    channel = _get_or_create_channel(session, parsed_sale.canal)
    customer = _get_or_create_customer(session, parsed_sale)

    extracted_json = json.dumps(parsed_sale.model_dump(), ensure_ascii=False)
    sale = Venta(
        canal_id=channel.id,
        cliente_id=customer.id if customer else None,
        cliente_nombre_raw=(
            parsed_sale.cliente.nombre if parsed_sale.cliente else None
        ),
        subtotal=amounts["subtotal"],
        costo_envio=amounts["costo_envio"],
        descuento=amounts["descuento"],
        total=amounts["total"],
        estado=EstadoVenta.pendiente,
        fuente_referido=parsed_sale.fuente_referido,
        notas=parsed_sale.notas,
        mensaje_original=original_text,
        json_extraido=extracted_json,
    )
    session.add(sale)
    session.flush()

    # Load catalog once for all SKU matching
    catalog = session.execute(select(Producto)).scalars().all()

    matched_items = _create_sale_items(session, sale, parsed_sale, catalog)

    payment_data = parsed_sale.pago
    payment = Pago(
        venta_id=sale.id,
        metodo=payment_data.metodo,
        cuenta_destino=payment_data.cuenta_destino,
        monto=amounts["total"],
        referencia=payment_data.referencia,
    )
    session.add(payment)

    if parsed_sale.envio:
        e = parsed_sale.envio
        shipping = Envio(
            venta_id=sale.id,
            direccion=e.direccion,
            ciudad=e.ciudad,
            departamento=e.departamento,
            codigo_postal=e.codigo_postal,
        )
        session.add(shipping)

    if parsed_sale.rappi_detalle:
        r = parsed_sale.rappi_detalle
        order_type = r.tipo or ("Pro" if "Pro" in parsed_sale.canal else "Regular")
        rappi = RappiDetalle(
            venta_id=sale.id,
            order_id=r.order_id or "sin-id",
            tipo=order_type,
            comision_porcentaje=r.comision_porcentaje,
            comision_monto=amounts["comision_monto"],
        )
        session.add(rappi)

    _deduct_stock(session, matched_items, sale.id)

    return sale


# ---------------------------------------------------------------------------
# Backward-compatible aliases
# ---------------------------------------------------------------------------
guardar_venta = save_sale
_normalizar = _normalize
_tokenizar = _tokenize
_buscar_sku = _match_sku
_obtener_o_crear_canal = _get_or_create_channel
_obtener_o_crear_cliente = _get_or_create_customer
_crear_items = _create_sale_items
_descontar_stock = _deduct_stock
