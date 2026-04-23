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
    VentaItem, Pago, Envio, RappiDetalle, Producto,
    ComboComponente, AlertaPedido,
)
from api.motor_ia import VentaParseada, calcular_montos


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------

def _normalizar(texto: str) -> str:
    """Convierte a minúsculas y elimina caracteres especiales para comparación."""
    return re.sub(r"[^a-z0-9 ]", "", texto.lower().strip())


def _tokenizar(texto: str) -> set[str]:
    """
    Normaliza y divide en tokens separando límites número-letra.
    Aplica stemming básico: quita la "s" final en palabras de más de 3 chars
    para que singular/plural coincidan (mancuernas → mancuerna).
    """
    normalizado = _normalizar(texto)
    separado = re.sub(r"(\d)([a-z])", r"\1 \2", normalizado)
    separado = re.sub(r"([a-z])(\d)", r"\1 \2", separado)
    tokens = separado.split()
    # Stemming mínimo: plural → singular
    tokens = [t[:-1] if t.endswith("s") and len(t) > 3 else t for t in tokens]
    return set(tokens)


def _buscar_sku(productos_catalogo: list, nombre_raw: str) -> Optional[str]:
    """
    Busca el SKU de un producto en el catálogo ya cargado en memoria.

    El catálogo se pasa como lista para evitar una consulta a la BD por cada item.
    Estrategia: overlap de palabras clave con umbral del 60%.
    Los tokens se separan en límites número-letra para que "5kg" coincida con "5".

    Args:
        productos_catalogo: Lista de objetos Producto ya traídos de la BD.
        nombre_raw:         Nombre del producto tal como apareció en el mensaje.

    Returns:
        SKU del mejor match, o None si no supera el umbral.
    """
    tokens_raw = _tokenizar(nombre_raw)
    # Incluir palabras >= 2 chars (ej: "kg", "lb") y dígitos solos (ej: "5", "20")
    palabras_clave = [
        p for p in tokens_raw
        if (len(p) >= 2 or p.isdigit()) and p not in {"und", "unidad", "par", "x2", "x4", "x8"}
    ]

    if not palabras_clave or not productos_catalogo:
        return None

    mejor_match: Optional[str] = None
    mejor_score = 0.0

    for producto in productos_catalogo:
        palabras_catalogo = _tokenizar(producto.nombre)
        coincidencias = sum(1 for p in palabras_clave if p in palabras_catalogo)
        recall = coincidencias / len(palabras_clave)

        if recall < 0.6:
            continue

        # F1 combina recall y precisión: penaliza productos con muchos tokens extra
        # (evita que un kit que contiene el producto gane sobre el producto individual)
        precision = coincidencias / len(palabras_catalogo) if palabras_catalogo else 0
        score = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

        if score > mejor_score:
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


def _descontar_stock(
    session: Session,
    items_con_sku: list[tuple[str, int]],
    venta_id: int,
) -> None:
    """
    Descuenta el stock de cada producto vendido.

    - Si el SKU es un combo, descuenta los componentes individuales (no el combo).
    - Si un componente queda con stock negativo tras la venta, registra una
      fila en alertas_pedido para seguimiento de reposición.
    - Stock negativo en productos normales es intencional: indica venta sin stock.
    """
    # Cargar en memoria qué SKUs son combos y sus componentes
    combo_map: dict[str, list[tuple[str, int]]] = {}
    skus_vendidos = [sku for sku, _ in items_con_sku]
    filas_combo = session.execute(
        select(ComboComponente).where(ComboComponente.combo_sku.in_(skus_vendidos))
    ).scalars().all()
    for cc in filas_combo:
        combo_map.setdefault(cc.combo_sku, []).append((cc.componente_sku, cc.cantidad))

    for sku, cantidad in items_con_sku:
        if sku in combo_map:
            # Combo: descontar cada componente × cantidad vendida del combo
            for comp_sku, cant_por_combo in combo_map[sku]:
                cant_total = cant_por_combo * cantidad
                prod = session.execute(
                    select(Producto).where(Producto.sku == comp_sku)
                ).scalar_one_or_none()
                if prod is None:
                    continue
                stock_antes = prod.stock_actual
                session.execute(
                    update(Producto)
                    .where(Producto.sku == comp_sku)
                    .values(stock_actual=Producto.stock_actual - cant_total)
                )
                stock_despues = stock_antes - cant_total
                if stock_despues < 0:
                    session.add(AlertaPedido(
                        venta_id=venta_id,
                        combo_sku=sku,
                        componente_sku=comp_sku,
                        componente_nombre=prod.nombre,
                        cantidad_faltante=abs(stock_despues),
                    ))
        else:
            # Producto individual: descuento directo
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
        tipo = r.tipo or ("Pro" if "Pro" in venta_parseada.canal else "Regular")
        rappi = RappiDetalle(
            venta_id=venta.id,
            order_id=r.order_id or "sin-id",
            tipo=tipo,
            comision_porcentaje=r.comision_porcentaje,
            comision_monto=montos["comision_monto"],
        )
        session.add(rappi)

    # 10. Descontar stock (con expansión de combos y alertas automáticas)
    _descontar_stock(session, items_con_sku, venta.id)

    return venta
