# Colsports — Sistema de Ventas e Inventario

Sistema de automatización omnicanal para un negocio colombiano de suplementos e implementos deportivos. Transforma mensajes de WhatsApp, Rappi e Instagram en registros estructurados en base de datos, con interfaz web para gestión de ventas, métricas e inventario.

---

## Arquitectura general

```
Mensaje WhatsApp / Rappi / Instagram
            │
            ▼
normalizar_texto_venta()    ← limpieza de whitespace
            │
            ▼
OpenAI GPT-4o-mini          ← extrae campos (nunca calcula montos)
            │
            ▼
VentaParseada (Pydantic v2) ← validación de esquema
            │
            ▼
calcular_montos()           ← aritmética 100% en Python
            │
            ▼
guardar_venta()             ← 1 transacción: venta + items + pago + envío + stock
            │
            ▼
PostgreSQL (Supabase)       ← fuente de verdad
            │
            ▼
Streamlit Dashboard         ← interfaz web: ventas, métricas e inventario
```

---

## Stack tecnológico

| Capa | Tecnología |
|---|---|
| Motor de IA | OpenAI GPT-4o-mini |
| Validación | Pydantic v2 |
| ORM / BD | SQLAlchemy 2.0 + PostgreSQL (Supabase) |
| Interfaz web | Streamlit + Plotly |
| Config | python-dotenv |
| Tests | pytest (42 tests) |

---

## Canales de venta soportados

| Canal | Prefijo del mensaje |
|---|---|
| WhatsApp | `VENTA WHATSAPP` |
| Local (tienda física) | `VENTA LOCAL` |
| Rappi | `VENTA RAPPI` |
| Rappi Pro | `VENTA RAPPI PRO` |
| TikTok Live | `VENTA LIVE TIK TOK` |
| Instagram | `VENTA INSTAGRAM` |

---

## Estructura del proyecto

```
col-inventory-app/
├── api/
│   ├── motor_ia.py            # Parser IA: mensaje → VentaParseada
│   └── guardar_venta.py       # Persistencia: VentaParseada → BD + descuento stock
├── app/
│   ├── streamlit_app.py       # Interfaz web principal (login, nav, 3 módulos)
│   ├── db_queries.py          # Queries con caché para el dashboard
│   └── charts.py              # Gráficos Plotly interactivos
├── models/
│   ├── venta.py               # Venta + EstadoVenta (pendiente/confirmada/despachada…)
│   ├── venta_item.py          # Línea de producto con SKU matcheado
│   ├── producto.py            # Catálogo con stock_actual
│   ├── cliente.py             # Comprador (deduplicado por cédula)
│   ├── canal.py               # Canal de venta
│   ├── pago.py                # Método y cuenta destino
│   ├── envio.py               # Dirección de despacho
│   ├── rappi_detalle.py       # Order ID, tipo y comisión Rappi
│   └── base.py                # DeclarativeBase compartida
├── scripts/
│   ├── procesar_venta.py      # CLI: procesa un mensaje por consola
│   ├── create_tables.py       # Crea tablas en la BD
│   └── consolidate_and_import.py  # ETL: importa catálogo desde CSV
├── tests/
│   ├── test_motor_ia.py       # 21 tests: normalización, cálculos, parseo
│   └── test_guardar_venta.py  # 21 tests: SKU matching, integración en SQLite
├── .env.example               # Plantilla de variables de entorno
├── .gitignore
└── requirements.txt
```

---

## Setup

### 1. Clonar e instalar dependencias

```bash
git clone https://github.com/Or0911/col-inventory-app.git
cd col-inventory-app

python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux

pip install -r requirements.txt
```

### 2. Configurar variables de entorno

```bash
cp .env.example .env
```

Edita `.env` con tus credenciales reales:

```env
DATABASE_URL=postgresql://usuario:contraseña@host:puerto/nombre_db
OPENAI_API_KEY=sk-proj-...
APP_PASSWORD=tu_contraseña_segura
```

> ⚠️ El archivo `.env` está en `.gitignore`. Nunca lo subas al repositorio.

### 3. Crear tablas en la base de datos

```bash
python scripts/create_tables.py
```

### 4. Importar catálogo de productos (opcional)

```bash
python scripts/consolidate_and_import.py
```

---

## Interfaz web

```bash
streamlit run app/streamlit_app.py
```

Abre `http://localhost:8501`. La contraseña se configura con `APP_PASSWORD` en `.env`.

| Módulo | Qué hace |
|---|---|
| **Nueva Venta** | Pegar mensaje → parseo IA → vista previa → confirmar y guardar en BD |
| **Dashboard** | KPIs (hoy/mes), tendencia diaria, ventas por canal, top productos, ingresos por método de pago |
| **Inventario** | Catálogo con buscador, alertas de stock negativo y stock bajo, detalle de pedidos sin stock, Hot Products |

---

## CLI — procesar venta por consola

```bash
# Mensaje como argumento
python scripts/procesar_venta.py "VENTA LOCAL\nDiby\n1 und Creatina IMN 133 serv\n$139.000\nEfectivo"

# Desde archivo
python scripts/procesar_venta.py --archivo mensaje.txt

# Modo interactivo
python scripts/procesar_venta.py --interactivo
```

---

## Tests

```bash
pytest tests/ -v
```

42 tests cubren normalización de texto, cálculo de montos, parseo con OpenAI mockeado, matching de SKU por F1-score e integración con SQLite en memoria.

---

## Esquema de base de datos

| Tabla | Descripción |
|---|---|
| `ventas` | Registro central: canal, cliente, montos (subtotal/envío/descuento/total), estado, mensaje original, JSON extraído |
| `venta_items` | Productos de cada venta con SKU matcheado, cantidad y precio |
| `productos` | Catálogo con `stock_actual` (se descuenta automáticamente al vender) |
| `clientes` | Compradores con deduplicación por cédula |
| `canales` | WhatsApp, Local, Rappi, Rappi Pro, TikTok Live, Instagram |
| `pagos` | Método, cuenta destino y monto |
| `envios` | Dirección, ciudad y departamento |
| `rappi_detalles` | Order ID, tipo (Regular/Pro), comisión % y monto calculado |

### Estados de una venta

```
pendiente → confirmada → despachada → entregada
                                  ↘ cancelada
```

---

## Decisiones de diseño

- **LLM solo extrae, nunca calcula.** Todos los montos se calculan en Python (`calcular_montos()`), no por el modelo.
- **SKU matching por F1-score.** Combina recall y precisión para que kits/combos no ganen a productos individuales. Incluye stemming plural→singular y tokenización número-letra.
- **Transacción única.** `guardar_venta()` persiste todo en un solo `commit`. Si algo falla, nada se guarda.
- **`total_declarado`** maneja mensajes con precio global sin desglose por producto.
- **`session_state` en Streamlit** preserva el mensaje y el parseo mientras el usuario revisa la vista previa antes de confirmar.

---

## Roadmap

- [ ] Sistema de alias de productos (ej: "92 serv" ↔ "550g")
- [ ] Gestión de combos (un combo descuenta múltiples SKUs individuales)
- [ ] Captura de segundo teléfono en `notas` (post-procesado Python)
- [ ] Webhook para recibir mensajes directamente desde WhatsApp / Rappi
- [ ] Módulo de reportes exportables (PDF / Excel)
- [ ] Carga inicial de stock real desde inventario físico
