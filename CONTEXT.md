# Colsports — Archivo de Contexto del Proyecto

> Actualizado el 2026-05-06 (v1.2-stable).

---

## 1. ¿Qué es este proyecto?

**Colsports** es un negocio colombiano de suplementos deportivos e implementos fitness (mancuernas, barras, discos, bandas de resistencia, proteínas, creatinas, etc.). Vende principalmente por WhatsApp, Rappi, Rappi Pro, TikTok Live, Instagram, Local y Página Web (WordPress).

Este repositorio es el **sistema interno de ventas e inventario** de Colsports: una aplicación web privada (acceso por contraseña) que permite:

- Registrar ventas copiando y pegando el mensaje de WhatsApp/Rappi → la IA extrae los datos automáticamente.
- Registrar compras a proveedores del mismo modo → actualiza el stock.
- Ver el inventario, alertas de stock bajo/negativo, y stock virtual de combos.
- Ver un dashboard con KPIs, tendencia de ventas, distribución por canal y top de productos.
- Editar ventas y compras dentro de una ventana de 24 horas desde el historial.

---

## 2. Stack tecnológico

| Capa | Tecnología |
|---|---|
| UI | Streamlit (Python ≥ 1.35) |
| Base de datos | PostgreSQL en Supabase |
| ORM | SQLAlchemy 2.x (mapped columns, typed) |
| IA extracción | OpenAI GPT-4o-mini (JSON mode, temperature=0) |
| Validación | Pydantic v2 |
| Deploy | Streamlit Community Cloud |
| Fuente tipográfica | Google Fonts — Poppins (sans-serif) |
| Assets estáticos | `assets/logo.png` — logo Colsports horizontal (PNG con fondo transparente). Fallback a texto "COLSPORTS" si no existe. En login se embebe como base64 en HTML (160px centrado). En sidebar se usa `st.image(width=150)`. |
| Estilos | CSS custom con variables `--cs-*` inyectadas desde dict `THEME` |

---

## 3. Arquitectura de archivos

```
col-inventory-app/
├── app/
│   ├── streamlit_app.py     ← Interfaz principal (login, sidebar, 5 páginas)
│   ├── db_queries.py        ← Todas las queries de lectura/escritura (@st.cache_data)
│   └── charts.py            ← Gráficos Plotly (tendencia, canal, top productos)
│
├── api/
│   ├── motor_ia.py          ← Parsea mensaje WhatsApp → ParsedSale (OpenAI)
│   ├── guardar_venta.py     ← Persiste ParsedSale en DB + descuenta stock + sync Rappi
│   ├── purchase_parser.py   ← Parsea texto proveedor → ParsedPurchase (OpenAI)
│   ├── guardar_compra.py    ← Persiste compra en DB + suma stock + sync Rappi
│   └── rappi_client.py      ← Sincroniza disponibilidad con Rappi (encender/apagar producto)
│
├── models/
│   ├── __init__.py          ← Exporta todos los modelos
│   ├── base.py              ← DeclarativeBase de SQLAlchemy
│   ├── producto.py          ← Producto (sku PK, nombre, marca, categoria, stock_actual, rappi_product_id)
│   ├── canal.py             ← Canal de venta (WhatsApp, Rappi, etc.)
│   ├── cliente.py           ← Cliente (nombre, cedula, telefono, email)
│   ├── venta.py             ← Venta + EstadoVenta enum
│   ├── venta_item.py        ← Línea de venta (sku nullable, nombre raw, qty, precio)
│   ├── pago.py              ← Método de pago (Nequi, Bancolombia, etc.)
│   ├── envio.py             ← Dirección de despacho
│   ├── rappi_detalle.py     ← order_id, tipo (Regular/Pro), comisión %
│   ├── combo_componente.py  ← Relación combo_sku → componente_sku + cantidad
│   ├── alerta_pedido.py     ← Componente de combo vendido sin stock suficiente
│   ├── compra.py            ← Cabecera de compra (proveedor, monto_total)
│   └── detalle_compra.py    ← Línea de compra (sku nullable, qty, costo)
│
├── scripts/
│   ├── create_tables.py     ← Crea todas las tablas en la DB (correr una vez)
│   ├── reset_data.py        ← TRUNCATE tablas transaccionales + stock=0 (pide "RESET")
│   ├── setup_combos.py      ← Inserta filas en combo_componentes (safe to re-run)
│   ├── mapear_rappi_skus.py ← Rellena rappi_product_id desde ProductosActualizacion-es.xlsx
│   └── consolidate_and_import.py ← Importación masiva histórica (legacy)
│
├── assets/
│   └── logo.png             ← Logo horizontal Colsports (PNG, fondo transparente)
│
├── .env                     ← DATABASE_URL, OPENAI_API_KEY, APP_PASSWORD (local)
├── requirements.txt
├── README.md
└── CONTEXT.md               ← Este archivo
```

