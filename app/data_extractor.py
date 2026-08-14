import os
import re
import csv
import shutil
import time
import unicodedata

try:
    from app.logger import logger
except ImportError:
    from logger import logger

def clean_txt(text):
    return text.strip() if text else ""

def sanitize_name_component(name):
    """
    Normaliza o nome para minúsculas, remove acentos, mantém apenas primeiro e último nome,
    e junta-os com underline.
    """
    name = unicodedata.normalize('NFD', name)
    name = ''.join(c for c in name if unicodedata.category(c) != 'Mn')
    name = name.lower()
    
    parts = [p.strip() for p in name.split() if p.strip()]
    if not parts:
        return "sem_nome"
    if len(parts) == 1:
        return re.sub(r'[^a-z0-9]', '', parts[0])
        
    first = re.sub(r'[^a-z0-9]', '', parts[0])
    last = re.sub(r'[^a-z0-9]', '', parts[-1])
    return f"{first}_{last}"


def parse_md_to_rows(md_path):
    rows = []
    
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extrair Metadados Gerais do Arquivo
    paciente_match = re.search(r'CLIENTE:\s*([^\n\d]+)', content)
    paciente = paciente_match.group(1).strip() if paciente_match else "PACIENTE NAO IDENTIFICADO"
    # Limpar DN (Data de Nascimento) do nome do paciente
    if "DN:" in paciente:
        paciente = paciente.split("DN:")[0].strip()
    
    medico_match = re.search(r'NOME MÉDICO:\s*([^\n]+)', content)
    medico = medico_match.group(1).strip() if medico_match else ""
    if "CRM" in medico:
        medico = medico.split("CRM")[0].strip()
        
    data_match = re.search(r'DATA ENTRADA:\s*(\d{2}/\d{2}/\d{4})', content)
    data_exame = data_match.group(1) if data_match else ""
    
    lab_match = re.search(r'\*\*Laboratório:\*\*\s*([^\n]+)', content)
    laboratorio = lab_match.group(1).strip() if lab_match else "Pretti"

    # Dividir por páginas para capturar exames específicos
    paginas = content.split('## Página ')
    
    for pag in paginas[1:]:
        lines = [line.strip() for line in pag.split('\n') if line.strip()]
        if not lines:
            continue
            
        # Filtrar linhas de cabeçalho padrão para encontrar o título real do exame
        header_patterns = ['CLIENTE:', 'NOME MÉDICO:', 'DATA ENTRADA:', 'CONVÊNIO:', 'CPF:', 'RG:', 'NOME SOCIAL:', 'DN:']
        
        filtered_lines = []
        for line in lines:
            if not any(pat in line for pat in header_patterns) and not line.startswith('##') and not line.startswith('---'):
                filtered_lines.append(line)
                
        if not filtered_lines:
            continue
            
        # Título do exame na página
        exame_titulo = filtered_lines[0].strip()
        
        # Ignorar se o título for apenas um número residual da paginação ou ruído
        if re.match(r'^\d+$', exame_titulo):
            # Se for só um número, tenta a próxima linha
            if len(filtered_lines) > 1:
                exame_titulo = filtered_lines[1].strip()
            else:
                continue

        # Seção do Hemograma/Leucograma
        if "HEMOGRAMA COMPLETO" in exame_titulo or "LEUCOGRAMA" in exame_titulo:
            for line in filtered_lines:
                # 1. Hemácias, Hemoglobina, Hematócrito, V.C.M, H.C.M, C.H.C.M, R.D.W
                match_hemo = re.search(r'^(Hemacias em milhoes|Hemoglobina|Hematocrito|V\.C\.M|H\.C\.M|C\.H\.C\.M|R\.D\.W)\s+([\d,.]+)\s*([a-zA-Z%/³]+)?\s+([\d,.\s\-a-zA-Záéíóú]+)?$', line, re.IGNORECASE)
                if match_hemo:
                    comp = match_hemo.group(1).strip()
                    val = match_hemo.group(2).strip()
                    uni = match_hemo.group(3).strip() if match_hemo.group(3) else ""
                    ref = match_hemo.group(4).strip() if match_hemo.group(4) else ""
                    rows.append([data_exame, paciente, medico, laboratorio, f"Hemograma - {comp}", val, uni, ref])
                    continue
                    
                # 2. Leucócitos e Plaquetas
                match_leuco = re.search(r'^(Leucocitos|Plaquetas)\s+([\d.]+)\s+([\d.\s\-–]+)$', line, re.IGNORECASE)
                if match_leuco:
                    comp = match_leuco.group(1).strip()
                    val = match_leuco.group(2).strip()
                    ref = match_leuco.group(3).strip()
                    uni = "/mm³"
                    rows.append([data_exame, paciente, medico, laboratorio, comp, val, uni, ref])
                    continue
                    
                # 3. Componentes do Leucograma
                match_comp = re.search(r'^(Blastos|Promielocitos|Mielocitos|Metamielocitos|N\.\s*Bastoes|N\.\s*Segmentados|Eosinofilos|Basãofilos|Monocitos|Linfocitos)\s+([\d,.]+)\s+([\d.]+)\s+([\d.\s\-a-zA-Zé]+)$', line, re.IGNORECASE)
                if match_comp:
                    comp = match_comp.group(1).strip()
                    val_pct = match_comp.group(2).strip()
                    val_abs = match_comp.group(3).strip()
                    ref = match_comp.group(4).strip()
                    rows.append([data_exame, paciente, medico, laboratorio, f"Leucograma - {comp} (%)", val_pct, "%", ""])
                    rows.append([data_exame, paciente, medico, laboratorio, f"Leucograma - {comp} (Absoluto)", val_abs, "/mm³", ref])
            
        else:
            # Outros exames da página
            # Como em uma mesma página podemos ter múltiplos exames (ex: Sódio e Potássio na página 8), vamos processar linha por linha
            
            # Vamos segmentar a página por blocos de exames se houver mais de um título em maiúsculo
            # Ou simplesmente usar uma varredura sequencial para capturar múltiplos resultados e referências.
            current_exam = exame_titulo
            
            # Varre todas as linhas da página
            for idx, line in enumerate(filtered_lines):
                # Títulos de exames costumam ser apenas letras maiúsculas, hífens e podem conter números (como 25-HIDROXIVITAMINA D)
                if re.match(r'^[0-9A-ZÁÉÍÓÚÂÊÔÃÕÇ\s\(\)/\-]+$', line) and len(line) > 3 and not re.match(r'^\d+$', line) and not any(k in line for k in ["RESULTADO", "VALOR", "MÉTODO", "MATERIAL", "FONTE", "CRBM", "CRM", "ASSINATURA", "RESPONSÁVEL"]):
                    current_exam = line.strip()
                
                # Detecta resultado
                # Ex: RESULTADO 1,01 mg/dL ou RESULTADO: 112 mg/dL ou Resultado 86 mL/min ou RESULTADO: HEMOGLOBINA GLICADA (A1C): 6,5 %
                match_res = re.search(r'^(?:RESULTADO|Resultado)\s*:?\s*(?:[^:\n]+:\s*)?([\d,.]+)\s*([a-zA-Z%/\d\s³²μ\-]+)?$', line, re.IGNORECASE)
                if match_res:
                    val = match_res.group(1).strip()
                    uni = match_res.group(2).strip() if match_res.group(2) else ""
                    
                    # Tentar achar a referência nas linhas adjacentes
                    ref = ""
                    for offset in range(1, 6):
                        if idx + offset < len(filtered_lines):
                            ref_line = filtered_lines[idx + offset]
                            if any(k in ref_line for k in ["Valor de", "Referência", "VR", "Vr:", "Vr "]):
                                ref = ref_line.strip()
                                break
                                
                    rows.append([data_exame, paciente, medico, laboratorio, examen_alias(current_exam), val, uni, ref])
                
                # Trata sub-itens específicos como "COLESTEROL NÃO-HDL" ou "GLICEMIA MÉDIA ESTIMADA"
                elif "COLESTEROL NAO HDL:" in line or "COLESTEROL NÃO HDL:" in line:
                    match_sub = re.search(r'COLESTEROL N[AÃ]O HDL:\s*([\d,.]+)\s*([a-zA-Z%/]+)?', line, re.IGNORECASE)
                    if match_sub:
                        rows.append([data_exame, paciente, medico, laboratorio, "Colesterol Não-HDL", match_sub.group(1).strip(), match_sub.group(2).strip() if match_sub.group(2) else "mg/dL", ""])
                elif "GLICEMIA MÉDIA ESTIMADA-RESULTADO:" in line or "GLICEMIA MEDIA ESTIMADA-RESULTADO:" in line:
                    match_sub = re.search(r'RESULTADO:\s*([\d,.]+)\s*([a-zA-Z%/]+)?', line, re.IGNORECASE)
                    if match_sub:
                        rows.append([data_exame, paciente, medico, laboratorio, "Glicemia Média Estimada", match_sub.group(1).strip(), match_sub.group(2).strip() if match_sub.group(2) else "mg/dL", ""])

    return rows

