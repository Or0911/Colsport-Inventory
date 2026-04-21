"""
Tests para api/guardar_venta.py

Cubre:
- _normalizar(): limpieza de texto para matching
- _buscar_sku(): matching de SKU desde lista en memoria
- guardar_venta(): integración con SQLite en memoria
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from models.base import Base
from models import Canal, Cliente, Venta, VentaItem, Pago, Producto
from api.guardar_venta import _normalizar, _buscar_sku, guardar_venta
from api.motor_ia import VentaParseada, ItemData, PagoData, ClienteData, RappiDetalleData


# ---------------------------------------------------------------------------
# Fixture: base de datos SQLite en memoria
# ---------------------------------------------------------------------------

@pytest.fixture
def engine():
    eng = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)


@pytest.fixture
def session(engine):
    with Session(engine) as s:
        yield s


@pytest.fixture
def catalogo_basico(session):
    """Inserta algunos productos de prueba en la BD."""
    productos = [
        Producto(sku="PROT-001", nombre="proteina whey gold standard", stock_actual=10),
        Producto(sku="BAND-001", nombre="banda de latex azul wonder", stock_actual=20),
        Producto(sku="ISO-001",  nombre="iso 100 1.3lb dymatize vainilla", stock_actual=5),
    ]
    for p in productos:
        session.add(p)
    session.commit()
    return productos


# ---------------------------------------------------------------------------
# _normalizar
# ---------------------------------------------------------------------------

class TestNormalizar:
    def test_convierte_a_minusculas(self):
        assert _normalizar("PROTEÍNA") == "protena"

    def test_elimina_caracteres_especiales(self):
        assert _normalizar("iso-100 1.3lb") == "iso100 13lb"

    def test_elimina_espacios_extremos(self):
        assert _normalizar("  gold standard  ") == "gold standard"

    def test_texto_ya_normalizado(self):
        assert _normalizar("proteina whey") == "proteina whey"


# ---------------------------------------------------------------------------
# _buscar_sku
# ---------------------------------------------------------------------------

class TestBuscarSku:
    @pytest.fixture
    def catalogo(self):
        class P:
            def __init__(self, sku, nombre):
                self.sku = sku
                self.nombre = nombre
        return [
            P("PROT-001", "proteina whey gold standard"),
            P("BAND-001", "banda de latex azul wonder"),
            P("ISO-001",  "iso 100 1.3lb dymatize vainilla"),
        ]

    def test_match_exacto(self, catalogo):
        assert _buscar_sku(catalogo, "proteina whey gold standard") == "PROT-001"

    def test_match_parcial_suficiente(self, catalogo):
        assert _buscar_sku(catalogo, "iso 100 dymatize") == "ISO-001"

    def test_sin_match_retorna_none(self, catalogo):
        assert _buscar_sku(catalogo, "creatina monohidratada") is None

    def test_catalogo_vacio_retorna_none(self):
        assert _buscar_sku([], "proteina") is None

    def test_nombre_vacio_retorna_none(self, catalogo):
        assert _buscar_sku(catalogo, "") is None

    def test_solo_palabras_cortas_retorna_none(self, catalogo):
        # "und" y "x" están excluidos, palabras de ≤2 chars también
        assert _buscar_sku(catalogo, "1 und x") is None

    def test_no_confunde_productos_similares(self, catalogo):
        # "banda de latex" → BAND-001, no PROT-001
        assert _buscar_sku(catalogo, "banda de latex") == "BAND-001"


# ---------------------------------------------------------------------------
# guardar_venta — integración con SQLite
# ---------------------------------------------------------------------------

def _venta_local(nombre_cliente: str = "Diby", precio: int = 12_100) -> VentaParseada:
    return VentaParseada(
        canal="Local",
        cliente=ClienteData(nombre=nombre_cliente),
        items=[ItemData(
            producto_nombre_raw="banda de latex azul wonder",
            cantidad=1,
            precio_unitario=precio,
        )],
        pago=PagoData(metodo="Nequi", cuenta_destino="JR"),
    )


class TestGuardarVenta:
    def test_crea_venta_con_id(self, session, catalogo_basico):
        venta = guardar_venta(session, _venta_local(), "VENTA LOCAL\nDiby\n1 und banda\n$12.100")
        session.commit()
        assert venta.id is not None

    def test_montos_calculados_en_python(self, session, catalogo_basico):
        venta = guardar_venta(session, _venta_local(precio=80_000), "msg")
        session.commit()
        assert venta.subtotal == 80_000
        assert venta.total == 80_000
        assert venta.costo_envio == 0

    def test_guarda_mensaje_original(self, session, catalogo_basico):
        texto = "VENTA LOCAL\nDiby\n1 und banda\n$12.100"
        venta = guardar_venta(session, _venta_local(), texto)
        session.commit()
        assert venta.mensaje_original == texto

    def test_guarda_json_extraido(self, session, catalogo_basico):
        venta = guardar_venta(session, _venta_local(), "msg")
        session.commit()
        assert venta.json_extraido is not None
        import json
        data = json.loads(venta.json_extraido)
        assert data["canal"] == "Local"

    def test_crea_item_con_sku_matcheado(self, session, catalogo_basico):
        venta = guardar_venta(session, _venta_local(), "msg")
        session.commit()
        session.refresh(venta)
        assert len(venta.items) == 1
        assert venta.items[0].sku == "BAND-001"

    def test_descuenta_stock(self, session, catalogo_basico):
        from sqlalchemy import select
        from models import Producto as P
        guardar_venta(session, _venta_local(), "msg")
        session.commit()
        producto = session.execute(
            select(P).where(P.sku == "BAND-001")
        ).scalar_one()
        assert producto.stock_actual == 19  # era 20, se vendió 1

    def test_crea_canal_si_no_existe(self, session, catalogo_basico):
        venta = guardar_venta(session, _venta_local(), "msg")
        session.commit()
        from sqlalchemy import select
        canal = session.execute(
            select(Canal).where(Canal.nombre == "Local")
        ).scalar_one_or_none()
        assert canal is not None

    def test_reutiliza_canal_existente(self, session, catalogo_basico):
        from sqlalchemy import select, func
        guardar_venta(session, _venta_local(), "msg1")
        guardar_venta(session, _venta_local(), "msg2")
        session.commit()
        count = session.execute(
            select(func.count()).select_from(Canal).where(Canal.nombre == "Local")
        ).scalar()
        assert count == 1

    def test_crea_cliente(self, session, catalogo_basico):
        guardar_venta(session, _venta_local(nombre_cliente="Diby"), "msg")
        session.commit()
        from sqlalchemy import select
        cliente = session.execute(
            select(Cliente).where(Cliente.nombre == "Diby")
        ).scalar_one_or_none()
        assert cliente is not None

    def test_rappi_comision_calculada_en_python(self, session, catalogo_basico):
        venta_rappi = VentaParseada(
            canal="Rappi",
            items=[ItemData(
                producto_nombre_raw="iso 100 dymatize",
                cantidad=1,
                precio_unitario=100_000,
            )],
            pago=PagoData(metodo="Contra entrega Rappi"),
            rappi_detalle=RappiDetalleData(
                order_id="ORD-TEST",
                tipo="Regular",
                comision_porcentaje=16.0,
            ),
        )
        venta = guardar_venta(session, venta_rappi, "msg")
        session.commit()
        session.refresh(venta)
        assert venta.descuento == 16_000
        assert venta.total == 84_000
        assert venta.rappi_detalle.comision_monto == 16_000
