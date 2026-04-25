# Colsports — Sales & Inventory System

Omnichannel automation system for a Colombian sports supplements and equipment business.
Transforms WhatsApp, Rappi, and Instagram messages into structured database records,
with a web interface for sales management, analytics, and inventory tracking.

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
Streamlit Dashboard         ← web interface: sales, analytics, inventory, purchases
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| AI Engine | OpenAI GPT-4o-mini |
| Validation | Pydantic v2 |
| ORM / DB | SQLAlchemy 2.0 + PostgreSQL (Supabase) |
| Web Interface | Streamlit + Plotly |
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
│   ├── guardar_venta.py       # Persistence: ParsedSale → DB + stock deduction
│   ├── purchase_parser.py     # AI parser: supplier text → ParsedPurchase
│   └── guardar_compra.py      # Persistence: purchase DataFrame → DB + stock addition
├── app/
│   ├── streamlit_app.py       # Main web interface (login, nav, 4 modules)
│   ├── db_queries.py          # Cached queries for dashboard and pages
│   └── charts.py              # Interactive Plotly charts (dark theme)
├── models/
│   ├── venta.py               # Sale + SaleStatus (pendiente/confirmada/despachada…)
│   ├── venta_item.py          # Product line with matched SKU
│   ├── producto.py            # Catalog with stock_actual
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
│   ├── reset_data.py          # Clears all sales/purchases and zeros stock
│   ├── consolidate_and_import.py  # ETL: imports product catalog from CSV
│   └── procesar_venta.py      # CLI: process a message from the console
├── tests/
│   ├── test_motor_ia.py       # Tests: normalization, calculations, parsing
│   └── test_guardar_venta.py  # Tests: SKU matching, SQLite integration
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
```

> The `.env` file is in `.gitignore`. Never commit it to the repository.

### 3. Create database tables

```bash
python scripts/create_tables.py
```

### 4. Import product catalog (optional)

```bash
python scripts/consolidate_and_import.py
```

### 5. Run the app

```bash
streamlit run app/streamlit_app.py
```

Open `http://localhost:8501`. Password is set with `APP_PASSWORD` in `.env`.

---

## Web Interface Modules

| Module | What it does |
|---|---|
| **Nueva Venta** | Paste message → AI parsing → preview → confirm and save to DB |
| **Dashboard** | KPIs (today/month), daily trend, sales by channel, top products |
| **Inventario** | Catalog with search, negative/low stock alerts, combo virtual stock, hot products |
| **Compras** | Paste supplier message → AI parsing → review table → confirm and update stock |

---

## How to Add New Products to the Catalog

Products are stored in the `productos` table. There are two ways to add them:

### Option A — Direct SQL in Supabase (recommended for bulk)

Go to your Supabase project → SQL Editor and run:

```sql
INSERT INTO productos (sku, nombre, marca, categoria, stock_actual)
VALUES
  ('SKU-001', 'Creatina IMN 133 serv 550g', 'IMN', 'Suplementos', 0),
  ('SKU-002', 'Whey Protein IMN 2lb Chocolate', 'IMN', 'Suplementos', 0);
```

Rules:
- `sku` must be unique and never change (it is the permanent identifier used for stock tracking)
- `stock_actual` starts at `0`; use the **Compras** module to fill it
- `categoria` is free text — use consistent values for the dashboard to group correctly

### Option B — Edit the CSV and re-import

1. Edit `suplementos.csv` or `implementos.csv` with the new products
2. Run `python scripts/consolidate_and_import.py`

---

## How to Add Combos

A combo is a product SKU whose stock is derived from its component SKUs.
When a combo is sold, stock is deducted from each component, not from the combo itself.

### Step 1 — Create the combo as a regular product

```sql
INSERT INTO productos (sku, nombre, marca, categoria, stock_actual)
VALUES ('COMBO-001', 'Kit Inicio Deportivo', 'Colsports', 'Combos', 0);
```

### Step 2 — Define its components

Each row in `combo_componentes` means: "to make 1 unit of this combo, use N units of this component".

```sql
INSERT INTO combo_componentes (combo_sku, componente_sku, cantidad)
VALUES
  ('COMBO-001', 'SKU-001', 1),   -- 1 unit of Creatina IMN
  ('COMBO-001', 'SKU-002', 1);   -- 1 unit of Whey Protein IMN
```

### How it works at sale time

When `COMBO-001` is sold:
- `SKU-001` stock decreases by 1
- `SKU-002` stock decreases by 1
- If any component goes negative, an alert is created in `alertas_pedido`

The **Inventario → Combos** tab shows the virtual stock (how many combos can be assembled with current component stock).

---

## Reset Data (start fresh)

```bash
python scripts/reset_data.py
```

Clears: all sales, purchases, payments, shipping, and restock alerts.
Sets all product `stock_actual` to 0.
Does NOT touch: product catalog, combos, or channel/payment configuration.

---

## Database Schema

| Table | Description |
|---|---|
| `ventas` | Sale header: channel, customer, amounts, status, original message, extracted JSON |
| `venta_items` | Product lines per sale with matched SKU, quantity, and unit price |
| `productos` | Product catalog with `stock_actual` (auto-decremented on sale) |
| `clientes` | Customers deduplicated by cedula |
| `canales` | Sales channels (WhatsApp, Local, Rappi, etc.) |
| `pagos` | Payment method, destination account, and amount |
| `envios` | Shipping address, city, and department |
| `rappi_detalles` | Order ID, type (Regular/Pro), commission % and calculated amount |
| `compras` | Purchase order header: supplier, date, total amount |
| `detalle_compras` | Purchase line items: raw name, matched SKU, quantity, unit cost |
| `combo_componentes` | Combo → component mapping with quantity per unit |
| `alertas_pedido` | Restock alerts when combo components go negative |

### Sale lifecycle

```
pendiente → confirmada → despachada → entregada
                                  ↘ cancelada
```

---

## Design Decisions

- **LLM extracts, never calculates.** All amounts are computed in Python (`calculate_amounts()`), never by the model. This eliminates hallucinated totals.
- **F1-score SKU matching.** `_match_sku()` combines recall and precision so kits/combos do not outscore individual products. Includes plural→singular stemming and digit-letter tokenization.
- **Single transaction.** `save_sale()` and `save_purchase()` persist everything in one `commit`. If anything fails, nothing is saved.
- **`total_declarado`** handles messages with a global price and no per-item breakdown.
- **`session_state` in Streamlit** preserves the parsed sale while the user reviews the preview before confirming.
- **Backward-compatible aliases.** All renamed functions keep Spanish aliases so existing scripts and tests continue to work without modification.

---

## Running Tests

```bash
pytest tests/ -v
```

Tests cover: text normalization, amount calculation, OpenAI-mocked parsing, F1-score SKU matching, and SQLite in-memory integration.

---

## Roadmap

See the Scaling Plan section in the project documentation for:
- Rappi inventory sync (webhook or polling approach)
- WhatsApp Business API integration (eliminate copy-paste)
- PDF/Excel report exports
- Product alias system (e.g. "92 serv" ↔ "550g")
