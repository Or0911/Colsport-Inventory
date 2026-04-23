from sqlalchemy import String, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base


class ComboComponente(Base):
    """
    Define qué productos individuales componen un combo.
    Un combo descuenta stock de cada componente, no del SKU del combo en sí.
    """
    __tablename__ = "combo_componentes"
    __table_args__ = (
        UniqueConstraint("combo_sku", "componente_sku", name="uq_combo_componente"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    combo_sku: Mapped[str] = mapped_column(
        String, ForeignKey("productos.sku", ondelete="CASCADE"), nullable=False
    )
    componente_sku: Mapped[str] = mapped_column(
        String, ForeignKey("productos.sku", ondelete="CASCADE"), nullable=False
    )
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    combo: Mapped["Producto"] = relationship(foreign_keys=[combo_sku])
    componente: Mapped["Producto"] = relationship(foreign_keys=[componente_sku])
