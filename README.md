# Colsports — Sales & Inventory System

Omnichannel automation system for a Colombian sports supplements and equipment business.
Transforms WhatsApp, Rappi, and Instagram messages into structured database records,
with a web interface for sales management, analytics, inventory tracking, and purchase editing.

Deployed at: **Streamlit Community Cloud** (accessible from any phone or computer)

---

## Architecture

```
WhatsApp / Rappi / Instagram message
            │
            ▼
normalize_sale_text()       ← whitespace cleanup
            │
            ▼
OpenAI GPT-4o-mini          ← field extraction only (never calculates amounts)
            │
            ▼
ParsedSale (Pydantic v2)    ← schema validation
            │
            ▼
calculate_amounts()         ← 100% Python arithmetic
            │
            ▼
save_sale()                 ← 1 transaction: sale + items + payment + shipping + stock
            │
            ▼
PostgreSQL (Supabase)       ← source of truth
            │
            ▼
Streamlit Dashboard         ← web interface: sales, purchases, analytics, inventory
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| AI Engine | OpenAI GPT-4o-mini |
| Validation | Pydantic v2 |
| ORM / DB | SQLAlchemy 2.0 + PostgreSQL (Supabase) |
| Web Interface | Streamlit ≥ 1.35 + Plotly |
| Config | python-dotenv |
| Tests | pytest |

---

## Supported Sales Channels

| Channel | Message prefix |
|---|---|
| WhatsApp | `VENTA WHATSAPP` |
| Local (physical store) | `VENTA LOCAL` |
| Rappi | `VENTA RAPPI` |
| Rappi Pro | `VENTA RAPPI PRO` |
| TikTok Live | `VENTA LIVE TIK TOK` |
| Instagram | `VENTA INSTAGRAM` |

---

## Project Structure

```
col-inventory-app/
├── api/
│   ├── motor_ia.py            # AI parser: raw message → ParsedSale
│   ├── guardar_venta.py       # Persistence: ParsedSale → DB + stock deduction + Rappi sync
│   ├── purchase_parser.py     # AI parser: supplier text → ParsedPurchase
│   ├── guardar_compra.py      # Persistence: purchase DataFrame → DB + stock addition + Rappi sync
│   └── rappi_client.py        # HTTP client to enable/disable products in Rappi
├── app/
│   ├── streamlit_app.py       # Main web interface (login, nav, 6 pages)
│   ├── db_queries.py          # Cached read queries + write helpers
│   └── charts.py              # Interactive Plotly charts
├── models/
│   ├── venta.py               # Sale + SaleStatus enum
│   ├── venta_item.py          # Product line with matched SKU
│   ├── producto.py            # Catalog: stock_actual, rappi_product_id, alias
│   ├── cliente.py             # Customer (deduplicated by cedula)
│   ├── canal.py               # Sales channel
│   ├── pago.py                # Payment method and destination account
│   ├── envio.py               # Shipping address
│   ├── rappi_detalle.py       # Rappi order ID, type, and commission
│   ├── compra.py              # Purchase order header
│   ├── detalle_compra.py      # Purchase order line items
│   ├── combo_componente.py    # Combo → component mapping
│   ├── alerta_pedido.py       # Restock alerts for combo components
│   └── base.py                # Shared DeclarativeBase
├── scripts/
│   ├── create_tables.py       # Creates all tables in the DB
│   ├── migrate_rappisync.py   # DB migration: rappi_product_id + unique constraint
│   ├── migrate_alias.py       # DB migration: alias column on productos
│   ├── mapear_rappi_skus.py   # Fills rappi_product_id from ProductosActualizacion-es.xlsx
│   ├── reset_data.py          # Clears all sales/purchases and zeros stock
│   └── procesar_venta.py      # CLI: process a message from the console
├── tests/
│   ├── test_motor_ia.py       # Tests: normalization, calculations, parsing
│   └── test_guardar_venta.py  # Tests: SKU matching, SQLite integration
├── assets/
│   └── logo.png               # Colsports logo (PNG, transparent bg)
├── .env.example               # Environment variables template
├── .gitignore
└── requirements.txt
```

---

## Setup (local development)

### 1. Clone and install

```bash
git clone https://github.com/Or0911/Colsport-Inventory.git
cd col-inventory-app

python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux

pip install -r requirements.txt
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
DATABASE_URL=postgresql://user:password@host:port/dbname
OPENAI_API_KEY=sk-proj-...
APP_PASSWORD=your_secure_password

# Optional: visual theme
THEME_PRIMARY=#314457
THEME_PRIMARY_DARK=#243344
THEME_PRIMARY_TEXT=#ffffff

# Optional: Rappi sync
RAPPI_CLIENT_ID=...
RAPPI_CLIENT_SECRET=...
RAPPI_STORE_ID=900283093
```

> The `.env` file is in `.gitignore`. Never commit it.

### 3. Create database tables

```bash
python scripts/create_tables.py
```

### 4. Run database migrations (first deploy or after upgrade)

```bash
python scripts/migrate_rappisync.py   # adds rappi_product_id column
python scripts/migrate_alias.py       # adds alias column
```

### 5. Run the app

```bash
streamlit run app/streamlit_app.py
```

Open `http://localhost:8501`. Password is set with `APP_PASSWORD` in `.env`.

