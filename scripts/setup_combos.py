"""
setup_combos.py
===============
Inserts combo_componentes rows for all combos with unambiguous components.

Includes:
  - Kits de barras: COL I-III, FULL BODY, OLYMPIC I-VI
  - Mancuernas ajustables 1075-1080 (seguros vienen incluidos con la barra)
  - Kits de bandas: x5 WONDER, Tela x2/x5, Therabands, Poder
  - Kit Basic (1137)
  - Combos suplementos 4000-4006 (proteína = sabor Vainilla por defecto)

See combos_pendientes.sql for the manual-completion templates.

Safe to re-run: uses INSERT ... ON CONFLICT DO NOTHING.

Run:
    python scripts/setup_combos.py
"""

import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _root)
load_dotenv(dotenv_path=os.path.join(_root, ".env"), override=True)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("[ERROR] DATABASE_URL not set in .env")
    sys.exit(1)

# (combo_sku, componente_sku, cantidad)
COMBO_COMPONENTES = [

    # ---------------------------------------------------------------
    # KITS DE BARRAS ESTÁNDAR (discos vendidos como pares x2)
    # ---------------------------------------------------------------

    # Kit FULL BODY (1089): Discos 10lb x4 + Barra 120cm + Barras mancuerna x2
    ("1089", "1021", 2),   # Discos 10lb x2 ESTÁNDAR × 2 pares = x4
    ("1089", "1059", 1),   # Barra recta 120cm
    ("1089", "1058", 2),   # Barras mancuernas 35cm x2

    # Kit COL I (1090): Disco 10lb x2 + Barra 120cm
    ("1090", "1021", 1),
    ("1090", "1059", 1),

    # Kit COL II (1091): Disco 5lb x2 + Disco 10lb x2 + Barra 120cm
    ("1091", "1020", 1),
    ("1091", "1021", 1),
    ("1091", "1059", 1),

    # Kit COL III (1092): Disco 10lb x4 + Barra 120cm
    ("1092", "1021", 2),
    ("1092", "1059", 1),

    # Kit OLYMPIC I (1093): Disco 20lb x2 + Barra 150cm
    ("1093", "1022", 1),
    ("1093", "1060", 1),

    # Kit OLYMPIC II (1094): Disco 25lb x2 + Barra 150cm
    ("1094", "1023", 1),
    ("1094", "1060", 1),

    # Kit OLYMPIC III (1095): Disco 30lb x2 + Barra 150cm
    ("1095", "1024", 1),
    ("1095", "1060", 1),

    # Kit OLYMPIC IV (1096): Disco 40lb x2 + Barra 150cm
    ("1096", "1025", 1),
    ("1096", "1060", 1),

    # Kit OLYMPIC V (1097): Disco 50lb x2 + Barra 180cm
    ("1097", "1026", 1),
    ("1097", "1061", 1),

    # Kit OLYMPIC VI (1098): Disco 60lb x2 + Barra 180cm
    ("1098", "1027", 1),
    ("1098", "1061", 1),

    # ---------------------------------------------------------------
    # MANCUERNAS AJUSTABLES
    # Note: seguros roscados omitted — no SKU in catalog
    # ---------------------------------------------------------------

    # 1075: Disco 5lb x4 + Barra mancuerna x2
    ("1075", "1020", 2),
    ("1075", "1058", 2),

    # 1076: Disco 3lb x8 + Barra mancuerna x2
    ("1076", "1019", 4),
    ("1076", "1058", 2),

    # 1077: Disco 3lb x4 + Disco 5lb x4 + Barra x2
    ("1077", "1019", 2),
    ("1077", "1020", 2),
    ("1077", "1058", 2),

    # 1078: Disco 5lb x8 + Barra x2
    ("1078", "1020", 4),
    ("1078", "1058", 2),

    # 1079: Disco 5lb x4 + Disco 10lb x4 + Barra x2
    ("1079", "1020", 2),
    ("1079", "1021", 2),
    ("1079", "1058", 2),

    # 1080: Disco 3lb x4 + Disco 5lb x4 + Disco 10lb x4 + Barra x2
    ("1080", "1019", 2),
    ("1080", "1020", 2),
    ("1080", "1021", 2),
    ("1080", "1058", 2),

    # ---------------------------------------------------------------
    # KITS DE BANDAS DE RESISTENCIA
    # ---------------------------------------------------------------

    # Kit de Bandas x5 WONDER (1152): Dorada + Negra + Azul + Verde + Roja
    ("1152", "1153", 1),
    ("1152", "1154", 1),
    ("1152", "1155", 1),
    ("1152", "1156", 1),
    ("1152", "1157", 1),

    # Kit de Bandas de Tela x2 WONDER (1163): 25lb/30lb = Dorada + Negra
    ("1163", "1158", 1),   # Tela Dorada 30-40lb
    ("1163", "1159", 1),   # Tela Negra 25-30lb

    # Kit de Bandas de Tela x5 WONDER (1164): todas las tela
    ("1164", "1158", 1),
    ("1164", "1159", 1),
    ("1164", "1160", 1),
    ("1164", "1161", 1),
    ("1164", "1162", 1),

    # Kit de Therabands (1172): Verde/Azul/Negra/Gris/Dorada
    ("1172", "1167", 1),
    ("1172", "1168", 1),
    ("1172", "1169", 1),
    ("1172", "1170", 1),
    ("1172", "1171", 1),

    # Kit de Bandas de Poder (1179): Roja/Negra/Morada/Verde/Azul
    ("1179", "1174", 1),
    ("1179", "1175", 1),
    ("1179", "1176", 1),
    ("1179", "1177", 1),
    ("1179", "1178", 1),

    # ---------------------------------------------------------------
    # KIT BASIC (1137): Colchoneta Yumbolon + Banda negra 22lb + Mancuernas 5kg x2
    # ---------------------------------------------------------------
    ("1137", "1234", 1),   # Colchoneta YUMBOLON - COLSPORTS
    ("1137", "1154", 1),   # Banda negra WONDER 22lb
    ("1137", "1013", 1),   # Mancuerna 5kg x2

    # ---------------------------------------------------------------
    # COMBOS DE SUPLEMENTOS (proteína = sabor Vainilla por defecto)
    # ---------------------------------------------------------------

    # 4000: Combo BI PRO CLASSIC 2 LB + CREASMART 92 SERV
    ("4000", "2117", 1),   # Bi Pro Classic 2lb - Vainilla
    ("4000", "2030", 1),   # Creatina Creasmart 550g

    # 4001: Combo WHEY GOLD 2 LB + CREASMART 92 SERV
    ("4001", "2160", 1),   # Whey Gold Standard 2lb - Vainilla
    ("4001", "2030", 1),   # Creatina Creasmart 550g

    # 4002: Combo WHEY PURE 2 LB + CREASMART 92 SERV
    ("4002", "2171", 1),   # Whey Pure 2lb - Vainilla
    ("4002", "2030", 1),   # Creatina Creasmart 550g

    # 4003: Combo WHEY PURE 2 LB + CREATINA IN 100 SERV
    ("4003", "2171", 1),   # Whey Pure 2lb - Vainilla
    ("4003", "2009", 1),   # Creatina IN 100 serv

    # 4004: Combo ISO 100 1.3 LB + CREASMART 92 SERV
    ("4004", "2127", 1),   # Iso 100 1.3lb - Vainilla
    ("4004", "2030", 1),   # Creatina Creasmart 550g

    # 4005: Combo ISO 100 1.3 LB + CREATINA PLATINUM 80 SERV
    ("4005", "2127", 1),   # Iso 100 1.3lb - Vainilla
    ("4005", "2006", 1),   # Creatina Platinum Micronized 80 serv

    # 4006: Creatina IMN + Proteína BiPro – Pack Fitness
    ("4006", "2003", 1),   # Creatina IMN 133 serv
    ("4006", "2117", 1),   # Bi Pro Classic 2lb - Vainilla
]

engine = create_engine(DATABASE_URL)

inserted = 0
skipped = 0
errors = []

with engine.begin() as conn:
    for combo_sku, componente_sku, cantidad in COMBO_COMPONENTES:
        try:
            result = conn.execute(text("""
                INSERT INTO combo_componentes (combo_sku, componente_sku, cantidad)
                VALUES (:combo, :comp, :qty)
                ON CONFLICT ON CONSTRAINT uq_combo_componente DO NOTHING
            """), {"combo": combo_sku, "comp": componente_sku, "qty": cantidad})
            if result.rowcount:
                inserted += 1
            else:
                skipped += 1
        except Exception as e:
            errors.append(f"  ({combo_sku}, {componente_sku}): {e}")

print(f"\nCombos setup complete:")
print(f"  Inserted : {inserted}")
print(f"  Skipped (already exist): {skipped}")
if errors:
    print(f"  Errors ({len(errors)}):")
    for err in errors:
        print(err)
else:
    print(f"  Errors   : 0")

print("""
Done. See scripts/combos_pendientes.sql for combos that need manual completion.
""")
