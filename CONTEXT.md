# Colsports — Archivo de Contexto del Proyecto

> Actualizado el 2026-05-01.

---

## 1. ¿Qué es este proyecto?

**Colsports** es un negocio colombiano de suplementos deportivos e implementos fitness (mancuernas, barras, discos, bandas de resistencia, proteínas, creatinas, etc.). Vende principalmente por WhatsApp, Rappi, Rappi Pro, TikTok Live, Instagram y canal Local.

Este repositorio es el **sistema interno de ventas e inventario** de Colsports: una aplicación web privada (acceso por contraseña) que permite:

- Registrar ventas copiando y pegando el mensaje de WhatsApp/Rappi → la IA extrae los datos automáticamente.
- Registrar compras a proveedores del mismo modo → actualiza el stock.
- Ver el inventario, alertas de stock bajo/negativo, y stock virtual de combos.
- Ver un dashboard con KPIs, tendencia de ventas, distribución por canal y top de productos.

---

## 2. Stack tecnológico

| Capa | Tecnología |
|---|---|
| UI | Streamlit (Python) |
| Base de datos | PostgreSQL en Supabase |
| ORM | SQLAlchemy 2.x (mapped columns, typed) |
| IA extracción | OpenAI GPT-4o-mini (JSON mode, temperature=0) |
| Validación | Pydantic v2 |
| Deploy | Streamlit Community Cloud |
| Fuente tipográfica | Google Fonts — Poppins (sans-serif) |
| Assets estáticos | `assets/logo.png` (logo Colsports, con fallback a texto si no existe) |
| Estilos | CSS custom con variables `--cs-*` inyectadas desde dict `THEME` |

---

## 3. Arquitectura de archivos

```
col-inventory-app/
├── app/
│   ├── streamlit_app.py     ← Interfaz principal (login, sidebar, 4 páginas)
│   ├── db_queries.py        ← Todas las queries de lectura (@st.cache_data)
│   └── charts.py            ← Gráficos Plotly (tendencia, canal, top productos)
│
├── api/
│   ├── motor_ia.py          ← Parsea mensaje WhatsApp → ParsedSale (OpenAI)
│   ├── guardar_venta.py     ← Persiste ParsedSale en DB + descuenta stock
│   ├── purchase_parser.py   ← Parsea texto proveedor → ParsedPurchase (OpenAI)
│   └── guardar_compra.py    ← Persiste compra en DB + suma stock
│
├── models/
│   ├── __init__.py          ← Exporta todos los modelos
│   ├── base.py              ← DeclarativeBase de SQLAlchemy
│   ├── producto.py          ← Producto (sku PK, nombre, marca, categoria, stock_actual)
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
│   └── consolidate_and_import.py ← Importación masiva histórica (legacy)
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
    ├─ _match_sku() por item         F1-score nombre vs catálogo
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

## 6. Lógica de combos

- Los combos son productos normales en el catálogo (tienen SKU propio, ej: `1089`).
- Su `stock_actual` se deja **siempre en 0** — no se llena manualmente.
- La tabla `combo_componentes` define qué productos individuales componen cada combo.
- **Stock virtual** = `min(floor(componente.stock_actual / qty_por_combo))` — lo muestra el tab "Combos" en Inventario.
- Al vender un combo, `_deduct_stock()` descuenta de los componentes, no del combo.
- Si un componente queda negativo → `alertas_pedido` para seguimiento de reposición.
- Para registrar combos en la DB: `python scripts/setup_combos.py`.

---

## 7. SKU matching (F1-score)

`_match_sku()` en `guardar_venta.py`:

1. Tokeniza el nombre raw del mensaje (separa dígitos/letras, stemming básico `s` final).
2. Para cada producto del catálogo calcula F1 entre keywords del mensaje y tokens del nombre.
3. Umbral mínimo de recall: 60%. Devuelve el mejor SKU o `None`.
4. Stock negativo en productos normales es **intencional**: indica venta sin stock previo.

> La rama `CombosManage` tiene una mejora: además del `nombre`, revisa un campo `alias` (comma-separated) por producto para catchear nombres alternativos. Requiere `ALTER TABLE productos ADD COLUMN IF NOT EXISTS alias TEXT;` en la DB antes de activar.

---

## 8. Base de datos — tablas principales

| Tabla | Descripción |
|---|---|
| `productos` | Catálogo de productos (sku, nombre, marca, categoria, stock_actual) |
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

## 9. Páginas de la app

| Página | Ruta `current_page` | Descripción |
|---|---|---|
| Nueva Venta | `nueva_venta` | Textarea → parsear → previsualizar → confirmar |
| Dashboard | `dashboard` | KPIs, tendencia, donut canal, top 10 productos, últimas ventas, dinero por cuenta, visor de venta completa |
| Inventario | `inventario` | Tabs: Catálogo / Alertas stock / Combos / Hot Products |
| Compras | `compras` | Tabs: Nueva Compra / Historial |
| Ventas | `ventas` | Tabs: Historial filtrable / Editar venta (estado + notas) |

---

## 10. Variables de entorno

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
```

