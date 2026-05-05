# Colsports — Archivo de Contexto del Proyecto

> Actualizado el 2026-05-05.

---

## 1. ¿Qué es este proyecto?

**Colsports** es un negocio colombiano de suplementos deportivos e implementos fitness (mancuernas, barras, discos, bandas de resistencia, proteínas, creatinas, etc.). Vende principalmente por WhatsApp, Rappi, Rappi Pro, TikTok Live, Instagram y canal Local.

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
Mensaje WhatsApp
    │
    ▼
motor_ia.parse_sale_message()
    ├─ normalize_sale_text()         limpia espacios/saltos
    ├─ GPT-4o-mini (JSON mode)       extrae campos → ParsedSale
    └─ ParsedSale validado con Pydantic
    │
    ▼
Previsualización en Streamlit
(el usuario revisa canal, cliente, items, montos, pago)
    │
    ▼ [Confirmar y Guardar]
    │
guardar_venta.save_sale()
    ├─ calculate_amounts()           subtotal/total/comisión en Python (no IA)
    ├─ _get_or_create_channel()      → canales
    ├─ _get_or_create_customer()     → clientes
    ├─ INSERT ventas
    ├─ catalog = SELECT todos los Producto (una sola vez)
    ├─ _match_sku() por item         F1-score nombre vs catálogo (umbral recall 60%)
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
4. Stock negativo en productos normales es **intencional**: indica venta sin stock previo.

**Causas conocidas de error en el matching:**
- **Falsos positivos**: combos con texto ambiguo hacen que el modelo incluya productos no pedidos.
- **Variantes no diferenciadas**: si el texto ingresado no especifica el sabor/variante (ej: "Creatina Creasmart 550g" sin "Sin sabor"), el modelo elige la variante más similar que no necesariamente es la correcta. La raíz es la falta de aliases diferenciados por variante en el catálogo.
- **Sin alias**: la rama `CombosManage` agrega el campo `alias` por producto. Hasta que se mergee, el matching solo compara contra `nombre`.

> La rama `CombosManage` tiene una mejora: además del `nombre`, revisa un campo `alias` (comma-separated) por producto para catchear nombres alternativos. Requiere `ALTER TABLE productos ADD COLUMN IF NOT EXISTS alias TEXT;` en la DB antes de activar.

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
| Nueva Venta | `nueva_venta` | Textarea → parsear → previsualizar → confirmar |
| Dashboard | `dashboard` | KPIs, tendencia, donut canal, top 5 productos (cards), últimas ventas, dinero por cuenta, visor de venta completa |
| Inventario | `inventario` | Tabs: Catálogo / Alertas stock (negativos) / Combos / Hot Products |
| Compras | `compras` | Tabs: Nueva Compra / Historial (con visor de detalle + edición inline últimas 24h) |
| Ventas | `ventas` | Historial filtrable + visor de detalle por ID + edición inline (últimas 24h, sin ajuste de stock) |

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

## 12. Estado actual (2026-05-05)

### ✅ Rama `main` — en producción
- Login con contraseña
- Registro de ventas (todos los canales), descuento de stock automático
- Cálculo de comisiones Rappi
- Compras de proveedor con parser IA + data_editor revisable
- Stock sumado al confirmar compra
- Dashboard: KPIs del período, tendencia ventas/compras, donut canal, top 5 productos (barras solucionadas), dinero por cuenta
- Inventario: alertas stock negativo, combos con stock virtual
- Sistema de estilos Poppins + tema marrón/canvas configurable

### 🔀 Rama `purchase-edit-and-fixes` (lista para merge)
Implementada sobre `rappisync`. Commits principales:

1. **`eafe4ed`** — Edición de compras con ajuste de stock:
   - `update_purchase_items()` en `db_queries.py`: revierte stock anterior, aplica nuevo, todo atómico con column expressions.
   - `get_purchase_detail()`: carga ítems con nombre de catálogo.
   - `get_all_sales()`: agrega columna `fecha_dt` (timestamp crudo) para filtro de ventana.
   - `get_recent_purchases()`: agrega columna `fecha_dt`.
   - `update_sale_items()`: reemplaza ítems de venta, recalcula totales, actualiza estado/notas. **No ajusta stock** (por diseño).
   - Fix en `get_top_products`: GROUP BY solo (sku, nombre) → barras del chart ya no fragmentadas.
   - Fix CSS sidebar: header transparente, botón expand con color primario.

2. **`d828108`** — Ventana de edición de 24 horas:
   - Constante `EDIT_WINDOW_HOURS = 24`.
   - Helper `_is_editable(fecha)`.
   - `fecha_dt` añadido a ambas queries para comparación en pandas.

3. **`dd79e6e`** — Edición inline en el historial:
   - Eliminados tabs separados "Editar venta" y "Editar compra".
   - Sección "Registros editables (últimas 24h)" al final del historial de cada página.
   - Botón "✏️ Editar" por registro (toggle — un solo formulario abierto a la vez).
   - Helpers `_render_purchase_edit_form()` y `_render_sale_edit_form()`.
   - Widget keys incluyen el ID del registro para evitar conflictos entre formularios.

4. **Commits adicionales** — Correcciones CSS sidebar y logo login:
   - `pointer-events: none` en el header para no bloquear clicks en el contenido principal; `pointer-events: all` solo en el botón de toggle.
   - Texto de keyboard shortcut de Streamlit 1.35+ oculto con `[data-testid="stSidebarCollapseButton"] p, span { display: none }`.
   - Logo en la tarjeta de login embebido como base64 en el bloque HTML — elimina el cuadro vacío que aparecía sobre "Bienvenido".

### 🔀 Rama `rappisync` (base de `purchase-edit-and-fixes`)
Sincronización automática de disponibilidad con Rappi. Ver sección 13.

### 🔀 Rama `CombosManage` (pendiente de merge)
- Mejora de `_match_sku`: también busca en campo `alias` por producto.
- Requiere migración: `ALTER TABLE productos ADD COLUMN IF NOT EXISTS alias TEXT;`

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
- **Merge `purchase-edit-and-fixes` → `rappisync` → `main`**: rama lista.
- **Merge `CombosManage` → main** + migración `alias` en DB: habilita distinción de variantes.
- **Enriquecer aliases del catálogo**: agregar sabor/variante a los aliases de productos con múltiples variantes (ej: SKU 2030 vs 2045 para Creatina Creasmart sin sabor vs vainilla). Previene el error de matching más frecuente.

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
| CSS sidebar con pointer-events | `pointer-events: none` en el header contenedor evita que bloquee clicks del contenido principal; se reactiva con `pointer-events: all` solo en el botón de toggle |
| Nombres de campos Pydantic en español | Los JSON keys deben coincidir con lo que el LLM retorna; cambiarlos rompería el prompt |
| `st.stop()` no va dentro de `try/except` | En Streamlit, `StopException` hereda de `BaseException`; un `except Exception` genérico puede capturarlo y silenciarlo |
| `cs-card` no debe envolver widgets nativos | `st.markdown('<div class="cs-card">', ...)` seguido de widgets nativos de Streamlit genera una barra visual vacía: el div HTML y los widgets son nodos DOM hermanos, no padre/hijo |
| `.pyc` no deben commitearse | El proyecto tuvo un bug por `.pyc` de una rama en otra; `__pycache__/` debe estar en `.gitignore` |
