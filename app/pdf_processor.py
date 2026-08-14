import os
import pdfplumber
import re
import time

try:
    from app.logger import logger
except ImportError:
    from logger import logger

def clean_txt(text):
    if not text:
        return ""
    # Corrige alguns caracteres corrompidos comuns devido a encoding do PDF
    replacements = {
        'MDICO': 'MÉDICO',
        'Mtodo': 'Método',
        'referncia': 'referência',
        'Referncia': 'Referência',
        'Desejveis': 'Desejáveis',
        'Crianas': 'Crianças',
        'Normatizao': 'Normatização',
        'Determi': 'Determinação',
        'LQUIDA': 'LÍQUIDA',
        'CONVNIO': 'CONVÊNIO',
        'REQUISIO': 'REQUISIÇÃO',
        'SENSVEL': 'SENSÍVEL',
        'RESPONSVEL': 'RESPONSÁVEL',
        'TCNICO': 'TÉCNICO',
        'interpretao': 'interpretação',
        'diagnstica': 'diagnóstica',
        'so': 'são',
        'mdicos': 'médicos',
        'anlise': 'análise',
        'clnicos': 'clínicos'
    }
    for bad, good in replacements.items():
        if bad in ['so', 'mdicos', 'clnicos']:
            text = re.sub(rf'\b{bad}\b', good, text)
        else:
            text = text.replace(bad, good)
    return text

def convert_pdf_to_md(pdf_path, md_path):
    logger.debug(f"Convertendo {os.path.basename(pdf_path)} -> MD...")
    with pdfplumber.open(pdf_path) as pdf:
        md_content = []
        # Adiciona metadados baseados no nome do arquivo e primeira página
        filename = os.path.basename(pdf_path)
        md_content.append(f"# Exame Clínico: {filename}\n")
        
        # Tenta identificar o Laboratório (Dr Renato Pretti = Pretti)
        laboratorio = "Pretti" # Inferido pelo Responsável Técnico Renato Pretti
        md_content.append(f"**Laboratório:** {laboratorio}\n")
        
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if text:
                text = clean_txt(text)
                md_content.append(f"## Página {i+1}\n")
                md_content.append(text)
                md_content.append("\n---\n")
                
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(md_content))

def main():
    pdf_dir = "data/exames"
    md_dir = "data/exames/exames_md"
    os.makedirs(md_dir, exist_ok=True)
    
    t_start = time.time()
    converted_count = 0
    for f in os.listdir(pdf_dir):
        if f.endswith(".pdf"):
            pdf_path = os.path.join(pdf_dir, f)
            md_filename = f.replace(".pdf", ".md")
            md_path = os.path.join(md_dir, md_filename)
            
            # Pula se o arquivo MD já existe
            if os.path.exists(md_path):
                continue
                
            convert_pdf_to_md(pdf_path, md_path)
            converted_count += 1
            
    elapsed = time.time() - t_start
    if converted_count > 0:
        logger.success(f"Conversão concluída: {converted_count} PDFs convertidos em {elapsed:.1f}s")
    else:
        logger.info(f"Nenhum novo PDF para converter. ({elapsed:.1f}s)")

if __name__ == "__main__":
    main()
