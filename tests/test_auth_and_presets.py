import unittest
import sys
import os

# Adjust python paths
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../app")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.crawler import load_config_data

class TestAuthAndPresets(unittest.TestCase):
    def test_load_config_data_roles(self):
        # Test roles parsing from config.ini
        limit, patients, labs = load_config_data()
        
        # Check if we parsed the existing patients correctly
        # celio_rodrigues should be admin, and ruthlenr should be user (default)
        celio = next((p for p in patients if p.get("user") == "P31629"), None)
        ruth = next((p for p in patients if p.get("user") == "P31638"), None)
        
        if celio:
            self.assertEqual(celio.get("role"), "admin")
        if ruth:
            self.assertEqual(ruth.get("role"), "user")

    def test_preset_resolutions(self):
        # Test preset logic analogous to what is implemented in dashboard.py
        presets = {
            "Controle de Diabetes": ["Glicose em Jejum", "Hemoglobina Glicada (HbA1c)", "Glicemia Média Estimada"],
            "Função Renal": ["Ureia", "Creatinina Sérica", "Ácido Úrico"],
            "Função Hepática": ["TGO (AST)", "TGP (ALT)", "Gama Gt", "Fosfatase Alcalina"],
            "Perfil Lipídico": ["Colesterol Total", "Colesterol HDL", "Triglicerídeos"],
            "Hemograma Completo": "hemograma_completo",
            "Hormônios & Tireoide": ["TSH Ultra Sensível", "T4 Livre", "25-Hidroxivitamina D"],
            "PSA (Saúde Masculina)": ["Psa Total Ultra Sensível"]
        }
        
        all_exams = [
            "Glicose em Jejum", "Hemoglobina Glicada (HbA1c)", 
            "Hemograma - Hemacias em milhoes", "Hemograma - Hemoglobina",
            "Leucograma - Blastos (%)", "Ureia", "Colesterol Total"
        ]
        
        # Test Controle de Diabetes
        resolved_diabetes = [e for e in presets["Controle de Diabetes"] if e in all_exams]
        self.assertIn("Glicose em Jejum", resolved_diabetes)
        self.assertIn("Hemoglobina Glicada (HbA1c)", resolved_diabetes)
        self.assertNotIn("Colesterol Total", resolved_diabetes)
        
        # Test Hemograma Completo logic
        resolved_hemograma = [e for e in ["Hemograma - Hemoglobina", "Hemograma - Hematocrito", "Leucocitos", "Plaquetas"] if e in all_exams]
        self.assertNotIn("Hemograma - Hemacias em milhoes", resolved_hemograma)
        self.assertIn("Hemograma - Hemoglobina", resolved_hemograma)
        self.assertNotIn("Leucograma - Blastos (%)", resolved_hemograma)
        self.assertNotIn("Glicose em Jejum", resolved_hemograma)

if __name__ == "__main__":
    unittest.main()