En Streamlit Cloud se configuran en **Settings → Secrets** (formato TOML).

---

## 11. Estado actual (2026-05-02)

### ✅ Funcionando en producción (main)
- Login con contraseña
- Registro de ventas por todos los canales (WhatsApp, Rappi, Rappi Pro, Local, TikTok Live, Instagram)
- Cálculo de comisiones Rappi automático
- Stock se descuenta al guardar venta
- Compras de proveedor con data_editor editable
- Stock se suma al guardar compra
- Dashboard con KPIs del mes/hoy, tendencia, canal, top productos
- Inventario con alertas de stock negativo y bajo (slider)
- Combos: stock virtual, alertas de componentes faltantes, marcar como resuelta
- Sistema de estilos con fuente Caveat y tema marrón/canvas configurable por env vars

### 🔀 Rama `updates` (en testing — no mergear hasta validar)
Último commit: `97bc14e`. Diez mejoras implementadas en dos rondas:

1. **Mostrador de venta completa (Dashboard):** sección "🔍 Ver venta completa" debajo de Últimas Ventas. Se ingresa un ID y se despliega el detalle completo: canal, cliente (nombre, CC, teléfono), items con SKU y precios, totales, método de pago + cuenta destino, envío, info Rappi, mensaje original.

2. **Manejo de None en compras:** antes de persistir, el DataFrame del `data_editor` se limpia:
   - Columna SKU: `None`/`NaN` → `""` (sin SKU asignado), no bloquea el guardado.
   - Se descartan filas sin `producto_nombre_raw` o con nombre vacío.
   - Se descartan filas con `cantidad` nula, no numérica o ≤ 0.
   - Si no queda ninguna fila válida, muestra aviso en lugar de intentar guardar.

3. **Página Ventas (auditador/corrector):** nueva ruta `ventas` en el sidebar.
   - Tab "Historial": lista filtrable por rango de fechas, estado y canal; visor de detalle inline por ID.
   - Tab "Editar venta": busca por ID → venta actual colapsada como referencia → `data_editor` con productos (nombre libre, SKU selectbox, cantidad, precio unit.) → preview de total en tiempo real → estado y notas → guardar.
   - Al guardar: reemplaza `venta_items`, recalcula `subtotal` y `total` (conserva `costo_envio` + `descuento` originales), actualiza `estado` y `notas` en una sola transacción.
   - El stock **no se ajusta automáticamente** al editar items; el aviso aparece en la UI.

4. **Dinero por cuenta en Dashboard:** expander colapsable "💳 Dinero por cuenta / método de pago" que muestra, para el período seleccionado, el total acumulado por método + cuenta destino (Nequi, Bancolombia Colsports, etc.) con número de ventas.

5. **Editor de productos de venta:** el auditador permite editar los productos vendidos y sus precios directamente desde la app sin tocar la DB a mano.

**Ronda 2 — Rediseño visual (commit `97bc14e`):**

6. **Fuente: Caveat → Poppins:** toda la app usa ahora `Google Fonts — Poppins` (400/500/600/700). El import CSS fue reemplazado en el bloque `<style>` global.

7. **Logo en sidebar y login:** se carga `assets/logo.png` con `st.image(width=150/220)`. Si el archivo no existe, muestra el texto "COLSPORTS" con estilo inline como fallback. El archivo debe copiarse manualmente a `assets/logo.png` en el repo.

8. **Barra vacía eliminada:** los `st.markdown('<div class="cs-card">...</div>', unsafe_allow_html=True)` alrededor de widgets nativos de Streamlit creaban una barra visual vacía (~32 px) porque el div HTML y los widgets son nodos DOM hermanos, no padre/hijo. Se eliminaron todos los wrappers `cs-card` que rodeaban secciones con widgets nativos. También se ocultó la barra de header nativa de Streamlit con `[data-testid="stHeader"] { display: none !important; }`.

9. **KPIs del período filtrado:** los cuatro indicadores del Dashboard (Ventas, Inversión, Margen, Stock Negativo) ahora se calculan para el rango de fechas seleccionado con el filtro de período, no siempre para el mes en curso. Se creó `get_kpis_period(engine, start, end)` en `db_queries.py` que reemplaza a `get_kpis()` y `get_purchase_kpis()`.

10. **Alertas de stock solo negativo:** el tab "⚠️ Alertas" en Inventario ya no tiene slider "Stock bajo". Solo muestra productos con `stock_actual < 0`. La llamada usa `get_stock_alerts(engine, umbral=-1)`. El KPI "Stock Negativo" en el Dashboard también usa este mismo criterio.

