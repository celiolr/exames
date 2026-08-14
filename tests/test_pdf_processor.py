import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../app")))
from pdf_processor import clean_txt

class TestPdfProcessor(unittest.TestCase):
    def test_clean_txt_replacements(self):
        # Testa se a substituição de caracteres corrompidos funciona
        dirty = "O MDICO solicitou um Mtodo com referncia"
        expected = "O MÉDICO solicitou um Método com referência"
        self.assertEqual(clean_txt(dirty), expected)

    def test_clean_txt_none_or_empty(self):
        self.assertEqual(clean_txt(""), "")
        self.assertEqual(clean_txt(None), "")

if __name__ == "__main__":
    unittest.main()
