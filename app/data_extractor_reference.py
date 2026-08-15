import os
import re
import csv
import sys
import glob
import json
import configparser
import unicodedata
from datetime import datetime

try:
    from app.logger import logger
except ImportError:
    from logger import logger

try:
    from app.data_extractor import examen_alias, sanitize_name_component
except ImportError:
    from data_extractor import examen_alias, sanitize_name_component

def normalize_text(text):
    if not text:
        return ""
    text = unicodedata.normalize('NFD', text)
    return "".join(c for c in text if unicodedata.category(c) != 'Mn').upper().strip()

def get_most_recent_md_by_patient(md_dir="data/exames/exames_md"):
    md_files = glob.glob(os.path.join(md_dir, "*.md"))
    if not md_files:
        return []
    
    def extract_date(filepath):
        filename = os.path.basename(filepath)
        match = re.search(r'(\d{4})-(\d{2})-(\d{2})', filename)
        if match:
            try:
                return datetime.strptime(match.group(0), "%Y-%m-%d")
            except ValueError:
                pass
        return datetime.min

    by_patient = {}
    for f in md_files:
        filename = os.path.basename(f)
        match_paciente = re.search(r'^paciente_([a-z0-9_]+)-medico', filename)
        if match_paciente:
            paciente_key = match_paciente.group(1)
            if paciente_key not in by_patient:
                by_patient[paciente_key] = []
            by_patient[paciente_key].append(f)
            
    most_recents = []
    for paciente_key, files in by_patient.items():
        recent = max(files, key=extract_date)
        most_recents.append(recent)
        
    return most_recents

def load_patient_metadata(client_name):
    config = configparser.ConfigParser()
    config_path = "config.ini"
    if not os.path.exists(config_path):
        logger.warning("config.ini não encontrado!")
        return None

    config.read(config_path, encoding='utf-8')
    if 'Pacientes' not in config:
        return None

    normalized_client = normalize_text(client_name)
    
    try:
        from app.security import decrypt_password
    except ImportError:
        from security import decrypt_password

    for key, val in config['Pacientes'].items():
        try:
            patient_data = json.loads(val)
            normalized_pat_name = normalize_text(patient_data.get("nome", ""))
            if normalized_pat_name in normalized_client or normalized_client in normalized_pat_name:
                if "pass" in patient_data:
                    patient_data["pass"] = decrypt_password(patient_data["pass"])
                return patient_data
        except Exception as e:
            logger.error(f"Erro ao decodificar JSON do paciente {key}: {e}")
            
    return None

def calculate_age_at_exam(birth_date_str, exam_date_str):
    try:
        birth_date = datetime.strptime(birth_date_str, "%d/%m/%d%y" if len(birth_date_str.split('/')[-1]) == 2 else "%d/%m/%Y")
        exam_date = datetime.strptime(exam_date_str, "%d/%m/%Y")
        age = exam_date.year - birth_date.year - ((exam_date.month, exam_date.day) < (birth_date.month, birth_date.day))
        return age
    except Exception as e:
        logger.error(f"Erro ao calcular idade: {e}")
        return None

def clean_vr_text(vr_text):
    if not vr_text:
        return ""
    vr_text = re.sub(r'\bDE\s+DE\b', 'DE', vr_text, flags=re.IGNORECASE)
    
    prefixes_to_remove = [
        r'^VALOR\s+DE\s+REFERENCIA\s*:?\s*',
        r'^VALORES\s+REFERENCIAIS\s*:?\s*',
        r'^VALORES\s+DE\s+REFERENCIA\s*:?\s*',
        r'^VALOR\s+DE\s*:?\s*',
        r'^REFERENCIA\s*:?\s*',
        r'^VR\s*:?\s*'
    ]
    
    for prefix in prefixes_to_remove:
        vr_text = re.sub(prefix, '', vr_text, flags=re.IGNORECASE).strip()
        
    replacements = {
        r'\bMASCUL\b': 'MASCULINO',
        r'\bFEMIN\b': 'FEMININO',
        r'\bANOS\b': 'ANOS',
    }
    
    for bad, good in replacements.items():
        vr_text = re.sub(bad, good, vr_text, flags=re.IGNORECASE)
        
    return vr_text.strip()

