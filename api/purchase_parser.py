"""
purchase_parser.py
==================
Transforms unstructured supplier text into a ParsedPurchase object.

Flow:
    raw text  →  OpenAI GPT-4o-mini  →  validated JSON  →  ParsedPurchase

The model only EXTRACTS fields. Totals are calculated in Python.
This module does NOT touch the database.

Scalability note — Vision API:
    In the future the text_area can be replaced with an invoice image.
    The commented process_invoice_image() function is ready for that integration.
"""

import os
import json
import logging
from typing import Optional, List

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field

load_dotenv()

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pydantic models
# Note: field names stay in Spanish to match the JSON keys the LLM returns.
# ---------------------------------------------------------------------------

class PurchaseItemData(BaseModel):
    producto_nombre_raw: str = Field(
        description="Product name exactly as it appears in the supplier's message"
    )
    cantidad: int = Field(default=1, ge=1)
    precio_costo_unitario: Optional[int] = Field(
        default=None,
        description="Unit cost price in COP (integer, no decimals). None if not mentioned."
    )


class ParsedPurchase(BaseModel):
    proveedor: Optional[str] = Field(
        default=None,
        description="Name of the supplier or distributor mentioned in the message"
    )
    items: List[PurchaseItemData]
    notas: Optional[str] = None


# ---------------------------------------------------------------------------
# System prompt — Spanish intentional: instructs LLM on Colombian business context
# ---------------------------------------------------------------------------

PURCHASE_SYSTEM_PROMPT = """
Eres un asistente especializado en EXTRAER datos estructurados de mensajes de proveedores
para un negocio colombiano de suplementos e implementos deportivos llamado Colsports.

Tu tarea es SOLO EXTRAER lo que aparece en el texto. NO calcules totales ni hagas aritmética.
Si un valor no aparece explícitamente, usa null (JSON null, NUNCA el string "null").

REGLAS DE EXTRACCIÓN:

1. PROVEEDOR: Nombre de la empresa o persona que envía la mercancía. Si no se menciona, null.

2. PRECIOS (sistema colombiano: punto = miles):
   - "$89.900" → extrae el entero 89900
   - Si hay IVA o descuentos mencionados, extrae el precio NETO que pagaría Colsports.
   - Si no se menciona precio → precio_costo_unitario=null

3. PRODUCTOS: Extrae cada referencia como un item separado.
   - Incluye presentación, sabor o variante si aparece (ej: "Proteína X 5lb vainilla").

4. CANTIDADES: Número de unidades que llegan al inventario.
   - "12 und" → cantidad=12
   - "1 caja × 6" → cantidad=6 (lo que importa es el stock que suma al inventario).

5. Si el mensaje es una lista de precios sin cantidades específicas, usa cantidad=1 como placeholder.

ESTRUCTURA EXACTA DEL JSON:

{
  "proveedor": "IMN Colombia",
  "items": [
    {"producto_nombre_raw": "Creatina IMN 133 serv 550g", "cantidad": 12, "precio_costo_unitario": 75000},
    {"producto_nombre_raw": "Proteína Whey IMN 2lb chocolate", "cantidad": 6, "precio_costo_unitario": 95000}
  ],
  "notas": null
}

Responde ÚNICAMENTE con el JSON. Sin texto adicional ni markdown.
"""


# ---------------------------------------------------------------------------
# Scalability hook — future Vision API integration
# ---------------------------------------------------------------------------

# def process_invoice_image(image_bytes: bytes) -> ParsedPurchase:
#     """
#     [FUTURE] Processes an invoice or remission image using GPT-4o Vision.
#
#     To activate: in streamlit_app.py replace st.text_area with
#     st.file_uploader(type=["jpg","png","pdf"]) and call
#     process_invoice_image(uploaded_file.read()) instead of parse_purchase().
#     """


# ---------------------------------------------------------------------------
# Main function
# ---------------------------------------------------------------------------

def parse_purchase(text: str) -> ParsedPurchase:
    """
    Parses supplier text and returns a ParsedPurchase.

    Args:
        text: Message or product list from the supplier.

    Returns:
        ParsedPurchase with supplier, items, and notes.

    Raises:
        ValueError: If the JSON is invalid or does not match the schema.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        try:
            import streamlit as st
            api_key = st.secrets["OPENAI_API_KEY"]
        except Exception:
            pass
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set in .env or st.secrets")

    client = OpenAI(api_key=api_key)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": PURCHASE_SYSTEM_PROMPT},
            {"role": "user",   "content": f"Parsea esta compra:\n\n{text.strip()}"},
        ],
    )

    raw_json = response.choices[0].message.content

    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError as e:
        logger.error("Invalid JSON from model | error=%s | response=%s", e, raw_json)
        raise ValueError(f"AI returned invalid JSON: {e}\n\nResponse: {raw_json}")

    try:
        purchase = ParsedPurchase.model_validate(data)
    except Exception as e:
        logger.error("JSON does not match schema | error=%s | json=%s", e, raw_json)
        raise ValueError(f"JSON does not match expected schema: {e}\n\nJSON: {raw_json}")

    return purchase


# ---------------------------------------------------------------------------
# Backward-compatible aliases
# ---------------------------------------------------------------------------
CompraParseada = ParsedPurchase
ItemCompraData = PurchaseItemData
parsear_compra = parse_purchase