---

## Web Interface Pages

| Page | Description |
|---|---|
| **Nueva Venta** | Paste message → AI parsing → preview → confirm and save |
| **Dashboard** | KPIs (period/today/month), daily trend, channel distribution, top 5 products, money by account |
| **Inventario** | Catalog with search, negative stock alerts, combo virtual stock, hot products |
| **Compras** | Paste supplier message → review table → confirm and update stock. History with inline editing (24 h window, full stock reversal + reapply) |
| **Ventas** | Filterable history + detail viewer + inline editing (24 h window, no stock adjustment) |
| **Catálogo / Aliases** | Manage product aliases used as fallback in SKU matching |

---

## SKU Matching

`_match_sku()` in `api/guardar_venta.py` uses F1-score between tokenized product name and catalog entries:

1. Tokenizes raw name (digit-letter boundary split, minimal stemming).
2. Scores against `producto.nombre` — 60 % recall threshold.
3. If score = 0, falls back to each comma-separated entry in `producto.alias`.
4. Returns the SKU with the highest score, or `None`.

**Aliases allow distinguishing variants** that share the same base name:
```sql
-- Example: distinguish Creatina variants by alias
UPDATE productos SET alias = 'Creatina Creasmart 550g Sin sabor, Creasmart sin sabor'
WHERE sku = '2045';
```

---

## Sale and Purchase Editing (24-hour window)

Both the Ventas and Compras history pages show an **editable records** section for records created in the last 24 hours.

- **Purchase edit**: full stock reversal of old items → delete lines → insert new lines → apply new stock. Atomic single transaction.
- **Sale edit**: replaces items, recalculates totals, updates status and notes. **Stock is NOT adjusted** — correct via a purchase if quantities changed.

---

## Rappi Sync

When a product's stock changes, the system automatically enables or disables it in Rappi:

- **Sale recorded** → stock drops to 0 → product disabled in Rappi.
- **Purchase recorded** → stock rises above 0 → product re-enabled in Rappi.

Requires `RAPPI_CLIENT_ID`, `RAPPI_CLIENT_SECRET`, and `RAPPI_STORE_ID` in `.env`.
Silent no-op if not configured.

---

## How to Add Products and Aliases

### Add a new product

```sql
INSERT INTO productos (sku, nombre, marca, categoria, stock_actual)
VALUES ('1999', 'Whey Protein IMN 2lb Chocolate', 'IMN', 'Proteinas', 0);
```

Or use the **Catálogo / Aliases** page in the app.

### Add aliases to help the AI match variants

```sql
UPDATE productos SET alias = 'Alias 1, Alias 2, Alias 3'
WHERE sku = 'XXXX';
```

Or use the **Catálogo / Aliases** page in the app.

---

## How to Add Combos

```sql
-- 1. Create the combo as a regular product (stock stays 0)
INSERT INTO productos (sku, nombre, stock_actual)
VALUES ('COMBO-001', 'Kit Inicio Deportivo', 0);

-- 2. Define its components
INSERT INTO combo_componentes (combo_sku, componente_sku, cantidad)
VALUES ('COMBO-001', 'SKU-A', 1), ('COMBO-001', 'SKU-B', 1);
```

Or edit `scripts/setup_combos.py` and re-run it (idempotent).

---

## Rollback / Safe Point

The tag `v1.1-stable` marks a known-good commit:

```bash
git reset --hard v1.1-stable   # revert working directory
git push --force origin main   # push rollback (confirm first)
```

---

## Reset Data (development only)

```bash
python scripts/reset_data.py   # clears sales/purchases, zeros all stock
```

---

## Database Schema

| Table | Description |
|---|---|
| `productos` | Catalog: sku (PK), nombre, stock_actual, rappi_product_id, alias |
| `ventas` | Sale header: channel, customer, amounts, status, original message |
| `venta_items` | Product lines: matched SKU, quantity, unit price |
| `clientes` | Customers deduplicated by cedula |
| `canales` | Sales channels |
| `pagos` | Payment method and destination account |
| `envios` | Shipping address |
| `rappi_detalles` | Rappi order ID, type, commission (unique constraint on order_id) |
| `compras` | Purchase header: supplier, date, total |
| `detalle_compras` | Purchase line items: raw name, matched SKU, quantity, cost |
| `combo_componentes` | Combo → component mapping |
| `alertas_pedido` | Restock alerts when combo components go negative |

---

## Design Decisions

- **LLM extracts, never calculates.** All amounts computed in Python, never by the model.
- **F1-score SKU matching with alias fallback.** Combines recall and precision; checks `alias` field when `nombre` doesn't match.
- **Single transaction per write.** `save_sale()`, `save_purchase()`, `update_purchase_items()` — everything or nothing.
- **Column expressions in stock UPDATEs.** `values(stock_actual=Producto.stock_actual ± qty)` — DB performs the arithmetic atomically, avoiding ORM cache staleness.
- **24-hour edit window.** Limits retroactive corrections; errors obvious on the same day.
- **Sale edit does not adjust stock.** Sale = product already left the store. Purchase edit does adjust stock: purchase = physical receiving of goods.

---

## Running Tests

```bash
pytest tests/ -v
```
