import streamlit as pd_st
import pandas as pd
import plotly.express as px
import os
import time
import sys
import re
# Adicionar o diretorio pai ao sys.path para importacoes absolutas do modulo 'app'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from app.logger import logger
except ImportError:
    from logger import logger

# Configuração inicial do Streamlit
pd_st.set_page_config(
    page_title="Dashboard de Exames Clínicos",
    page_icon="🩸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo CSS customizado para aparência Premium
pd_st.markdown("""
<style>
    .main {
        background-color: var(--background-color);
        color: var(--text-color);
    }
    .stAppHeader {
        background-color: var(--background-color);
    }
    h1, h2, h3 {
        color: var(--text-color) !important;
        font-family: 'Outfit', 'Inter', sans-serif;
    }
    .stSidebar {
        background-color: var(--secondary-background-color) !important;
        border-right: 1px solid rgba(128, 128, 128, 0.2);
    }
    /* Estilo para tornar os filtros mais compactos verticalmente */
    div[data-testid="stSidebar"] {
        padding-top: 0px !important;
    }
    div[data-testid="stSidebarUserContent"] {
        padding-top: 0.0rem !important;
        margin-top: -1.0rem !important;
        padding-bottom: 0.2rem !important;
    }
    div[data-testid="stSidebarUserContent"] [data-testid="stVerticalBlock"] {
        gap: 0.25rem !important;
    }
    div[data-testid="stSidebarUserContent"] .stSelectbox, 
    div[data-testid="stSidebarUserContent"] .stMultiSelect {
        margin-bottom: -0.8rem !important;
    }
    /* Diminuir altura e paddings de campos e labels na sidebar */
    div[data-testid="stSidebarUserContent"] label {
        margin-bottom: -0.4rem !important;
        padding-bottom: 0px !important;
    }
    /* Reduzir a altura das caixas de selecao (selectbox e multiselect) em ~15% */
    div[data-testid="stSidebarUserContent"] div[data-baseweb="select"] > div {
        min-height: 32px !important;
        height: auto !important;
        padding-top: 2px !important;
        padding-bottom: 2px !important;
    }
    /* Ajustar o multiselect para que as tags internas nao fiquem excessivamente grandes */
    div[data-testid="stSidebarUserContent"] div[role="button"] {
        padding-top: 1px !important;
        padding-bottom: 1px !important;
        margin-top: 1px !important;
        margin-bottom: 1px !important;
        font-size: 0.8rem !important;
    }
    /* Reduzir o espacamento entre o label e a caixa de selecao */
    div[data-testid="stSidebarUserContent"] [data-testid="stWidgetLabel"] {
        margin-bottom: -0.3rem !important;
    }
    /* Botões na Sidebar (tanto Atualizar quanto Grupos de Exames) compactos */
    div[data-testid="stSidebarUserContent"] div.stButton > button {
        padding: 2px 8px !important;
        min-height: 28px !important;
        height: auto !important;
        margin-bottom: -0.2rem !important;
        font-size: 0.85rem !important;
    }
    /* Primary/Action buttons styling */
    div.stButton > button[data-testid="baseButton-primary"],
    div.stFormSubmitButton > button[data-testid="baseButton-primary"],
    div.stFormSubmitButton > button,
    button[kind="primary"] {
        background-color: #0284c7 !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
    }
    div.stButton > button[data-testid="baseButton-primary"]:hover,
    div.stFormSubmitButton > button[data-testid="baseButton-primary"]:hover,
    div.stFormSubmitButton > button:hover,
    button[kind="primary"]:hover {
        background-color: #0ea5e9 !important;
        color: white !important;
    }
    /* Preset/Secondary buttons styling (Clinical Groups) */
    div.stButton > button[data-testid="baseButton-secondary"] {
        background-color: #0f766e !important;
        color: #ffffff !important;
        border: 1px solid #115e59 !important;
        border-radius: 8px !important;
    }
    div.stButton > button[data-testid="baseButton-secondary"]:hover {
        background-color: #0d9488 !important;
        color: #ffffff !important;
        border-color: #14b8a6 !important;
    }
    /* Ocultar a barra de ferramentas padrao do Streamlit acima do grafico Plotly para evitar botoes em ingles */
    button[data-testid="stPlotlyChartToolbar"],
    div[data-testid="stPlotlyChartToolbar"] {
        display: none !important;
    }
    .metric-card {
        background-color: rgba(128, 128, 128, 0.08);
        border: 1px solid rgba(128, 128, 128, 0.15);
        border-radius: 8px;
        padding: 10px 12px;
        margin-bottom: 8px;
    }
    .metric-card span {
        color: inherit !important;
    }
    .metric-card strong {
        color: inherit !important;
    }
    
    /* Configurações padrao confortaveis para titulos e textos do Streamlit */
    h2, h3 {
        margin-top: 1.2rem !important;
        margin-bottom: 0.6rem !important;
        padding-top: 0.2rem !important;
    }
    
    /* Espacamento padrao saudavel entre blocos normais */
    div[data-testid="stVerticalBlock"] > div {
        gap: 1.0rem !important;
    }

    /* Container de scroll para limitar altura e casar com o grafico */
    .metric-cards-container {
        max-height: 380px;
        overflow-y: auto;
        padding-right: 6px;
        margin-top: 10px;
    }
    .metric-cards-container::-webkit-scrollbar {
        width: 4px;
    }
    .metric-cards-container::-webkit-scrollbar-track {
        background: transparent;
    }
    .metric-cards-container::-webkit-scrollbar-thumb {
        background: rgba(128, 128, 128, 0.3);
        border-radius: 2px;
    }
    .metric-cards-container::-webkit-scrollbar-thumb:hover {
        background: rgba(128, 128, 128, 0.5);
    }

    /* Container da tabela sem margem negativa exagerada */
    .st-key-container_da_tabela {
        margin-top: 10px !important;
    }
    .st-key-container_da_tabela h3,
    .st-key-container_da_tabela h2 {
        margin-top: 0px !important;
        padding-top: 0px !important;
    }
</style>
<script>
// Aguarda o Plotly estar disponivel no contexto da janela principal ou pai
const registerPlotlyLocale = () => {
    const Plotly = window.Plotly || (window.parent && window.parent.Plotly);
    if (Plotly && Plotly.register) {
        try {
            Plotly.register({
                moduleType: 'locale',
                name: 'pt-BR',
                dictionary: {
                    'Autoscale': 'Autoescala',
                    'Box Select': 'Seleção em caixa',
                    'Click to zoom in': 'Clique para ampliar',
                    'Click to zoom out': 'Clique para reduzir',
                    'Compare data on hover': 'Comparar dados ao passar o mouse',
                    'Double-click to zoom back out': 'Duplo clique para redefinir zoom',
                    'Download plot as a png': 'Baixar gráfico como PNG',
                    'Download plot as png': 'Baixar gráfico como PNG',
                    'Download plot': 'Baixar gráfico',
                    'Download': 'Baixar',
                    'Edit in Chart Studio': 'Editar no Chart Studio',
                    'IE settings': 'Configurações do IE',
                    'Lasso Select': 'Seleção livre (laço)',
                    'Orbit rotation': 'Rotação orbital',
                    'Pan': 'Mover',
                    'Reset camera to default': 'Redefinir câmera',
                    'Reset camera to last save': 'Redefinir câmera para última gravação',
                    'Reset view': 'Restaurar visualização',
                    'Reset y axis limits': 'Redefinir limites do eixo Y',
                    'Reset axis limits': 'Redefinir limites dos eixos',
                    'Reset axes': 'Redefinir eixos',
                    'Reset scale': 'Redefinir escala',
                    'Select': 'Selecionar',
                    'Show closest data on hover': 'Mostrar dados mais próximos ao passar o mouse',
                    'Snapshot': 'Captura de tela',
                    'Toggle Hover': 'Alternar dicas ao passar o mouse',
                    'Toggle Spike Lines': 'Alternar linhas guia',
                    'Toggle Fullscreen': 'Tela cheia',
                    'toggle fullscreen': 'Tela cheia',
                    'Fullscreen': 'Tela cheia',
                    'fullscreen': 'Tela cheia',
                    'Turntable rotation': 'Rotação de mesa',
                    'Zoom': 'Zoom',
                    'Zoom in': 'Ampliar',
                    'Zoom out': 'Reduzir'
                },
                format: {
                    days: ['Domingo', 'Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado'],
                    shortDays: ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb'],
                    months: ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'],
                    shortMonths: ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'],
                    date: '%d/%m/%Y'
                }
            });
            clearInterval(plotlyInterval);
        } catch (e) {
            console.error("Erro ao registrar locale pt-BR no Plotly:", e);
        }
    }
};
const plotlyInterval = setInterval(registerPlotlyLocale, 500);
// Tenta rodar imediatamente tambem
registerPlotlyLocale();
</script>
""", unsafe_allow_html=True)

def run_pipeline_if_new_files(force=False, target_user=None):
    import sys
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    
    from app.crawler import main as run_crawler
    from app.pdf_processor import main as run_pdf_to_md
    from app.data_extractor import main as run_md_to_csv
    from app.auditoria import run_audit
    
    pdf_dir = "data/exames"
    md_dir = "data/exames/exames_md"
    
    # 1. Renomear arquivos .pdf.pdf redundantes no diretório 'exames' antes de processar
    if os.path.exists(pdf_dir):
        for f in os.listdir(pdf_dir):
            if f.endswith('.pdf.pdf'):
                old = os.path.join(pdf_dir, f)
                new = os.path.join(pdf_dir, f[:-4])
                os.rename(old, new)
    
    # 2. Verificar se há novos PDFs que ainda não têm um correspondente .md
    has_new = False
    if os.path.exists(pdf_dir):
        pdfs = [f for f in os.listdir(pdf_dir) if f.endswith(".pdf")]
        for pdf in pdfs:
            md_name = pdf.replace(".pdf", ".md")
            md_path = os.path.join(md_dir, md_name)
            if not os.path.exists(md_path):
                has_new = True
                break

    logger.info(f"Verificação de startup | PDFs sem MD: {has_new} | force={force} | target={target_user}")
                
    if has_new or force:
        t_pipeline = time.time()
        logger.info(f"=== Pipeline iniciado (force={force}, target_user={target_user}) ===")

        pd_st.toast("Buscando novos exames no portal (Crawler)...", icon="🔄")
        t0 = time.time()
        try:
            run_crawler(target_user=target_user)
            logger.info(f"[Scraping]    {time.time() - t0:.1f}s")
        except Exception as e:
            logger.error(f"[Scraping] ERRO: {e}")
            pd_st.error(f"Erro ao executar o crawler: {e}")
            
        pd_st.toast("Convertendo PDFs para Markdown...", icon="⚙️")
        t0 = time.time()
        try:
            run_pdf_to_md()
            logger.info(f"[Conversão]   {time.time() - t0:.1f}s")
        except Exception as e:
            logger.error(f"[Conversão] ERRO: {e}")
            pd_st.error(f"Erro ao converter PDFs: {e}")
            
        pd_st.toast("Extraindo dados estruturados...", icon="📊")
        t0 = time.time()
        try:
            run_md_to_csv()
            logger.info(f"[Extração]    {time.time() - t0:.1f}s")
        except Exception as e:
            logger.error(f"[Extração] ERRO: {e}")
            pd_st.error(f"Erro ao extrair dados para o CSV: {e}")
            
        pd_st.toast("Executando auditoria cruzada...", icon="🛡️")
        t0 = time.time()
        try:
            run_audit()
            logger.info(f"[Auditoria]   {time.time() - t0:.1f}s")
        except Exception as e:
            logger.error(f"[Auditoria] ERRO: {e}")
            pd_st.error(f"Erro ao auditar dados: {e}")
            
        pd_st.toast("Atualizando referências clínicas...", icon="🔬")
        t0 = time.time()
        try:
            from app.data_extractor_reference import main as run_extractor_ref
            from app.auditoria_reference import main as run_audit_ref
            run_extractor_ref()
            run_audit_ref()
            logger.info(f"[Referências] {time.time() - t0:.1f}s")
        except Exception as e:
            logger.error(f"[Referências] ERRO: {e}")
            pd_st.error(f"Erro ao processar referências dinâmicas: {e}")
        
        # Limpar o cache de carregamento de dados do streamlit para carregar os novos
        pd_st.cache_data.clear()
        logger.success(f"=== Pipeline completo em {time.time() - t_pipeline:.1f}s ===")
        pd_st.toast("Sincronização concluída!", icon="✅")
        return True
    
    logger.info("Pipeline pulado: nenhum PDF novo encontrado e force=False.")
    return False

# --- Startup do pipeline: roda UMA ÚNICA VEZ por processo do servidor (ANTES DE CARREGAR A TELA) ---
@pd_st.cache_resource(show_spinner=False)
def _startup_state():
    return {"done": False}

_state = _startup_state()

if not _state["done"]:
    from app.crawler import main as _run_crawler
    from app.pdf_processor import main as _run_pdf_to_md
    from app.data_extractor import main as _run_md_to_csv
    from app.auditoria import run_audit as _run_audit

    logger.info("=== Servidor iniciado. Executando pipeline de startup ===")
    t_total = time.time()
    
    # Grid de colunas para centralizar a barra de sincronizacao
    col_left, col_center, col_right = pd_st.columns([1, 1.5, 1])
    
    with col_center:
        # Título idêntico ao de login
        pd_st.markdown("""
        <div style="text-align: center; margin-bottom: 25px; font-family: 'Outfit', 'Inter', sans-serif;">
            <h1 style="font-size: 2.0rem; margin-bottom: 5px; color: #ffffff;">🩸 Dashboard de Exames Clínicos</h1>
            <h2 style="font-size: 1.3rem; color: #0284c7; margin-top: 0px; font-weight: normal;">🔄 Sincronização de Dados</h2>
        </div>
        """, unsafe_allow_html=True)
        
        # Barra de progresso dinâmica
        progress_bar = pd_st.progress(0)
        
        with pd_st.status("Sincronizando exames — aguarde...", expanded=True) as _status:
            pd_st.write("🌐 **Etapa 1/4** — Buscando novos exames no portal...")
            t0 = time.time()
            try:
                _run_crawler()
                logger.info(f"[Scraping]  {time.time() - t0:.1f}s")
            except Exception as e:
                logger.error(f"[Scraping] ERRO: {e}")
            progress_bar.progress(25)
    
            pd_st.write("⚙️ **Etapa 2/4** — Convertendo PDFs para Markdown...")
            t0 = time.time()
            try:
                _run_pdf_to_md()
                logger.info(f"[Conversão] {time.time() - t0:.1f}s")
            except Exception as e:
                logger.error(f"[Conversão] ERRO: {e}")
            progress_bar.progress(50)
    
            pd_st.write("📊 **Etapa 3/4** — Extraindo dados estruturados...")
            t0 = time.time()
            try:
                _run_md_to_csv()
                logger.info(f"[Extração]  {time.time() - t0:.1f}s")
            except Exception as e:
                logger.error(f"[Extração] ERRO: {e}")
            progress_bar.progress(75)
    
            pd_st.write("🛡️ **Etapa 4/4** — Executando auditoria de qualidade...")
            t0 = time.time()
            try:
                _run_audit()
                logger.info(f"[Auditoria] {time.time() - t0:.1f}s")
            except Exception as e:
                logger.error(f"[Auditoria] ERRO: {e}")
            progress_bar.progress(90)
            
            pd_st.write("🔬 **Etapa Final** — Atualizando referências clínicas dinâmicas...")
            t0 = time.time()
            try:
                from app.data_extractor_reference import main as _run_extractor_ref
                from app.auditoria_reference import main as _run_audit_ref
                _run_extractor_ref()
                _run_audit_ref()
                logger.info(f"[Referências] {time.time() - t0:.1f}s")
            except Exception as e:
                logger.error(f"[Referências] ERRO: {e}")
            progress_bar.progress(100)
    
            elapsed = time.time() - t_total
            logger.success(f"=== Pipeline completo em {elapsed:.1f}s ===")
            _status.update(label=f"✅ Exames sincronizados em {elapsed:.0f}s!", state="complete", expanded=False)
            
            # Pequeno delay antes de sumir e recarregar
            time.sleep(1.2)
            
    _state["done"] = True
    pd_st.rerun()


# --- Autenticação ---
if "authenticated" not in pd_st.session_state:
    pd_st.session_state["authenticated"] = False
    pd_st.session_state["user_data"] = None

# Tenta ler o usuario persistido nos query parameters da URL (nativos e síncronos no F5)
if not pd_st.session_state["authenticated"]:
    saved_user = pd_st.query_params.get("user")
    if saved_user:
        from app.crawler import load_config_data
        _, patients, _ = load_config_data()
        
        matched_user = None
        for p in patients:
            if p.get("user") == saved_user:
                matched_user = p
                break
        
        if matched_user:
            pd_st.session_state["authenticated"] = True
            pd_st.session_state["user_data"] = matched_user
            pd_st.query_params["user"] = saved_user
            pd_st.rerun()

import extra_streamlit_components as cookie_manager
cookies = cookie_manager.CookieManager(key="exames_cookie_manager")

if not pd_st.session_state["authenticated"]:
    # Espaçamento vertical inicial
    pd_st.write("")
    pd_st.write("")
    
    # Grid de colunas para centralizar o formulário
    col_left, col_center, col_right = pd_st.columns([1, 1.2, 1])
    
    with col_center:
        # Título centralizado: Dashboard primeiro (destaque), Autenticação depois (subtítulo)
        pd_st.markdown("""
        <div style="text-align: center; margin-bottom: 25px; font-family: 'Outfit', 'Inter', sans-serif;">
            <h1 style="font-size: 2.0rem; margin-bottom: 5px; color: #ffffff;">🩸 Dashboard de Exames Clínicos</h1>
            <h2 style="font-size: 1.3rem; color: #0284c7; margin-top: 0px; font-weight: normal;">🔑 Autenticação</h2>
        </div>
        """, unsafe_allow_html=True)
        
        with pd_st.form("login_form"):
            username_input = pd_st.text_input("Usuário")
            password_input = pd_st.text_input("Senha", type="password")
            submit_button = pd_st.form_submit_button("Entrar", type="primary", width="stretch")
        
        if submit_button:
            from app.crawler import load_config_data
            _, patients, _ = load_config_data()
            
            matched_user = None
            for p in patients:
                if p.get("user") == username_input and p.get("pass") == password_input:
                    matched_user = p
                    break
            
            if matched_user:
                # Salvar cookie no navegador por 30 dias
                try:
                    import datetime
                    expiry = datetime.date.today() + datetime.timedelta(days=30)
                    cookies.set("exames_auth_user", username_input, expires_at=expiry)
                except Exception as e:
                    logger.error(f"Erro ao salvar cookie: {e}")
                
                pd_st.query_params["user"] = username_input
                pd_st.session_state["authenticated"] = True
                pd_st.session_state["user_data"] = matched_user
                pd_st.success(f"Bem-vindo(a), {matched_user.get('nome')}!")
                pd_st.rerun()
            else:
                pd_st.error("Usuário ou senha incorretos.")
    pd_st.stop()

# Usuário logado
user_data = pd_st.session_state["user_data"]
is_admin = user_data.get("role") == "admin"

# Função para carregar dados
def load_data():
    results_dir = os.path.join("data", "exames", "results")
    if not os.path.exists(results_dir):
        return pd.DataFrame()
        
    csv_files = [f for f in os.listdir(results_dir) if f.startswith("results-") and f.endswith(".csv")]
    if not csv_files:
        return pd.DataFrame()
        
    dfs = []
    for f in csv_files:
        path = os.path.join(results_dir, f)
        try:
            dfs.append(pd.read_csv(path, encoding='utf-8'))
        except Exception as e:
            print(f"Erro ao ler {path}: {e}")
            
    if not dfs:
        return pd.DataFrame()
        
    df = pd.concat(dfs, ignore_index=True)
    
    # Converter a coluna de Data para datetime para ordenação correta
    df['Data Formatada'] = pd.to_datetime(df['Data Exame'], format='%d/%m/%Y', errors='coerce')
    # Ordenar por data
    df = df.sort_values(by='Data Formatada')
    
    # Garantir que a coluna 'Resultado' seja numérica onde possível
    df['Valor Numérico'] = df['Resultado'].astype(str).str.replace('.', '', regex=False)
    df['Valor Numérico'] = df['Valor Numérico'].str.replace(',', '.', regex=False)
    df['Valor Numérico'] = pd.to_numeric(df['Valor Numérico'], errors='coerce')
    
    return df

df = load_data()

# Filtragem de segurança por perfil (Role)
if not df.empty:
    if not is_admin:
        import unicodedata
        def normalize_name(n):
            if not isinstance(n, str):
                return ""
            n = unicodedata.normalize('NFD', n)
            n = ''.join(c for c in n if unicodedata.category(c) != 'Mn')
            return n.strip().lower()
        norm_user_fullname = normalize_name(user_data.get("nome", ""))
        df = df[df['Paciente'].apply(lambda x: normalize_name(x) == norm_user_fullname)]

if df.empty:
    pd_st.title("🩸 Dashboard de Resultados de Exames Clínicos")
    pd_st.error("Nenhum dado de exame disponível.")
    
    # Adicionar botão de Sair na Sidebar mesmo se não houver dados
    if pd_st.sidebar.button("🚪 Sair", width="stretch", type="primary"):
        try:
            cookies.delete("exames_auth_user")
        except Exception:
            pass
        pd_st.query_params.clear()
        pd_st.session_state["authenticated"] = False
        pd_st.session_state["user_data"] = None
        pd_st.rerun()
        
    if pd_st.button("🔄 Buscar Meus Exames (Crawler)", type="primary"):
        with pd_st.spinner("Buscando exames..."):
            target_user = None if is_admin else user_data.get("user")
            if run_pipeline_if_new_files(force=True, target_user=target_user):
                pd_st.cache_data.clear()
                pd_st.success("Exames importados com sucesso!")
                pd_st.rerun()
            else:
                pd_st.info("Nenhum novo exame para processar.")
else:
    pd_st.title("🩸 Dashboard de Resultados de Exames Clínicos")
    pd_st.markdown("Visualize a evolução histórica de seus indicadores clínicos laboratoriais.")
    
    # Sidebar: informações de login e Sair
    pd_st.sidebar.markdown(f"👤 **Usuário:** {user_data.get('nome')}")
    role_label = "Administrador" if user_data.get('role') == "admin" else "Usuário"
    pd_st.sidebar.markdown(f"🔑 **Perfil:** {role_label}")
    if pd_st.sidebar.button("🚪 Sair", width="stretch", type="primary"):
        try:
            cookies.delete("exames_auth_user")
        except Exception:
            pass
        pd_st.query_params.clear()
        pd_st.session_state["authenticated"] = False
        pd_st.session_state["user_data"] = None
        pd_st.rerun()
        
    # Botão de atualizar exames diretamente no topo da Sidebar (exclusivo para admin)
    if is_admin:
        if pd_st.sidebar.button("🔄 Atualizar Exames (PDF)", type="primary", width="stretch"):
            with pd_st.spinner("Buscando novos PDFs e processando..."):
                target_user = None if is_admin else user_data.get("user")
                updated = run_pipeline_if_new_files(force=True, target_user=target_user)
                if updated:
                    pd_st.cache_data.clear()
                    pd_st.success("Exames atualizados com sucesso!")
                    pd_st.rerun()
                else:
                    pd_st.info("Nenhum novo exame para processar.")

    # Detecta dinamicamente se o tema ativo do Streamlit é escuro ou claro
    tema_is_dark = True
    try:
        # Tenta ler a opção de tema das configurações do Streamlit
        theme_base = pd_st.config.get_option("theme.base")
        if theme_base:
            tema_is_dark = (theme_base.lower() != "light")
    except Exception:
        try:
            theme_base = pd_st.get_option("theme.base")
            if theme_base:
                tema_is_dark = (theme_base.lower() != "light")
        except Exception:
            tema_is_dark = True

    # SIDEBAR - Filtros solicitados
    pd_st.sidebar.header("🔍 Filtros de Busca")
    
    # Presets Section
    pd_st.sidebar.subheader("🎯 Grupos de Exames")
    presets = {
        "Controle de Diabetes": ["Glicose em Jejum", "Hemoglobina Glicada (HbA1c)", "Glicemia Média Estimada"],
        "Função Renal": ["Ureia", "Creatinina Sérica", "Ácido Úrico"],
        "Função Hepática": ["TGO (AST)", "TGP (ALT)", "Gama Gt", "Fosfatase Alcalina"],
        "Perfil Lipídico": ["Colesterol Total", "Colesterol HDL", "Triglicerídeos"],
        "Hemograma Completo": "hemograma_completo",
        "Hormônios & Tireoide": ["TSH Ultra Sensível", "T4 Livre", "25-Hidroxivitamina D"],
        "PSA (Saúde Masculina)": ["Psa Total Ultra Sensível"]
    }
    
    all_exams = sorted(df['Exame/Componente'].dropna().unique().tolist())
    
    # Inicializa estado selecionado se necessário
    if "selected_exames_multiselect" not in pd_st.session_state:
        # Default presets (Controle de Diabetes completo)
        default_preset = ["Glicose em Jejum", "Hemoglobina Glicada (HbA1c)", "Glicemia Média Estimada"]
        pd_st.session_state["selected_exames_multiselect"] = [e for e in default_preset if e in all_exams]
        if not pd_st.session_state["selected_exames_multiselect"] and all_exams:
            pd_st.session_state["selected_exames_multiselect"] = [all_exams[0]]
    
    pd_st.session_state["selected_exames"] = pd_st.session_state["selected_exames_multiselect"]
            
    # Renderizar botões de preset
    for p_name in presets.keys():
        if pd_st.sidebar.button(p_name, width="stretch"):
            if p_name == "Hemograma Completo":
                resolved = [e for e in ["Hemograma - Hemoglobina", "Hemograma - Hematocrito", "Leucocitos", "Plaquetas"] if e in all_exams]
            else:
                resolved = [e for e in presets[p_name] if e in all_exams]
            pd_st.session_state["selected_exames"] = resolved
            pd_st.session_state["selected_exames_multiselect"] = resolved
            pd_st.rerun()

    # 1. Filtro Paciente
    pacientes_lista = sorted(df['Paciente'].dropna().unique().tolist())
    if is_admin:
        if pacientes_lista:
            selected_paciente = pd_st.sidebar.selectbox("Paciente", pacientes_lista, index=0)
        else:
            selected_paciente = "Todos"
    else:
        # Usuário comum: apenas seu próprio nome de forma travada
        if pacientes_lista:
            selected_paciente = pd_st.sidebar.selectbox(
                "Paciente", 
                pacientes_lista, 
                index=0, 
                disabled=True,
                help="Você só possui autorização para ver seus próprios exames."
            )
        else:
            selected_paciente = pd_st.sidebar.selectbox(
                "Paciente",
                [user_data.get("nome")],
                index=0,
                disabled=True
            )
            
    # Criamos o DataFrame intermediário filtrado pelo Paciente selecionado
    df_paciente = df.copy()
    if selected_paciente != "Todos":
        df_paciente = df_paciente[df_paciente['Paciente'] == selected_paciente]

    # Para evitar que seleções de um paciente antigo fiquem presas ao mudar de paciente,
    # verificamos se o paciente mudou
    if "last_selected_paciente" not in pd_st.session_state:
        pd_st.session_state["last_selected_paciente"] = selected_paciente
        
    if pd_st.session_state["last_selected_paciente"] != selected_paciente:
        # Paciente mudou! Vamos limpar/reiniciar a seleção de exames
        pd_st.session_state["last_selected_paciente"] = selected_paciente
        # Define padrões para o novo paciente (Controle de Diabetes completo)
        exames_opts_novo = sorted(df_paciente['Exame/Componente'].dropna().unique().tolist())
        default_preset = ["Glicose em Jejum", "Hemoglobina Glicada (HbA1c)", "Glicemia Média Estimada"]
        valid_selections = [e for e in default_preset if e in exames_opts_novo]
        if not valid_selections and exames_opts_novo:
            valid_selections = [exames_opts_novo[0]]
        pd_st.session_state["selected_exames_multiselect"] = valid_selections
        pd_st.session_state["selected_exames"] = valid_selections
        pd_st.rerun()
    
    # 2. Filtro Médico (baseado no paciente selecionado)
    medicos_opts = ["Todos"] + sorted(df_paciente['Médico'].dropna().unique().tolist())
    selected_medico = pd_st.sidebar.selectbox("Médico", medicos_opts)
    
    # 5. Filtro Exame / Componente (baseado no paciente selecionado) - reposicionado para logo após Médico
    exames_opts = sorted(df_paciente['Exame/Componente'].dropna().unique().tolist())
    selected_exames = pd_st.sidebar.multiselect(
        "Exame / Componente", 
        exames_opts, 
        key="selected_exames_multiselect"
    )
    pd_st.session_state["selected_exames"] = selected_exames
    
    # 3. Filtro Laboratório (baseado no paciente selecionado)
    labs_opts = ["Todos"] + sorted(df_paciente['Laboratório'].dropna().unique().tolist())
    selected_lab = pd_st.sidebar.selectbox("Laboratório", labs_opts)
    
    # 4. Filtro Data Exame (baseado no paciente selecionado)
    datas_opts = sorted(df_paciente['Data Exame'].dropna().unique().tolist())
    selected_datas = pd_st.sidebar.multiselect("Data do Exame", datas_opts, default=[])

    # Aplicando filtros no DataFrame final
    df_filtered = df_paciente.copy()
    if selected_medico != "Todos":
        df_filtered = df_filtered[df_filtered['Médico'] == selected_medico]
    if selected_lab != "Todos":
        df_filtered = df_filtered[df_filtered['Laboratório'] == selected_lab]
    if selected_datas:
        df_filtered = df_filtered[df_filtered['Data Exame'].isin(selected_datas)]
    if selected_exames:
        df_filtered = df_filtered[df_filtered['Exame/Componente'].isin(selected_exames)]

    if not selected_exames:
        # Exibe um único aviso amigável se não houver exames selecionados
        pd_st.info("💡 **Dica**: Selecione um ou mais exames no filtro **Exame / Componente** na barra lateral (ou clique em um dos **Grupos de Exames**) para visualizar a evolução gráfica e os resumos históricos.")
    else:
        # Paleta de cores premium consistente para os exames (compartilhada entre gráfico e cards)
        cores_paleta = ["#0284c7", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899", "#14b8a6", "#f97316", "#06b6d4"]
        exames_selecionados_color = sorted(df_filtered['Exame/Componente'].dropna().unique().tolist())
        cor_map = {exame: cores_paleta[idx % len(cores_paleta)] for idx, exame in enumerate(exames_selecionados_color)}

        # Layout Principal (proporção 3:1 para expandir o gráfico e reduzir a coluna de resumo)
        col1, col2 = pd_st.columns([3, 1])

        with col1:
            pd_st.subheader("📈 Gráfico de Evolução Histórica")
            if df_filtered.empty:
                pd_st.warning("Nenhum dado corresponde aos filtros selecionados.")
            else:
                import plotly.graph_objects as go
                
                df_plot = df_filtered.dropna(subset=['Valor Numérico']).copy()
                if df_plot.empty:
                    pd_st.info("Nenhum dado numérico encontrado para gerar o gráfico com os filtros atuais.")
                else:
                    # Identifica unidades selecionadas e cria a figura
                    unidades = df_plot['Unidade'].dropna().unique()
                    fig = go.Figure()
                    
                    exames_selecionados = sorted(df_plot['Exame/Componente'].dropna().unique().tolist())
                    
                    posicoes_texto = ["top center", "bottom center", "top right", "bottom left", "top left", "bottom right"]
                    
                    # Pré-calcula posições de texto para evitar sobreposição em pontos coincidentes/próximos
                    df_plot = df_plot.sort_values(by=['Data Formatada', 'Valor Numérico']).copy()
                    df_plot['Posicao Texto'] = 'top center' # Default
                    
                    posicoes_conflito = ["bottom center", "top center", "top right", "bottom left", "top left", "bottom right"]
                    for data_formatada, date_group in df_plot.groupby('Data Formatada'):
                        if len(date_group) > 1:
                            for i, (idx, row) in enumerate(date_group.iterrows()):
                                pos = posicoes_conflito[i % len(posicoes_conflito)]
                                df_plot.loc[idx, 'Posicao Texto'] = pos
                        else:
                            idx_exame = exames_selecionados.index(date_group['Exame/Componente'].iloc[0]) if date_group['Exame/Componente'].iloc[0] in exames_selecionados else 0
                            df_plot.loc[date_group.index[0], 'Posicao Texto'] = posicoes_texto[idx_exame % len(posicoes_texto)]
                    
                    # Se houver mais de uma unidade diferente (ex: mg/dL e %)
                    if len(unidades) > 1:
                        primary_unit = unidades[0]
                        secondary_unit = unidades[1]
                        
                        for exame_nome, group in df_plot.groupby('Exame/Componente'):
                            unit = group['Unidade'].iloc[0] if not group['Unidade'].empty else ""
                            cor = cor_map.get(exame_nome, "#0284c7")
                            idx_exame = exames_selecionados.index(exame_nome) if exame_nome in exames_selecionados else 0
                            text_pos = posicoes_texto[idx_exame % len(posicoes_texto)]
                            
                            if unit == secondary_unit:
                                # Plota no Eixo Y Secundário
                                fig.add_trace(go.Scatter(
                                    x=group['Data Formatada'],
                                    y=group['Valor Numérico'],
                                    name=f"{exame_nome} ({unit})",
                                    mode='lines+markers+text',
                                    text=group['Resultado'],
                                    textposition=group['Posicao Texto'].tolist(),
                                    yaxis="y2",
                                    line=dict(color=cor),
                                    marker=dict(color=cor),
                                    customdata=[exame_nome] * len(group),
                                    hovertemplate=f"<span style='color:{cor}; font-weight:bold;'>%{{customdata}}</span><br>Resultado: %{{text}} {unit}<extra></extra>",
                                    hoverlabel=dict(bordercolor=cor)
                                ))
                            else:
                                # Plota no Eixo Y Primário
                                fig.add_trace(go.Scatter(
                                    x=group['Data Formatada'],
                                    y=group['Valor Numérico'],
                                    name=f"{exame_nome} ({unit})",
                                    mode='lines+markers+text',
                                    text=group['Resultado'],
                                    textposition=group['Posicao Texto'].tolist(),
                                    line=dict(color=cor),
                                    marker=dict(color=cor),
                                    customdata=[exame_nome] * len(group),
                                    hovertemplate=f"<span style='color:{cor}; font-weight:bold;'>%{{customdata}}</span><br>Resultado: %{{text}} {unit}<extra></extra>",
                                    hoverlabel=dict(bordercolor=cor)
                                ))
                        
                        # Configura layouts dos dois eixos
                        fig.update_layout(
                            yaxis=dict(
                                title=f"Resultados ({primary_unit})",
                                showgrid=True,
                                gridcolor='#2d313f'
                            ),
                            yaxis2=dict(
                                title=f"Resultados ({secondary_unit})",
                                anchor="x",
                                overlaying="y",
                                side="right",
                                showgrid=False
                            ),
                            title="Evolução Temporal (Múltiplas Unidades)"
                        )
                    else:
                        # Eixo único se tudo tiver a mesma unidade
                        unit = unidades[0] if len(unidades) == 1 else ""
                        for exame_nome, group in df_plot.groupby('Exame/Componente'):
                            cor = cor_map.get(exame_nome, "#0284c7")
                            fig.add_trace(go.Scatter(
                                x=group['Data Formatada'],
                                y=group['Valor Numérico'],
                                name=f"{exame_nome}",
                                mode='lines+markers+text',
                                text=group['Resultado'],
                                textposition=group['Posicao Texto'].tolist(),
                                line=dict(color=cor),
                                marker=dict(color=cor),
                                customdata=[exame_nome] * len(group),
                                hovertemplate=f"<span style='color:{cor}; font-weight:bold;'>%{{customdata}}</span><br>Resultado: %{{text}} {unit}<extra></extra>",
                                hoverlabel=dict(bordercolor=cor)
                            ))
                            
                            # Se for selecionado exatamente um único exame, adiciona linhas de limite de referência no gráfico
                            if len(exames_selecionados) == 1:
                                ref_csv_path = "data/exames/exame_references.csv"
                                if os.path.exists(ref_csv_path):
                                    try:
                                        import csv
                                        from datetime import datetime
                                        # Coleta dados clínicos do paciente exibido na tela para carregar o VR correto
                                        p_sex = "Ambos"
                                        p_birth = None
                                        p_preg = False
                                        
                                        # Tenta carregar metadados do config correspondentes ao selected_paciente
                                        from app.data_extractor_reference import load_patient_metadata
                                        pat_meta = load_patient_metadata(selected_paciente)
                                        if pat_meta:
                                            p_sex = pat_meta.get("sexo", "Ambos")
                                            p_birth = pat_meta.get("data_nascimento")
                                            p_preg = pat_meta.get("gravidez", False)
                                        else:
                                            # Fallback para o usuário logado se não achar
                                            p_sex = user_data.get("sexo", "Ambos")
                                            p_birth = user_data.get("data_nascimento")
                                            p_preg = user_data.get("gravidez", False)
                                            
                                        p_age = None
                                        p_faixa = "Ambos"
                                        
                                        # Identifica a data mais recente do grupo para calcular idade
                                        if 'Data Formatada' in group.columns and not group['Data Formatada'].isna().all():
                                            idx_max = group['Data Formatada'].idxmax()
                                            last_coleta = group.loc[idx_max, 'Data Exame']
                                        else:
                                            last_coleta = group['Data Exame'].max()
                                            
                                        if p_birth and last_coleta:
                                            birth_d = datetime.strptime(p_birth, "%d/%m/%d%y" if len(p_birth.split('/')[-1]) == 2 else "%d/%m/%Y")
                                            exam_d = datetime.strptime(last_coleta, "%d/%m/%Y")
                                            p_age = exam_d.year - birth_d.year - ((exam_d.month, exam_d.day) < (birth_d.month, birth_d.day))
                                            p_faixa = "Adulto" if p_age > 20 else "Infantil"
                                            
                                        ref_text = ""
                                        print(f"DEBUG GRAPH REF: exame_nome={exame_nome}, p_sex={p_sex}, p_faixa={p_faixa}, p_preg={p_preg}")
                                        with open(ref_csv_path, 'r', encoding='utf-8') as ref_f:
                                            ref_reader = csv.reader(ref_f)
                                            next(ref_reader, None)  # Pula header
                                            for ref_row in ref_reader:
                                                if len(ref_row) >= 8:
                                                    exam_name, _, ref_c, ref_p, r_sex, r_faixa, r_preg, _ = ref_row
                                                    if exam_name.upper().strip() == exame_nome.upper().strip():
                                                        print(f"DEBUG GRAPH MATCH: exam_name={exam_name}, r_sex={r_sex}, r_faixa={r_faixa}, r_preg={r_preg}")
                                                        # Valida compatibilidade clínica
                                                        if r_sex and r_sex != "Ambos" and p_sex and r_sex.upper() != p_sex.upper():
                                                            print("DEBUG GRAPH SKIP: sex mismatch")
                                                            continue
                                                        if r_faixa and r_faixa != "Ambos" and p_faixa and r_faixa.upper() != p_faixa.upper():
                                                            print("DEBUG GRAPH SKIP: faixa mismatch")
                                                            continue
                                                        if r_preg and r_preg.upper() != str(p_preg).upper():
                                                            print("DEBUG GRAPH SKIP: preg mismatch")
                                                            continue
                                                        ref_text = ref_p if ref_p else ref_c
                                                        print(f"DEBUG GRAPH FOUND REF: {ref_text}")
                                                        break
                                        
                                        if ref_text:
                                            # Tenta extrair padrões comuns de valores numéricos de referência
                                            # Substitui virgulas por pontos para facilitar
                                            ref_norm = ref_text.replace(',', '.')
                                            
                                            limit_min = None
                                            limit_max = None
                                            
                                            # Intervalo: "DE X A Y" ou "X A Y" ou "X - Y" ou "X E Y" ou "X ATE Y"
                                            match_range = re.search(r'(?:DE\s+)?([\d\.]+)\s*(?:A|ATE|-|E)\s+([\d\.]+)', ref_norm, re.IGNORECASE)
                                            # Superior: "SUPERIOR A X" ou "MAIOR QUE X" ou "SUPERIOR OU IGUAL A X" ou "MAIOR OU IGUAL A X"
                                            match_sup = re.search(r'(?:SUPERIOR|MAIOR)\s+(?:A|QUE|OU\s+IGUAL\s+A)?\s*([\d\.]+)', ref_norm, re.IGNORECASE)
                                            # Inferior: "INFERIOR A X" ou "MENOR QUE X" ou "ATE X" ou "INFERIOR OU IGUAL A X" ou "MENOR OU IGUAL A X"
                                            match_inf = re.search(r'(?:INFERIOR|MENOR|ATE)\s+(?:A|QUE|OU\s+IGUAL\s+A)?\s*([\d\.]+)', ref_norm, re.IGNORECASE)
                                            
                                            if match_range:
                                                limit_min = float(match_range.group(1))
                                                limit_max = float(match_range.group(2))
                                            elif match_inf:
                                                limit_max = float(match_inf.group(1))
                                            elif match_sup:
                                                limit_min = float(match_sup.group(1))
                                                
                                            # Adiciona as linhas horizontais de referência
                                            if limit_min is not None or limit_max is not None:
                                                x_vals = group['Data Formatada'].tolist()
                                                if len(x_vals) >= 1:
                                                                                     # Define a cor das referências de acordo com o tema selecionado
                                                    ref_line_color = 'rgba(253, 224, 71, 0.85)' if tema_is_dark else 'rgba(239, 68, 68, 0.85)'
                                                    
                                                    if limit_min is not None:
                                                        fig.add_trace(go.Scatter(
                                                            x=x_vals,
                                                            y=[limit_min] * len(x_vals),
                                                            name=f"Mínimo Ref ({limit_min})",
                                                            mode='lines',
                                                            line=dict(color=ref_line_color, width=1.5, dash='dash'),
                                                            hoverinfo='none',
                                                            showlegend=True
                                                        ))
                                                    if limit_max is not None:
                                                        fig.add_trace(go.Scatter(
                                                            x=x_vals,
                                                            y=[limit_max] * len(x_vals),
                                                            name=f"Máximo Ref ({limit_max})",
                                                            mode='lines',
                                                            line=dict(color=ref_line_color, width=1.5, dash='dash'),
                                                            hoverinfo='none',
                                                            showlegend=True
                                                        ))
                                    except Exception as ex_ref:
                                        logger.error(f"Erro ao plotar linhas de referência: {ex_ref}")
                         
                        fig.update_layout(
                            yaxis=dict(
                                title=f"Resultados ({unit})" if unit else "Resultados",
                                showgrid=True,
                                gridcolor='#2d313f' if tema_is_dark else '#e2e8f0'
                            ),
                            title="Evolução Temporal dos Indicadores Selecionados"
                        )
 
                    # Coletar datas reais de exames e formatar rótulos em duas linhas com mês abreviado em português (ex: 19-Fev)
                    datas_reais = sorted(df_plot['Data Formatada'].dropna().unique())
                    tick_vals = [d for d in datas_reais]
                     
                    meses_pt = {
                        1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr", 5: "Mai", 6: "Jun",
                        7: "Jul", 8: "Ago", 9: "Set", 10: "Out", 11: "Nov", 12: "Dez"
                    }
                     
                    tick_text = []
                    for d in datas_reais:
                        dt = pd.to_datetime(d)
                        dia = dt.strftime("%d")
                        mes = meses_pt.get(dt.month, "")
                        ano = dt.strftime("%Y")
                        tick_text.append(f"{dia}-{mes}<br>{ano}")
 
                    fig.update_layout(
                        template="plotly_dark" if tema_is_dark else "plotly_white",
                        plot_bgcolor="rgba(0,0,0,0)",
                        paper_bgcolor="rgba(0,0,0,0)",
                        height=435,  # Altura aprovada pelo usuario
                        margin=dict(t=80, b=20, l=10, r=10),  # Margens aprovadas pelo usuario
                        xaxis=dict(
                            title=f"Data do Exame<br>Paciente: {selected_paciente}",
                            tickmode="array",
                            tickvals=tick_vals,
                            ticktext=tick_text,
                            showgrid=True,
                            gridcolor='#2d313f' if tema_is_dark else '#e2e8f0',
                            showspikes=False  # Desativa qualquer linha guia vertical ao apontar o cursor
                        ),
                        hoverlabel=dict(
                            bgcolor="#161920" if tema_is_dark else "#ffffff",
                            font_size=11,  # Diminui o tamanho da fonte
                            font_family="Outfit, Inter, sans-serif",
                            bordercolor="#2d3748" if tema_is_dark else "#cbd5e1"
                        ),
                        hovermode="closest",  # Foca no ponto mais próximo individualmente, deixando o box pequeno
                        font=dict(family="Outfit, sans-serif", color="#ffffff" if tema_is_dark else "#1e293b"),
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                    )
                    plotly_config = {
                        'displaylogo': False,
                        'displayModeBar': 'hover',
                        'modeBarButtonsToRemove': ['sendDataToCloud', 'lasso2d', 'select2d'],
                        'locale': 'pt-BR',
                        'locales': {
                            'pt-BR': {
                                'dictionary': {
                                    'Autoscale': 'Autoescala',
                                    'Box Select': 'Seleção em caixa',
                                    'Click to zoom in': 'Clique para ampliar',
                                    'Click to zoom out': 'Clique para reduzir',
                                    'Compare data on hover': 'Comparar dados ao passar o mouse',
                                    'Double-click to zoom back out': 'Duplo clique para redefinir zoom',
                                    'Download plot as a png': 'Baixar gráfico como PNG',
                                    'Download plot as png': 'Baixar gráfico como PNG',
                                    'Download plot': 'Baixar gráfico',
                                    'Download': 'Baixar',
                                    'Edit in Chart Studio': 'Editar no Chart Studio',
                                    'IE settings': 'Configurações do IE',
                                    'Lasso Select': 'Seleção livre (laço)',
                                    'Orbit rotation': 'Rotação orbital',
                                    'Pan': 'Mover',
                                    'Reset camera to default': 'Redefinir câmera',
                                    'Reset camera to last save': 'Redefinir câmera para última gravação',
                                    'Reset view': 'Restaurar visualização',
                                    'Reset y axis limits': 'Redefinir limites do eixo Y',
                                    'Reset axis limits': 'Redefinir limites dos eixos',
                                    'Reset axes': 'Redefinir eixos',
                                    'Reset scale': 'Redefinir escala',
                                    'Select': 'Selecionar',
                                    'Show closest data on hover': 'Mostrar dados mais próximos ao passar o mouse',
                                    'Snapshot': 'Captura de tela',
                                    'Toggle Hover': 'Alternar dicas ao passar o mouse',
                                    'Toggle Spike Lines': 'Alternar linhas guia',
                                    'Toggle Fullscreen': 'Tela cheia',
                                    'toggle fullscreen': 'Tela cheia',
                                    'Fullscreen': 'Tela cheia',
                                    'fullscreen': 'Tela cheia',
                                    'Turntable rotation': 'Rotação de mesa',
                                    'Zoom': 'Zoom',
                                    'Zoom in': 'Ampliar',
                                    'Zoom out': 'Reduzir',
                                    'zoom': 'zoom',
                                    'pan': 'mover',
                                    'select': 'selecionar',
                                    'lasso': 'laço',
                                    'zoomIn': 'ampliar',
                                    'zoomOut': 'reduzir',
                                    'autoScale': 'autoescala',
                                    'resetScale': 'resetar escala',
                                    'resetViews': 'resetar visualizações',
                                    'resetView': 'resetar visualização',
                                    'resetAxes': 'redefinir eixos',
                                    'hoverClosestCartesian': 'mostrar mais próximo',
                                    'hoverCompareCartesian': 'comparar dados',
                                    'toggleSpikelines': 'alternar linhas guia',
                                    'toggleHover': 'alternar dicas'
                                }
                            }
                        }
                    }
                    with pd_st.container(key="container_do_grafico"):
                        pd_st.plotly_chart(fig, width="stretch", config=plotly_config, key="plotly_static")


        with col2:
            pd_st.subheader("📋 Resumo do Filtro Atual")
            if not df_filtered.empty:
                pd_st.markdown(f"**Paciente:** {df_filtered['Paciente'].iloc[0]}")
                
                if 'Data Formatada' in df_filtered.columns and not df_filtered['Data Formatada'].isna().all():
                    idx_max = df_filtered['Data Formatada'].idxmax()
                    last_coleta = df_filtered.loc[idx_max, 'Data Exame']
                else:
                    last_coleta = df_filtered['Data Exame'].max()
                pd_st.markdown(f"**Última Coleta:** {last_coleta}")
                
                # Carrega referências dinâmicas se existirem
                ref_dict = {}
                ref_csv_path = "data/exames/exame_references.csv"
                
                # Coleta dados clínicos do paciente logado para carregar o VR correto
                p_sex = user_data.get("sexo", "Ambos")
                p_birth = user_data.get("data_nascimento")
                p_age = None
                p_faixa = "Ambos"
                p_preg = user_data.get("gravidez", False)
                
                if p_birth and last_coleta:
                    try:
                        birth_d = datetime.strptime(p_birth, "%d/%m/%d%y" if len(p_birth.split('/')[-1]) == 2 else "%d/%m/%Y")
                        exam_d = datetime.strptime(last_coleta, "%d/%m/%Y")
                        p_age = exam_d.year - birth_d.year - ((exam_d.month, exam_d.day) < (birth_d.month, birth_d.day))
                        p_faixa = "Adulto" if p_age > 20 else "Infantil"
                    except Exception:
                        pass
                
                if os.path.exists(ref_csv_path):
                    try:
                        import csv
                        with open(ref_csv_path, 'r', encoding='utf-8') as ref_f:
                            ref_reader = csv.reader(ref_f)
                            next(ref_reader, None)  # Pula header
                            for ref_row in ref_reader:
                                if len(ref_row) >= 8:
                                    exam_name, uni, ref_c, ref_p, r_sex, r_faixa, r_preg, _ = ref_row
                                    
                                    # Valida compatibilidade clínica
                                    if r_sex != "Ambos" and r_sex.upper() != p_sex.upper():
                                        continue
                                    if r_faixa != "Ambos" and r_faixa.upper() != p_faixa.upper():
                                        continue
                                    if r_preg.upper() != str(p_preg).upper():
                                        continue
                                        
                                    ref_dict[exam_name] = (ref_c, ref_p)
                    except Exception as e:
                        logger.error(f"Erro ao carregar referências do CSV: {e}")

                # Mostrar os últimos valores de forma resumida em cards
                last_values = df_filtered.sort_values(by='Data Formatada').groupby('Exame/Componente').last().reset_index()
                cards_html = []
                for _, row in last_values.iterrows():
                    val_uni = f"{row['Resultado']} {row['Unidade'] if pd.notna(row['Unidade']) else ''}"
                    cor_exame = cor_map.get(row['Exame/Componente'], "#0284c7")
                    
                    # Tenta obter a referência específica do paciente ou a completa
                    ref_text = "N/A"
                    if row['Exame/Componente'] in ref_dict:
                        ref_completa, ref_paciente = ref_dict[row['Exame/Componente']]
                        ref_text = ref_paciente if ref_paciente else ref_completa
                        
                    cards_html.append(
                        f'<div class="metric-card" style="border-left: 4px solid {cor_exame};">'
                        f'<strong style="font-size: 0.95em; display: inline-block; color: {cor_exame};">{row["Exame/Componente"]}</strong><br/>'
                        f'<span style="font-size: 1.25em; color: {cor_exame}; font-weight: bold; display: inline-block; margin-top: 3px;">{val_uni}</span>'
                        f'</div>'
                    )
                
                all_cards_html = "\n".join(cards_html)
                pd_st.markdown(
                    f'<div class="metric-cards-container">\n{all_cards_html}\n</div>',
                    unsafe_allow_html=True
                )
            else:
                pd_st.write("Sem dados para exibir resumo.")

        # Exibição da tabela de dados filtrados com container isolado
        with pd_st.container(key="container_da_tabela"):
            pd_st.subheader("🔎 Detalhes dos Dados")
            if not df_filtered.empty:
                # Se carregamos o dicionário de referências, podemos atualizar a coluna 'Referência' na tabela final com a do paciente
                df_table = df_filtered.copy()
                if ref_dict:
                    def get_specific_ref(row_exam, original_ref):
                        if row_exam in ref_dict:
                            comp, pac = ref_dict[row_exam]
                            return pac if pac else comp
                        return original_ref
                    df_table['Referência'] = df_table.apply(lambda r: get_specific_ref(r['Exame/Componente'], r['Referência']), axis=1)

                display_cols = ["Data Exame", "Exame/Componente", "Resultado", "Unidade", "Referência", "Médico", "Laboratório"]
                pd_st.dataframe(df_table[display_cols].reset_index(drop=True), width="stretch")
            else:
                pd_st.write("Selecione algum filtro na barra lateral.")
