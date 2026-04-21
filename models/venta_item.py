from typing import Optional
from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base


class VentaItem(Base):
    __tablename__ = "venta_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    venta_id: Mapped[int] = mapped_column(ForeignKey("ventas.id"), nullable=False)

    # Nullable si el producto aún no está en el catálogo
    sku: Mapped[Optional[str]] = mapped_column(ForeignKey("productos.sku"), nullable=True)

    # Texto tal como llegó en el mensaje (siempre se guarda para auditoría)
    producto_nombre_raw: Mapped[str] = mapped_column(String(300), nullable=False)

    cantidad: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    precio_unitario: Mapped[int] = mapped_column(Integer, nullable=False)
    subtotal: Mapped[int] = mapped_column(Integer, nullable=False)

    venta: Mapped["Venta"] = relationship(back_populates="items")
    producto: Mapped[Optional["Producto"]] = relationship(back_populates="items_venta", foreign_keys=[sku])
