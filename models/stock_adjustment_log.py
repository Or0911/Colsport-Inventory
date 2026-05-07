from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base


class StockAdjustmentLog(Base):
    __tablename__ = "stock_adjustment_log"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    fecha: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    sku: Mapped[str] = mapped_column(String(20), nullable=False)
    producto_nombre: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    stock_antes: Mapped[int] = mapped_column(Integer, nullable=False)
    delta: Mapped[int] = mapped_column(Integer, nullable=False)
    stock_despues: Mapped[int] = mapped_column(Integer, nullable=False)
    motivo: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
