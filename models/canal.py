from typing import List
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base


class Canal(Base):
    __tablename__ = "canales"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    # Rappi, Rappi Pro, WhatsApp, Local, TikTok Live, Web

    ventas: Mapped[List["Venta"]] = relationship(back_populates="canal")
