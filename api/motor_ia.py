"""
motor_ia.py
===========
Transforma un mensaje de WhatsApp en un objeto Python estructurado (VentaParseada).

Flujo:
    texto crudo  →  normalizar_texto_venta()  →  OpenAI GPT-4o-mini  →  JSON validado  →  VentaParseada

El modelo solo EXTRAE campos. Todos los cálculos (subtotal, comisión, total)
se realizan en Python mediante calcular_montos(). El LLM nunca hace aritmética.

Este módulo NO toca la base de datos. Solo parsea y expone utilidades de cálculo.
"""

import os
import re
import json
import logging
from typing import Optional, List
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field

load_dotenv()

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Modelos Pydantic — representan campos EXTRAÍDOS del mensaje (no calculados)
# ---------------------------------------------------------------------------

class ClienteData(BaseModel):
    """Datos del comprador extraídos del mensaje."""
    nombre: str
    cedula: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None


class ItemData(BaseModel):
    """Un producto dentro de la venta."""
    producto_nombre_raw: str = Field(
        description="Nombre del producto exactamente como aparece en el mensaje"
    )
    cantidad: int = Field(default=1, ge=1)
    precio_unitario: Optional[int] = Field(
        default=None,
        description="Precio por unidad en COP (entero). None si no aparece por separado en el mensaje."
    )


class EnvioData(BaseModel):
    """Datos de entrega. Solo aplica para ventas que requieren despacho."""
    direccion: Optional[str] = None
    ciudad: Optional[str] = None
    departamento: Optional[str] = None
    codigo_postal: Optional[str] = None


class PagoData(BaseModel):
    """Método de pago usado en la venta."""
    metodo: str
    cuenta_destino: Optional[str] = None
    referencia: Optional[str] = None


class RappiDetalleData(BaseModel):
    """Información exclusiva de pedidos Rappi / Rappi Pro."""
    order_id: str
    tipo: str = Field(description="'Regular' o 'Pro'")
    comision_porcentaje: Optional[float] = Field(
        default=None,
        description="Porcentaje de comisión cobrado por Rappi (ej: 16.0). Solo el porcentaje, no el monto."
    )


class VentaParseada(BaseModel):
    """
    Representación completa de una venta extraída del mensaje.

    Solo contiene datos EXTRAÍDOS del texto. Los montos calculados
    (subtotal, descuento, total) se obtienen mediante calcular_montos().
    """
    canal: str
    cliente: Optional[ClienteData] = None
    items: List[ItemData]
    costo_envio: Optional[int] = Field(
        default=None,
        description="Costo de envío en COP extraído del mensaje. None si no se menciona."
    )
    pago: PagoData
    envio: Optional[EnvioData] = None
    rappi_detalle: Optional[RappiDetalleData] = None
    fuente_referido: Optional[str] = None
    notas: Optional[str] = None


# ---------------------------------------------------------------------------
# Cálculos de dinero en Python (la aritmética nunca la hace el LLM)
# ---------------------------------------------------------------------------

def calcular_montos(venta: VentaParseada) -> dict:
    """
    Calcula subtotal, comisión, descuento y total desde los datos extraídos.

    Returns:
        dict con claves: subtotal, costo_envio, comision_monto, descuento, total
    """
    subtotal = sum(
        (item.precio_unitario or 0) * item.cantidad
        for item in venta.items
    )
    costo_envio = venta.costo_envio or 0
    comision_monto = 0

    if venta.rappi_detalle and venta.rappi_detalle.comision_porcentaje:
        comision_monto = round(subtotal * venta.rappi_detalle.comision_porcentaje / 100)

    descuento = comision_monto
    total = subtotal + costo_envio - descuento

    return {
        "subtotal": subtotal,
        "costo_envio": costo_envio,
        "comision_monto": comision_monto,
        "descuento": descuento,
        "total": total,
    }


# ---------------------------------------------------------------------------
# Normalización del texto antes de enviar al modelo
# ---------------------------------------------------------------------------

def normalizar_texto_venta(texto: str) -> str:
    """
    Limpia el mensaje antes de enviarlo al LLM:
    - Colapsa espacios múltiples en la misma línea
    - Elimina líneas vacías repetidas consecutivas (max 1 línea vacía)
    - Quita espacios al inicio/fin de cada línea
    - Preserva toda la información relevante del mensaje
    """
    texto = re.sub(r"[ \t]+", " ", texto)
    lineas = texto.splitlines()
    lineas = [l.strip() for l in lineas]

    resultado: list[str] = []
    linea_vacia_previa = False
    for linea in lineas:
        if linea == "":
            if not linea_vacia_previa:
                resultado.append(linea)
            linea_vacia_previa = True
        else:
            resultado.append(linea)
            linea_vacia_previa = False

    return "\n".join(resultado).strip()


# ---------------------------------------------------------------------------
# Prompt del sistema — solo extracción, sin instrucciones de cálculo
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

4. CLIENTE: En ventas locales puede haber solo el nombre. Crea objeto cliente solo con nombre.
   Si no hay ningún dato de cliente, cliente=null.

5. CEDULA: Número que aparece solo después del nombre. Típicamente 8-10 dígitos.
   No confundir con teléfono (10 dígitos empezando en 3 o 6).

6. FUENTE_REFERIDO: Si el cliente menciona cómo conoció el negocio → extrae como fuente_referido.

7. PAGO:
   - "Bancolombia Colsports Colombia" → metodo="Transferencia Bancolombia", cuenta_destino="Colsports Colombia"
   - "nequi JR" → metodo="Nequi", cuenta_destino="JR"
   - "efectivo" → metodo="Efectivo", cuenta_destino=null
   - "Contra entrega Rappi" → metodo="Contra entrega Rappi", cuenta_destino=null

8. DIRECCIÓN: Separar campos cuando sea posible.
   "Dosquebradas, Risaralda" → ciudad="Dosquebradas", departamento="Risaralda"

Responde ÚNICAMENTE con un JSON válido que siga el schema. Sin texto adicional.
"""


# ---------------------------------------------------------------------------
# Función principal
# ---------------------------------------------------------------------------

def parsear_mensaje(texto: str) -> VentaParseada:
    """
    Normaliza y parsea un mensaje de WhatsApp → VentaParseada.

    Args:
        texto: El mensaje tal como llega por WhatsApp (sin procesar).

    Returns:
        VentaParseada con los campos extraídos y validados por Pydantic.

    Raises:
        ValueError: Si el JSON retornado es inválido o no cumple el schema.
        openai.APIError: Si hay un error de comunicación con la API.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY no está definida en el archivo .env")

    texto_normalizado = normalizar_texto_venta(texto)

    client = OpenAI(api_key=api_key)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": f"Parsea esta venta:\n\n{texto_normalizado}"},
        ],
    )

    raw_json = response.choices[0].message.content

    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError as e:
        logger.error(
            "JSON inválido del modelo | error=%s | texto_original_inicio=%r | respuesta_modelo=%s",
            e, texto[:300], raw_json,
        )
        raise ValueError(f"La IA retornó un JSON inválido: {e}\n\nRespuesta: {raw_json}")

    try:
        venta = VentaParseada.model_validate(data)
    except Exception as e:
        logger.error(
            "JSON no cumple el schema | error=%s | texto_original_inicio=%r | json_recibido=%s",
            e, texto[:300], raw_json,
        )
        raise ValueError(f"El JSON no cumple el schema esperado: {e}\n\nJSON recibido: {raw_json}")

    return venta
