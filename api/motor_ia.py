"""
motor_ia.py
===========
Transforms a WhatsApp message into a structured Python object (ParsedSale).

Flow:
    raw text  →  normalize_sale_text()  →  OpenAI GPT-4o-mini  →  validated JSON  →  ParsedSale

The model only EXTRACTS fields. All calculations (subtotal, commission, total)
are done in Python via calculate_amounts(). The LLM never performs arithmetic.

This module does NOT touch the database.
"""

import os
import re
import json
import logging
from typing import Optional, List
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field, field_validator

load_dotenv()

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pydantic models — represent EXTRACTED fields from the message (not calculated)
# Note: field names stay in Spanish because they match the JSON keys the LLM returns.
# ---------------------------------------------------------------------------

class CustomerData(BaseModel):
    """Buyer data extracted from the message."""
    nombre: str
    cedula: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None


class SaleItemData(BaseModel):
    """A single product line within the sale."""
    producto_nombre_raw: str = Field(
        description="Product name exactly as it appears in the message"
    )
    cantidad: int = Field(default=1, ge=1)
    precio_unitario: Optional[int] = Field(
        default=None,
        description="Unit price in COP (integer). None if not explicitly listed per product."
    )


class ShippingData(BaseModel):
    """Delivery details. Only applies to sales that require dispatch."""
    direccion: Optional[str] = None
    ciudad: Optional[str] = None
    departamento: Optional[str] = None
    codigo_postal: Optional[str] = None


class PaymentData(BaseModel):
    """Payment method used in the sale."""
    metodo: Optional[str] = Field(default="Sin especificar")
    cuenta_destino: Optional[str] = None
    referencia: Optional[str] = None

    @field_validator("metodo", mode="before")
    @classmethod
    def payment_method_not_null(cls, v):
        return v if v else "Sin especificar"


class RappiDetailData(BaseModel):
    """Data exclusive to Rappi / Rappi Pro orders."""
    order_id: Optional[str] = Field(default=None, description="Rappi numeric order ID")
    tipo: Optional[str] = Field(default=None, description="'Regular' or 'Pro'")
    comision_porcentaje: Optional[float] = Field(
        default=None,
        description="Commission percentage charged by Rappi (e.g. 16.0). Percentage only, not the amount."
    )


class ParsedSale(BaseModel):
    """
    Complete representation of a sale extracted from the message.

    Contains only EXTRACTED data. Calculated amounts (subtotal, discount, total)
    are obtained via calculate_amounts().
    """
    canal: str
    cliente: Optional[CustomerData] = None
    items: List[SaleItemData]
    costo_envio: Optional[int] = Field(
        default=None,
        description="Shipping cost in COP extracted from the message. None if not mentioned."
    )
    total_declarado: Optional[int] = Field(
        default=None,
        description="Overall total stated in the message when no per-item prices exist."
    )
    pago: PaymentData
    envio: Optional[ShippingData] = None
    rappi_detalle: Optional[RappiDetailData] = None
    fuente_referido: Optional[str] = None
    notas: Optional[str] = None


# ---------------------------------------------------------------------------
# Money calculations in Python (the LLM never does arithmetic)
# ---------------------------------------------------------------------------

def calculate_amounts(sale: ParsedSale) -> dict:
    """
    Computes subtotal, commission, discount, and total from extracted data.

    If items have no unit price but the message declares an overall total,
    that value is used as the subtotal.

    Returns:
        dict with keys: subtotal, costo_envio, comision_monto, descuento, total
    """
    calculated_subtotal = sum(
        (item.precio_unitario or 0) * item.cantidad
        for item in sale.items
    )

    subtotal = calculated_subtotal if calculated_subtotal > 0 else (sale.total_declarado or 0)
    shipping = sale.costo_envio or 0
    commission = 0

    if sale.rappi_detalle and sale.rappi_detalle.comision_porcentaje:
        commission = round(subtotal * sale.rappi_detalle.comision_porcentaje / 100)

    discount = commission
    total = subtotal + shipping - discount

    return {
        "subtotal": subtotal,
        "costo_envio": shipping,
        "comision_monto": commission,
        "descuento": discount,
        "total": total,
    }


