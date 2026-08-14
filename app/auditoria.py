import os
import re
import csv
import sys
import random
import time
import unicodedata
import pdfplumber
from datetime import datetime

# Garantir que a pasta raiz do projeto esteja no PATH de imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.data_extractor import sanitize_name_component

try:
    from app.logger import logger
except ImportError:
    from logger import logger

def format_date_to_iso(date_str):
    """
    Converte DD/MM/YYYY para YYYY-MM-DD.
    """
    match = re.search(r'(\d{2})/(\d{2})/(\d{4})', date_str)
    if match:
        day, month, year = match.groups()
        return f"{year}-{month}-{day}"
    return date_str

def get_pdf_search_terms(componente):
    """
    Mapeia o nome do componente no CSV para os termos de busca reais do PDF.
    Retorna uma lista de termos de busca em maiúsculas e sem acentos.
    """
    comp = componente.upper()
    
    # Remover acentos
    comp_norm = unicodedata.normalize('NFD', comp)
    comp_norm = ''.join(c for c in comp_norm if unicodedata.category(c) != 'Mn')
    
    # Dicionário de mapeamento: nome no CSV (normalizado, sem acentos, maiúsculo) -> termos reais no PDF
    # REGRA: sempre que data_extractor.py criar um alias, adicionar aqui o termo original do PDF.
    mappings = {
        # Glicose — no PDF aparece como "GLICOSE JEJUM" (sem "EM")
        "GLICOSE EM JEJUM": ["GLICOSE JEJUM", "GLICOSE"],
        "GLICEMIA MEDIA ESTIMADA": ["GLICEMIA MEDIA ESTIMADA", "MEDIA ESTIMADA"],
        "HEMOGLOBINA GLICADA (HBA1C)": ["HEMOGLOBINA GLICADA", "HBA1C"],
        "INSULINA BASAL": ["INSULINA BASAL", "INSULINA"],
        # Lipídios
        "COLESTEROL TOTAL": ["COLESTEROL TOTAL"],
        "COLESTEROL HDL": ["COLESTEROL HDL", "HDL"],
        "COLESTEROL NAO-HDL": ["COLESTEROL NAO HDL", "NAO HDL", "NAO-HDL"],
        "TRIGLICERIDEOS": ["TRIGLICERIDE", "TRIGLICERIDES", "TRIGLICERID"],
        # Função renal
        "CREATININA SERICA": ["CREATININA"],
        "UREIA": ["UREIA"],
        "RITMO DE FILTRACAO GLOMERULAR": ["FILTRACAO GLOMERULAR", "RITMO DE FILTRACAO"],
        # Eletrolitos
        "SODIO": ["SODIO"],
        "POTASSIO": ["POTASSIO", "POTASSO"],
        # Função hepática
        "TGO (AST)": ["TGO", "OXALACETICA", "AST"],
        "TGP (ALT)": ["TGP", "PIRUVICA", "ALT"],
        "GAMA GT": ["GAMA GT", "GAMA-GT", "GAMA GLUTAMIL"],
        "FOSFATASE ALCALINA": ["FOSFATASE ALCALINA", "FOSFATASE"],
        "CPK (CK TOTAL)": ["CPK", "CREATINOFOSFOQUINASE"],
        # Tireoide
        "T4 LIVRE": ["T4 LIVRE", "T4L"],
        "TSH ULTRA SENSIVEL": ["TSH"],
        # Vitaminas e minerais
        "VITAMINA D (25-HIDROXI)": ["VITAMINA D", "25-HIDROXIVITAMINA", "25 HIDROXIVITAMINA"],
        "25-HIDROXIVITAMINA D": ["25-HIDROXIVITAMINA", "VITAMINA D"],
        # PSA
        "PSA TOTAL ULTRA SENSIVEL": ["PSA TOTAL", "PSA"],
        "PSA TOTAL": ["PSA TOTAL", "PSA"],
        # Ácido úrico
        "ACIDO URICO": ["ACIDO URICO", "URICO"],
    }
    
    # Se for componente de Hemograma ou Leucograma
    if "HEMOGRAMA - " in comp_norm:
        term = comp_norm.replace("HEMOGRAMA - ", "")
        return [term]
    if "LEUCOGRAMA - " in comp_norm:
        term = comp_norm.replace("LEUCOGRAMA - ", "")
        term = term.replace(" (ABSOLUTO)", "").replace(" (%)", "")
        if "BASTOES" in term:
            return ["BASTOES", "BASTONETES"]
        if "SEGMENTADOS" in term:
            return ["SEGMENTADOS"]
        return [term]
        
    for key, terms in mappings.items():
        if key in comp_norm or comp_norm in key:
            return terms
            
    # Fallback: remove acentos e retorna a última parte
    fallback_term = comp_norm.split(" - ")[-1]
    return [fallback_term]

# ---------------------------------------------------------------------------
# Cache global de conteúdo de PDFs normalizados.
# Cada PDF é aberto UMA ÚNICA VEZ por auditoria e seu conteúdo fica em memória,
# evitando centenas de chamadas redundantes a pdfplumber.open().
# ---------------------------------------------------------------------------
_pdf_cache = {}

