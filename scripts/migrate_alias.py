"""
migrate_alias.py
================
Aplica la migración de DB necesaria para el campo alias en productos.

Cambios:
  1. productos: ADD COLUMN alias TEXT

Es idempotente: usa IF NOT EXISTS para no fallar si ya se corrió.

Uso:
    python scripts/migrate_alias.py

Después de correr este script, puedes poblar los aliases en la DB:
    UPDATE productos SET alias = 'Nombre alternativo 1, Nombre alternativo 2'
    WHERE sku = 'XXXX';

Ejemplo para distinguir variantes de Creatina Creasmart:
    UPDATE productos SET alias = 'Creatina Creasmart 550g Sin sabor, Creasmart sin sabor'
    WHERE sku = '2045';
"""

import os
import sys

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _root)

from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(_root, ".env"), override=True)

from sqlalchemy import create_engine, text

MIGRATIONS = [
    (
        "productos.alias",
        """
        ALTER TABLE productos
        ADD COLUMN IF NOT EXISTS alias TEXT;
        """,
    ),
]


def run() -> None:
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("ERROR: DATABASE_URL no está configurado en .env")
        sys.exit(1)

    engine = create_engine(db_url)

    with engine.begin() as conn:
        for name, sql in MIGRATIONS:
            print(f"  Aplicando: {name} ... ", end="", flush=True)
            conn.execute(text(sql))
            print("OK")

    print("\nMigración aplicada. Ahora puedes poblar aliases con UPDATE en la DB.")
    print("Ejemplo:")
    print("  UPDATE productos SET alias = 'Creatina Creasmart 550g Sin sabor'")
    print("  WHERE sku = '2045';")


if __name__ == "__main__":
    run()