---

## 4. Flujo de una venta

```
Mensaje WhatsApp / Rappi / Página Web / etc.
    │
    ▼
motor_ia.parse_sale_message()
    ├─ normalize_sale_text()         limpia espacios/saltos
    ├─ GPT-4o-mini (JSON mode)       extrae campos → ParsedSale
    └─ ParsedSale validado con Pydantic
    │
    ▼
Formulario editable en Streamlit (ANTES de confirmar)
    ├─ Selectbox de canal (incluye "Página Web")
    ├─ Campos de cliente editables (nombre, CC, teléfono, email)
    ├─ data_editor de ítems con SKU pre-sugerido por IA (editable)
    ├─ Selectbox de método de pago + cuenta destino
    └─ Notas editables / totales en tiempo real
    │
    ▼ [Confirmar y Guardar]
    │  ParsedSale reconstruido con los valores editados;
    │  SaleItemData.sku contiene el SKU seleccionado en el editor
    │
guardar_venta.save_sale()
    ├─ calculate_amounts()           subtotal/total/comisión en Python (no IA)
    ├─ _get_or_create_channel()      → canales
    ├─ _get_or_create_customer()     → clientes
    ├─ INSERT ventas
    ├─ catalog = SELECT todos los Producto (una sola vez)
    ├─ _create_sale_items() por item:
    │   └─ usa item.sku si ya viene resuelto; si no → _match_sku() F1-score (umbral 60%)
    ├─ INSERT venta_items
    ├─ INSERT pagos
    ├─ INSERT envios (si aplica)
    ├─ INSERT rappi_detalles (si aplica)
    └─ _deduct_stock()
         ├─ Si SKU es combo → descuenta de cada componente
         │   └─ Si componente queda negativo → INSERT alertas_pedido
         └─ Si SKU es producto normal → descuenta directo
    │
    ▼
session.commit()  (todo en una sola transacción)
```

---

## 5. Flujo de una compra

```
Texto del proveedor
    │
    ▼
purchase_parser.parse_purchase()   GPT-4o-mini → ParsedPurchase
    │
    ▼
data_editor en Streamlit
(usuario ajusta SKU, cantidad, costo antes de confirmar)
    │
    ▼ [Confirmar e Ingresar a Inventario]
    │
guardar_compra.save_purchase()
    ├─ INSERT compras
    ├─ Por cada fila con SKU válido:
    │   ├─ INSERT detalle_compras
    │   └─ UPDATE productos SET stock_actual = stock_actual + cantidad
    └─ session.commit()
```

---

## 6. Flujo de edición de compra (ventana 24 h)

```
Historial de Compras → sección "Registros editables (últimas 24 h)"
    │
    ▼ [✏️ Editar] en la fila
    │
st.session_state["ep_editing_id"] = compra_id
st.session_state["ep_detalle_edit"] = get_purchase_detail(engine, compra_id)
    │
    ▼
_render_purchase_edit_form() muestra:
    ├─ Campo proveedor (text_input)
    ├─ data_editor con ítems actuales (Producto, SKU selectbox, Cantidad, Costo)
    └─ Preview total en tiempo real
    │
    ▼ [💾 Guardar cambios]
    │
update_purchase_items() — una sola transacción:
    ├─ 1. Revertir stock de ítems anteriores (column expr: stock_actual - cantidad_old)
    ├─ 2. DELETE detalle_compras WHERE compra_id = X
    ├─ 3. INSERT nuevos detalle_compras + stock_actual + cantidad_new (column expr)
    └─ 4. UPDATE compras (proveedor, monto_total recalculado)
    │
    ▼
Invalidar caches + st.rerun()
```

