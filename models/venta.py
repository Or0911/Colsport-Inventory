from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Integer, DateTime, ForeignKey, func, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base
import enum


class EstadoVenta(str, enum.Enum):
    pendiente = "pendiente"      # registrada pero no confirmada
    confirmada = "confirmada"    # pago verificado
    despachada = "despachada"    # enviada al cliente
    entregada = "entregada"      # cliente recibió
    cancelada = "cancelada"


class Venta(Base):
    __tablename__ = "ventas"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    fecha: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    canal_id: Mapped[int] = mapped_column(ForeignKey("canales.id"), nullable=False)
    canal: Mapped["Canal"] = relationship(back_populates="ventas")

    # Nullable para ventas locales rápidas (ej: "Diby, 1 banda $12.100")
    cliente_id: Mapped[Optional[int]] = mapped_column(ForeignKey("clientes.id"), nullable=True)
    cliente: Mapped[Optional["Cliente"]] = relationship(back_populates="ventas")
    cliente_nombre_raw: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)

    subtotal: Mapped[int] = mapped_column(Integer, nullable=False)
    costo_envio: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    descuento: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    total: Mapped[int] = mapped_column(Integer, nullable=False)

    estado: Mapped[EstadoVenta] = mapped_column(
        Enum(EstadoVenta), default=EstadoVenta.pendiente, server_default="pendiente"
    )

    fuente_referido: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    notas: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    mensaje_original: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)
    json_extraido: Mapped[Optional[str]] = mapped_column(String(5000), nullable=True)

    items: Mapped[List["VentaItem"]] = relationship(back_populates="venta", cascade="all, delete-orphan")
    pagos: Mapped[List["Pago"]] = relationship(back_populates="venta", cascade="all, delete-orphan")
    envio: Mapped[Optional["Envio"]] = relationship(back_populates="venta", uselist=False, cascade="all, delete-orphan")
    rappi_detalle: Mapped[Optional["RappiDetalle"]] = relationship(back_populates="venta", uselist=False, cascade="all, delete-orphan")
