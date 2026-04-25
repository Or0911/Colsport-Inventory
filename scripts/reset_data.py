"""
reset_data.py
=============
Borra todas las ventas, compras y pone stock en 0.
Útil para arrancar en producción con datos reales.

Uso:
    python scripts/reset_data.py

Requiere DATABASE_URL en .env o variable de entorno.
"""

import os
import sys

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _root)

from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(_root, ".env"))

from sqlalchemy import create_engine, text

url = os.getenv("DATABASE_URL")
if not url:
    print("ERROR: DATABASE_URL no está configurada en .env")
    sys.exit(1)

engine = create_engine(url)

print("=" * 55)
print("RESET DE DATOS — Colsports")
print("=" * 55)
print()
print("Esto BORRARÁ:")
print("  • Todas las ventas y sus items")
print("  • Todas las compras y sus detalles")
print("  • Todas las alertas de pedido")
print("  • Pondrá el stock de cada producto en 0")
print()
print("NO toca el catálogo de productos ni los combos.")
print()

confirm = input("Escribe RESET para confirmar: ").strip()
if confirm != "RESET":
    print("Cancelado.")
    sys.exit(0)

with engine.begin() as conn:
    conn.execute(text("DELETE FROM alerta_pedido"))
    conn.execute(text("DELETE FROM venta_items"))
    conn.execute(text("DELETE FROM ventas"))
    conn.execute(text("DELETE FROM detalle_compras"))
    conn.execute(text("DELETE FROM compras"))
    conn.execute(text("UPDATE productos SET stock_actual = 0"))

print()
print("✓ Tablas de ventas y compras vaciadas.")
print("✓ Stock de todos los productos puesto en 0.")
print()
print("El catálogo, los combos y los usuarios siguen intactos.")
print("Ya puedes empezar a ingresar compras para llenar el stock.")
