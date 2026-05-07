"""
tests/test_match_sku.py
=======================
Tests unitarios para _normalize, _tokenize, _f1_score y _match_sku
en api/guardar_venta.py.

Cubre los bugs reales que ocurrieron en producción:
- alias solo evaluado como fallback → alias siempre compite (corregido)
- "1 und Megaplex 2 lb" matcheaba "Viga 2lb" en vez de "Megaplex..." (corregido)
"""

import pytest
from types import SimpleNamespace

from api.guardar_venta import _normalize, _tokenize, _f1_score, _match_sku


# ---------------------------------------------------------------------------
# Helper: producto simulado (sin DB)
# ---------------------------------------------------------------------------

def p(sku: str, nombre: str, alias: str = None) -> SimpleNamespace:
    return SimpleNamespace(sku=sku, nombre=nombre, alias=alias)


# ---------------------------------------------------------------------------
# _normalize
# ---------------------------------------------------------------------------

class TestNormalize:
    def test_lowercase(self):
        assert _normalize("CREATINA") == "creatina"

    def test_removes_accents_and_special_chars(self):
        # á, é, ó no están en [a-z0-9 ] → se eliminan
        assert _normalize("Proteína") == "protena"

    def test_removes_hyphens_and_brackets(self):
        assert _normalize("Viga 2lb - Fitmafia [2230]") == "viga 2lb  fitmafia 2230"

    def test_removes_parentheses(self):
        assert _normalize("Creatina (300g)") == "creatina 300g"

    def test_strips_edges(self):
        assert _normalize("  gold standard  ") == "gold standard"

    def test_already_clean(self):
        assert _normalize("creatina 300g") == "creatina 300g"

    def test_empty_string(self):
        assert _normalize("") == ""


# ---------------------------------------------------------------------------
# _tokenize
# ---------------------------------------------------------------------------

class TestTokenize:
    def test_digit_letter_split(self):
        # "2lb" → separar en "2" y "lb"
        assert _tokenize("2lb") == {"2", "lb"}

    def test_letter_digit_split(self):
        # "lb2" → "lb" y "2"
        assert _tokenize("lb2") == {"lb", "2"}

    def test_compound_like_2lb(self):
        # "Creatina 2lb" → {creatina, 2, lb}
        assert _tokenize("Creatina 2lb") == {"creatina", "2", "lb"}

    def test_plural_stemming(self):
        # Palabras de > 3 chars que terminan en 's' → se les quita la 's'
        assert "mancuerna" in _tokenize("mancuernas")

    def test_plural_stemming_proteina(self):
        assert "proteina" in _tokenize("proteinas")

    def test_no_stemming_short_words(self):
        # "abs" tiene len=3 → no se le quita la 's'
        assert "abs" in _tokenize("abs")

    def test_uppercase_normalised(self):
        assert _tokenize("CREATINA") == {"creatina"}

    def test_special_chars_stripped(self):
        # Guiones y corchetes se eliminan en _normalize antes de tokenizar
        tokens = _tokenize("Viga 2lb - Fitmafia [2230]")
        assert "viga" in tokens
        assert "2" in tokens
        assert "fitmafia" in tokens
        assert "2230" in tokens
        assert "-" not in tokens

    def test_returns_set(self):
        # Garantiza que no hay duplicados
        assert isinstance(_tokenize("creatina creatina"), set)


# ---------------------------------------------------------------------------
# _f1_score
# ---------------------------------------------------------------------------

class TestF1Score:
    def test_perfect_match(self):
        assert _f1_score(["creatina", "300"], {"creatina", "300"}) == pytest.approx(1.0)

    def test_empty_keywords_returns_zero(self):
        assert _f1_score([], {"creatina"}) == 0.0

    def test_empty_catalog_tokens_returns_zero(self):
        assert _f1_score(["creatina"], set()) == 0.0

    def test_below_recall_threshold_returns_zero(self):
        # recall = 1/3 ≈ 0.33 < 0.60 → 0.0
        assert _f1_score(["a", "b", "c"], {"a"}) == 0.0

    def test_at_recall_threshold(self):
        # recall = 2/3 ≈ 0.667 ≥ 0.6 → F1 > 0
        score = _f1_score(["a", "b", "c"], {"a", "b"})
        assert score > 0.0

    def test_partial_precision(self):
        # keywords = [a, b], catalog = {a, b, c, d} → precision = 2/4 = 0.5, recall = 1.0
        score = _f1_score(["a", "b"], {"a", "b", "c", "d"})
        assert score == pytest.approx(2 * 0.5 * 1.0 / (0.5 + 1.0))

    def test_no_overlap_returns_zero(self):
        assert _f1_score(["proteina"], {"creatina"}) == 0.0


