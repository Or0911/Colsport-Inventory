"""
Tests para api/motor_ia.py

Cubre:
- normalizar_texto_venta(): limpieza de texto antes de enviar al LLM
- calcular_montos(): aritmética de dinero (sin llamadas a la API)
- parsear_mensaje(): integración con OpenAI (con mock de la respuesta)
"""

import json
import pytest
from unittest.mock import MagicMock, patch

from api.motor_ia import (
    normalizar_texto_venta,
    calcular_montos,
    parsear_mensaje,
    VentaParseada,
    ItemData,
    PagoData,
    RappiDetalleData,
    ClienteData,
)


# ---------------------------------------------------------------------------
# normalizar_texto_venta
# ---------------------------------------------------------------------------

class TestNormalizarTextoVenta:
    def test_colapsa_espacios_multiples_en_linea(self):
        assert normalizar_texto_venta("hola   mundo") == "hola mundo"

    def test_quita_tabs(self):
        assert normalizar_texto_venta("hola\tmundo") == "hola mundo"

    def test_elimina_lineas_vacias_repetidas(self):
        resultado = normalizar_texto_venta("linea1\n\n\nlinea2")
        assert "\n\n\n" not in resultado
        assert "linea1" in resultado
        assert "linea2" in resultado

    def test_permite_una_linea_vacia_entre_parrafos(self):
        resultado = normalizar_texto_venta("parrafo1\n\nparrafo2")
        assert resultado == "parrafo1\n\nparrafo2"

    def test_quita_espacios_al_inicio_y_fin_de_lineas(self):
        resultado = normalizar_texto_venta("  VENTA LOCAL  \n  Diby  ")
        assert resultado == "VENTA LOCAL\nDiby"

    def test_preserva_informacion_del_mensaje(self):
        texto = "VENTA LOCAL\nDiby\n1 und banda de látex\n$12.100\nNequi JR"
        resultado = normalizar_texto_venta(texto)
        assert "Diby" in resultado
        assert "banda" in resultado
        assert "12.100" in resultado
        assert "Nequi" in resultado

    def test_texto_ya_limpio_no_cambia(self):
        texto = "VENTA LOCAL\nDiby\n1 und proteína\n$80.000"
        assert normalizar_texto_venta(texto) == texto

    def test_texto_vacio_retorna_vacio(self):
        assert normalizar_texto_venta("") == ""

    def test_solo_espacios_retorna_vacio(self):
        assert normalizar_texto_venta("   \n   \n   ") == ""


# ---------------------------------------------------------------------------
# calcular_montos
# ---------------------------------------------------------------------------

def _venta_simple(precio: int, cantidad: int = 1, costo_envio: int = None) -> VentaParseada:
    return VentaParseada(
        canal="Local",
        items=[ItemData(producto_nombre_raw="Producto", cantidad=cantidad, precio_unitario=precio)],
        pago=PagoData(metodo="Efectivo"),
        costo_envio=costo_envio,
    )