def _load_pdf_pages(pdf_path):
    """
    Carrega e normaliza todas as páginas de um PDF uma única vez.
    Retorna uma lista de dicts {'text': str, 'lines': list[str]} por página,
    ou None se o arquivo não existir ou houver erro de leitura.
    O resultado é cacheado em _pdf_cache para reutilização.
    """
    if pdf_path in _pdf_cache:
        return _pdf_cache[pdf_path]

    if not os.path.exists(pdf_path):
        _pdf_cache[pdf_path] = None
        return None

    pages_data = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if not text:
                    pages_data.append({"text": "", "lines": []})
                    continue
                norm_text = unicodedata.normalize('NFD', text)
                norm_text = ''.join(c for c in norm_text if unicodedata.category(c) != 'Mn').upper()
                lines = norm_text.split('\n')
                pages_data.append({"text": norm_text, "lines": lines})
    except Exception as e:
        logger.error(f"Erro ao carregar PDF para cache: {pdf_path} — {e}")
        _pdf_cache[pdf_path] = None
        return None

    _pdf_cache[pdf_path] = pages_data
    return pages_data


def verify_value_in_pdf(pdf_path, componente, resultado, unidade):
    """
    Verifica se o componente e o resultado existem no PDF bruto.
    Usa cache interno (_pdf_cache) para evitar reabrir o mesmo PDF múltiplas vezes.

    Estratégia de busca em 2 níveis:
      1. Busca ESTRITA: termo + valor na mesma linha (alta confiança)
      2. Busca CONTEXTUAL: termo + valor na mesma página (média confiança, sinalizada no relatório)

    Retorna (status, message):
      - status=True   → valor validado com sucesso
      - status=False   → valor NÃO encontrado no PDF (falha de validação real)
      - status=None    → PDF não disponível (não é falha de dados)
    """
    pages_data = _load_pdf_pages(pdf_path)

    if pages_data is None:
        return None, f"PDF não disponível: {os.path.basename(pdf_path)}"

    search_terms = get_pdf_search_terms(componente)

    resultado_str_comma = str(resultado).replace('.', ',')
    resultado_str_dot = str(resultado)
    val_clean_str = str(resultado)[:-2] if str(resultado).endswith(".0") else None

    def val_in(text):
        return (resultado_str_comma in text) or (resultado_str_dot in text) or (val_clean_str and val_clean_str in text)

    for page_idx, page_data in enumerate(pages_data):
        if not page_data["text"]:
            continue

        for search_term in search_terms:
            # Nível 1 — busca ESTRITA: mesmo termo e valor na mesma linha
            for line in page_data["lines"]:
                if search_term in line and val_in(line):
                    return True, f"[Estrita] pág {page_idx+1}: '{line.strip()}'"

        for search_term in search_terms:
            # Nível 2 — busca CONTEXTUAL: termo existe na página e valor existe na página
            # Mais suscetível a falso positivo — sinalizado no relatório
            if search_term in page_data["text"] and val_in(page_data["text"]):
                return True, f"[Contextual] pág {page_idx+1} — termo '{search_term}' e valor '{resultado_str_comma}' presentes (verificar manualmente se coincidência)"

    return False, f"Termos {search_terms} e/ou valor '{resultado_str_comma}' não correlacionados no PDF."

