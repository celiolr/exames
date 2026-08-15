import os
import re
import csv
import sys
import unicodedata
import pdfplumber
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from app.logger import logger
except ImportError:
    from logger import logger

try:
    from app.data_extractor_reference import get_most_recent_md_by_patient, load_patient_metadata, calculate_age_at_exam
    from app.auditoria import get_pdf_search_terms, sanitize_name_component
except ImportError:
    from data_extractor_reference import get_most_recent_md_by_patient, load_patient_metadata, calculate_age_at_exam
    from auditoria import get_pdf_search_terms, sanitize_name_component

def get_pdf_path_from_md(md_path):
    filename_md = os.path.basename(md_path)
    filename_pdf = filename_md.replace(".md", ".pdf")
    return os.path.join("data", "exames", filename_pdf)

def normalize_unit(unit):
    if not unit:
        return ""
    unit = unit.upper().strip()
    unit = unit.replace("³", "3").replace("²", "2")
    unit = unicodedata.normalize('NFD', unit)
    return "".join(c for c in unit if unicodedata.category(c) != 'Mn')

def clean_for_comparison(text):
    if not text:
        return ""
    text = unicodedata.normalize('NFD', text)
    text = "".join(c for c in text if unicodedata.category(c) != 'Mn').upper()
    text = text.replace("³", "3").replace("²", "2")
    text = re.sub(r'[^A-Z0-9/]', '', text)
    return text

def verify_references_in_pdf(pdf_path, csv_path="data/exames/exame_references.csv"):
    logger.info(f"Iniciando auditoria de referências contra o PDF original: {os.path.basename(pdf_path)}")
    
    if not os.path.exists(pdf_path):
        logger.error(f"PDF não encontrado: {pdf_path}")
        return False, []
        
    if not os.path.exists(csv_path):
        logger.error(f"CSV de referências não encontrado: {csv_path}")
        return False, []

    # Abrir PDF e normalizar
    pdf_pages = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            # Pega o cliente no laudo para cruzar config
            first_page_text = pdf.pages[0].extract_text() or ""
            paciente_match = re.search(r'CLIENTE:\s*([^\n\d]+)', first_page_text)
            paciente = paciente_match.group(1).strip() if paciente_match else ""
            if "DN:" in paciente:
                paciente = paciente.split("DN:")[0].strip()
                
            data_match = re.search(r'DATA ENTRADA:\s*(\d{2}/\d{2}/\d{4})', first_page_text)
            data_exame = data_match.group(1) if data_match else ""
            
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    pdf_pages.append(clean_for_comparison(text))
                else:
                    pdf_pages.append("")
    except Exception as e:
        logger.error(f"Erro ao abrir PDF: {e}")
        return False, []

    # Carrega os dados clínicos desse paciente logado no config
    patient_metadata = load_patient_metadata(paciente)
    sex = "Ambos"
    faixa_etaria = "Ambos"
    pregnancy = False
    
    if patient_metadata:
        birth_date = patient_metadata.get("data_nascimento")
        sex = patient_metadata.get("sexo", "Ambos")
        pregnancy = patient_metadata.get("gravidez", False)
        if birth_date and data_exame:
            age = calculate_age_at_exam(birth_date, data_exame)
            faixa_etaria = "Adulto" if age > 20 else "Infantil"

    # Encontra os exames que de fato constam no laudo do paciente sendo auditado.
    # Evita falsas falhas para exames exclusivos de sexo (como PSA na Ruth).
    available_exams_in_pdf = set()
    for page_text in pdf_pages:
        # Varre os exames e vê se o nome ou alias está na página
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                if not row:
                    continue
                exame = row[0]
                search_terms = [clean_for_comparison(term) for term in get_pdf_search_terms(exame)]
                if any(term in page_text for term in search_terms):
                    available_exams_in_pdf.add(exame)

    audit_results = []
    successes = 0
    failures = 0

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        headers = next(reader, None)
        
        for row in reader:
            if not row:
                continue
            exame, unidade, ref_completa, ref_paciente, ref_sex, ref_faixa, ref_preg, data_ref = row
            
            # Pula exames que não constam neste laudo sendo auditado (evita validar PSA na Ruth)
            if exame not in available_exams_in_pdf:
                continue

            # Filtra estritamente pelo sexo da linha de referência e do paciente.
            # Se for específico para homens, e o paciente for mulher, pula.
            if ref_sex != "Ambos" and ref_sex.upper() != sex.upper():
                continue
            if ref_faixa != "Ambos" and ref_faixa.upper() != faixa_etaria.upper():
                continue
            if ref_preg.upper() != str(pregnancy).upper():
                continue
                
            # Se for um valor calculado
            if "CALCULADA COM BASE" in ref_completa.upper() or "VER VALORES DESEJAVEIS" in ref_completa.upper():
                audit_results.append({
                    'Exame': exame,
                    'Unidade': unidade,
                    'Status': 'CALCULADO',
                    'Mensagem': 'Valor ou texto de referência gerado por fórmula (não auditável diretamente no PDF)'
                })
                successes += 1
                continue

            search_terms = [clean_for_comparison(term) for term in get_pdf_search_terms(exame)]
            uni_clean = clean_for_comparison(unidade)
            
            found = False
            message = ""
            
            vr_search_chunk = ref_completa[:25].strip()
            vr_search_clean = clean_for_comparison(vr_search_chunk)

            for page_idx, page_clean_text in enumerate(pdf_pages):
                if any(term in page_clean_text for term in search_terms):
                    if (not uni_clean or uni_clean in page_clean_text) and (not vr_search_clean or vr_search_clean in page_clean_text):
                        found = True
                        message = f"Validado na página {page_idx+1}"
                        break
                    else:
                        message = f"Exame localizado na página {page_idx+1}, mas unidade '{uni_clean}' ou texto de VR '{vr_search_clean}' não coincidem."

            if found:
                successes += 1
                audit_results.append({
                    'Exame': exame,
                    'Unidade': unidade,
                    'Status': 'OK',
                    'Mensagem': message
                })
            else:
                failures += 1
                audit_results.append({
                    'Exame': exame,
                    'Unidade': unidade,
                    'Status': 'FALHA',
                    'Mensagem': message or f"Exame/Componente ({search_terms}) não encontrado no PDF original."
                })

    total = successes + failures
    filename = os.path.basename(pdf_path)
    rate = (successes / total * 100) if total > 0 else 0
    logger.success(f"Auditoria de referências concluída para {filename}: {successes}/{total} OK ({rate:.1f}% de sucesso)")
    
    return rate >= 90.0, audit_results

