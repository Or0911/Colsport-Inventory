"""
rappi_client.py
===============
Sincroniza la disponibilidad de productos con Rappi luego de cada venta o compra.

Lógica:
  - Stock ≤ 0 tras una venta  → marcar como NO disponible en Rappi (unidades = 0).
  - Stock > 0 tras una compra → marcar como SI disponible en Rappi (unidades = stock).

Solo actúa sobre productos que tengan rappi_product_id registrado.
Si las credenciales no están configuradas, las llamadas son no-operaciones silenciosas.

Variables de entorno requeridas:
    RAPPI_CLIENT_ID      → Client ID del partner portal de Rappi
    RAPPI_CLIENT_SECRET  → Client Secret del partner portal de Rappi
    RAPPI_STORE_ID       → ID de la tienda en Rappi (ej: 900283093 para COLSPORTS)

Variables opcionales (con defaults):
    RAPPI_AUTH_URL       → URL del endpoint de autenticación
                           Default: https://auth.rappi.com/api/auth/token
    RAPPI_API_BASE_URL   → Base URL de la API de productos
                           Default: https://microservices.dev.rappi.com
"""

import os
import logging
from typing import Optional

import requests

logger = logging.getLogger(__name__)

_RAPPI_AUTH_URL  = os.getenv(
    "RAPPI_AUTH_URL",
    "https://auth.rappi.com/api/auth/token",
)
_RAPPI_API_BASE  = os.getenv(
    "RAPPI_API_BASE_URL",
    "https://microservices.dev.rappi.com",
)
_RAPPI_CLIENT_ID     = os.getenv("RAPPI_CLIENT_ID")
_RAPPI_CLIENT_SECRET = os.getenv("RAPPI_CLIENT_SECRET")
_RAPPI_STORE_ID      = os.getenv("RAPPI_STORE_ID")


def _is_configured() -> bool:
    return bool(_RAPPI_CLIENT_ID and _RAPPI_CLIENT_SECRET and _RAPPI_STORE_ID)


def _get_token() -> Optional[str]:
    """Obtiene un bearer token vía OAuth2 client_credentials."""
    try:
        resp = requests.post(
            _RAPPI_AUTH_URL,
            json={
                "client_id": _RAPPI_CLIENT_ID,
                "client_secret": _RAPPI_CLIENT_SECRET,
            },
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json().get("access_token")
    except Exception as exc:
        logger.warning("Rappi auth failed: %s", exc)
        return None


def _update_availability(rappi_product_id: str, available: bool, units: int) -> bool:
    """
    Llama a la API de Rappi para actualizar disponibilidad de un producto.

    Args:
        rappi_product_id: ID del producto en Rappi (ej: '2126240804').
        available:        True → SI, False → NO.
        units:            Unidades disponibles (0 si available=False).

    Returns:
        True si la actualización fue exitosa, False en caso contrario.
    """
    if not _is_configured():
        return False

    token = _get_token()
    if not token:
        return False

    url = (
        f"{_RAPPI_API_BASE}/api/v2/restaurants/integrated-products"
        f"/{_RAPPI_STORE_ID}/products/{rappi_product_id}"
    )
    payload = {
        "availability": "SI" if available else "NO",
        "stock": units,
    }

    try:
        resp = requests.patch(
            url,
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        resp.raise_for_status()
        logger.info(
            "Rappi sync OK — product %s → %s (%d u)",
            rappi_product_id,
            payload["availability"],
            units,
        )
        return True
    except Exception as exc:
        logger.warning("Rappi update failed for product %s: %s", rappi_product_id, exc)
        return False


# ---------------------------------------------------------------------------
# Public helpers — llamados desde guardar_venta y guardar_compra
# ---------------------------------------------------------------------------

def sync_after_sale(sku: str, rappi_product_id: str, new_stock: int) -> None:
    """
    Llama a Rappi cuando el stock baja tras una venta.
    Si new_stock ≤ 0 → apaga el producto en Rappi.
    """
    if new_stock <= 0:
        _update_availability(rappi_product_id, available=False, units=0)
        logger.info("SKU %s apagado en Rappi (stock=%d)", sku, new_stock)


def sync_after_purchase(sku: str, rappi_product_id: str, new_stock: int) -> None:
    """
    Llama a Rappi cuando el stock sube tras una compra.
    Si new_stock > 0 → enciende el producto en Rappi con las unidades actuales.
    """
    if new_stock > 0:
        _update_availability(rappi_product_id, available=True, units=new_stock)
        logger.info("SKU %s encendido en Rappi (stock=%d)", sku, new_stock)
