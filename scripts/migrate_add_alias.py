"""
migrate_add_alias.py
====================
Adds the 'alias' column to the existing 'productos' table.
Safe to run multiple times: does nothing if the column already exists.

Run once against Supabase (or any existing DB) after pulling this update:
    python scripts/migrate_add_alias.py
"""

import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _root)
load_dotenv(dotenv_path=os.path.join(_root, ".env"), override=True)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("[ERROR] DATABASE_URL not set in .env")
    sys.exit(1)

engine = create_engine(DATABASE_URL)

with engine.begin() as conn:
    # Check if column already exists
    result = conn.execute(text("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'productos' AND column_name = 'alias'
    """))
    if result.fetchone():
        print("Column 'alias' already exists in 'productos'. Nothing to do.")
    else:
        conn.execute(text("ALTER TABLE productos ADD COLUMN alias TEXT"))
        print("Column 'alias' added to 'productos' successfully.")