> **Nota importante**: La edición de ventas NO ajusta el stock. Solo corrige ítems, precios, estado y notas. Si una venta se registró con el SKU incorrecto y ya descontó stock, la corrección de inventario debe hacerse mediante una compra o ajuste directo en DB.

---

## 7. Lógica de combos

- Los combos son productos normales en el catálogo (tienen SKU propio, ej: `1089`).
- Su `stock_actual` se deja **siempre en 0** — no se llena manualmente.
- La tabla `combo_componentes` define qué productos individuales componen cada combo.
- **Stock virtual** = `min(floor(componente.stock_actual / qty_por_combo))` — lo muestra el tab "Combos" en Inventario.
- Al vender un combo, `_deduct_stock()` descuenta de los componentes, no del combo.
- Si un componente queda negativo → `alertas_pedido` para seguimiento de reposición.
- Para registrar combos en la DB: `python scripts/setup_combos.py`.

---

## 8. SKU matching (F1-score)

`_match_sku()` en `guardar_venta.py`:

1. Tokeniza el nombre raw del mensaje (separa dígitos/letras, stemming básico `s` final).
2. Para cada producto del catálogo calcula F1 entre keywords del mensaje y tokens del nombre.
3. Umbral mínimo de recall: 60%. Devuelve el mejor SKU o `None`.
4. Si el producto ya trae `SaleItemData.sku` (asignado en el editor de la UI), se usa directamente y se omite el matching. Esto permite que el usuario corrija el SKU antes de guardar.
5. Stock negativo en productos normales es **intencional**: indica venta sin stock previo.

**Causas conocidas de error en el matching:**
- **Falsos positivos**: combos con texto ambiguo hacen que el modelo incluya productos no pedidos.
- **Variantes no diferenciadas**: si el texto ingresado no especifica el sabor/variante (ej: "Creatina Creasmart 550g" sin "Sin sabor"), el modelo elige la variante más similar que no necesariamente es la correcta. La raíz es la falta de aliases diferenciados por variante en el catálogo.
- **Marcas compuestas tokenizadas distinto**: "bi pro" (dos tokens) no hace match con "bipro" (un token en el catálogo). Solución: agregar alias `bi pro sachet, bi pro saschet` al producto vía la página Catálogo / Aliases.
- **Abreviaturas de marca**: nombres como "creatina in 60 serv" donde "IN" es la abreviatura de la marca pueden no matchear si el producto no está en el catálogo o no tiene el alias correcto.

> **Flujo de corrección recomendado:** si el matching falla, corregir el SKU en el `data_editor` antes de confirmar la venta/compra. Para que el sistema aprenda, agregar el nombre alternativo como alias en la página **Catálogo / Aliases**.

> **Campo `alias`:** además del `nombre`, `_match_sku()` revisa un campo `alias` (comma-separated) por producto. Requiere `ALTER TABLE productos ADD COLUMN IF NOT EXISTS alias TEXT;` en la DB si no se hizo aún.

---

## 9. Base de datos — tablas principales

| Tabla | Descripción |
|---|---|
| `productos` | Catálogo de productos (sku, nombre, marca, categoria, stock_actual, rappi_product_id) |
| `canales` | WhatsApp / Rappi / Rappi Pro / Local / TikTok Live / Instagram |
| `clientes` | Compradores (cedula como deduplicador) |
| `ventas` | Cabecera de venta (canal, cliente, totales, estado, mensaje_original, json_extraido) |
| `venta_items` | Líneas (sku nullable, nombre_raw, qty, precio_unitario, subtotal) |
| `pagos` | Método de pago por venta |
| `envios` | Dirección de despacho (si aplica) |
| `rappi_detalles` | order_id, tipo, comisión % y monto (solo ventas Rappi) |
| `combo_componentes` | (combo_sku, componente_sku, cantidad) — unicidad por par |
| `alertas_pedido` | Componentes de combos vendidos sin stock; campo `resuelta` para seguimiento |
| `compras` | Cabecera de compra a proveedor |
| `detalle_compras` | Líneas de compra (sku nullable, nombre_raw, qty, costo_unitario) |

