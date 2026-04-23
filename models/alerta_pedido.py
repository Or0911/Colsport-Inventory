from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, ForeignKey, DateTime, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base


class AlertaPedido(Base):
    """
    Registra componentes de combos que quedaron con stock insuficiente al momento de la venta.
    Permite dar seguimiento a reposiciones pendientes.
    """
    __tablename__ = "alertas_pedido"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    venta_id: Mapped[int] = mapped_column(ForeignKey("ventas.id"), nullable=False)
    combo_sku: Mapped[str] = mapped_column(String, nullable=False)
    componente_sku: Mapped[str] = mapped_column(String, nullable=False)
    componente_nombre: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    cantidad_faltante: Mapped[int] = mapped_column(Integer, nullable=False)
    fecha_creada: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    resuelta: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", nullable=False
    )

    venta: Mapped["Venta"] = relationship()
