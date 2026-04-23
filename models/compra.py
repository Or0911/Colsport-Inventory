from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Integer, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base


class Compra(Base):
    __tablename__ = "compras"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    fecha: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    proveedor: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    monto_total: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    detalles: Mapped[List["DetalleCompra"]] = relationship(back_populates="compra")
