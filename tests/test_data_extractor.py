import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../app")))
from data_extractor import clean_txt, examen_alias

class TestDataExtractor(unittest.TestCase):
    def test_clean_txt(self):
        self.assertEqual(clean_txt("  valor limpo  "), "valor limpo")
        self.assertEqual(clean_txt(""), "")
        self.assertEqual(clean_txt(None), "")

    def test_examen_alias(self):
        # Testa mapeamento de aliases de exames
        self.assertEqual(examen_alias("GLICOSE JEJUM"), "Glicose em Jejum")
        self.assertEqual(examen_alias("TRIGLICERIDES"), "Triglicerídeos")
        self.assertEqual(examen_alias("EXAME DESCONHECIDO"), "Exame Desconhecido")

if __name__ == "__main__":
    unittest.main()
