"""
guardar_venta.py
================
Persiste una VentaParseada en la base de datos y descuenta el stock de los productos.

Flujo:
    VentaParseada
        │
        ├─► calcular_montos()          → subtotal, comisión, total (Python, no IA)
        ├─► _obtener_o_crear_canal()   → fila en tabla 'canales'
        ├─► _obtener_o_crear_cliente() → fila en tabla 'clientes' (si hay datos)
        ├─► _crear_venta()             → fila en tabla 'ventas'
        ├─► _crear_items()             → filas en 'venta_items' (catalogo cargado 1 sola vez)
        ├─► _crear_pago()              → fila en tabla 'pagos'
        ├─► _crear_envio()             → fila en tabla 'envios' (si aplica)
        ├─► _crear_rappi_detalle()     → fila en 'rappi_detalles' (si es Rappi)
        └─► _descontar_stock()         → actualiza productos.stock_actual

Todo ocurre en una sola transacción. Si algo falla, nada se guarda.

Matching de SKU:
    El catálogo completo se carga UNA sola vez antes de procesar los items.
    _buscar_sku() trabaja sobre esa lista en memoria: 0 consultas adicionales por item.
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
    VentaItem, Pago, Envio, RappiDetalle, Producto
)
from api.motor_ia import VentaParseada, calcular_montos


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------

def _normalizar(texto: str) -> str:
    """Convierte a minúsculas y elimina caracteres especiales para comparación."""
    return re.sub(r"[^a-z0-9 ]", "", texto.lower().strip())


def _buscar_sku(productos_catalogo: list, nombre_raw: str) -> Optional[str]:
    """
    Busca el SKU de un producto en el catálogo ya cargado en memoria.

    El catálogo se pasa como lista para evitar una consulta a la BD por cada item.
    Estrategia: overlap de palabras clave con umbral del 60%.

    Args:
        productos_catalogo: Lista de objetos Producto ya traídos de la BD.
        nombre_raw:         Nombre del producto tal como apareció en el mensaje.

    Returns:
        SKU del mejor match, o None si no supera el umbral.
    """
    palabras = _normalizar(nombre_raw).split()
    palabras_clave = [p for p in palabras if len(p) > 2 and p not in {"und", "unidad"}]

    if not palabras_clave or not productos_catalogo:
        return None

    mejor_match: Optional[str] = None
    mejor_score = 0.0

    for producto in productos_catalogo:
        nombre_normalizado = _normalizar(producto.nombre)
        coincidencias = sum(1 for p in palabras_clave if p in nombre_normalizado)
        score = coincidencias / len(palabras_clave)

        if score > mejor_score and score >= 0.6:
            mejor_score = score
            mejor_match = producto.sku

    return mejor_match


def _obtener_o_crear_canal(session: Session, nombre_canal: str) -> Canal:
    canal = session.execute(
        select(Canal).where(Canal.nombre == nombre_canal)
    ).scalar_one_or_none()

    if not canal:
        canal = Canal(nombre=nombre_canal)
        session.add(canal)
        session.flush()

    return canal


def _obtener_o_crear_cliente(session: Session, venta_parseada: VentaParseada) -> Optional[Cliente]:
    datos = venta_parseada.cliente
    if not datos:
        return None

    if datos.cedula:
        cliente = session.execute(
            select(Cliente).where(Cliente.cedula == datos.cedula)
        ).scalar_one_or_none()

        if cliente:
            if datos.telefono and not cliente.telefono:
                cliente.telefono = datos.telefono
            if datos.email and not cliente.email:
                cliente.email = datos.email
            return cliente

    cliente = Cliente(
        nombre=datos.nombre,
        cedula=datos.cedula,
        telefono=datos.telefono,
        email=datos.email,
    )
    session.add(cliente)
    session.flush()
    return cliente


def _crear_items(
    session: Session,
    venta: Venta,
    venta_parseada: VentaParseada,
    productos_catalogo: list,
) -> list[tuple[str, int]]:
    """
    Crea los VentaItem usando el catálogo precargado (0 queries extra por item).

    Returns:
        Lista de (sku, cantidad) para los items con SKU matcheado.
    """
    items_con_sku: list[tuple[str, int]] = []

    for item_data in venta_parseada.items:
        sku = _buscar_sku(productos_catalogo, item_data.producto_nombre_raw)
        subtotal_item = (item_data.precio_unitario or 0) * item_data.cantidad

        item = VentaItem(
            venta_id=venta.id,
            sku=sku,
            producto_nombre_raw=item_data.producto_nombre_raw,
            cantidad=item_data.cantidad,
            precio_unitario=item_data.precio_unitario or 0,
            subtotal=subtotal_item,
        )
        session.add(item)

        if sku:
            items_con_sku.append((sku, item_data.cantidad))

    return items_con_sku


def _descontar_stock(session: Session, items_con_sku: list[tuple[str, int]]) -> None:
    """
    Descuenta el stock de cada producto vendido.
    Stock negativo es intencional: señala venta sin stock registrado.
    """
    for sku, cantidad in items_con_sku:
        session.execute(
            update(Producto)
            .where(Producto.sku == sku)
            .values(stock_actual=Producto.stock_actual - cantidad)
        )


# ---------------------------------------------------------------------------
# Función principal
# ---------------------------------------------------------------------------

def guardar_venta(session: Session, venta_parseada: VentaParseada, texto_original: str) -> Venta:
    """
    Persiste una VentaParseada completa en la base de datos.

    - Los montos (subtotal, descuento, total) se calculan en Python, no vienen del LLM.
    - El catálogo de productos se carga una sola vez para todos los items.
    - Guarda el JSON estructurado y el texto original para auditoría.

    Args:
        session:         Sesión SQLAlchemy activa (sin commit).
        venta_parseada:  Output de motor_ia.parsear_mensaje().
        texto_original:  Mensaje crudo de WhatsApp (para auditoría).

    Returns:
        Objeto Venta recién creado con id asignado.
    """
    # 1. Calcular montos en Python
    montos = calcular_montos(venta_parseada)

    # 2. Canal
    canal = _obtener_o_crear_canal(session, venta_parseada.canal)

    # 3. Cliente
    cliente = _obtener_o_crear_cliente(session, venta_parseada)

    # 4. Venta principal
    json_extraido = json.dumps(venta_parseada.model_dump(), ensure_ascii=False)
    venta = Venta(
        canal_id=canal.id,
        cliente_id=cliente.id if cliente else None,
        cliente_nombre_raw=(
            venta_parseada.cliente.nombre if venta_parseada.cliente else None
        ),
        subtotal=montos["subtotal"],
        costo_envio=montos["costo_envio"],
        descuento=montos["descuento"],
        total=montos["total"],
        estado=EstadoVenta.pendiente,
        fuente_referido=venta_parseada.fuente_referido,
        notas=venta_parseada.notas,
        mensaje_original=texto_original,
        json_extraido=json_extraido,
    )
    session.add(venta)
    session.flush()

    # 5. Cargar catálogo UNA sola vez para matching de SKU
    productos_catalogo = session.execute(select(Producto)).scalars().all()

    # 6. Items + matching SKU
    items_con_sku = _crear_items(session, venta, venta_parseada, productos_catalogo)

    # 7. Pago
    pago_data = venta_parseada.pago
    pago = Pago(
        venta_id=venta.id,
        metodo=pago_data.metodo,
        cuenta_destino=pago_data.cuenta_destino,
        monto=montos["total"],
        referencia=pago_data.referencia,
    )
    session.add(pago)

    # 8. Envío
    if venta_parseada.envio:
        e = venta_parseada.envio
        envio = Envio(
            venta_id=venta.id,
            direccion=e.direccion,
            ciudad=e.ciudad,
            departamento=e.departamento,
            codigo_postal=e.codigo_postal,
        )
        session.add(envio)

    # 9. Detalle Rappi (comision_monto calculado en Python)
    if venta_parseada.rappi_detalle:
        r = venta_parseada.rappi_detalle
        rappi = RappiDetalle(
            venta_id=venta.id,
            order_id=r.order_id,
            tipo=r.tipo,
            comision_porcentaje=r.comision_porcentaje,
            comision_monto=montos["comision_monto"],
        )
        session.add(rappi)

    # 10. Descontar stock
    _descontar_stock(session, items_con_sku)

    return venta