---

## 10. Páginas de la app

| Página | Ruta `current_page` | Descripción |
|---|---|---|
| Nueva Venta | `nueva_venta` | Textarea → parsear → **formulario editable** (canal, cliente, ítems+SKU, pago, notas) → confirmar |
| Dashboard | `dashboard` | KPIs, tendencia, donut canal, top 5 productos (cards), últimas ventas, dinero por cuenta, visor de venta completa |
| Inventario | `inventario` | Tabs: Catálogo / Alertas stock (negativos) / Combos / Hot Products |
| Compras | `compras` | Tabs: Nueva Compra (con data_editor revisable) / Historial (con visor de detalle + edición inline últimas 24h) |
| Ventas | `ventas` | Historial filtrable + visor de detalle por ID + edición inline (últimas 24h, sin ajuste de stock) |
| Catálogo / Aliases | `catalogo` | Lista de productos con campo alias editable para mejorar el SKU matching |

---

## 11. Variables de entorno

```
DATABASE_URL=postgresql://...     # Conexión Supabase (pooler en modo transaction)
OPENAI_API_KEY=sk-...             # Para motor_ia y purchase_parser
APP_PASSWORD=...                  # Contraseña de acceso a la app

# Opcionales — para personalizar el tema visual
THEME_PRIMARY=#314457
THEME_PRIMARY_DARK=#243344
THEME_PRIMARY_TEXT=#ffffff
THEME_SECONDARY=#1a1a1a
THEME_CANVAS=#edeae3

# Para sincronización Rappi (rama rappisync)
RAPPI_CLIENT_ID=...
RAPPI_CLIENT_SECRET=...
RAPPI_STORE_ID=900283093
```

En Streamlit Cloud se configuran en **Settings → Secrets** (formato TOML).

---

## 12. Estado actual (2026-05-06)

### ✅ Rama `main` — en producción
- Login con contraseña
- Registro de ventas (todos los canales), descuento de stock automático
- Cálculo de comisiones Rappi
- Compras de proveedor con parser IA + data_editor revisable
- Stock sumado al confirmar compra
- Dashboard: KPIs del período, tendencia ventas/compras, donut canal, top 5 productos (barras solucionadas), dinero por cuenta
- Inventario: alertas stock negativo, combos con stock virtual
- Sistema de estilos Poppins + tema marrón/canvas configurable
- Gestión de aliases por producto (página Catálogo / Aliases)

### 🔀 Rama `opt-sale-edit-and-fixes` (lista para merge)
Implementada sobre `main`. Commits:

1. **`6330db4`** — Editor de ítems en nueva venta + canal Página Web + fixes matching:
   - **Nueva Venta editable**: la columna derecha reemplaza la previsualización estática por un formulario completamente editable antes de confirmar: selectbox de canal, campos de cliente, `data_editor` de ítems con SKU pre-sugerido, selectbox de pago, notas editables, totales en tiempo real.
   - **Canal "Página Web"**: añadido a `SYSTEM_PROMPT` de `motor_ia.py`, a `CANAL_COLORS` y al selectbox de canales.
   - **Fix matching 3a/3b**: `motor_ia.py` y `purchase_parser.py` tienen regla explícita de no expandir abreviaturas ni añadir palabras ausentes en el nombre del producto. `_create_sale_items()` usa `item_data.sku` si ya viene pre-asignado del editor (evita re-matching).
   - `SaleItemData` tiene nuevo campo opcional `sku: Optional[str] = None` — lo asigna el editor de la UI, nunca el LLM.
   - `sale_parse_v` en session_state: contador que se incrementa en cada parseo, garantiza que el `data_editor` se resetea al parsear una nueva venta.

2. **`ea24b8b`** — Robustez data_editor contra None/NaN/pd.NA:
   - Extractor de filas envuelve `nombre` y `SKU` en `try/except` con `isna()` explícito.
   - Filas fantasma del `data_editor` (celdas `pandas.NA`) se filtran sin lanzar `TypeError`.

### 🔀 Rama `rappisync` (en main a través de merges anteriores)
Sincronización automática de disponibilidad con Rappi. Ver sección 13.