def generate_audit_report(results, pdf_path):
    report_dir = "data/exames/auditoria"
    os.makedirs(report_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.basename(pdf_path)
    report_filename = f"auditoria_referencias_{filename.replace('.pdf', '')}_{timestamp}.md"
    report_path = os.path.join(report_dir, report_filename)
    
    successes = sum(1 for r in results if r['Status'] in ['OK', 'CALCULADO'])
    failures = sum(1 for r in results if r['Status'] == 'FALHA')
    total = len(results)
    rate = (successes / total * 100) if total > 0 else 0
    
    report_content = [
        f"# Relatório de Auditoria de Valores de Referência",
        f"**Data de Execução:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**PDF Analisado:** `{filename}`\n",
        f"## Resumo",
        f"* **Total de Referências Auditadas:** {total}",
        f"* **Sucessos (OK/Calculados):** {successes}",
        f"* **Falhas:** {failures}",
        f"* **Taxa de Integridade:** {rate:.1f}%\n",
        f"## Detalhamento das Referências",
        f"| Exame | Unidade | Status | Detalhes |",
        f"| --- | --- | --- | --- |"
    ]
    
    for r in results:
        status_icon = "✅" if r['Status'] == 'OK' else ("ℹ️" if r['Status'] == 'CALCULADO' else "❌")
        report_content.append(f"| {r['Exame']} | {r['Unidade']} | {status_icon} {r['Status']} | {r['Mensagem']} |")
        
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(report_content))
        
    logger.success(f"Relatório de auditoria de referências gerado: {report_filename}")

def main():
    recent_mds = get_most_recent_md_by_patient()
    if not recent_mds:
        logger.error("Nenhum arquivo Markdown/Exame recente encontrado para auditar.")
        sys.exit(1)
        
    for md_path in recent_mds:
        pdf_path = get_pdf_path_from_md(md_path)
        success, results = verify_references_in_pdf(pdf_path)
        if results:
            generate_audit_report(results, pdf_path)

if __name__ == "__main__":
    main()
