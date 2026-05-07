from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base


class SkuMatchLog(Base):
    __tablename__ = "sku_match_log"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    fecha: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    producto_nombre_raw: Mapped[str] = mapped_column(Text, nullable=False)
    sku_sugerido: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    sku_confirmado: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    tipo: Mapped[str] = mapped_column(String(10), default="compra", server_default="compra")
