"""
purchase_parser.py
==================
Transforma texto desordenado de un proveedor en un objeto CompraParseada.

Flujo:
    texto crudo  →  OpenAI GPT-4o-mini  →  JSON validado  →  CompraParseada

El modelo solo EXTRAE campos. Los totales se calculan en Python.
Este módulo NO toca la base de datos.

Punto de escalabilidad — Vision:
    En el futuro se podrá reemplazar el text_area por una imagen de factura.
    La función process_invoice_image() está preparada para esa integración.
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
# Modelos Pydantic
# ---------------------------------------------------------------------------

class ItemCompraData(BaseModel):
    producto_nombre_raw: str = Field(
        description="Nombre del producto tal como aparece en el mensaje del proveedor"
    )
    cantidad: int = Field(default=1, ge=1)
    precio_costo_unitario: Optional[int] = Field(
        default=None,
        description="Precio de costo por unidad en COP (entero sin decimales). None si no se menciona."
    )


class CompraParseada(BaseModel):
    proveedor: Optional[str] = Field(
        default=None,
        description="Nombre del proveedor o distribuidor mencionado en el mensaje"
    )
    items: List[ItemCompraData]
    notas: Optional[str] = None


# ---------------------------------------------------------------------------
# Prompt del sistema
# ---------------------------------------------------------------------------

SYSTEM_PROMPT_COMPRAS = """
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
   - Para kits o combos que se reciben como un solo paquete, trátalo como un solo item.

4. CANTIDADES: Número de unidades que llegan al inventario.
   - "12 und" → cantidad=12
   - "1 caja × 6" → cantidad=6 (lo que importa es el stock que suma al inventario).

5. Si el mensaje es una lista de precios o catálogo sin cantidades específicas,
   usa cantidad=1 para cada item como placeholder.

ESTRUCTURA EXACTA DEL JSON (respeta estos nombres sin excepción):

{
  "proveedor": "IMN Colombia",
  "items": [
    {
      "producto_nombre_raw": "Creatina IMN 133 serv 550g",
      "cantidad": 12,
      "precio_costo_unitario": 75000
    },
    {
      "producto_nombre_raw": "Proteína Whey IMN 2lb chocolate",
      "cantidad": 6,
      "precio_costo_unitario": 95000
    }
  ],
  "notas": null
}

Responde ÚNICAMENTE con el JSON. Sin texto adicional ni markdown.
"""


# ---------------------------------------------------------------------------
# Punto de escalabilidad: integración futura con Vision de OpenAI
# ---------------------------------------------------------------------------

# def process_invoice_image(image_bytes: bytes) -> CompraParseada:
#     """
#     [FUTURO] Procesa una imagen de factura o remisión usando GPT-4o Vision.
#
#     Integración:
#         client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
#         import base64
#         b64 = base64.b64encode(image_bytes).decode()
#         response = client.chat.completions.create(
#             model="gpt-4o",                  # gpt-4o tiene visión nativa
#             temperature=0,
#             response_format={"type": "json_object"},
#             messages=[
#                 {"role": "system", "content": SYSTEM_PROMPT_COMPRAS},
#                 {"role": "user", "content": [
#                     {"type": "text", "text": "Extrae los datos de esta factura:"},
#                     {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
#                 ]},
#             ],
#         )
#         return CompraParseada.model_validate(json.loads(response.choices[0].message.content))
#
#     Para activar: en streamlit_app.py reemplaza el st.text_area por st.file_uploader(type=["jpg","png","pdf"])
#     y llama a process_invoice_image(uploaded_file.read()) en lugar de parsear_compra().
# """


# ---------------------------------------------------------------------------
# Función principal
# ---------------------------------------------------------------------------

def parsear_compra(texto: str) -> CompraParseada:
    """
    Parsea el texto de un proveedor y devuelve una CompraParseada.

    Args:
        texto: Mensaje o lista de productos del proveedor.

    Returns:
        CompraParseada con proveedor, items y notas.

    Raises:
        ValueError: Si el JSON es inválido o no cumple el schema.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        try:
            import streamlit as st
            api_key = st.secrets["OPENAI_API_KEY"]
        except Exception:
            pass
    if not api_key:
        raise ValueError("OPENAI_API_KEY no está definida en .env ni en st.secrets")

    client = OpenAI(api_key=api_key)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT_COMPRAS},
            {"role": "user",   "content": f"Parsea esta compra:\n\n{texto.strip()}"},
        ],
    )

    raw_json = response.choices[0].message.content

    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError as e:
        logger.error("JSON inválido del modelo | error=%s | respuesta=%s", e, raw_json)
        raise ValueError(f"La IA retornó un JSON inválido: {e}\n\nRespuesta: {raw_json}")

    try:
        compra = CompraParseada.model_validate(data)
    except Exception as e:
        logger.error("JSON no cumple schema | error=%s | json=%s", e, raw_json)
        raise ValueError(f"El JSON no cumple el schema esperado: {e}\n\nJSON: {raw_json}")

    return compra
