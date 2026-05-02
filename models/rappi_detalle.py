from typing import Optional
from sqlalchemy import String, Integer, Numeric, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base


class RappiDetalle(Base):
    __tablename__ = "rappi_detalles"
    __table_args__ = (UniqueConstraint("order_id", name="uq_rappi_detalles_order_id"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    venta_id: Mapped[int] = mapped_column(ForeignKey("ventas.id"), unique=True, nullable=False)

    order_id: Mapped[str] = mapped_column(String(50), nullable=False)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)  # "Regular" | "Pro"

    comision_porcentaje: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    comision_monto: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    venta: Mapped["Venta"] = relationship(back_populates="rappi_detalle")
