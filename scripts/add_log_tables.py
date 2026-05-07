"""
add_log_tables.py
=================
Creates sku_match_log and stock_adjustment_log tables.
Safe to re-run: uses CREATE TABLE IF NOT EXISTS via SQLAlchemy metadata.

Usage:
    python scripts/add_log_tables.py
"""

import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _root)
load_dotenv(dotenv_path=os.path.join(_root, ".env"), override=True)

from models import Base, SkuMatchLog, StockAdjustmentLog  # noqa: F401 — imports register metadata


def main():
    url = os.getenv("DATABASE_URL")
    if not url:
        sys.exit("DATABASE_URL not set in .env")

    engine = create_engine(url)

    # Only create the two new tables — leave existing tables untouched
    Base.metadata.create_all(
        engine,
        tables=[
            SkuMatchLog.__table__,
            StockAdjustmentLog.__table__,
        ],
        checkfirst=True,
    )
    print("✓ sku_match_log created/verified")
    print("✓ stock_adjustment_log created/verified")


if __name__ == "__main__":
    main()
