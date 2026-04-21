# ColSports — Motor de Automatización de Inventario

Sistema de automatización omnicanal para un negocio de suplementos e implementos deportivos. El núcleo del proyecto es un motor de IA que transforma mensajes de texto no estructurados (WhatsApp, TikTok Live) en registros estructurados en una base de datos SQL, eliminando el registro manual y los errores humanos.

---

## Visión del Proyecto

Convertir una operación basada en chats en una empresa impulsada por datos.

| Objetivo | Descripción |
|---|---|
| **Control de Inventario** | Sincronización en tiempo real entre ventas de WhatsApp/Local y el stock disponible |
| **Inteligencia de Negocio** | Dashboard con métricas: ventas totales, rotación de productos, ventas por canal |
| **Escalabilidad** | Manejo de alto volumen durante TikTok Lives sin colapsar el inventario |
| **Gestión de Faltantes** | Alertas automáticas de productos sin stock para generar pedidos a proveedores |

### Canales Operativos
- WhatsApp
- Rappi *(fase futura)*
- Tienda Física
- TikTok Live
- Web *(fase futura)*

---

## Stack Tecnológico

| Capa | Tecnología |
|---|---|
| Backend / API | FastAPI + Uvicorn |
| Base de Datos | PostgreSQL (Supabase) |
| ORM | SQLAlchemy 2.0 |
| Motor de IA | OpenAI API |
| ETL / Data | Pandas |
| Hojas de Cálculo | gspread (Google Sheets) |
| Config | python-dotenv |

---

## Estructura del Proyecto

```
col-inventory-app/
├── api/                        # API REST (FastAPI) — en desarrollo
├── models/                     # Modelos de datos SQLAlchemy — en desarrollo
├── scripts/
│   └── consolidate_and_import.py   # ETL: carga CSVs y hace upsert en PostgreSQL
├── implementos.csv             # Catálogo de implementos deportivos (kettlebells, etc.)
├── suplementos.csv             # Catálogo de suplementos (proteínas, creatina, etc.)
├── requirements.txt
└── .env                        # Variables de entorno (no subir al repo)
```

---

## Estado Actual

- [x] Pipeline ETL funcional — importa y sincroniza productos desde CSVs a PostgreSQL
- [x] Deduplicación por SKU con upsert (no destruye datos existentes)
- [ ] Modelos de datos SQLAlchemy (`models/`)
- [ ] API REST con FastAPI (`api/`)
- [ ] Motor de IA para parsear mensajes de WhatsApp → registros de venta
- [ ] Sistema de alertas de stock
- [ ] Dashboard de métricas

---

## Setup

### 1. Clonar e instalar dependencias

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configurar variables de entorno

Crear un archivo `.env` en la raíz del proyecto:

```env
DATABASE_URL=postgresql://usuario:password@host:puerto/nombre_db
```

### 3. Importar catálogo de productos

```bash
python scripts/consolidate_and_import.py
```

Esto creará la tabla `productos` si no existe y hará upsert de todos los SKUs desde los CSVs.

---

## Esquema de Base de Datos

### Tabla `productos`

| Columna | Tipo | Descripción |
|---|---|---|
| `sku` | String (PK) | Código único del producto |
| `nombre` | String | Nombre del producto |
| `peso` | String | Peso/presentación (aplica a implementos) |
| `marca` | String | Marca del producto |
| `categoria` | String | `Implemento` o `Suplemento` |
| `stock_actual` | Integer | Stock disponible (default: 0) |