class TestCalcularMontos:
    def test_venta_simple_sin_envio(self):
        venta = _venta_simple(precio=80_000)
        m = calcular_montos(venta)
        assert m["subtotal"] == 80_000
        assert m["costo_envio"] == 0
        assert m["descuento"] == 0
        assert m["comision_monto"] == 0
        assert m["total"] == 80_000

    def test_venta_con_envio(self):
        venta = _venta_simple(precio=80_000, costo_envio=5_000)
        m = calcular_montos(venta)
        assert m["subtotal"] == 80_000
        assert m["costo_envio"] == 5_000
        assert m["total"] == 85_000

    def test_multiples_items(self):
        venta = VentaParseada(
            canal="Local",
            items=[
                ItemData(producto_nombre_raw="A", cantidad=2, precio_unitario=10_000),
                ItemData(producto_nombre_raw="B", cantidad=1, precio_unitario=5_000),
            ],
            pago=PagoData(metodo="Efectivo"),
        )
        m = calcular_montos(venta)
        assert m["subtotal"] == 25_000
        assert m["total"] == 25_000

    def test_rappi_con_comision_16_pct(self):
        venta = VentaParseada(
            canal="Rappi",
            items=[ItemData(producto_nombre_raw="ISO 100", cantidad=1, precio_unitario=100_000)],
            pago=PagoData(metodo="Contra entrega Rappi"),
            rappi_detalle=RappiDetalleData(
                order_id="ORD-123",
                tipo="Regular",
                comision_porcentaje=16.0,
            ),
        )
        m = calcular_montos(venta)
        assert m["subtotal"] == 100_000
        assert m["comision_monto"] == 16_000
        assert m["descuento"] == 16_000
        assert m["total"] == 84_000

    def test_rappi_sin_comision_porcentaje(self):
        venta = VentaParseada(
            canal="Rappi",
            items=[ItemData(producto_nombre_raw="Proteína", cantidad=1, precio_unitario=89_900)],
            pago=PagoData(metodo="Contra entrega Rappi"),
            rappi_detalle=RappiDetalleData(
                order_id="ORD-456",
                tipo="Regular",
                comision_porcentaje=None,
            ),
        )
        m = calcular_montos(venta)
        assert m["comision_monto"] == 0
        assert m["total"] == 89_900

    def test_items_sin_precio_no_crashea(self):
        venta = VentaParseada(
            canal="Local",
            items=[ItemData(producto_nombre_raw="Producto sin precio", cantidad=1, precio_unitario=None)],
            pago=PagoData(metodo="Efectivo"),
        )
        m = calcular_montos(venta)
        assert m["subtotal"] == 0
        assert m["total"] == 0

    def test_cantidad_multiplicada_correctamente(self):
        venta = _venta_simple(precio=15_000, cantidad=3)
        m = calcular_montos(venta)
        assert m["subtotal"] == 45_000

    def test_redondeo_comision(self):
        venta = VentaParseada(
            canal="Rappi",
            items=[ItemData(producto_nombre_raw="Producto", cantidad=1, precio_unitario=99_900)],
            pago=PagoData(metodo="Contra entrega Rappi"),
            rappi_detalle=RappiDetalleData(
                order_id="ORD-789",
                tipo="Regular",
                comision_porcentaje=16.0,
            ),
        )
        m = calcular_montos(venta)
        # 99900 * 0.16 = 15984.0 → 15984
        assert m["comision_monto"] == 15_984
        assert m["total"] == 99_900 - 15_984


# ---------------------------------------------------------------------------
# parsear_mensaje — con mock de OpenAI
# ---------------------------------------------------------------------------

RESPUESTA_MOCK = {
    "canal": "Local",
    "cliente": {"nombre": "Diby", "cedula": None, "telefono": None, "email": None},
    "items": [
        {
            "producto_nombre_raw": "banda de látex azul wonder",
            "cantidad": 1,
            "precio_unitario": 12100,
        }
    ],
    "costo_envio": None,
    "pago": {"metodo": "Nequi", "cuenta_destino": "JR", "referencia": None},
    "envio": None,
    "rappi_detalle": None,
    "fuente_referido": None,
    "notas": None,
}


@pytest.fixture
def mock_openai_response():
    mock_choice = MagicMock()
    mock_choice.message.content = json.dumps(RESPUESTA_MOCK)

    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    return mock_response


def test_parsear_mensaje_retorna_venta_parseada(mock_openai_response, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    with patch("api.motor_ia.OpenAI") as mock_openai_cls:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_openai_response
        mock_openai_cls.return_value = mock_client

        resultado = parsear_mensaje("VENTA LOCAL\nDiby\n1 und banda\n$12.100\nNequi JR")

    assert isinstance(resultado, VentaParseada)
    assert resultado.canal == "Local"
    assert resultado.cliente.nombre == "Diby"
    assert len(resultado.items) == 1
    assert resultado.items[0].precio_unitario == 12100


def test_parsear_mensaje_sin_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        parsear_mensaje("VENTA LOCAL\nDiby\n1 und banda")


def test_parsear_mensaje_json_invalido(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    mock_choice = MagicMock()
    mock_choice.message.content = "esto no es json {"
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    with patch("api.motor_ia.OpenAI") as mock_openai_cls:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_cls.return_value = mock_client

        with pytest.raises(ValueError, match="JSON inválido"):
            parsear_mensaje("VENTA LOCAL\nDiby")


def test_parsear_mensaje_schema_invalido(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    mock_choice = MagicMock()
    mock_choice.message.content = json.dumps({"campo_desconocido": "valor"})
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    with patch("api.motor_ia.OpenAI") as mock_openai_cls:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_cls.return_value = mock_client

        with pytest.raises(ValueError, match="schema"):
            parsear_mensaje("VENTA LOCAL\nDiby")
