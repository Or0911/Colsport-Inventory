"""
consolidate_and_import.py
Procesa implementos.csv y suplementos.csv y hace upsert en PostgreSQL.
"""

import os
import sys
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import (
    create_engine, text,
    Column, String, Integer, MetaData, Table
)
from sqlalchemy.dialects.postgresql import insert as pg_insert

# Carga .env desde la raíz del proyecto (un nivel arriba de /scripts)
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(dotenv_path=os.path.join(_root, ".env"), override=True)

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMPLEMENTOS_PATH = os.path.join(BASE_DIR, "implementos.csv")
SUPLEMENTOS_PATH = os.path.join(BASE_DIR, "suplementos.csv")


# ---------------------------------------------------------------------------
# Helpers de carga y limpieza
# ---------------------------------------------------------------------------

def cargar_implementos(path: str) -> tuple[pd.DataFrame, int]:
    """
    Lee implementos.csv, limpia y estandariza columnas.
    Retorna (DataFrame limpio, cantidad de filas descartadas).
    """
    df = pd.read_csv(path, dtype=str)

    # Normalizar nombres de columna (quitar espacios extra)
    df.columns = df.columns.str.strip()

    # Seleccionar solo las columnas relevantes
    df = df[["COD", "PRODUCTO", "Peso"]].copy()

    total_antes = len(df)

    # Eliminar filas sin COD o sin PRODUCTO
    df = df[df["COD"].notna() & df["COD"].str.strip().ne("")]
    df = df[df["PRODUCTO"].notna() & df["PRODUCTO"].str.strip().ne("")]

    descartados = total_antes - len(df)

    # Rellenar Peso vacío
    df["Peso"] = df["Peso"].fillna("N/A").str.strip().replace("", "N/A")

    # Columnas constantes
    df["categoria"] = "Implemento"
    df["MARCA"] = "N/A"

    # Renombrar a esquema unificado
    df = df.rename(columns={"COD": "sku", "PRODUCTO": "nombre", "Peso": "peso", "MARCA": "marca"})

    return df[["sku", "nombre", "peso", "marca", "categoria"]], descartados


def cargar_suplementos(path: str) -> tuple[pd.DataFrame, int]:
    """
    Lee suplementos.csv, limpia y estandariza columnas.
    Retorna (DataFrame limpio, cantidad de filas descartadas).
    """
    df = pd.read_csv(path, dtype=str)

    df.columns = df.columns.str.strip()

    df = df[["COD", "PRODUCTO", "MARCA"]].copy()

    total_antes = len(df)

    # Eliminar filas sin COD o sin PRODUCTO
    df = df[df["COD"].notna() & df["COD"].str.strip().ne("")]
    df = df[df["PRODUCTO"].notna() & df["PRODUCTO"].str.strip().ne("")]

    descartados = total_antes - len(df)

    # Rellenar MARCA vacía
    df["MARCA"] = df["MARCA"].fillna("Genérico").str.strip().replace("", "Genérico")

    # Columnas constantes
    df["categoria"] = "Suplemento"
    df["Peso"] = "N/A"

    df = df.rename(columns={"COD": "sku", "PRODUCTO": "nombre", "Peso": "peso", "MARCA": "marca"})

    return df[["sku", "nombre", "peso", "marca", "categoria"]], descartados


# ---------------------------------------------------------------------------
# Base de datos
# ---------------------------------------------------------------------------

def crear_tabla_si_no_existe(engine) -> Table:
    metadata = MetaData()

    productos = Table(
        "productos",
        metadata,
        Column("sku",          String,  primary_key=True),
        Column("nombre",       String,  nullable=False),
        Column("peso",         String,  default="N/A"),
        Column("marca",        String,  default="N/A"),
        Column("categoria",    String),
        Column("stock_actual", Integer, default=0, server_default="0"),
    )

    metadata.create_all(engine)
    return productos


def upsert_productos(engine, tabla: Table, df: pd.DataFrame) -> int:
    """
    Inserta filas nuevas o actualiza nombre/peso/marca/categoria si el sku ya existe.
    Retorna la cantidad de filas procesadas.
    """
    records = df.to_dict(orient="records")
    if not records:
        return 0

    with engine.begin() as conn:
        stmt = pg_insert(tabla).values(records)
        stmt = stmt.on_conflict_do_update(
            index_elements=["sku"],
            set_={
                "nombre":    stmt.excluded.nombre,
                "peso":      stmt.excluded.peso,
                "marca":     stmt.excluded.marca,
                "categoria": stmt.excluded.categoria,
            }
        )
        conn.execute(stmt)

    return len(records)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    # --- Verificar archivos ---
    for path, nombre in [(IMPLEMENTOS_PATH, "implementos.csv"), (SUPLEMENTOS_PATH, "suplementos.csv")]:
        if not os.path.exists(path):
            print(f"[ERROR] No se encontró el archivo: {path}")
            sys.exit(1)

    # --- Cargar y limpiar ---
    df_impl, desc_impl   = cargar_implementos(IMPLEMENTOS_PATH)
    df_supl, desc_supl   = cargar_suplementos(SUPLEMENTOS_PATH)

    validos_impl = len(df_impl)
    validos_supl = len(df_supl)

    # --- Concatenar ---
    df_total = pd.concat([df_impl, df_supl], ignore_index=True)

    # Limpiar SKUs
    df_total["sku"] = df_total["sku"].str.strip()
    df_total["nombre"] = df_total["nombre"].str.strip()

    # --- Eliminar duplicados por sku (mantiene la primera ocurrencia) ---
    duplicados = df_total.duplicated(subset="sku").sum()
    df_total = df_total.drop_duplicates(subset="sku", keep="first")

    # --- Base de datos ---
    if not DATABASE_URL:
        print("[ERROR] DATABASE_URL no definida. Revisa tu archivo .env")
        sys.exit(1)

    print(f"\nConectando a la base de datos...")
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("Conexión exitosa.")
    except Exception as e:
        print(f"[ERROR] No se pudo conectar a la base de datos: {e}")
        sys.exit(1)

    tabla = crear_tabla_si_no_existe(engine)
    total_importados = upsert_productos(engine, tabla, df_total)

    # --- Reporte final ---
    print("\n" + "=" * 50)
    print("           RESUMEN DE IMPORTACIÓN")
    print("=" * 50)
    print(f"  Implementos válidos importados : {validos_impl}")
    print(f"  Suplementos válidos importados : {validos_supl}")
    print(f"  Duplicados eliminados (por SKU): {duplicados}")
    print(f"  Registros descartados (impl.)  : {desc_impl}  [sin COD o PRODUCTO]")
    print(f"  Registros descartados (supl.)  : {desc_supl}  [sin COD o PRODUCTO]")
    print(f"  Total upsert ejecutados        : {total_importados}")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    main()
