from typing import Optional
from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base


class Pago(Base):
    __tablename__ = "pagos"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    venta_id: Mapped[int] = mapped_column(ForeignKey("ventas.id"), nullable=False)

    # Ej: "Transferencia Bancolombia", "Nequi", "Efectivo", "Contra entrega Rappi"
    metodo: Mapped[str] = mapped_column(String(80), nullable=False)

    # Ej: "Colsports Colombia", "JR" — cuenta destino del negocio
    cuenta_destino: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    monto: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    referencia: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    venta: Mapped["Venta"] = relationship(back_populates="pagos")
