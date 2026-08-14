# Product Requirement Document (PRD): Download e Estruturação de Exames Clínicos

## 1. Visão Geral do Produto
O objetivo deste produto é automatizar a coleta, armazenamento e visualização histórica de exames clínicos laboratoriais a partir do portal de resultados do laboratório (inicialmente focado no **Laboratório Pretti**). 

O sistema deve fazer login de forma segura para múltiplos pacientes, identificar novos exames disponíveis, efetuar a raspagem das informações (ou download do documento), converter os resultados para um formato textual estruturado (Markdown) e consolidar os dados históricos em arquivos CSV específicos por paciente, realizando uma auditoria de amostragem configurável dos dados no CSV contra os PDFs originais para exibição em um dashboard interativo.

---

## 2. Objetivos Principais
1. **Automação do Download:** Efetuar login no portal de exames utilizando credenciais seguras (user/password) armazenadas localmente no arquivo `config.ini`.
2. **Coleta de Histórico:** Baixar os últimos N exames (configurados no `config.ini`) de cada paciente cadastrado.
3. **Conversão Incremental:** Converter novos arquivos de exames (PDF) para Markdown (.md), pulando os que já foram processados anteriormente.
4. **Estruturação Analítica:** Parsear o Markdown gerando arquivos CSV por paciente com as métricas individuais dos exames (formato: uma linha por métrica/componente).
5. **Dashboard Interativo:** Exibir a evolução temporal dos resultados com suporte a filtros dinâmicos e eixos múltiplos de escala (dual-axis) no Streamlit.

---

## 3. Especificações Técnicas & Arquitetura

