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
from pydantic import BaseModel, Field, field_validator

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
    metodo: Optional[str] = Field(default="Sin especificar")
    cuenta_destino: Optional[str] = None
    referencia: Optional[str] = None

    @field_validator("metodo", mode="before")
    @classmethod
    def metodo_no_nulo(cls, v):
        return v if v else "Sin especificar"


class RappiDetalleData(BaseModel):
    """Información exclusiva de pedidos Rappi / Rappi Pro."""
    order_id: Optional[str] = Field(default=None, description="ID numérico del pedido Rappi")
    tipo: Optional[str] = Field(default=None, description="'Regular' o 'Pro'")
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
    total_declarado: Optional[int] = Field(
        default=None,
        description="Total general mencionado en el mensaje cuando no hay precios por item. Ej: '$338.000' con 2 productos sin desglose."
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

    Si los items no tienen precio_unitario pero hay un total_declarado en el mensaje,
    usa ese valor como subtotal (caso: un precio global para múltiples productos).

    Returns:
        dict con claves: subtotal, costo_envio, comision_monto, descuento, total
    """
    subtotal_calculado = sum(
        (item.precio_unitario or 0) * item.cantidad
        for item in venta.items
    )

    # Si no se pudo calcular desde items pero el mensaje declara un total, usarlo
    subtotal = subtotal_calculado if subtotal_calculado > 0 else (venta.total_declarado or 0)

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
     (un "par" = presentación x2; estandariza el nombre con "x2" para facilitar búsqueda en catálogo)

4. CLIENTE: En ventas locales puede haber solo el nombre. Crea objeto cliente solo con nombre.
   Si no hay ningún dato de cliente, cliente=null.

5. CEDULA: Número que aparece solo después del nombre. Típicamente 8-10 dígitos.
   No confundir con teléfono (10 dígitos empezando en 3 o 6).

6. FUENTE_REFERIDO: Si el cliente menciona cómo conoció el negocio → extrae solo la fuente puntual (ej: "covoley", "Instagram", "TikTok"). No copies la frase completa.

11. PAGO PARCIAL / ABONO: Si el mensaje indica que el cliente abona una parte y queda un saldo pendiente, captura esa información en notas. Ejemplo: "abona $65.500 / pendiente por pagar $65.500". El precio_unitario y total_declarado reflejan el valor total del producto, no el abono.

9. TELÉFONOS MÚLTIPLES: Identifica TODOS los números de teléfono del mensaje (10 dígitos, empiezan en 3 o 6).
   - El primero va en cliente.telefono (sin espacios ni guiones).
   - Los demás van en notas, uno por línea: "Teléfono adicional: XXXXXXXXXX".
   - Si notas ya tiene otro texto (ej: receptor), concaténalos separados por " | ".
   Ejemplo: "301 4083472 - 3158305413" → telefono="3014083472", notas contiene "Teléfono adicional: 3158305413".

10. RECEPTOR DIFERENTE AL COMPRADOR: Si el mensaje indica que quien recibe el pedido es otra persona distinta al comprador (ej: "Recibe: Richar Vásquez"), agrégalo en notas (ej: "Recibe: Richar Vásquez").

7. PAGO:
   - "Bancolombia Colsports Colombia" → metodo="Transferencia Bancolombia", cuenta_destino="Colsports Colombia"
   - "nequi JR" → metodo="Nequi", cuenta_destino="JR"
   - "efectivo" → metodo="Efectivo", cuenta_destino=null
   - "Contra entrega Rappi" → metodo="Contra entrega Rappi", cuenta_destino=null
   - "transferencia", "Transferencia", "pago por transferencia" o cualquier variante sin banco específico → metodo="Transferencia Bancolombia", cuenta_destino=null
     IMPORTANTE: La palabra "Transferencia" sola SIEMPRE se convierte en "Transferencia Bancolombia".
   - "tarjeta de crédito bold" o "tarjeta bold" → metodo="Tarjeta de crédito", cuenta_destino="Bold"
   - "tarjeta de crédito" sin terminal → metodo="Tarjeta de crédito", cuenta_destino=null

8. DIRECCIÓN: Separar campos cuando sea posible.
   "Dosquebradas, Risaralda" → ciudad="Dosquebradas", departamento="Risaralda"
   Si hay ciudad o dirección pero no se menciona departamento → departamento="Antioquia" (valor por defecto del negocio).
   Si NO hay dirección NI ciudad en el mensaje → envio=null (objeto completo en null, no un objeto con campos null).
   NUNCA pongas el string "null" como valor — usa null (JSON null) si realmente no hay dato.

ESTRUCTURA EXACTA DEL JSON (respeta estos nombres de campo sin excepción):

{
  "canal": "TikTok Live",
  "cliente": {
    "nombre": "Nombre completo",
    "cedula": "1050277346",
    "telefono": "3016986941",
    "email": "correo@gmail.com"
  },
  "items": [
    {
      "producto_nombre_raw": "Creatina IN 60 serv",
      "cantidad": 1,
      "precio_unitario": 80000
    }
  ],
  "costo_envio": 5000,
  "total_declarado": null,
  "pago": {
    "metodo": "Nequi",
    "cuenta_destino": "JR",
    "referencia": null
  },
  "envio": {
    "direccion": "calle 28 kr 63A casa",
    "ciudad": "El Carmen de Bolívar",
    "departamento": "Bolívar",
    "codigo_postal": null
  },
  "rappi_detalle": {
    "order_id": "2449862303",
    "tipo": "Pro",
    "comision_porcentaje": 16.0
  },
  "fuente_referido": "TikTok",
  "notas": null
}

IMPORTANTE:
- Si hay un precio total general sin desglose por producto (ej: "$338.000" para 2 items), ponlo en "total_declarado" y deja precio_unitario de cada item en null
- Si hay precios individuales por producto, ponlos en precio_unitario de cada item y deja total_declarado en null
- cedula, telefono y email van DENTRO del objeto "cliente", nunca en la raíz
- Los productos van en "items" (no "productos"), con el campo "producto_nombre_raw" (no "nombre_producto")
- El método de pago va en "pago" (no "metodo_pago")
- La dirección va dentro de "envio" (no "direccion" en la raíz)
- Responde ÚNICAMENTE con el JSON. Sin texto adicional.
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