def run_audit():
    global _pdf_cache
    _pdf_cache = {}  # Limpar cache no início de cada auditoria

    import configparser
    t_start = time.time()

    # 1. Carregar sample percentage de config.ini se existir
    sample_pct = 0.20
    config_path = "config.ini"
    if os.path.exists(config_path):
        try:
            config = configparser.ConfigParser()
            config.read(config_path, encoding='utf-8')
            if 'Config' in config:
                sample_pct = config['Config'].getfloat('AUDIT_SAMPLE_PERCENTAGE', 0.20)
        except Exception as e:
            logger.warning(f"Erro ao ler config.ini na auditoria: {e}")

    logger.info(f"Iniciando auditoria de qualidade (amostra de {sample_pct*100:.1f}% contra PDF bruto)...")
    results_dir = os.path.join("data", "exames", "results")
    pdf_dir = os.path.join("data", "exames")
    report_dir = os.path.join("data", "exames", "auditoria")

    os.makedirs(report_dir, exist_ok=True)

    if not os.path.exists(results_dir):
        logger.error(f"Diretório de resultados não encontrado: {results_dir}")
        return

    csv_files = [f for f in os.listdir(results_dir) if f.startswith("results-") and f.endswith(".csv")]
    if not csv_files:
        logger.warning("Nenhum CSV de resultados encontrado para auditar.")
        return

    now = datetime.now()
    audit_timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
    file_timestamp = now.strftime("%Y%m%d_%H%M%S")

    for f in csv_files:
        csv_path = os.path.join(results_dir, f)
        rows = []
        with open(csv_path, 'r', encoding='utf-8') as csv_file:
            reader = csv.reader(csv_file)
            headers = next(reader, None)
            for row in reader:
                if row:
                    rows.append(row)

        total_rows = len(rows)
        if total_rows == 0:
            continue

        paciente = rows[0][1]
        paciente_san = sanitize_name_component(paciente)

        # Amostra baseada no config.ini
        sample_size = max(1, int(total_rows * sample_pct))
        sample_rows = random.sample(rows, sample_size)

        successes = 0
        failures = 0
        missing_pdf_count = 0
        audit_details = []      # Registros auditáveis (PDF encontrado)
        missing_details = []    # Registros com PDF não disponível

        for s_row in sample_rows:
            data_exame = s_row[0]
            medico = s_row[2]
            componente = s_row[4]
            resultado_csv = s_row[5]
            unidade_csv = s_row[6]

            # Reconstruir nome do arquivo PDF
            medico_san = sanitize_name_component(medico)
            data_iso = format_date_to_iso(data_exame)

            pdf_filename = f"paciente_{paciente_san}-medico_{medico_san}-{data_iso}.pdf"
            pdf_path = os.path.join(pdf_dir, pdf_filename)

            # Executa a verificação diretamente contra o PDF (com cache)
            is_valid, message = verify_value_in_pdf(pdf_path, componente, resultado_csv, unidade_csv)

            detail_line = f"| {componente} | {data_exame} | {resultado_csv} {unidade_csv} | {message} |"

            if is_valid is None:
                # PDF não disponível — categoria separada, NÃO conta como falha
                missing_pdf_count += 1
                missing_details.append(f"{detail_line} ⚠️ SEM PDF |")
            elif is_valid:
                successes += 1
                audit_details.append(f"{detail_line} ✅ OK |")
            else:
                failures += 1
                audit_details.append(f"{detail_line} ❌ FALHA |")

        # Taxa de sucesso calculada SOMENTE sobre registros auditáveis (PDF disponível)
        auditable_count = successes + failures
        success_rate = (successes / auditable_count * 100) if auditable_count > 0 else 0

        # Gerar o relatório específico para este paciente
        report_filename = f"auditoria_valores_{paciente_san}_{file_timestamp}.md"
        report_path = os.path.join(report_dir, report_filename)

        report_content = [
            f"# Relatório de Auditoria de Qualidade dos Dados (Validação Cruzada PDF Original)",
            f"**Data de Execução:** {audit_timestamp}",
            f"**Arquivo de Dados Auditado:** `{f}`\n",
            f"Este relatório apresenta a verificação amostral de {sample_pct*100:.1f}% dos dados estruturados no CSV confrontando diretamente o texto extraído do **PDF original** (sem usar o Markdown intermediário).\n",
            "## Resumo da Auditoria",
            f"* **Total de registros no CSV:** {total_rows}",
            f"* **Tamanho da amostra ({sample_pct*100:.1f}%):** {sample_size}",
            f"* **PDFs não disponíveis:** {missing_pdf_count} (registros sem PDF correspondente — excluídos da taxa)",
            f"* **Registros auditáveis:** {auditable_count}",
            f"* **Amostras com sucesso:** {successes}",
            f"* **Amostras com falha:** {failures}",
            f"* **Taxa de Sucesso (sobre auditáveis):** {success_rate:.1f}%\n",
        ]

        # Seção de registros auditados
        report_content += [
            "## Detalhes das Amostras Auditadas",
            "",
            "| Componente | Data | Resultado Esperado (CSV) | Mensagem de Validação do PDF | Status |",
            "| --- | --- | --- | --- | --- |"
        ] + audit_details

        # Seção separada para PDFs não disponíveis (se houver)
        if missing_details:
            report_content += [
                "",
                f"## ⚠️ Registros com PDF Não Disponível ({missing_pdf_count})",
                "",
                "Estes registros existem no CSV mas o PDF original correspondente não foi encontrado na pasta `data/exames/`.",
                "Possíveis causas: PDF ainda não baixado pelo crawler, nome do arquivo divergente, ou exame atribuído ao paciente errado pelo extrator.\n",
                "| Componente | Data | Resultado (CSV) | Mensagem | Status |",
                "| --- | --- | --- | --- | --- |"
            ] + missing_details

        with open(report_path, 'w', encoding='utf-8') as f_rep:
            f_rep.write('\n'.join(report_content))

        success_icon = "✅" if success_rate >= 95 else ("⚠️" if success_rate >= 80 else "❌")
        missing_note = f" | ⚠️ {missing_pdf_count} sem PDF" if missing_pdf_count else ""
        logger.success(f"{success_icon} Auditoria de '{paciente}' | {successes}/{auditable_count} OK ({success_rate:.1f}%){missing_note} | Relatório: {report_filename}")

    _pdf_cache = {}  # Liberar memória ao final
    elapsed = time.time() - t_start
    logger.success(f"Auditoria completa em {elapsed:.1f}s")

if __name__ == "__main__":
    run_audit()