### 🔀 Rama `CombosManage` (pendiente de merge)
- Mejora de `_match_sku`: también busca en campo `alias` por producto (ya implementado en main vía commits anteriores).
- Requiere migración si no se ha corrido: `ALTER TABLE productos ADD COLUMN IF NOT EXISTS alias TEXT;`

### 🔀 Rama `updates` (pendiente de merge)
Mejoras de UI y visor de venta completa. Validar antes de mergear.

---

## 13. Funcionalidades de Rappi Sync (`rappisync`)

1. **`models/producto.py`:** columna `rappi_product_id` (String, nullable).
2. **`models/rappi_detalle.py`:** `UniqueConstraint` sobre `order_id` — previene doble descuento.
3. **`api/rappi_client.py`:**
   - `sync_after_sale(sku, rappi_product_id, new_stock)` → apaga si stock ≤ 0.
   - `sync_after_purchase(sku, rappi_product_id, new_stock)` → enciende si stock > 0.
4. **`DuplicateRappiOrderError`:** se lanza si el `order_id` ya existe; la UI muestra aviso.

**Migración de DB necesaria:**
```sql
ALTER TABLE productos ADD COLUMN IF NOT EXISTS rappi_product_id VARCHAR(30);
ALTER TABLE rappi_detalles ADD CONSTRAINT uq_rappi_detalles_order_id UNIQUE (order_id);
```

---

## 14. Deploy

- **URL producción:** Streamlit Community Cloud (cuenta Or0911)
- **Repo GitHub:** `Or0911/Colsport-Inventory` rama `main`
- Streamlit Cloud detecta nuevos commits y redespliega automáticamente (~1-3 min).
- Si no redespliega: dashboard en `share.streamlit.io` → menú ⋮ → **Reboot app**.
- **Python:** 3.10 (mínimo requerido por el proyecto).

---

## 15. Operaciones de mantenimiento

### Agregar un producto al catálogo
```sql
INSERT INTO productos (sku, nombre, peso, marca, categoria, stock_actual)
VALUES ('1999', 'Nombre del Producto', '1kg', 'Marca', 'Categoria', 0);
```

### Agregar alias para mejorar el matching (tras merge de CombosManage)
```sql
UPDATE productos SET alias = 'Alias1, Alias2, Alias3' WHERE sku = 'XXXX';
```

### Corrección manual de stock por error de SKU en compra
Usar la **edición inline de compras** (historial → ✏️ Editar). Solo disponible dentro de las 24h posteriores al registro. Después de ese plazo, usar SQL directo:
```sql
UPDATE productos SET stock_actual = stock_actual - 6 WHERE sku = '2030'; -- revertir
UPDATE productos SET stock_actual = stock_actual + 6 WHERE sku = '2045'; -- aplicar correcto
UPDATE detalle_compras SET producto_sku = '2045' WHERE compra_id = X AND producto_sku = '2030';
```

### Borrar la última compra (duplicado)
```sql
DO $$
DECLARE ultima_id INTEGER;
BEGIN
  SELECT MAX(id) INTO ultima_id FROM compras;
  UPDATE productos p SET stock_actual = p.stock_actual - dc.cantidad
  FROM detalle_compras dc WHERE dc.compra_id = ultima_id AND dc.producto_sku = p.sku;
  DELETE FROM detalle_compras WHERE compra_id = ultima_id;
  DELETE FROM compras WHERE id = ultima_id;
END $$;
```

### Resetear datos transaccionales (desarrollo)
```bash
python scripts/reset_data.py   # pide escribir "RESET" para confirmar
```

---

## 16. Roadmap (próximos pasos)

### Prioridad alta
- **Merge `opt-sale-edit-and-fixes` → `main`**: rama lista con editor de venta, canal Página Web y fixes de matching.
- **Enriquecer aliases del catálogo**: agregar nombres alternativos a productos cuyo matching falla (ej: `bi pro sachet, bi pro saschet` para el sachet de BiPro; variantes por sabor como `creatina creasmart vainilla`). Es la acción más efectiva para reducir errores de matching.