def examen_alias(titulo):
    titulo = titulo.upper().strip()
    aliases = {
        "GLICOSE JEJUM": "Glicose em Jejum",
        "COLESTEROL TOTAL": "Colesterol Total",
        "COLESTEROL HDL": "Colesterol HDL",
        "TRIGLICERIDES": "Triglicerídeos",
        "ACIDO URICO": "Ácido Úrico",
        "ÁCIDO ÚRICO": "Ácido Úrico",
        "HEMOGLOBINA GLICADA": "Hemoglobina Glicada (HbA1c)",
        "HEMOGLOBINA GLICADA (HBA1C)": "Hemoglobina Glicada (HbA1c)",
        "TESTOSTERONA TOTAL": "Testosterona Total",
        "TSH ULTRA SENSÍVEL": "TSH Ultra Sensível",
        "TSH ULTRA SENSIVEL": "TSH Ultra Sensível",
        "CREATININA SERICA": "Creatinina Sérica",
        "CREATININA SÉRICA": "Creatinina Sérica",
        "RITMO DE FILTRAÇÃO GLOMERULAR": "Ritmo de Filtração Glomerular",
        "SODIO": "Sódio",
        "SÓDIO": "Sódio",
        "POTASSIO": "Potássio",
        "POTÁSSIO": "Potássio",
        "TRANSAMINASE OXALACÉTICA (TGO/AST)": "TGO (AST)",
        "TRANSAMINASE OXALACETICA (TGO/AST)": "TGO (AST)",
        "TRANSAMINASE PIRÚVICA (TGP/ALT)": "TGP (ALT)",
        "TRANSAMINASE PIRUVICA (TGP/ALT)": "TGP (ALT)",
        "GAMA GLUTAMIL TRANSFERASE (GAMA GT)": "Gama GT",
        "FOSFATASE ALCALINA": "Fosfatase Alcalina",
        "CREATINOFOSFOQUINASE (CPK/CK)": "CPK (CK Total)",
        "VITAMINA D - 25 HIDROXI": "Vitamina D (25-Hidroxi)",
        "VITAMINA D 25 HIDROXI": "Vitamina D (25-Hidroxi)",
        "PSA TOTAL": "PSA Total"
    }
    return aliases.get(titulo, titulo.title())