# ---------------------------------------------------------------------------
# Text normalization before sending to the model
# ---------------------------------------------------------------------------

def normalize_sale_text(text: str) -> str:
    """
    Cleans the message before sending to the LLM:
    - Collapses multiple spaces on the same line
    - Removes repeated consecutive blank lines (max 1 blank line)
    - Strips leading/trailing spaces from each line
    - Preserves all relevant message information
    """
    text = re.sub(r"[ \t]+", " ", text)
    lines = [line.strip() for line in text.splitlines()]

    output_lines: list[str] = []
    prev_blank = False
    for line in lines:
        if line == "":
            if not prev_blank:
                output_lines.append(line)
            prev_blank = True
        else:
            output_lines.append(line)
            prev_blank = False

    return "\n".join(output_lines).strip()


# ---------------------------------------------------------------------------
# System prompt — extraction only, no arithmetic instructions
# Spanish is intentional: the LLM must return JSON keys in Spanish to match
# the Pydantic schema.
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """
Eres un asistente especializado en EXTRAER datos estructurados de mensajes de ventas
de un negocio colombiano de suplementos e implementos deportivos llamado Colsports.

Tu tarea es SOLO EXTRAER lo que aparece en el texto. NO calcules totales, subtotales,
comisiones ni ninguna aritmética. Si un valor no aparece explícitamente, usa null.

Las ventas llegan por WhatsApp con este formato según el canal:

CANALES VÁLIDOS:
- "Rappi"       → mensaje empieza con "VENTA RAPPI" (sin "PRO")
- "Rappi Pro"   → mensaje empieza con "VENTA RAPPI PRO"
- "WhatsApp"    → mensaje empieza con "VENTA WHATSAPP"
- "Local"       → mensaje empieza con "VENTA LOCAL"
- "TikTok Live" → mensaje empieza con "VENTA LIVE TIK TOK" o similar
- "Instagram"   → mensaje empieza con "VENTA INSTAGRAM"

REGLAS DE EXTRACCIÓN:

1. PRECIOS (sistema colombiano: punto = miles):
   - "$299.485" → extrae el entero 299485
   - "$80.000 + $5.000 de envío" → precio_unitario=80000 en el item, costo_envio=5000
   - "envío gratis" o "envio gratis" → costo_envio=0
   - Sin mención de envío → costo_envio=null

2. COMISIÓN RAPPI: Si dice "(-16% comisión)" o similar:
   - Extrae comision_porcentaje=16.0 en rappi_detalle
   - NO calcules montos ni el neto resultante

3. PRODUCTOS: Formato típico "X Und nombre_producto"
   - "1 Und iso 100 1.3lb - dymatize - vainilla → $89.900" → cantidad=1, precio_unitario=89900
   - Si el precio no aparece junto al producto → precio_unitario=null
   - Si hay un total general sin desglose por item → precio_unitario=null en todos los items
   - "1 par Mancuernas 5kg" → producto_nombre_raw="Mancuerna 5kg x2", cantidad=1

4. CLIENTE: En ventas locales puede haber solo el nombre. Crea objeto cliente solo con nombre.
   Si no hay ningún dato de cliente, cliente=null.

5. CEDULA: Número que aparece solo después del nombre. Típicamente 8-10 dígitos.
   No confundir con teléfono (10 dígitos empezando en 3 o 6).

6. FUENTE_REFERIDO: Si el cliente menciona cómo conoció el negocio → extrae solo la fuente puntual (ej: "covoley", "Instagram", "TikTok").

11. PAGO PARCIAL / ABONO: Si el mensaje indica que el cliente abona una parte y queda un saldo pendiente, captura esa información en notas.

9. TELÉFONOS MÚLTIPLES: Identifica TODOS los números de teléfono del mensaje (10 dígitos, empiezan en 3 o 6).
   - El primero va en cliente.telefono (sin espacios ni guiones).
   - Los demás van en notas, uno por línea: "Teléfono adicional: XXXXXXXXXX".

10. RECEPTOR DIFERENTE AL COMPRADOR: Si el mensaje indica que quien recibe el pedido es otra persona, agrégalo en notas.

7. PAGO:
   - "Bancolombia Colsports Colombia" → metodo="Transferencia Bancolombia", cuenta_destino="Colsports Colombia"
   - "nequi JR" → metodo="Nequi", cuenta_destino="JR"
   - "efectivo" → metodo="Efectivo", cuenta_destino=null
   - "Contra entrega Rappi" → metodo="Contra entrega Rappi", cuenta_destino=null
   - "transferencia" sola → metodo="Transferencia Bancolombia", cuenta_destino=null
   - "tarjeta bold" → metodo="Tarjeta de crédito", cuenta_destino="Bold"

8. DIRECCIÓN:
   "Dosquebradas, Risaralda" → ciudad="Dosquebradas", departamento="Risaralda"
   Si NO hay dirección NI ciudad → envio=null.
   NUNCA pongas el string "null" como valor — usa null (JSON null).

ESTRUCTURA EXACTA DEL JSON (respeta estos nombres de campo sin excepción):

{
  "canal": "TikTok Live",
  "cliente": {"nombre": "Nombre completo", "cedula": "1050277346", "telefono": "3016986941", "email": null},
  "items": [{"producto_nombre_raw": "Creatina IN 60 serv", "cantidad": 1, "precio_unitario": 80000}],
  "costo_envio": 5000,
  "total_declarado": null,
  "pago": {"metodo": "Nequi", "cuenta_destino": "JR", "referencia": null},
  "envio": {"direccion": "calle 28 kr 63A", "ciudad": "El Carmen de Bolívar", "departamento": "Bolívar", "codigo_postal": null},
  "rappi_detalle": {"order_id": "2449862303", "tipo": "Pro", "comision_porcentaje": 16.0},
  "fuente_referido": "TikTok",
  "notas": null
}

Responde ÚNICAMENTE con el JSON. Sin texto adicional.
"""


