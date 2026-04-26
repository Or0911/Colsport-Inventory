# Colsport Inventory — Design System

Derived from the RestoManage Pro wireframe language. The aesthetic is **pencil-on-paper**: warm off-white backgrounds, rough sketch borders, handwritten Caveat font, and dark sidebar. Every new screen or component must follow this guide.

---

## 1. Philosophy

- **Sketch aesthetic** — borders feel hand-drawn (roughness), not pixel-perfect
- **Warm neutrals** — parchment backgrounds, never cold grays or pure white
- **Dark anchors** — sidebar, headers, and primary buttons use near-black (`#1a1a1a`)
- **Subtle depth** — cards have a 3–4 px offset shadow in a darker warm tone, not CSS box-shadow
- **Sparse color** — accent colors only for status signals; everything else is neutral

---

## 2. Color Palette

### Backgrounds
| Name | Hex | Use |
|---|---|---|
| Canvas | `#edeae3` | Page/app background |
| Paper | `#faf8f4` | Card fill, default panel |
| Paper Light | `#fffef9` | Input fields, table cells |
| Paper Mid | `#f5f2eb` | Alternating table rows, section fills |
| Paper Dark | `#ece8e0` | Table header background, secondary button |

### Dark (Sidebar / Headers / Buttons)
| Name | Hex | Use |
|---|---|---|
| Ink Black | `#1a1a1a` | Primary button, sidebar, top bar |
| Ink Dark | `#1c1c1c` | Sidebar panel fill |
| Ink Mid | `#2a2a2a` | Dividers inside dark panels |
| Ink Light | `#3a3a3a` | Secondary dark button, icon borders |

### Text
| Name | Hex | Use |
|---|---|---|
| Text Primary | `#1a1a1a` | Headlines, KPI values, bold labels |
| Text Body | `#333` | Table cell content, card body |
| Text Secondary | `#555` | Card titles, section headers |
| Text Muted | `#777` | Form labels, sidebar inactive items |
| Text Faint | `#999` | KPI sub-labels, column headers |
| Text Placeholder | `#bbb` | Input placeholders, annotations |
| Text Ghost | `#ccc` | Disabled states, footnotes |

### Borders & Dividers
| Name | Hex | Use |
|---|---|---|
| Border Strong | `#ccc` | Card outlines, input fields |
| Border Mid | `#d4d0c8` | Panel separators |
| Border Soft | `#e0ddd8` | Internal dividers, row lines |
| Shadow Offset | `#e8e4dc` | Card drop shadow (offset rect) |
| Sidebar text | `#e0ddd8` | Active nav text, sidebar title |

### Accent / Status
| Name | Hex | Use |
|---|---|---|
| Green (positive) | `#5aaa88` | Positive delta, active toggle, "Listo" |
| Amber (warning) | `#aa8844` | Low stock, pending state |
| Blue (info) | `#4488aa` | In-progress state, info badges |
| Red (danger) | `#cc4444` | Overdue, out-of-stock, error |
| Alert Background | `#fff8f2` | Alert card fill |
| Alert Border | `#c89070` | Alert card outline |

### KDS Dark Mode (Kitchen / high-contrast screens only)
| Name | Hex |
|---|---|
| KDS Background | `#0e0e0e` |
| KDS Surface | `#141414` |
| KDS Dot Grid | `#1e1e1e` |
| KDS Pending | `#1e1208` / border `#996633` |
| KDS Cooking | `#081422` / border `#336688` |
| KDS Ready | `#081a10` / border `#3a9960` |

---

## 3. Typography

