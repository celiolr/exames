import os
import re
import time
import unicodedata
from dotenv import load_dotenv
from scrapling.fetchers import DynamicSession

try:
    from app.logger import logger
except ImportError:
    from logger import logger

def sanitize_filename(text):
    """
    Remove acentos, converte para minúsculas e substitui caracteres especiais por hífens.
    """
    text = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    text = text.lower()
    text = re.sub(r'[^a-z0-9_-]', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')

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


def format_date_to_iso(date_str):
    """
    Converte uma data no formato "DD/MM/YYYY - HH:MM:SS" ou "DD/MM/YYYY" para "YYYY-MM-DD".
    """
    match = re.search(r'(\d{2})/(\d{2})/(\d{4})', date_str)
    if match:
        day, month, year = match.groups()
        return f"{year}-{month}-{day}"
    return sanitize_filename(date_str)

def load_config_data():
    """
    Carrega as configurações (limite, pacientes e laboratórios) do config.ini se existir.
    Caso contrário, carrega do .env (fallback).
    Retorna (limit, patients, labs)
    """
    import json
    import configparser
    from dotenv import load_dotenv
    
    config_path = "config.ini"
    limit = 2
    patients = []
    labs = {}
    
    if os.path.exists(config_path):
        config = configparser.ConfigParser()
        config.read(config_path, encoding='utf-8')
        
        # 1. Carregar Configs gerais
        if 'Config' in config:
            limit = config['Config'].getint('LIMIT_EXAM_DOWNLOAD', 2)
            
        # 2. Carregar Laboratórios
        if 'Laboratorios' in config:
            for key, value in config['Laboratorios'].items():
                labs[key.lower()] = value
            
        # 3. Carregar Pacientes da subseção [Pacientes]
        if 'Pacientes' in config:
            for idx, (key, value) in enumerate(config['Pacientes'].items(), 1):
                try:
                    patient_data = json.loads(value)
                    patients.append({
                        'idx': idx,
                        'nome': patient_data.get("nome"),
                        'user': patient_data.get("user"),
                        'pass': patient_data.get("pass"),
                        'role': patient_data.get("role", "user"),
                        'lab': patient_data.get("lab", "pretti")
                    })
                except Exception as e:
                    logger.warning(f"Falha ao decodificar JSON do paciente '{key}' no config.ini: {e}")
                    
        if patients:
            if not labs:
                labs = {
                    "pretti": "https://pretti.shiftcloud.com.br/shift/lis/pretti/elis/s01.iu.web.Login.cls?config=UNICO&sigla="
                }
            return limit, patients, labs

    # Fallback para o formato do .env
    load_dotenv()
    limit_str = os.getenv("LIMIT_EXAM_DOWNLOAD", "2")
    try:
        limit = int(limit_str)
    except ValueError:
        limit = 2
        
    labs = {
        "pretti": "https://pretti.shiftcloud.com.br/shift/lis/pretti/elis/s01.iu.web.Login.cls?config=UNICO&sigla="
    }
    
    i = 1
    while True:
        value = os.getenv(f"PACIENTE_{i}")
        if not value:
            if os.getenv(f"PACIENTE_{i}_NOME"):
                nome = os.getenv(f"PACIENTE_{i}_NOME")
                user = os.getenv(f"PACIENTE_{i}_USER")
                senha = os.getenv(f"PACIENTE_{i}_PASS")
                if nome and user and senha:
                    patients.append({
                        'idx': i,
                        'nome': nome,
                        'user': user,
                        'pass': senha,
                        'role': os.getenv(f"PACIENTE_{i}_ROLE", "user"),
                        'lab': 'pretti'
                    })
                i += 1
                continue
            else:
                break
        
        try:
            patient_data = json.loads(value)
            patients.append({
                'idx': i,
                'nome': patient_data.get("nome"),
                'user': patient_data.get("user"),
                'pass': patient_data.get("pass"),
                'role': patient_data.get("role", "user"),
                'lab': patient_data.get("lab", "pretti")
            })
        except Exception as e:
            logger.warning(f"Variável PACIENTE_{i} não é um JSON válido no .env: {e}")
        i += 1
        
    return limit, patients, labs

def process_patient(patient, limit, output_dir, login_url):
    t_start = time.time()
    logger.info(f"{'='*45}")
    logger.info(f"Scraping | Paciente: {patient['nome']}")
    logger.info(f"{'='*45}")
    
    def crawler_action(page):
        # 1. Login
        logger.debug("Inserindo credenciais...")
        page.fill("input#control_42", patient['user'])
        page.fill("input#control_45", patient['pass'])
        
        logger.debug("Clicando no botão de entrar...")
        page.click("input#control_56")
        
        # Verificar se houve erro de login (ex: se continuarmos na página de login)
        page.wait_for_timeout(3000)
        title = page.title()
        if "Login" in title or "Entrar" in title or not page.locator("a[name='listaOS']").first.is_visible(timeout=5000):
            logger.error(f"Falha na autenticação para o paciente: {patient['nome']}. Verifique as credenciais.")
            # Captura screenshot de erro
            page.screenshot(path=f"data/exames/output/error_login_paciente_{patient['idx']}.png")
            return
            
        logger.success("Login realizado com sucesso!")
        
        # 2. Obter HTML da lista de exames
        html_content = page.content()
        
        # Regex para capturar os exames da listaOS
        # Cada exame tem: onclick="zenPage.selecionarProcedimento('OS', 'SolicitanteID', 'CodOS', 'Medico', ...)"
        full_pattern = r'(<a[^>]*name="listaOS"[^>]*>.*?</a>)'
        matches = list(re.finditer(full_pattern, html_content, re.DOTALL))
        logger.info(f"Total de exames disponíveis no portal: {len(matches)}")
        
        # Processar os exames encontrados (ordenados do mais recente para o mais antigo)
        exams_to_process = matches[:limit]
        logger.info(f"Limitando o processamento aos {len(exams_to_process)} exames mais recentes.")
        
        for idx, match in enumerate(exams_to_process):
            anchor_html = match.group(1)
            
            # Extrair atributos
            id_match = re.search(r'id="([^"]+)"', anchor_html)
            id_val = id_match.group(1) if id_match else None
            
            onclick_match = re.search(r'onclick="zenPage\.selecionarProcedimento\((.*?)\)"', anchor_html)
            if not onclick_match or not id_val:
                continue
                
            args = [arg.strip('"\'&quot;') for arg in onclick_match.group(1).split(",")]
            
            # Mapeamento de argumentos do zenPage.selecionarProcedimento:
            # args[2] = CodOS
            # args[3] = Nome do Médico
            # args[9] = Data do Exame
            cod_os = args[2] if len(args) > 2 else "sem-os"
            medico = args[3] if len(args) > 3 else "sem-medico"
            data_exame_bruta = args[9] if len(args) > 9 else "sem-data"
            
            data_iso = format_date_to_iso(data_exame_bruta)
            
            # Sanitizar componentes do nome de arquivo (primeiro_ultimo nome)
            paciente_sanitizado = sanitize_name_component(patient['nome'])
            medico_sanitizado = sanitize_name_component(medico)
            
            filename = f"paciente_{paciente_sanitizado}-medico_{medico_sanitizado}-{data_iso}.pdf"
            filepath = os.path.join(output_dir, filename)
            
            # Verificar incrementalidade
            if os.path.exists(filepath):
                logger.debug(f"[Ignorado] Exame {cod_os} de {data_exame_bruta} já existe: {filename}")
                continue
                
            logger.info(f"[Baixando] OS {cod_os} ({data_exame_bruta}) | Médico: {medico}")
            
            # Clicar no link do exame correspondente na barra lateral
            page.click(f"a#{id_val}")
            page.wait_for_timeout(2000)
                        # Esperar pelo botão de visualização/impressão do laudo
            try:
                page.wait_for_selector("text=Imprimir laudo", timeout=8000)
                
                # Abre popup contendo a renderização do Laudo
                with page.context.expect_page() as new_page_info:
                    page.click("text=Imprimir laudo")
                new_page = new_page_info.value
                
                # Esperar o redirect interno do visualizador que gera o PDF temporário
                logger.debug("Aguardando geração do PDF...")
                new_page.wait_for_url("**/pdf", timeout=20000)
                pdf_url = new_page.url
                
                # Baixar o binário usando o context da sessão autenticada
                response = page.context.request.get(pdf_url)
                if response.status == 200:
                    pdf_data = response.body()
                    # Checagem básica de integridade do cabeçalho PDF
                    if pdf_data.startswith(b"%PDF"):
                        with open(filepath, "wb") as pdf_file:
                            pdf_file.write(pdf_data)
                        logger.success(f"Salvo: {filename}")
                    else:
                        logger.error("Conteúdo baixado não é um PDF válido.")
                else:
                    logger.error(f"Falha ao baixar PDF. HTTP {response.status}")
                
                # Fecha a aba popup para liberar recursos
                new_page.close()
                
            except Exception as e:
                logger.error(f"Falha durante a captura do laudo {cod_os}: {e}")
            
            # Delay para evitar sobrecarga no portal
            time.sleep(1)

    # Iniciar sessão do D4vinci/Scrapling
    with DynamicSession(headless=True) as session:
        session.fetch(login_url, page_action=crawler_action)
    elapsed = time.time() - t_start
    logger.info(f"Scraping concluído para '{patient['nome']}' em {elapsed:.1f}s")

def main(target_user=None):
    # 1. Carregar limite, pacientes e laboratórios configurados (config.ini ou .env)
    limit, patients, labs = load_config_data()
        
    output_dir = "data/exames"
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.join(output_dir, "output"), exist_ok=True)
    
    if not patients:
        logger.error("Nenhum paciente configurado corretamente no config.ini ou .env.")
        logger.info("Crie o arquivo config.ini com a seção [Pacientes] ou configure o .env.")
        return
        
    if target_user:
        patients = [p for p in patients if p.get("user") == target_user]
        if not patients:
            logger.error(f"Paciente com usuário '{target_user}' não encontrado.")
            return

    logger.info(f"Configuração carregada. Pacientes: {len(patients)} | Limite por paciente: {limit}")
    t_total = time.time()
    
    # 2. Executar o crawler para cada paciente
    for patient in patients:
        lab_name = patient.get("lab", "pretti").lower()
        login_url = labs.get(lab_name, labs.get("pretti"))
        try:
            process_patient(patient, limit, output_dir, login_url)
        except Exception as e:
            logger.error(f"Falha no fluxo do paciente {patient['nome']}: {e}")
    logger.success(f"Pipeline de scraping finalizado em {time.time() - t_total:.1f}s")

if __name__ == "__main__":
    main()
