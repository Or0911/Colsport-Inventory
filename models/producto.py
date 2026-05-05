from typing import Optional
from sqlalchemy import String, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base


class Producto(Base):
    __tablename__ = "productos"

    sku: Mapped[str] = mapped_column(String, primary_key=True)
    nombre: Mapped[str] = mapped_column(String, nullable=False)
    peso: Mapped[str] = mapped_column(String, default="N/A", server_default="N/A")
    marca: Mapped[str] = mapped_column(String, default="N/A", server_default="N/A")
    categoria: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    stock_actual: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    # Rappi product ID (ID del producto en el catálogo de Rappi).
    # Null si el producto no está publicado en Rappi.
    rappi_product_id: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    # Nombres alternativos separados por coma para mejorar el SKU matching.
    # Ejemplo: "Creatina Creasmart 550g Sin sabor, Creasmart sin sabor 550"
    alias: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    items_venta: Mapped[list["VentaItem"]] = relationship(back_populates="producto", foreign_keys="VentaItem.sku")