def main():
    t_start = time.time()
    md_dir = "data/exames/exames_md"
    results_dir = os.path.join("data", "exames", "results")
    os.makedirs(results_dir, exist_ok=True)
    logger.info("Iniciando extração de dados dos Markdowns...")
    
    headers = ["Data Exame", "Paciente", "Médico", "Laboratório", "Exame/Componente", "Resultado", "Unidade", "Referência"]
    all_rows = []
    
    if os.path.exists(md_dir):
        for f in os.listdir(md_dir):
            if f.endswith(".md"):
                md_path = os.path.join(md_dir, f)
                all_rows.extend(parse_md_to_rows(md_path))
            
    # Dedup de linhas idênticas se houver
    unique_rows = []
    seen = set()
    for row in all_rows:
        # Cria uma tupla identificadora (Data, Paciente, Exame, Resultado) para evitar duplicatas acidentais
        key = (row[0], row[1], row[4], row[5])
        if key not in seen:
            seen.add(key)
            unique_rows.append(row)
            
    # Agrupar linhas por paciente para gerar arquivos individuais
    rows_by_patient = {}
    for row in unique_rows:
        paciente = row[1]
        if paciente not in rows_by_patient:
            rows_by_patient[paciente] = []
        rows_by_patient[paciente].append(row)
        
    for paciente, p_rows in rows_by_patient.items():
        paciente_sanitizado = sanitize_name_component(paciente)
        csv_filename = f"results-{paciente_sanitizado}.csv"
        csv_path = os.path.join(results_dir, csv_filename)
        bak_path = csv_path + ".bak"
        
        # Backup automático antes de reescrever
        if os.path.exists(csv_path):
            shutil.copy2(csv_path, bak_path)
            
        with open(csv_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(p_rows)
            
        logger.success(f"CSV gerado: {csv_filename} ({len(p_rows)} registros)")
    
    elapsed = time.time() - t_start
    logger.success(f"Extração concluída em {elapsed:.1f}s. Total de pacientes: {len(rows_by_patient)}")

if __name__ == "__main__":
    main()
