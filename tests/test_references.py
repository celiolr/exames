import unittest
import os
import sys
import tempfile
import json
import csv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../app")))

from app.data_extractor_reference import parse_patient_specific_vr, calculate_age_at_exam

class TestPatientReferences(unittest.TestCase):
    
    def test_calculate_age(self):
        # 1. Teste de cálculo simples de idade
        birth = "31/08/1965"
        exam = "10/08/2026"
        age = calculate_age_at_exam(birth, exam)
        self.assertEqual(age, 60)
        
        # 2. Teste no dia do aniversário
        birth_bday = "10/08/1965"
        age_bday = calculate_age_at_exam(birth_bday, exam)
        self.assertEqual(age_bday, 61)

    def test_parse_patient_specific_vr_simple(self):
        # VR simples de glicose (não tem condicionais)
        vr_text = "DE 60 A 99 mg/dL"
        res = parse_patient_specific_vr(vr_text, age=60, sex="Masculino")
        self.assertEqual(res, "DE 60 A 99 mg/dL")

    def test_parse_patient_specific_vr_cholesterol(self):
        # VR de Colesterol Total com regras de adultos e crianças
        vr_text = "PARA ADULTOS ACIMA 20 ANOS : INFERIOR A 190 mg/dL. PARA CRIANÇAS E ADOLESCENTES: INFERIOR A 170 mg/dL"
        
        # Teste para Adulto (> 20)
        res_adult = parse_patient_specific_vr(vr_text, age=60, sex="Masculino")
        self.assertIn("INFERIOR A 190", res_adult)
        self.assertNotIn("INFERIOR A 170", res_adult)
        
        # Teste para Criança (<= 20)
        res_child = parse_patient_specific_vr(vr_text, age=12, sex="Feminino")
        self.assertIn("INFERIOR A 170", res_child)
        self.assertNotIn("INFERIOR A 190", res_child)

    def test_parse_patient_specific_vr_cholesterol_with_footnotes(self):
        # Texto real do exame contendo nota de rodapé com outros números/faixas etárias (ex: 2 e 19 anos, 310 mg/dL)
        vr_text = (
            "VALORES REFERENCIAIS DESEJÁVEIS (COM OU SEM JEJUM): PARA ADULTOS ACIMA 20 ANOS : INFERIOR A 190 mg/dL "
            "PARA CRIANÇAS E ADOLESCENTES: INFERIOR A 170 mg/dL NOTA: - Valores de Colesterol Total maior ou igual a 310 mg/dL "
            "(para adultos) ou Colesterol Total maior ou igual a 230 mg/dL (entre 2 e 19 ANOS) podem ser indicativos..."
        )
        
        # Teste para Adulto (> 20)
        res_adult = parse_patient_specific_vr(vr_text, age=60, sex="Masculino")
        self.assertIn("INFERIOR A 190", res_adult)
        self.assertNotIn("INFERIOR A 170", res_adult)
        # Garante que a nota de rodapé e seus números enganosos foram removidos
        self.assertNotIn("310", res_adult)
        self.assertNotIn("19 ANOS", res_adult)

    def test_parse_patient_specific_vr_sex_dependent(self):
        # VR dependente de sexo (exemplo fictício com Homem / Mulher)
        vr_text = "Homens: 10 a 50 pg/mL. Mulheres: 5 a 30 pg/mL."
        
        # Homem
        res_male = parse_patient_specific_vr(vr_text, age=40, sex="Masculino")
        self.assertIn("Homens: 10 a 50 pg/mL", res_male)
        self.assertNotIn("Mulheres: 5 a 30 pg/mL", res_male)
        
        # Mulher
        res_female = parse_patient_specific_vr(vr_text, age=40, sex="Feminino")
        self.assertIn("Mulheres: 5 a 30 pg/mL", res_female)
        self.assertNotIn("Homens: 10 a 50 pg/mL", res_female)

if __name__ == "__main__":
    unittest.main()
