import unittest
import sys
import os
import unicodedata

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../app")))

from app.auditoria import get_pdf_search_terms
from app.data_extractor import examen_alias


def normalize(text):
    """Remove acentos e converte para maiúsculas."""
    t = unicodedata.normalize("NFD", text.upper())
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


# Mapeamento completo: alias gerado pelo data_extractor -> termos reais que devem existir no PDF
# Manter este dicionário sincronizado com examen_alias() em data_extractor.py
ALIAS_TO_PDF_TERMS = {
    "GLICOSE JEJUM":                    ["GLICOSE JEJUM"],
    "HEMOGLOBINA GLICADA":              ["HEMOGLOBINA GLICADA"],
    "HEMOGLOBINA GLICADA (HBA1C)":      ["HEMOGLOBINA GLICADA", "HBA1C"],
    "COLESTEROL TOTAL":                 ["COLESTEROL TOTAL"],
    "COLESTEROL HDL":                   ["COLESTEROL HDL"],
    "TRIGLICERIDES":                    ["TRIGLICERIDE"],
    "ACIDO URICO":                      ["ACIDO URICO"],
    "TSH ULTRA SENSIVEL":               ["TSH"],
    "TSH ULTRA SENSÍVEL":               ["TSH"],
    "CREATININA SERICA":                ["CREATININA"],
    "CREATININA SÉRICA":                ["CREATININA"],
    "RITMO DE FILTRAÇÃO GLOMERULAR":    ["FILTRACAO GLOMERULAR"],
    "SODIO":                            ["SODIO"],
    "SÓDIO":                            ["SODIO"],
    "POTASSIO":                         ["POTASSIO"],
    "POTÁSSIO":                         ["POTASSIO"],
    "TRANSAMINASE OXALACÉTICA (TGO/AST)":  ["TGO"],
    "TRANSAMINASE PIRÚVICA (TGP/ALT)":     ["TGP"],
    "GAMA GLUTAMIL TRANSFERASE (GAMA GT)": ["GAMA GT"],
    "FOSFATASE ALCALINA":               ["FOSFATASE ALCALINA"],
    "CREATINOFOSFOQUINASE (CPK/CK)":    ["CPK"],
    "VITAMINA D - 25 HIDROXI":          ["VITAMINA D", "25-HIDROXIVITAMINA"],
    "PSA TOTAL":                        ["PSA TOTAL"],
}


class TestAuditoriaMapping(unittest.TestCase):
    """
    Testa se get_pdf_search_terms(alias) retorna pelo menos um dos termos
    reais que existem no PDF para cada alias conhecido do data_extractor.

    REGRA: se um teste falhar aqui, significa que um alias foi adicionado a
    data_extractor.py sem o correspondente mapeamento em auditoria.py.
    """

    def _check_alias(self, raw_alias, expected_pdf_terms):
        alias_name = examen_alias(raw_alias)          # ex: "Glicose em Jejum"
        search_terms = get_pdf_search_terms(alias_name)  # ex: ["GLICOSE JEJUM", "GLICOSE"]
        search_terms_norm = [normalize(t) for t in search_terms]

        found_any = False
        for expected in expected_pdf_terms:
            if normalize(expected) in search_terms_norm:
                found_any = True
                break

        self.assertTrue(
            found_any,
            f"\nAlias '{raw_alias}' → nome CSV '{alias_name}'\n"
            f"  get_pdf_search_terms retornou: {search_terms}\n"
            f"  Mas nenhum dos termos esperados do PDF estava presente: {expected_pdf_terms}\n"
            f"  → Adicione o mapeamento em auditoria.py → get_pdf_search_terms() → mappings"
        )

    def test_glicose_jejum(self):
        self._check_alias("GLICOSE JEJUM", ["GLICOSE JEJUM"])

    def test_hemoglobina_glicada(self):
        self._check_alias("HEMOGLOBINA GLICADA", ["HEMOGLOBINA GLICADA"])

    def test_colesterol_total(self):
        self._check_alias("COLESTEROL TOTAL", ["COLESTEROL TOTAL"])

    def test_colesterol_hdl(self):
        self._check_alias("COLESTEROL HDL", ["COLESTEROL HDL", "HDL"])

    def test_triglicerides(self):
        self._check_alias("TRIGLICERIDES", ["TRIGLICERIDE"])

    def test_acido_urico(self):
        self._check_alias("ACIDO URICO", ["ACIDO URICO"])

    def test_tsh(self):
        self._check_alias("TSH ULTRA SENSIVEL", ["TSH"])

    def test_creatinina(self):
        self._check_alias("CREATININA SERICA", ["CREATININA"])

    def test_sodio(self):
        self._check_alias("SODIO", ["SODIO"])

    def test_potassio(self):
        self._check_alias("POTASSIO", ["POTASSIO"])

    def test_tgo(self):
        self._check_alias("TRANSAMINASE OXALACETICA (TGO/AST)", ["TGO"])

    def test_tgp(self):
        self._check_alias("TRANSAMINASE PIRUVICA (TGP/ALT)", ["TGP"])

    def test_gama_gt(self):
        self._check_alias("GAMA GLUTAMIL TRANSFERASE (GAMA GT)", ["GAMA GT", "GAMA-GT"])

    def test_fosfatase_alcalina(self):
        self._check_alias("FOSFATASE ALCALINA", ["FOSFATASE ALCALINA"])

    def test_cpk(self):
        self._check_alias("CREATINOFOSFOQUINASE (CPK/CK)", ["CPK"])

    def test_vitamina_d(self):
        self._check_alias("VITAMINA D - 25 HIDROXI", ["VITAMINA D", "25-HIDROXIVITAMINA"])

    def test_psa_total(self):
        self._check_alias("PSA TOTAL", ["PSA TOTAL"])

    def test_ritmo_filtracao(self):
        self._check_alias("RITMO DE FILTRAÇÃO GLOMERULAR", ["FILTRACAO GLOMERULAR", "RITMO DE FILTRACAO"])