def parse_patient_specific_vr(vr_text, age, sex, pregnancy=False):
    if not vr_text:
        return ""
    
    # Remove tudo a partir de termos de rodapé/nota para evitar processar valores de lá
    vr_text_clean = re.split(r'\b(?:NOTA|OBS|OBSERVAÇÃO|OBSERVACOES|FONTE|METODO|MÉTODO|ATENÇÃO|ATENÇAO)\b', vr_text, flags=re.IGNORECASE)[0].strip()
    # Remove ponto-e-vírgula, vírgula, dois-pontos ou espaço residual no final
    vr_text_clean = re.sub(r'[;,:,\s]+$', '', vr_text_clean)
    
    vr_upper = vr_text_clean.upper()
    
    if "ADULTOS" not in vr_upper and "CRIANÇAS" not in vr_upper and "HOMEM" not in vr_upper and "MULHER" not in vr_upper and "FEMININO" not in vr_upper and "MASCULINO" not in vr_upper:
        return vr_text_clean

    sentences = re.split(r'[;\n\.]|\bPARA\b|\bDE\s+\d+\s+A\b|(?=MASCULINO)|(?=FEMININO)', vr_text_clean, flags=re.IGNORECASE)
    matched_vr = []
    
    for sent in sentences:
        sent_upper = sent.upper().strip()
        if not sent_upper:
            continue
            
        is_adult_rule = "ADULTO" in sent_upper or "ACIMA" in sent_upper or "MAIOR" in sent_upper or ">" in sent_upper
        is_child_rule = "CRIANÇA" in sent_upper or "ADOLESCENTE" in sent_upper or "INFANTIL" in sent_upper or "INFERIOR A 20" in sent_upper or "DE 0 A" in sent_upper or "DE 10 A" in sent_upper
        
        is_male_rule = "HOMEM" in sent_upper or "MASCULINO" in sent_upper or "HOMENS" in sent_upper
        is_female_rule = "MULHER" in sent_upper or "FEMININO" in sent_upper or "MULHERES" in sent_upper
        
        if age is not None:
            if age > 20 and is_child_rule and not is_adult_rule:
                continue
            if age <= 20 and is_adult_rule and not is_child_rule:
                continue
                
        if sex:
            sex_norm = sex.upper()
            if "MASC" in sex_norm or "HOMEM" in sex_norm:
                if is_female_rule and not is_male_rule:
                    continue
            elif "FEM" in sex_norm or "MULHER" in sex_norm:
                if is_male_rule and not is_female_rule:
                    continue
                    
        if "GESTANTE" in sent_upper or "GRAVIDEZ" in sent_upper:
            if not pregnancy:
                continue
        
        matched_vr.append(sent.strip())
        
    if matched_vr:
        cleaned_res = "; ".join(matched_vr)
        # Se restou apenas lixo ou ficou muito vazio, retorna a limpa
        if not cleaned_res.strip() or len(re.sub(r'[^a-zA-Z0-9]', '', cleaned_res)) < 3:
            return vr_text_clean
        return cleaned_res
    return vr_text_clean

def is_hemogram_component(exam_name):
    name_upper = examen_alias(exam_name).upper()
    return any(k in name_upper for k in [
        "HEMOGRAMA", "HEMOCITOGRAMA", "LEUCOGRAMA", "PLAQUETAS", "LEUCOCITOS", 
        "HEMALIAS", "HEMACIAS", "HEMOGLOBINA", "HEMATOCRITO", "VCM", "HCM", "CHCM", "RDW"
    ])