# ---------------------------------------------------------------------------
# Main function
# ---------------------------------------------------------------------------

def parse_sale_message(text: str) -> ParsedSale:
    """
    Normalizes and parses a WhatsApp message into a ParsedSale object.

    Args:
        text: The raw message as received from WhatsApp.

    Returns:
        ParsedSale with extracted and Pydantic-validated fields.

    Raises:
        ValueError: If the returned JSON is invalid or fails schema validation.
        openai.APIError: If there is a communication error with the API.
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

    normalized_text = normalize_sale_text(text)

    client = OpenAI(api_key=api_key)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": f"Parsea esta venta:\n\n{normalized_text}"},
        ],
    )

    raw_json = response.choices[0].message.content

    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError as e:
        logger.error(
            "Invalid JSON from model | error=%s | text_preview=%r | response=%s",
            e, text[:300], raw_json,
        )
        raise ValueError(f"AI returned invalid JSON: {e}\n\nResponse: {raw_json}")

    try:
        sale = ParsedSale.model_validate(data)
    except Exception as e:
        logger.error(
            "JSON does not match schema | error=%s | text_preview=%r | json=%s",
            e, text[:300], raw_json,
        )
        raise ValueError(f"JSON does not match expected schema: {e}\n\nJSON: {raw_json}")

    return sale


# ---------------------------------------------------------------------------
# Backward-compatible aliases (used by legacy scripts and tests)
# ---------------------------------------------------------------------------
VentaParseada = ParsedSale
ClienteData = CustomerData
ItemData = SaleItemData
EnvioData = ShippingData
PagoData = PaymentData
RappiDetalleData = RappiDetailData
calcular_montos = calculate_amounts
normalizar_texto_venta = normalize_sale_text
parsear_mensaje = parse_sale_message