class TestGetPdfSearchTermsDirect(unittest.TestCase):
    """
    Testa get_pdf_search_terms() diretamente com o nome CSV (como chega da auditoria).
    Garante regressão zero para o bug do 'GLICOSE EM JEJUM' vs 'GLICOSE JEJUM'.
    """

    def test_glicose_em_jejum_retorna_glicose_jejum(self):
        """Bug histórico: auditoria buscava 'GLICOSE EM JEJUM' mas PDF tem 'GLICOSE JEJUM'."""
        terms = get_pdf_search_terms("Glicose em Jejum")
        terms_norm = [normalize(t) for t in terms]
        self.assertIn("GLICOSE JEJUM", terms_norm,
            "get_pdf_search_terms('Glicose em Jejum') deve retornar 'GLICOSE JEJUM' para bater com o PDF.")

    def test_glicose_em_jejum_nao_retorna_apenas_com_em(self):
        """Garante que 'GLICOSE EM JEJUM' (inexistente no PDF) não seja o único termo de busca."""
        terms = get_pdf_search_terms("Glicose em Jejum")
        # O termo tem que conter algo além de "GLICOSE EM JEJUM"
        self.assertGreater(len(terms), 0, "Deve retornar ao menos um termo de busca.")
        terms_norm = [normalize(t) for t in terms]
        # Pelo menos um dos termos deve aparecer num PDF real (GLICOSE JEJUM ou GLICOSE)
        self.assertTrue(
            any(t in ["GLICOSE JEJUM", "GLICOSE"] for t in terms_norm),
            f"Esperava 'GLICOSE JEJUM' ou 'GLICOSE' nos termos, mas obteve: {terms}"
        )

    def test_hemograma_prefix(self):
        terms = get_pdf_search_terms("Hemograma - Hemoglobina")
        self.assertIn("HEMOGLOBINA", [normalize(t) for t in terms])

    def test_leucograma_bastoes(self):
        terms = get_pdf_search_terms("Leucograma - N. Bastoes (%)")
        terms_norm = [normalize(t) for t in terms]
        self.assertTrue(
            any(t in ["BASTOES", "BASTONETES"] for t in terms_norm),
            f"Esperava BASTOES ou BASTONETES, obteve: {terms}"
        )

    def test_fallback_retorna_algo(self):
        """Exame desconhecido deve retornar pelo menos o próprio nome como fallback."""
        terms = get_pdf_search_terms("Exame Completamente Desconhecido")
        self.assertGreater(len(terms), 0)
        self.assertIsInstance(terms[0], str)


if __name__ == "__main__":
    unittest.main(verbosity=2)