def extract_references_from_md(md_path):
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    paciente_match = re.search(r'CLIENTE:\s*([^\n\d]+)', content)
    paciente = paciente_match.group(1).strip() if paciente_match else ""
    if "DN:" in paciente:
        paciente = paciente.split("DN:")[0].strip()
        
    data_match = re.search(r'DATA ENTRADA:\s*(\d{2}/\d{2}/\d{4})', content)
    data_exame = data_match.group(1) if data_match else ""
    
    patient_metadata = load_patient_metadata(paciente)
    age = None
    sex = "Ambos"
    pregnancy = False
    faixa_etaria = "Ambos"
    
    if patient_metadata:
        birth_date = patient_metadata.get("data_nascimento")
        sex = patient_metadata.get("sexo", "Ambos")
        pregnancy = patient_metadata.get("gravidez", False)
        if birth_date and data_exame:
            age = calculate_age_at_exam(birth_date, data_exame)
            faixa_etaria = "Adulto" if age > 20 else "Infantil"
            logger.info(f"Paciente: {paciente} | Idade no exame: {age} anos | Sexo: {sex} | Faixa: {faixa_etaria}")
            
    paginas = content.split('## Página ')
    extracted_references = {}

    for pag in paginas[1:]:
        lines = [line.strip() for line in pag.split('\n') if line.strip()]
        if not lines:
            continue
            
        header_patterns = ['CLIENTE:', 'NOME MÉDICO:', 'DATA ENTRADA:', 'CONVÊNIO:', 'CPF:', 'RG:', 'NOME SOCIAL:', 'DN:']
        filtered_lines = [l for l in lines if not any(pat in l for pat in header_patterns) and not l.startswith('##') and not l.startswith('---')]
        
        if not filtered_lines:
            continue
            
        exame_titulo = filtered_lines[0]
        if re.match(r'^\d+$', exame_titulo) and len(filtered_lines) > 1:
            exame_titulo = filtered_lines[1]
            
        is_hemogram_page = any(k in pag.upper() for k in ["HEMOGRAMA", "HEMOCITOGRAMA", "LEUCOGRAMA"])
        
        if is_hemogram_page:
            for line in filtered_lines:
                match_hemo = re.search(
                    r'^(Hemacias em milhoes|Hemoglobina|Hematocrito|V\.C\.M|H\.C\.M|C\.H\.C\.M|R\.D\.W)\s+([\d,.]+)\s*([a-zA-Z%/³]+)?\s+([\d,.\s\-a-zA-Záéíóú/]+)$',
                    line, re.IGNORECASE
                )
                if match_hemo:
                    comp = examen_alias(f"Hemograma - {match_hemo.group(1).strip()}")
                    uni = match_hemo.group(3).strip() if match_hemo.group(3) else ""
                    ref = clean_vr_text(match_hemo.group(4).strip()) if match_hemo.group(4) else ""
                    
                    key = (comp, sex, faixa_etaria, pregnancy)
                    extracted_references[key] = {
                        'Exame': comp,
                        'Unidade': uni,
                        'Referencia_Texto_Completo': ref,
                        'Referencia_Paciente_Especifico': parse_patient_specific_vr(ref, age, sex, pregnancy),
                        'Sexo': sex,
                        'Faixa_Etaria': faixa_etaria,
                        'Gestante': pregnancy,
                        'Data_Ultima_Atualizacao': data_exame
                    }
                    continue
                
                match_leuco = re.search(r'^(Leucocitos|Plaquetas)\s+([\d.]+)\s+([a-zA-Z0-9/³\s\-–]+)$', line, re.IGNORECASE)
                if match_leuco:
                    comp = examen_alias(match_leuco.group(1).strip())
                    ref = clean_vr_text(match_leuco.group(3).strip())
                    uni = "/mm³"
                    if "/mm" in ref:
                        # Se a referência contém a unidade (ex: "/mm3 150.000 A 450.000/mm3"), limpa a unidade inicial/final
                        # Normalmente o padrão é "150.000 A 450.000/mm3" ou "/mm3 150.000 A 450.000/mm3"
                        ref_clean = re.sub(r'^/?mm³?\s*', '', ref, flags=re.IGNORECASE)
                        ref_clean = re.sub(r'^/?mm3?\s*', '', ref_clean, flags=re.IGNORECASE)
                        ref = ref_clean.strip()
                    
                    key = (comp, sex, faixa_etaria, pregnancy)
                    extracted_references[key] = {
                        'Exame': comp,
                        'Unidade': uni,
                        'Referencia_Texto_Completo': ref,
                        'Referencia_Paciente_Especifico': parse_patient_specific_vr(ref, age, sex, pregnancy),
                        'Sexo': sex,
                        'Faixa_Etaria': faixa_etaria,
                        'Gestante': pregnancy,
                        'Data_Ultima_Atualizacao': data_exame
                    }
                    continue
                
                match_comp = re.search(
                    r'^(Blastos|Promielocitos|Mielocitos|Metamielocitos|N\.\s*Bastoes|N\.\s*Segmentados|Eosinofilos|Basãofilos|Monocitos|Linfocitos)\s+([\d,.]+)\s+([\d.]+)\s+([\d.\s\-a-zA-Zé/]+)$',
                    line, re.IGNORECASE
                )
                if match_comp:
                    comp_name = match_comp.group(1).strip()
                    ref = clean_vr_text(match_comp.group(4).strip())
                    
                    comp_abs = examen_alias(f"Leucograma - {comp_name} (Absoluto)")
                    key_abs = (comp_abs, sex, faixa_etaria, pregnancy)
                    extracted_references[key_abs] = {
                        'Exame': comp_abs,
                        'Unidade': "/mm³",
                        'Referencia_Texto_Completo': ref,
                        'Referencia_Paciente_Especifico': parse_patient_specific_vr(ref, age, sex, pregnancy),
                        'Sexo': sex,
                        'Faixa_Etaria': faixa_etaria,
                        'Gestante': pregnancy,
                        'Data_Ultima_Atualizacao': data_exame
                    }
                    
                    comp_pct = examen_alias(f"Leucograma - {comp_name} (%)")
                    key_pct = (comp_pct, sex, faixa_etaria, pregnancy)
                    extracted_references[key_pct] = {
                        'Exame': comp_pct,
                        'Unidade': "%",
                        'Referencia_Texto_Completo': "",
                        'Referencia_Paciente_Especifico': "",
                        'Sexo': sex,
                        'Faixa_Etaria': faixa_etaria,
                        'Gestante': pregnancy,
                        'Data_Ultima_Atualizacao': data_exame
                    }
        else:
            current_exam = examen_alias(exame_titulo)
            
            for idx, line in enumerate(filtered_lines):
                if re.match(r'^[0-9A-ZÁÉÍÓÚÂÊÔÃÕÇ\s\(\)/\-]+$', line) and len(line) > 3 and not re.match(r'^\d+$', line) and not any(k in line for k in ["RESULTADO", "VALOR", "MÉTODO", "MATERIAL", "FONTE", "CRBM", "CRM", "ASSINATURA", "RESPONSÁVEL"]):
                    current_exam = examen_alias(line.strip())
                
                match_res = re.search(r'^(?:RESULTADO|Resultado)\s*:?\s*(?:[^:\n]+:\s*)?([\d,.]+)\s*([a-zA-Z%/\d\s³²μ\-]+)?$', line, re.IGNORECASE)
                if match_res:
                    uni = match_res.group(2).strip() if match_res.group(2) else ""
                    
                    vr_lines = []
                    for offset in range(1, 15):
                        if idx + offset < len(filtered_lines):
                            vr_line = filtered_lines[idx + offset]
                            if any(k in vr_line for k in ["RESULTADO", "Resultado", "Material :", "Metodo :", "Data/Hora Coleta:", "Resultado conferido"]):
                                break
                            if any(k in vr_line for k in ["ASSINATURA DIGITAL", "RESPONSÁVEL TÉCNICO:", "A interpretação do resultado"]):
                                break
                            vr_lines.append(vr_line)
                    
                    vr_texto = " ".join(vr_lines).strip()
                    vr_texto = re.sub(r'\s+', ' ', vr_texto)
                    vr_texto = clean_vr_text(vr_texto)
                    
                    sex_key = sex
                    if "PSA" in current_exam.upper():
                        sex_key = "Masculino"
                    elif is_hemogram_component(current_exam):
                        sex_key = sex
                    elif "HOMEM" not in vr_texto.upper() and "MULHER" not in vr_texto.upper() and "MASCULINO" not in vr_texto.upper() and "FEMININO" not in vr_texto.upper() and "AMBOS" not in vr_texto.upper():
                        sex_key = "Ambos"
                        
                    faixa_key = faixa_etaria
                    if is_hemogram_component(current_exam):
                        faixa_key = faixa_etaria
                    elif "ADULTO" not in vr_texto.upper() and "CRIANÇA" not in vr_texto.upper() and "ADOLESCENTE" not in vr_texto.upper() and "RECÉM-NASCIDO" not in vr_texto.upper():
                        faixa_key = "Ambos"
                        
                    key = (current_exam, sex_key, faixa_key, pregnancy)
                    extracted_references[key] = {
                        'Exame': current_exam,
                        'Unidade': uni,
                        'Referencia_Texto_Completo': vr_texto,
                        'Referencia_Paciente_Especifico': parse_patient_specific_vr(vr_texto, age, sex_key, pregnancy),
                        'Sexo': sex_key,
                        'Faixa_Etaria': faixa_key,
                        'Gestante': pregnancy,
                        'Data_Ultima_Atualizacao': data_exame
                    }
                
                elif "COLESTEROL NAO HDL:" in line or "COLESTEROL NÃO HDL:" in line:
                    match_sub = re.search(r'COLESTEROL N[AÃ]O HDL:\s*([\d,.]+)\s*([a-zA-Z%/]+)?', line, re.IGNORECASE)
                    if match_sub:
                        comp = "Colesterol Não-HDL"
                        uni = match_sub.group(2).strip() if match_sub.group(2) else "mg/dL"
                        
                        vr_lines = []
                        for offset in range(1, 15):
                            if idx + offset < len(filtered_lines):
                                vr_line = filtered_lines[idx + offset]
                                if any(k in vr_line for k in ["RESULTADO", "Resultado", "Material :", "Metodo :", "Data/Hora Coleta:", "Resultado conferido"]):
                                    break
                                if any(k in vr_line for k in ["ASSINATURA DIGITAL", "RESPONSÁVEL TÉCNICO:", "A interpretação do resultado"]):
                                    break
                                vr_lines.append(vr_line)
                        
                        vr_texto = " ".join(vr_lines).strip()
                        vr_texto = re.sub(r'\s+', ' ', vr_texto)
                        vr_texto = clean_vr_text(vr_texto)
                        
                        key = (comp, "Ambos", "Ambos", False)
                        extracted_references[key] = {
                            'Exame': comp,
                            'Unidade': uni,
                            'Referencia_Texto_Completo': vr_texto,
                            'Referencia_Paciente_Especifico': parse_patient_specific_vr(vr_texto, age, sex, pregnancy),
                            'Sexo': "Ambos",
                            'Faixa_Etaria': "Ambos",
                            'Gestante': False,
                            'Data_Ultima_Atualizacao': data_exame
                        }
                        
                elif "GLICEMIA MÉDIA ESTIMADA-RESULTADO:" in line or "GLICEMIA MEDIA ESTIMADA-RESULTADO:" in line:
                    comp = "Glicemia Média Estimada"
                    extracted_references[comp] = {
                        'Exame': comp,
                        'Unidade': "mg/dL",
                        'Referencia_Texto_Completo': "Calculada com base na HbA1c",
                        'Referencia_Paciente_Especifico': "Calculada com base na HbA1c",
                        'Sexo': "Ambos",
                        'Faixa_Etaria': "Ambos",
                        'Gestante': False,
                        'Data_Ultima_Atualizacao': data_exame
                    }

    return extracted_references

