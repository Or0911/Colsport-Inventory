"""
procesar_venta.py
=================
Script de línea de comandos para procesar un mensaje de venta.

Uso:
    # Desde la raíz del proyecto, con el entorno virtual activado:

    # Opción 1: pegar el mensaje directamente como argumento
    python scripts/procesar_venta.py "VENTA LOCAL\nDiby\n1 und banda de látex azul wonder\n12.100"

    # Opción 2: leer el mensaje desde un archivo de texto
    python scripts/procesar_venta.py --archivo mensaje.txt

    # Opción 3: modo interactivo (pegar y presionar Enter dos veces)
    python scripts/procesar_venta.py --interactivo

Salida:
    - JSON extraído por la IA
    - Confirmación de lo guardado en la base de datos
    - Resumen financiero (bruto / comisión / neto / envío / método de pago)
    - Stock actualizado de los productos matcheados
"""

import os
import sys
import json
import argparse

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _root)

from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(_root, ".env"), override=True)

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from api.motor_ia import parsear_mensaje, calcular_montos
from api.guardar_venta import guardar_venta
from models import Producto


# ---------------------------------------------------------------------------
# Helpers de presentación
# ---------------------------------------------------------------------------

def _separador(titulo: str = "") -> None:
    linea = "=" * 55
    if titulo:
        print(f"\n{linea}")
        print(f"  {titulo}")
        print(linea)
    else:
        print(linea)


def _fmt_cop(monto: int) -> str:
    return f"${monto:,.0f} COP".replace(",", ".")


def _mostrar_resultado(venta_parseada, venta_guardada, montos: dict, session) -> None:
    """Imprime un resumen legible de la venta procesada."""

    _separador("RESULTADO DEL PARSEO (IA)")
    print(json.dumps(venta_parseada.model_dump(), indent=2, ensure_ascii=False))

    _separador("GUARDADO EN BASE DE DATOS")
    print(f"  Venta ID    : {venta_guardada.id}")
    print(f"  Estado      : {venta_guardada.estado.value}")
    print(f"  Items       : {len(venta_parseada.items)}")
    for i, item in enumerate(venta_parseada.items, 1):
        precio_str = _fmt_cop(item.precio_unitario) if item.precio_unitario else "precio no extraído"
        print(f"    {i}. {item.cantidad}x {item.producto_nombre_raw}  ({precio_str})")

    _separador("RESUMEN FINANCIERO")
    canal = venta_parseada.canal
    cliente = venta_parseada.cliente.nombre if venta_parseada.cliente else "(sin datos)"
    metodo_pago = venta_parseada.pago.metodo
    if venta_parseada.pago.cuenta_destino:
        metodo_pago += f" → {venta_parseada.pago.cuenta_destino}"

    print(f"  Canal       : {canal}")
    print(f"  Cliente     : {cliente}")
    print(f"  Items       : {len(venta_parseada.items)}")
    print(f"  Bruto       : {_fmt_cop(montos['subtotal'])}")
    if montos["comision_monto"]:
        pct = venta_parseada.rappi_detalle.comision_porcentaje if venta_parseada.rappi_detalle else 0
        print(f"  Comisión    : -{_fmt_cop(montos['comision_monto'])}  ({pct:.0f}%)")
    if montos["costo_envio"]:
        print(f"  Envío       : +{_fmt_cop(montos['costo_envio'])}")
    print(f"  Neto        : {_fmt_cop(montos['total'])}")
    print(f"  Pago        : {metodo_pago}")

    # Consultar stock de todos los SKUs matcheados en una sola operación
    _separador("STOCK ACTUALIZADO")
    skus_matcheados = [item.sku for item in venta_guardada.items if item.sku]

    if skus_matcheados:
        productos_dict = {
            p.sku: p
            for p in session.execute(
                select(Producto).where(Producto.sku.in_(skus_matcheados))
            ).scalars().all()
        }
        for item in venta_guardada.items:
            if item.sku and item.sku in productos_dict:
                p = productos_dict[item.sku]
                alerta = "  *** STOCK NEGATIVO - REVISAR ***" if p.stock_actual < 0 else ""
                print(f"  [{item.sku}] {p.nombre}")
                print(f"    Stock actual: {p.stock_actual}{alerta}")
    else:
        print("  Ningún producto fue matcheado con el catálogo.")
        print("  Verifica que los productos existan en la tabla 'productos'.")

    _separador()


# ---------------------------------------------------------------------------
# Lógica de entrada de texto
# ---------------------------------------------------------------------------

def _leer_interactivo() -> str:
    """Modo interactivo: el usuario pega el mensaje y presiona Enter dos veces."""
    print("Pega el mensaje de venta y presiona Enter dos veces cuando termines:\n")
    lineas = []
    while True:
        try:
            linea = input()
            lineas.append(linea)
        except EOFError:
            break
        if len(lineas) >= 2 and lineas[-1] == "" and lineas[-2] == "":
            break
    return "\n".join(lineas).strip()


def _leer_desde_archivo(path: str) -> str:
    if not os.path.exists(path):
        print(f"[ERROR] Archivo no encontrado: {path}")
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Procesa un mensaje de venta de WhatsApp y lo guarda en la BD."
    )
    grupo = parser.add_mutually_exclusive_group()
    grupo.add_argument("--archivo", "-f", metavar="RUTA",
                       help="Ruta a un archivo .txt con el mensaje de venta")
    grupo.add_argument("--interactivo", "-i", action="store_true",
                       help="Pega el mensaje directamente en la terminal")
    parser.add_argument("mensaje", nargs="?",
                        help="El mensaje de venta como texto (entre comillas)")
    args = parser.parse_args()

    if args.archivo:
        texto = _leer_desde_archivo(args.archivo)
    elif args.interactivo:
        texto = _leer_interactivo()
    elif args.mensaje:
        texto = args.mensaje.replace("\\n", "\n")
    else:
        print("[ERROR] Debes proporcionar un mensaje. Usa --help para ver las opciones.")
        sys.exit(1)

    if not texto:
        print("[ERROR] El mensaje está vacío.")
        sys.exit(1)

    if not os.getenv("OPENAI_API_KEY"):
        print("[ERROR] OPENAI_API_KEY no está definida en el archivo .env")
        sys.exit(1)

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("[ERROR] DATABASE_URL no está definida en el archivo .env")
        sys.exit(1)

    # --- Paso 1: Parsear con IA ---
    print("\nParsando mensaje con IA...")
    try:
        venta_parseada = parsear_mensaje(texto)
        print("Parseo exitoso.")
    except Exception as e:
        print(f"[ERROR] Falló el parseo: {e}")
        sys.exit(1)

    # --- Calcular montos en Python ---
    montos = calcular_montos(venta_parseada)

    # --- Paso 2: Guardar en BD ---
    print("Guardando en base de datos...")
    engine = create_engine(database_url)

    try:
        with Session(engine) as session:
            venta_guardada = guardar_venta(session, venta_parseada, texto)
            session.commit()
            session.refresh(venta_guardada)
            venta_guardada.items  # eager load

            _mostrar_resultado(venta_parseada, venta_guardada, montos, session)

    except Exception as e:
        print(f"[ERROR] Falló al guardar: {e}")
        raise


if __name__ == "__main__":
    main()