# ---------------------------------------------------------------------------
# _match_sku — comportamiento básico
# ---------------------------------------------------------------------------

class TestMatchSkuBasic:
    @pytest.fixture
    def catalog(self):
        return [
            p("1001", "Creatina Monohidratada 300g"),
            p("1002", "Proteína Whey 2lb"),
            p("1003", "Banda de Resistencia Latex Azul"),
        ]

    def test_exact_nombre_match(self, catalog):
        assert _match_sku(catalog, "creatina monohidratada 300g") == "1001"

    def test_partial_nombre_match(self, catalog):
        assert _match_sku(catalog, "creatina monohidratada") == "1001"

    def test_case_insensitive(self, catalog):
        assert _match_sku(catalog, "CREATINA MONOHIDRATADA 300G") == "1001"

    def test_empty_raw_name_returns_none(self, catalog):
        assert _match_sku(catalog, "") is None

    def test_empty_catalog_returns_none(self):
        assert _match_sku([], "creatina") is None

    def test_no_match_returns_none(self, catalog):
        assert _match_sku(catalog, "mancuerna hexagonal") is None

    def test_best_score_wins(self, catalog):
        # "creatina 300g" tiene más tokens en común con 1001 que con los demás
        assert _match_sku(catalog, "creatina 300g") == "1001"

    def test_doesnt_confuse_similar_products(self, catalog):
        assert _match_sku(catalog, "proteina whey 2lb") == "1002"


# ---------------------------------------------------------------------------
# _match_sku — filtrado de palabras vacías y tokens cortos
# ---------------------------------------------------------------------------

class TestMatchSkuStopWords:
    @pytest.fixture
    def catalog(self):
        return [p("1001", "Creatina 300g")]

    def test_und_filtered(self, catalog):
        # "1 und" → "und" filtrado, "1" pasa (isdigit). Pero "1" no matchea "creatina 300g"
        assert _match_sku(catalog, "1 und creatina 300g") == "1001"

    def test_unidad_filtered(self, catalog):
        assert _match_sku(catalog, "unidad creatina 300g") == "1001"

    def test_par_filtered(self, catalog):
        assert _match_sku(catalog, "par creatina 300g") == "1001"

    def test_x2_filtered(self, catalog):
        assert _match_sku(catalog, "x2 creatina 300g") == "1001"

    def test_only_stop_words_returns_none(self, catalog):
        assert _match_sku(catalog, "und par unidad") is None

    def test_single_char_non_digit_filtered(self, catalog):
        # "g" sola con len=1 no es dígito → filtrada
        assert _match_sku(catalog, "g") is None


# ---------------------------------------------------------------------------
# _match_sku — stemming de plurales
# ---------------------------------------------------------------------------

class TestMatchSkuStemming:
    def test_plural_matches_singular_product(self):
        catalog = [p("1001", "Mancuerna Hexagonal 10kg")]
        assert _match_sku(catalog, "mancuernas hexagonales 10kg") == "1001"

    def test_proteinas_matches_proteina(self):
        catalog = [p("1001", "Proteína Whey 2lb")]
        assert _match_sku(catalog, "proteinas whey 2lb") == "1001"


# ---------------------------------------------------------------------------
# _match_sku — aliases siempre compiten (regresión del bug de producción)
# ---------------------------------------------------------------------------