**Font:** [Caveat](https://fonts.google.com/specimen/Caveat) — import in Streamlit via `st.markdown` with a `<style>` block.

```css
@import url('https://fonts.googleapis.com/css2?family=Caveat:wght@400;500;600;700&display=swap');
```

| Role | Size | Weight | Color |
|---|---|---|---|
| Page title (top bar) | 22px | 700 | `#1a1a1a` |
| Card / panel title | 15px | 600 | `#555` |
| KPI value | 23px | 700 | `#1a1a1a` |
| KPI sub-label | 13px | 400 | `#aaa` |
| Table header | 12px | 600 | `#999` |
| Table cell | 13–14px | 400 | `#444` |
| Body / description | 14px | 400 | `#555` |
| Label / metadata | 13px | 400 | `#777` |
| Caption / footnote | 12px | 400 | `#bbb` |
| Primary button | 16–19px | 600–700 | `#f0ece4` |
| Secondary button | 15px | 400 | `#555` |
| Sidebar nav item | 15px | 400/600 | `#666` / `#ddd` |

---

## 4. Layout Patterns

### Shell
```
┌─────────────────────────────────────────────────────────┐
│  TOP BAR  bg:#fdfcf8  h:60px  border-bottom:#ddd8d0     │
│  [Page Title 22px bold]              [Date] [🔔] [⚙]   │
├──────────┬──────────────────────────────────────────────┤
│ SIDEBAR  │  CONTENT AREA                                │
│ w:224px  │  padding: 20px                               │
│ #1c1c1c  │  background: #edeae3 (dot grid)              │
│          │                                              │
│  Logo    │  ┌ KPI row ──────────────────────────────┐  │
│  Nav     │  │  4 cards × 25%  gap:12px  h:96px      │  │
│  ──────  │  └───────────────────────────────────────┘  │
│  User    │  ┌ Charts ─────────┐ ┌ Panel ──────────┐   │
└──────────┘  │  62% width      │ │  38% width      │   │
              └─────────────────┘ └─────────────────┘   │
              ┌ Data Table ───────────────────────────┐  │
              │  full width, alternating rows          │  │
              └────────────────────────────────────────┘  │
```

### Sidebar (224px, dark)
- Background: `#1c1c1c`
- Logo circle: `#272727`, 38px diameter
- Active nav item: `#2e2e2e` background pill, text `#ddd`, weight 600
- Inactive nav item: text `#666`
- Bottom divider + user avatar row
- Right border: 1px `#2a2a2a`

### Top Bar (60px, light)
- Background: `#fdfcf8`
- Bottom border: 1px `#ddd8d0`
- Left: page title (22px, 700, `#1a1a1a`)
- Right: date string + icon buttons

### Content Grid
- Outer padding: `20px` all sides
- KPI row: 4 equal columns, `12–13px` gap
- Charts row: `62% / 38%` split, `12px` gap
- Full-width tables below charts
- All panels use the Card pattern below

---

## 5. Components

### Card / Panel
Every content block uses a two-rect shadow technique:

```
Offset shadow rect:  x+3, y+4, same w/h  fill:#e8e4dc  stroke:none
Main card rect:      x,   y,   w,   h     fill:#fffef9  stroke:#d4d0c8  sw:1.5  roughness:1.0–1.2
```

In Streamlit CSS:
```css
.card {
  background: #fffef9;
  border: 1.5px solid #d4d0c8;
  border-radius: 2px;
  box-shadow: 3px 4px 0 #e8e4dc;
  padding: 16px 18px;
}
```

### KPI Card
```
┌─▌──────────────────────────────────┐
│  Label (13px #999)                 │
│                                    │
│  Value (23px 700 #1a1a1a)  ↑ badge │
│  Sub-label (13px #aaa)             │
└────────────────────────────────────┘
  ▌ = 4px left accent bar (#555 for primary, #ccc for others)
```
- Width: `(total - sidebar - padding) / 4`
- Height: `96px`
- Positive badge: `#5aaa88`

### Buttons

**Primary** (dark, action-confirming):
```css
background: #1a1a1a;
color: #f0ece4;
border: 2–2.5px solid #111;
font-size: 16–19px;
font-weight: 600–700;
padding: 12px 24px;
roughness: 1.0–1.1;
```

**Secondary** (light, alternative action):
```css
background: #f0ece4;
color: #555;
border: 1.5px solid #999;
font-size: 15px;
roughness: 1.2;
```

**Tertiary / Ghost** (low-priority action):
```css
background: #faf8f4;
color: #aaa;
border: 1px solid #ccc;
font-size: 15px;
roughness: 1.2;
```

**Danger** (destructive):
```css
background: #fff0ee;
color: #c08;
border: 1px solid #e0c0b8;
font-size: 12px;
```

### Input Field
```css
background: #fffef9;
border: 1.5px solid #ccc;
padding: 10px 14px;
font-size: 15px;
color: #333;
placeholder-color: #bbb;
roughness: 1.2;
```

### Data Table
| Element | Style |
|---|---|
| Header row | `background:#ece8e0`, 12px 600 `#999` |
| Even rows | `background:#fffef9` |
| Odd rows | `background:#f5f2eb` |
| Row divider | 1px `#eee` |
| Cell text | 13–14px `#444` |
| Section divider | 1px `#e0ddd8` roughness 0.5 |
| Pagination active | `#1c1c1c` bg, `#eee` text |
| Pagination inactive | `#fffef9` bg, `#888` text |

### Toggle (available/active states)
```
ON:  pill bg:#e4f5ee  border:#5aaa88  knob:#5aaa88  (knob right)
OFF: pill bg:#f0ece4  border:#ccc     knob:#ddd     (knob left)
```

### Status Badge (text only, colored)
| Status | Color |
|---|---|
| Confirmada / Pagada | `#5aaa88` |
| Pendiente | `#aaa` |
| En proceso / Cocina | `#aa8844` |
| Lista / Info | `#4488aa` |
| Cancelada / Error | `#cc4444` |

### Alert Card (low stock, restock)
```css
background: #fff8f2;
border: 1.5px solid #c89070;
padding: 8px 14px;
```
- Title: 14px 600 `#4a2a1a`
- Detail: 12px `#aa7055`
- Icon (`!`): 16px 700 `#c88`, in small rough box `#fff0e8`

### Form / Input Card
- Same card styling as panel
- Label above each input: 14px `#777`
- Input below: full width minus 32px padding
- Submit button spans full width at bottom

---

## 6. Spacing System

| Token | Value | Use |
|---|---|---|
| xs | 4px | Icon padding, tight gaps |
| sm | 8px | Between label and input |
| md | 12–13px | Gap between cards in a row |
| lg | 16–18px | Card internal padding |
| xl | 20px | Section padding, content margin |
| xxl | 32px | Between major sections |
| Row height (dense) | 28px | Table rows, sidebar nav items |
| Row height (normal) | 48px | Table rows with actions |
| Card height (KPI) | 96px | |
| Card height (charts) | 230px | |
| Top bar height | 60px | |
| Sidebar width | 224px | |
| Right detail panel | 256px | |

---

## 7. Applying in Streamlit

Inject the design system globally at the top of `streamlit_app.py`:

```python
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Caveat:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Caveat', cursive !important;
    background-color: #edeae3;
}

/* Cards */
.cs-card {
    background: #fffef9;
    border: 1.5px solid #d4d0c8;
    border-radius: 2px;
    box-shadow: 3px 4px 0 #e8e4dc;
    padding: 16px 18px;
    margin-bottom: 12px;
}

/* KPI value */
.cs-kpi-value {
    font-size: 23px;
    font-weight: 700;
    color: #1a1a1a;
}
.cs-kpi-label {
    font-size: 13px;
    color: #999;
}
.cs-kpi-sub {
    font-size: 13px;
    color: #aaa;
}

/* Section titles */
.cs-section-title {
    font-size: 15px;
    font-weight: 600;
    color: #555;
    margin-bottom: 8px;
}

/* Status colors */
.cs-green  { color: #5aaa88; }
.cs-amber  { color: #aa8844; }
.cs-blue   { color: #4488aa; }
.cs-red    { color: #cc4444; }
.cs-muted  { color: #aaa; }

/* Alert card */
.cs-alert {
    background: #fff8f2;
    border: 1.5px solid #c89070;
    border-radius: 2px;
    padding: 8px 14px;
    margin: 4px 0;
}

/* Primary button override */
.stButton > button[kind="primary"] {
    background-color: #1a1a1a;
    color: #f0ece4;
    border: 2px solid #111;
    font-family: 'Caveat', cursive;
    font-size: 16px;
    font-weight: 600;
}

/* Dataframe table */
.stDataFrame { background: #fffef9; }
</style>
""", unsafe_allow_html=True)
```

### Reusable helper snippets

**KPI Card:**
```python
def kpi_card(label: str, value: str, sub: str = "", delta_color: str = "") -> str:
    delta_style = f"color:{delta_color};" if delta_color else "color:#aaa;"
    return f"""
    <div class="cs-card" style="border-left:4px solid #555;">
        <div class="cs-kpi-label">{label}</div>
        <div class="cs-kpi-value">{value}</div>
        <div class="cs-kpi-sub" style="{delta_style}">{sub}</div>
    </div>
    """
```

**Alert Card:**
```python
def alert_card(title: str, detail: str) -> str:
    return f"""
    <div class="cs-alert">
        <strong style="font-size:14px;color:#4a2a1a;">{title}</strong><br>
        <span style="font-size:12px;color:#aa7055;">{detail}</span>
    </div>
    """
```

**Section title:**
```python
def section_title(text: str) -> None:
    st.markdown(f'<div class="cs-section-title">{text}</div>', unsafe_allow_html=True)
```

---

## 8. Screen Patterns

### New Sale / New Purchase (form screen)
```
TOP BAR: "Nueva Venta" | channel badge | date
─────────────────────────────────────────────
[  TEXT AREA — paste message          ]  card
[  AI PARSE BUTTON (primary, full w)  ]

─────────────────────────────────────────────
PARSED PREVIEW (shows after parse)
  ┌──────────────┐ ┌────────────────────────┐
  │ Customer info│ │ Line items table       │
  │ Channel      │ │ + totals               │
  └──────────────┘ └────────────────────────┘
  [  CONFIRM & SAVE  (primary, full w)  ]
```

### Dashboard
```
TOP BAR: "Resumen del Día" | date | icons
───────────────────────────────────────────────
[ KPI ] [ KPI ] [ KPI ] [ KPI ]   ← 4 columns
[ Strip: tax/purchase summary     ]
[ Bar chart 62% ] [ Donut 38%    ]
[ Recent sales table  ] [ Alerts ]
```

### Inventory
```
TOP BAR: "Inventario" | search input
─────────────────────────────────────
TABS: Catálogo | Alertas | Combos
─────────────────────────────────────
[  Full-width data table with pagination  ]
  columns: SKU | Nombre | Marca | Stock | Categoría
  stock < 0 → red row tint
  stock < threshold → amber row tint
```

### Purchases
```
TOP BAR: "Compras"
─────────────────────────────────────
[  TEXT AREA — paste supplier message  ]  card
[  PARSE BUTTON (primary, full w)      ]

PARSED TABLE (editable):
  SKU | Producto | Cantidad | Costo Unit.
[  SAVE PURCHASE (primary, full w)     ]

─────────────────────────────────────
Recent purchases table (below)
```

---

## 9. Do's and Don'ts

| Do | Don't |
|---|---|
| Use Caveat font everywhere | Use system sans-serif or Streamlit defaults |
| Warm parchment backgrounds (#faf8f4, #f5f2eb) | Use pure white (#fff) or cold gray |
| Offset shadow on every card (3px, 4px, #e8e4dc) | Use CSS box-shadow with blur radius |
| Status as colored text only | Use colored filled badges/pills for status |
| Primary button always dark (#1a1a1a) | Use blue/green/default Streamlit button colors |
| Left accent bar on KPI cards | Skip the accent bar |
| Alternating warm tints on table rows | Solid white or no alternation |
| 12–13px gaps between cards | Large 24px+ gutters between cards |
| Sparse accent colors — only for signals | Use accent colors decoratively |
| Roughness feeling via border-radius: 2px + box-shadow offset | Hard borders with large radius |
