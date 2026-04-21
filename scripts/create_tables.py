"""
create_tables.py
Crea todas las tablas en la base de datos (incluye modelos de ventas).
Seguro de correr múltiples veces: usa CREATE TABLE IF NOT EXISTS.
"""

import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _root)
load_dotenv(dotenv_path=os.path.join(_root, ".env"), override=True)

from models import Base  # importa todos los modelos via __init__

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("[ERROR] DATABASE_URL no definida en .env")
    sys.exit(1)

print("Conectando a la base de datos...")
try:
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print("Conexión exitosa.\n")
except Exception as e:
    print(f"[ERROR] No se pudo conectar: {e}")
    sys.exit(1)

print("Creando tablas...")
Base.metadata.create_all(engine)

tablas = list(Base.metadata.tables.keys())
print(f"\nTablas creadas/verificadas ({len(tablas)}):")
for t in sorted(tablas):
    print(f"  + {t}")

print("\nListo.")