Nuevas funciones en `db_queries.py`:
- `get_sale_detail(engine, sale_id)` → `dict` con todas las relaciones de una venta.
- `get_money_by_account(engine, start, end)` → `DataFrame` agrupado por método + cuenta.
- `get_all_sales(engine, start, end, estado, canal_nombre)` → `DataFrame` filtrable para el auditador.
- `update_sale(engine, sale_id, new_estado, new_notas)` → escribe directo, sin cache.
- `update_sale_items(engine, sale_id, items, new_estado, new_notas)` → reemplaza items, recalcula totales, actualiza estado/notas.
- `get_kpis_period(engine, start, end)` → `dict` con KPIs de ventas y compras para un rango de fechas arbitrario.

Nueva función helper en `streamlit_app.py`:
- `_render_sale_detail(detalle)` → renderiza el dict de detalle; compartido entre Dashboard y página Ventas.

### 🔀 Rama `CombosManage` (pendiente de merge)
- Mejora de `_match_sku`: también busca en campo `alias` (nombres alternativos) por producto.
- Requiere migración en DB: `ALTER TABLE productos ADD COLUMN IF NOT EXISTS alias TEXT;`
- Una vez corrida la migración, hacer merge a main.

### 🌿 Otras ramas (históricas, no mergear)
- `Version1`, `MVP-visualization-refinement`, `Promt_Refinement`, `update_inventory`, `app` — estados anteriores del proyecto.

---

## 12. Deploy

- **URL producción:** Streamlit Community Cloud (cuenta Or0911)
- **Repo GitHub:** `Or0911/Colsport-Inventory` rama `main`
- Streamlit Cloud detecta nuevos commits y redespliega automáticamente (~1-3 min).
- Si no redespliega: dashboard en `share.streamlit.io` → menú ⋮ → **Reboot app**.
- **Python:** 3.10 (mínimo requerido por el proyecto).

---

## 13. Operaciones de mantenimiento

### Agregar un producto al catálogo
```sql
INSERT INTO productos (sku, nombre, peso, marca, categoria, stock_actual)
VALUES ('1999', 'Nombre del Producto', '1kg', 'Marca', 'Categoria', 0);
```

### Agregar un combo
1. Agregar el combo como producto normal con `stock_actual = 0`.
2. Agregar sus componentes en `combo_componentes`:
```sql
INSERT INTO combo_componentes (combo_sku, componente_sku, cantidad)
VALUES ('SKU_COMBO', 'SKU_COMPONENTE', cantidad_por_unidad);
```
O editar `scripts/setup_combos.py` y volver a correrlo (es idempotente).

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

## 14. Roadmap (próximas funcionalidades)

### Prioridad alta
- **Merge `updates` → main** una vez validado en testing.
- **Merge CombosManage → main** + migración `alias` en DB.
- **Resumen de ventas del día:** vista rápida para cierre diario.

### Prioridad media
- **Sincronización Rappi:** webhook o polling a la API de Rappi para importar órdenes automáticamente sin copiar/pegar.
- **WhatsApp Business API:** recibir mensajes directamente vía webhook, parsear y registrar sin abrir la app.
- **Exportación a Excel/CSV:** desde el historial de ventas y compras.

### Prioridad baja / ideas
- **Multi-usuario:** roles (admin, vendedor) con sesiones separadas.
- **Fotos de productos:** campo `imagen_url` en catálogo, mostrar en inventario.
- **Integración contable:** exportar resumen mensual a formato compatible con Siigo u otro.

---

## 15. Decisiones de diseño importantes

| Decisión | Razón |
|---|---|
| IA solo extrae, no calcula | Evitar errores aritméticos del modelo; Python hace todos los cálculos |
| Stock negativo permitido | Refleja la realidad: se vende y luego se consigue; las alertas hacen el seguimiento |
| Combo `stock_actual = 0` siempre | El stock virtual se calcula en tiempo real desde los componentes |
| Una sola transacción por venta/compra | Si algo falla, nada queda a medias en la DB |
| Nombres de campos Pydantic en español | Los JSON keys deben coincidir con lo que el LLM retorna; cambiarlos rompería el prompt |
| Aliases backward-compatible en todos los módulos | Permite renombrar funciones sin romper código existente o tests |
| `.pyc` no deben commitearse | El proyecto tuvo un bug por `.pyc` de una rama en otra; agregar `__pycache__/` al `.gitignore` si no está |
| `st.stop()` no va dentro de `try/except` | En Streamlit, `StopException` hereda de `BaseException`; un `except Exception` genérico puede capturarlo y silenciarlo. Usar bloque `else` en su lugar. |
| Limpieza del `data_editor` antes de persistir | El widget puede generar filas vacías si el usuario desplaza horizontalmente y toca campos vacíos. Siempre filtrar `NaN`, strings vacíos y cantidades ≤ 0 antes de llamar a `save_purchase`. |
| `cs-card` no debe envolver widgets nativos | `st.markdown('<div class="cs-card">', ...)` seguido de widgets nativos de Streamlit genera una barra visual vacía: el div HTML y los widgets son nodos DOM hermanos, no padre/hijo. Usar solo para contenido HTML puro, o eliminar el wrapper y aplicar estilos directamente a los widgets. |