### 3.1. Crawler & Download (Módulo `crawler`)
- **Tecnologia:** Python + `scrapling` (com o motor adaptativo para lidar com mudanças no layout do portal do laboratório). Esse motor deve usar exclusivamente o repositório do [D4vinci/Scrapling](https://github.com/D4vinci/Scrapling). 
- **Configurações e Credenciais:** Armazenadas no arquivo local `config.ini` no formato:
  ```ini
  [Config]
  LIMIT_EXAM_DOWNLOAD = 2
  AUDIT_SAMPLE_PERCENTAGE = 0.20

  [Laboratorios]
  pretti = https://pretti.shiftcloud.com.br/shift/lis/pretti/elis/s01.iu.web.Login.cls?config=UNICO&sigla=

  [Pacientes]
  paciente_exemplo = {"nome": "Paciente Exemplo", "user": "P12345", "pass": "SenhaExemplo123", "lab": "pretti"}
  ```
- **Fluxo do Downloader:**
  1. Efetuar o login no portal usando a URL e credenciais do lab.
  2. Navegar até a lista de exames.
  3. Identificar os N exames mais recentes.
  4. Salvar na pasta `data/exames/` usando a nomenclatura padrão: `paciente_<primeiro_ultimo>-medico_<primeiro_ultimo>-data.pdf`.

### 3.2. Processamento, Extração & Auditoria (Módulo `parser`)
- **Conversão e Integração Incremental:**
  - **Conversor PDF para MD (`pdf_processor.py`):** Executa incrementalmente na inicialização do servidor ou sob demanda (ignora se o arquivo `.md` correspondente já existir em `exames_md/`). Realiza a higienização de codificações e caracteres corrompidos comuns.
  - **Conversor MD para CSV (`data_extractor.py`):** Mapeia tabelas e componentes dos exames para arquivos CSV específicos por paciente: `data/exames/results/results-{paciente_sanitizado}.csv`. Gera backup automático `.csv.bak` de segurança individual antes de alterar dados existentes.
- **Auditoria Automática de Qualidade:**
  - Realiza uma checagem/auditoria amostral independente baseada na taxa `AUDIT_SAMPLE_PERCENTAGE` dos dados gerados no CSV contra os arquivos **PDF originais** extraindo o texto bruto para atestar a precisão final da extração. Os relatórios de auditoria são gerados individualmente em `data/exames/auditoria/auditoria_valores_{paciente_sanitizado}_{timestamp}.md`.

### 3.3. Painel de Visualização & Gatilhos (Módulo `dashboard` / `dashboard.py`)
O painel Streamlit é o hub central do projeto e gerencia os fluxos de dados de ponta a ponta:
- **Fluxo na Inicialização:** Ao subir o servidor do Streamlit (`dashboard.py`), o sistema executa automaticamente a rotina incremental do `pdf_processor.py` e `data_extractor.py` para garantir que quaisquer arquivos locais pendentes na pasta `exames/` sejam processados e auditados antes do render.
- **Sincronização em Tempo Real (Botão de Atualização):**
  - Um botão interativo na interface permite que o usuário dispare o ciclo completo:
    1. Executar o **Crawler** (buscar e baixar novos exames no portal do Laboratório Pretti de todos os pacientes configurados no `config.ini`).
    2. Executar o **Parser** de forma incremental (converter novos arquivos de `exames/` para `exames_md/` e atualizar os CSVs em `exames/results/`).
    3. Executar o processo de **Auditoria** diretamente contra os PDFs.
    4. Limpar o cache de dados do Streamlit e recarregar a visualização instantaneamente.
- **Visualização Analítica:**
  - **Filtros Dinâmicos:** Filtros na barra lateral por Paciente (inicia selecionando o primeiro disponível na base), Médico, Laboratório, Data e Componente/Exame.
  - **Gráfico de Evolução:** Exibição temporal com múltiplos eixos Y dinâmicos (eixo duplo) se os exames selecionados possuírem unidades diferentes (ex: Glicose em `mg/dL` e Hemoglobina Glicada em `%`).

---

## 4. Requisitos Não-Funcionais
- **Privacidade e Segurança:** As credenciais do portal nunca devem ser commitadas no Git (configuradas no `.gitignore`).
- **Resiliência:** Tratamento de erros caso o portal de exames esteja instável ou exija novos fluxos de autenticação.
- **Incrementalidade:** Otimização do tempo de carregamento pulando downloads e conversões de arquivos que já existem localmente.

---

## 5. Estrutura de Diretórios do Projeto
A estrutura do repositório segue os padrões de uma aplicação estruturada, com os arquivos executáveis centralizados no diretório `app/`, e todo o ecossistema de dados (arquivos brutos, convertidos e base consolidadas) encapsulado no diretório `data/`:

```text
exames/
├── config.ini            # Credenciais e parâmetros do crawler/pacientes (Ignorado no Git)
├── .env                  # Variáveis de ambiente locais auxiliares (Ignorado no Git)
├── .gitignore            # Filtros do Git (ignora config.ini, .env, venv, caches)
├── requirements.txt      # Dependências do Python (pandas, streamlit, scrapling, etc.)
├── setup.ps1             # Script auxiliar de setup de ambiente local
├── README.md             # Guia de instalação, configuração e execução
│
├── _docs/                # Documentação técnica do projeto
│   ├── PRD.md            # Este Documento de Requisitos
│   └── TASKS.md          # Cronograma de desenvolvimento e tarefas
│
├── data/                 # Pasta contendo todo o ciclo de dados
│   └── exames/           # Gerenciamento de exames locais
│       ├── paciente_exemplo-medico_exemplo-2026-08-10.pdf # PDFs baixados
│       ├── exames_md/    # Arquivos MD convertidos pelo parser
│       │   └── paciente_exemplo-medico_exemplo-2026-08-10.md
│       ├── auditoria/    # Relatórios históricos de auditoria de qualidade
│       │   └── auditoria_valores_*.md
│       ├── output/       # Screenshots de erro de login (debugging do crawler)
│       └── results/      # Base de dados estruturada por paciente
│           ├── results-paciente_exemplo.csv     # Dados tabulares individuais
│           └── results-paciente_exemplo.csv.bak # Backup automático
│
└── app/                  # Pasta da aplicação contendo os scripts (.py)
    ├── crawler.py        # Robô de raspagem e download (Scrapling)
    ├── pdf_processor.py  # Conversor de PDFs originais para Markdown
    ├── data_extractor.py # Extrator e consolidador de dados do Markdown para o CSV
    ├── auditoria.py      # Script para validação de 20% das amostras CSV vs PDF
    └── dashboard.py      # Interface Streamlit e orquestrador principal das tarefas
```
