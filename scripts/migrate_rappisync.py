"""
migrate_rappisync.py
====================
Aplica las migraciones de DB necesarias para la rama rappisync.

Cambios:
  1. productos: ADD COLUMN rappi_product_id VARCHAR(30)
  2. rappi_detalles: ADD UNIQUE CONSTRAINT uq_rappi_detalles_order_id

Es idempotente: usa IF NOT EXISTS / IF NOT EXISTS checks para no fallar si ya se corrió.
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
        "productos.rappi_product_id",
        """
        ALTER TABLE productos
        ADD COLUMN IF NOT EXISTS rappi_product_id VARCHAR(30);
        """,
    ),
    (
        "rappi_detalles.uq_order_id",
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'uq_rappi_detalles_order_id'
            ) THEN
                ALTER TABLE rappi_detalles
                ADD CONSTRAINT uq_rappi_detalles_order_id UNIQUE (order_id);
            END IF;
        END $$;
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

    print("\nMigraciones aplicadas correctamente.")


if __name__ == "__main__":
    run()