### Prioridad media
- **Ajuste manual de stock desde la app**: página o modal para `stock_actual += X` sin necesidad de crear una compra completa. Útil para correcciones de inventario físico.
- **Pipeline de evaluación del modelo de matching**: loguear en una tabla `sku_match_log(fecha, texto_ingresado, sku_propuesto, sku_confirmado)`. Con 30-50 correcciones se puede calcular precisión/recall por categoría de producto.
- **Rappi webhook/polling**: importar órdenes automáticamente sin copiar/pegar.
- **Exportación Excel/CSV** desde historial de ventas y compras.

### Prioridad baja
- **Multi-usuario**: roles admin/vendedor con sesiones separadas.
- **Resumen de cierre diario**: vista rápida para fin del día.
- **Fotos de productos**: campo `imagen_url` en catálogo.

---

## 17. Decisiones de diseño importantes

| Decisión | Razón |
|---|---|
| IA solo extrae, no calcula | Evitar errores aritméticos del modelo; Python hace todos los cálculos |
| Stock negativo permitido | Refleja la realidad: se vende y luego se consigue; las alertas hacen el seguimiento |
| Combo `stock_actual = 0` siempre | El stock virtual se calcula en tiempo real desde los componentes |
| Una sola transacción por venta/compra/edición | Si algo falla, nada queda a medias en la DB |
| Edición de compras ajusta stock; edición de ventas NO | Compra = entrada física (reversible y mensurable); venta = ya salió del local (ajuste ambiguo) |
| Column expressions en UPDATE de stock | `values(stock_actual=Producto.stock_actual ± cantidad)` evita el riesgo de ORM staleness cuando el mismo SKU aparece en múltiples filas de una edición |
| Ventana de 24h para edición | Limita el impacto de correcciones retroactivas; errores evidentes se corrigen el mismo día |
| Widget keys incluyen ID del registro | Evita conflictos en session_state cuando múltiples formularios de edición comparten la página |
| Logo en login como base64 en HTML | `st.image()` dentro de una columna no permite anidarse dentro de un div HTML; la alternativa es embeber la imagen en el propio bloque HTML |
| CSS sidebar sin pointer-events | El header de Streamlit está encima del contenido (no sobre él) por el padding-top del layout; NO es necesario `pointer-events: none`. Se aplica solo estilo visual transparente + `opacity/visibility/display: flex` explícitos en el botón de expandir para asegurar visibilidad |
| Nombres de campos Pydantic en español | Los JSON keys deben coincidir con lo que el LLM retorna; cambiarlos rompería el prompt |
| `st.stop()` no va dentro de `try/except` | En Streamlit, `StopException` hereda de `BaseException`; un `except Exception` genérico puede capturarlo y silenciarlo |
| `cs-card` no debe envolver widgets nativos | `st.markdown('<div class="cs-card">', ...)` seguido de widgets nativos de Streamlit genera una barra visual vacía: el div HTML y los widgets son nodos DOM hermanos, no padre/hijo |
| `.pyc` no deben commitearse | El proyecto tuvo un bug por `.pyc` de una rama en otra. `.gitignore` cubre `__pycache__/`, `**/__pycache__/`, `*.pyc`, `*.pyo`. Los archivos ya trackeados se eliminaron del índice con `git rm -r --cached` |
| `SaleItemData.sku` es asignado por la UI, nunca por el LLM | El LLM extrae `producto_nombre_raw`; el SKU se resuelve por F1-score o selección manual en el editor. Al viajar en el mismo objeto Pydantic, `_create_sale_items` puede saltarse el re-matching sin cambiar la firma de `save_sale` |
| `sale_parse_v` para resetear el data_editor de nueva venta | El `data_editor` de Streamlit mantiene estado por `key`. Usar un contador que se incrementa con cada parseo garantiza que el editor se inicializa con los ítems nuevos sin depender de `sale_msg_v` (que controla el textarea) |
| data_editor: extractor de filas con doble guard (isna + try/except) | `pandas.NA` en celdas vacías lanza `TypeError` en `pd.NA or ""`. El extractor usa `isna()` explícito antes de `str()` y envuelve en `try/except (TypeError, ValueError)` para tolerar cualquier tipo devuelto por Streamlit |
