from typing import Optional
from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base


class DetalleCompra(Base):
    __tablename__ = "detalle_compras"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    compra_id: Mapped[int] = mapped_column(ForeignKey("compras.id"), nullable=False)
    producto_sku: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("productos.sku"), nullable=True
    )
    producto_nombre_raw: Mapped[str] = mapped_column(String(300), nullable=False)
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False)
    precio_costo_unitario: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    compra: Mapped["Compra"] = relationship(back_populates="detalles")
    producto: Mapped[Optional["Producto"]] = relationship(foreign_keys=[producto_sku])