class TestMatchSkuAliases:
    def test_alias_wins_over_long_nombre(self):
        """
        Bug de producción: "Megaplex 2 lb" matcheaba "Viga 2lb" porque el
        nombre largo "Megaplex Creatine Power 2lb..." tenía F1 bajo (precisión baja),
        y el alias solo se evaluaba si score == 0.0.

        Con la corrección, el alias "Megaplex 2 lb" (F1=1.0) siempre compite
        y gana sobre "Viga 2lb" (F1≈0.67).
        """
        catalog = [
            p("2230", "Viga 2lb - Fitmafia"),
            p("2140", "Megaplex Creatine Power 2lb Nutramerican Pharma Vainilla",
              alias="Megaplex 2 lb"),
        ]
        assert _match_sku(catalog, "Megaplex 2 lb") == "2140"

    def test_alias_with_unit_prefix(self):
        """El mismo bug con el prefijo '1 und' que viene del mensaje real."""
        catalog = [
            p("2230", "Viga 2lb - Fitmafia"),
            p("2140", "Megaplex Creatine Power 2lb Nutramerican Pharma Vainilla",
              alias="Megaplex 2 lb"),
        ]
        assert _match_sku(catalog, "1 und Megaplex 2 lb") == "2140"

    def test_alias_wins_even_when_nombre_has_nonzero_score(self):
        """
        El alias debe competir aunque el nombre del producto ya tenga un score > 0.
        Con el bug original (alias solo si score==0), este test fallaría.
        """
        catalog = [
            p("1001", "ISO 100 Whey Protein 2lb Dymatize Gourmet Chocolate"),
            p("1002", "Proteína Whey 2lb"),  # sin alias
        ]
        # "ISO 100 2lb" da score no-nulo contra "1001" por el nombre,
        # pero el alias "ISO 100 2lb" daría F1=1.0 si existiera
        catalog_with_alias = [
            p("1001", "ISO 100 Whey Protein 2lb Dymatize Gourmet Chocolate",
              alias="ISO 100 2lb"),
            p("1002", "Proteína Whey 2lb"),
        ]
        assert _match_sku(catalog_with_alias, "ISO 100 2lb") == "1001"

    def test_multiple_aliases_best_wins(self):
        """De múltiples aliases, gana el de mayor F1."""
        catalog = [
            p("1001", "Suplemento X Plus 500g",
              alias="Suplemento X, X Plus 500g, X500"),
        ]
        # "X Plus 500g" → F1=1.0 contra alias "X Plus 500g"
        assert _match_sku(catalog, "X Plus 500g") == "1001"

    def test_alias_none_doesnt_crash(self):
        """Productos sin alias no deben lanzar error."""
        catalog = [p("1001", "Creatina 300g", alias=None)]
        assert _match_sku(catalog, "creatina 300g") == "1001"

    def test_alias_empty_string_doesnt_crash(self):
        """Alias vacío (no None) tampoco debe lanzar error."""
        catalog = [p("1001", "Creatina 300g", alias="")]
        assert _match_sku(catalog, "creatina 300g") == "1001"

    def test_alias_doesnt_steal_better_nombre_match(self):
        """
        Si el nombre de otro producto ya da mejor F1 que el alias,
        el alias no debe "robar" el match.
        """
        catalog = [
            p("1001", "Creatina Monohidratada 300g"),
            p("1002", "Proteína Whey 2lb", alias="creatina"),  # alias parcial
        ]
        # "creatina monohidratada 300g" → 1001 da F1 altísimo vs 1002 con alias "creatina"
        # (alias "creatina" tiene recall=1/3 → debajo del umbral 0.6)
        assert _match_sku(catalog, "creatina monohidratada 300g") == "1001"


# ---------------------------------------------------------------------------
# _match_sku — caracteres especiales y formatos reales
# ---------------------------------------------------------------------------

class TestMatchSkuEdgeCases:
    def test_brackets_in_catalog_name_stripped(self):
        """Nombres de catálogo con corchetes/guiones no interfieren."""
        catalog = [p("2230", "Viga 2lb - Fitmafia [2230]")]
        assert _match_sku(catalog, "Viga 2lb Fitmafia") == "2230"

    def test_digit_weight_format(self):
        """Formatos "2lb", "300g", "1kg" se tokenízan correctamente."""
        catalog = [
            p("1001", "Creatina 300g"),
            p("1002", "Creatina 1kg"),
        ]
        assert _match_sku(catalog, "creatina 1kg") == "1002"
        assert _match_sku(catalog, "creatina 300g") == "1001"

    def test_recall_threshold_boundary(self):
        """
        Con 2 de 3 keywords (recall=0.667 ≥ 0.6): debe matchear.
        Con 1 de 3 keywords (recall=0.333 < 0.6): debe retornar None.
        """
        catalog = [p("1001", "Creatina Monohidratada 300g")]
        # 2/3 keywords → debe matchear
        assert _match_sku(catalog, "creatina monohidratada sabor") == "1001"
        # "sabor" no está en el catálogo → matches=2, recall=2/3 ≥ 0.6 ✓

    def test_only_one_keyword_below_threshold(self):
        """1 de 3 keywords → recall < 0.6 → None."""
        catalog = [p("1001", "Creatina Monohidratada 300g")]
        # "proteina vitamina creatina" → 1 match ("creatina"), recall=1/3 < 0.6
        assert _match_sku(catalog, "proteina vitamina creatina") is None