def save_references(references_dict, output_path="data/exames/exame_references.csv"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    headers = ["Exame", "Unidade", "Referencia_Texto_Completo", "Referencia_Paciente_Especifico", "Sexo", "Faixa_Etaria", "Gestante", "Data_Ultima_Atualizacao"]
    
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for ref in references_dict.values():
            writer.writerow([
                ref['Exame'],
                ref['Unidade'],
                ref['Referencia_Texto_Completo'],
                ref['Referencia_Paciente_Especifico'],
                ref['Sexo'],
                ref['Faixa_Etaria'],
                str(ref['Gestante']).upper(),
                ref['Data_Ultima_Atualizacao']
            ])
            
    logger.success(f"Referências salvas em {output_path} ({len(references_dict)} exames únicos consolidados de múltiplos pacientes)")

def main():
    md_dir = "data/exames/exames_md"
    md_files = glob.glob(os.path.join(md_dir, "*.md"))
    if not md_files:
        logger.error("Nenhum arquivo Markdown encontrado em data/exames/exames_md/")
        sys.exit(1)
        
    def extract_date(filepath):
        filename = os.path.basename(filepath)
        match = re.search(r'(\d{4})-(\d{2})-(\d{2})', filename)
        if match:
            try:
                return datetime.strptime(match.group(0), "%Y-%m-%d")
            except ValueError:
                pass
        return datetime.min

    # Ordena do mais antigo ao mais recente para que as referências mais novas sobrescrevam as antigas
    md_files_sorted = sorted(md_files, key=extract_date)
    
    consolidated_references = {}
    
    for md_path in md_files_sorted:
        logger.info(f"Processando metadados e referências para {os.path.basename(md_path)}")
        patient_refs = extract_references_from_md(md_path)
        
        for key, ref_data in patient_refs.items():
            consolidated_references[key] = ref_data
                    
    save_references({i: v for i, v in enumerate(consolidated_references.values())})

if __name__ == "__main__":
    main()
