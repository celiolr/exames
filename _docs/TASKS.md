# Cronograma de Tarefas (TASKS.md)

Este documento detalha o planejamento de desenvolvimento dividido em Sprints granulares para a automatização e visualização de exames clínicos.

---

## Sprint 0: Análise de Viabilidade (HTML vs PDF)
**Objetivo:** Inspecionar o portal de resultados do Laboratório Pretti e definir a melhor estratégia de coleta de dados (seja por download de PDF impresso ou raspagem da árvore HTML diretamente na tela).

- [x] **Tarefa 0.1: Mapeamento de Autenticação**
  - [x] 0.1.1: Inspecionar seletores CSS do formulário de login (CPF/usuário, senha, botão de entrar).
  - [x] 0.1.2: Validar comportamento da sessão (cookies, persistência, tempo de expiração).
  - [x] 0.1.3: Verificar presença de mecanismos de segurança anti-bot (CAPTCHA, Cloudflare, etc.).
  - [x] 0.1.4: Tarefa Concluída
- [x] **Tarefa 0.2: Inspeção do Painel de Resultados**
  - [x] 0.2.1: Mapear a navegação pós-login até a lista histórica de exames.
  - [x] 0.2.2: Inspecionar a estrutura do link de visualização/download de cada exame.
  - [x] 0.2.3: Tarefa Concluída
- [x] **Tarefa 0.3: Comparativo de Estrutura (HTML vs PDF)**
  - [x] 0.3.1: Capturar a estrutura HTML de um exame completo renderizado no navegador.
  - [x] 0.3.2: Baixar o PDF impresso equivalente desse mesmo exame.
  - [x] 0.3.3: Avaliar a facilidade de extração semântica de tabelas e metadados em cada formato (HTML ou PDF).
  - [x] 0.3.4: Definir a estratégia final (HTML ou PDF) e atualizar a arquitetura no `PRD.md` caso necessário.
  - [x] 0.3.5: Tarefa Concluída
- [x] Sprint 0 Concluída

---

## Sprint 1: Automação da Coleta (Crawler com D4vinci/Scrapling)
**Objetivo:** Desenvolver o script de automação (`crawler.py`) para realizar autenticação e downloads incrementais de novos exames utilizando credenciais seguras do `.env` e a biblioteca D4vinci/Scrapling.

- [x] **Tarefa 1.1: Configuração das Credenciais do Ambiente**
  - [x] 1.1.1: Estruturar o arquivo `.env` para suportar múltiplos pacientes dinamizados (Ex: `PACIENTE_1_NOME`, `PACIENTE_1_USER`, `PACIENTE_1_PASS`, `LIMIT_EXAM_DOWNLOAD`).
  - [x] 1.1.2: Desenvolver validador de variáveis de ambiente no crawler para evitar execuções sem credenciais.
  - [x] 1.1.3: Tarefa Concluída
- [x] **Tarefa 1.2: Implementação do Módulo de Autenticação**
  - [x] 1.2.1: Implementar a lógica de login exclusivamente com `D4vinci/Scrapling` (usando `scrapling` com `PlaywrightFetcher`) para o portal Pretti.
  - [x] 1.2.2: Criar tratamento de erros para credenciais incorretas ou falhas na carga da página de autenticação.
  - [x] 1.2.3: Tarefa Concluída
- [x] **Tarefa 1.3: Mapeamento e Download Incremental**
  - [x] 1.3.1: Implementar listagem e ordenação temporal dos últimos N exames.
  - [x] 1.3.2: Criar verificação incremental: verificar se o arquivo equivalente já existe na pasta `data/exames/` antes de efetuar o download.
  - [x] 1.3.3: Implementar o download efetivo e salvar os arquivos brutos com a nomenclatura padrão: `data/exames/paciente_<primeiro_ultimo>-medico_<primeiro_ultimo>-data.pdf`.
  - [x] 1.3.4: Adicionar checagem de integridade para confirmar se o nome do paciente no exame confere com o cadastrado no `.env`.
  - [x] 1.3.5: Tarefa Concluída
- [x] Sprint 1 Concluída

---

## Sprint 2: Módulo Parser (Extração e Estruturação de Dados)
**Objetivo:** Desenvolver/adaptar os scripts `pdf_processor.py` (ou correspondente HTML) e `data_extractor.py` para converter os dados brutos em registros tabulares no arquivo CSV.

- [x] **Tarefa 2.1: Conversão para Formato Intermediário (Markdown)**
  - [x] 2.1.1: Adaptar o script `pdf_processor.py` para ler os PDFs/HTMLs de `data/exames/`.
  - [x] 2.1.2: Implementar limpeza automática de encodings corrompidos e caracteres quebrados na extração textual.
  - [x] 2.1.3: Gravar a saída incrementalmente em `data/exames/exames_md/{nome_arquivo}.md`.
  - [x] 2.1.4: Tarefa Concluída
- [x] **Tarefa 2.2: Extração de Metadados e Componentes**
  - [x] 2.2.1: Adaptar o script `data_extractor.py` para ler arquivos MD da pasta `data/exames/exames_md/`.
  - [x] 2.2.2: Implementar regexes para extrair metadados comuns (Paciente, Médico, Laboratório, Data do Exame).
  - [x] 2.2.3: Desenvolver parser estruturado para extrair os componentes de Hemogramas, Leucogramas e exames bioquímicos avulsos (Valor, Unidade, Referência).
  - [x] 2.2.4: Tarefa Concluída
- [x] **Tarefa 2.3: Consolidação e Backup no CSV**
  - [x] 2.3.1: Desenvolver fluxo de backup: antes de atualizar `data/exames/results/results-*.csv`, copiar o atual para `.csv.bak`.
  - [x] 2.3.2: Consolidar novas métricas sem duplicar dados já processados (validando pela tupla única: Data Exame, Paciente, Exame/Componente, Resultado).
  - [x] 2.3.3: Tarefa Concluída
- [x] Sprint 2 Concluída

---

## Sprint 3: Validação de Qualidade (Auditoria de Dados)
**Objetivo:** Garantir a fidelidade e consistência dos resultados extraídos em relação aos exames originais.

- [x] **Tarefa 3.1: Algoritmo de Amostragem**
  - [x] 3.1.1: Desenvolver o script `auditoria.py` na pasta `app/`.
  - [x] 3.1.2: Implementar seleção randômica baseada na taxa carregada do `config.ini` das linhas geradas no arquivo CSV.
  - [x] 3.1.3: Tarefa Concluída
- [x] **Tarefa 3.2: Validação Cruzada (Amostra vs PDF Original)**
  - [x] 3.2.1: Implementar lógica para buscar os valores diretamente no PDF original da amostra sorteada e cruzar com o dado escrito no CSV.
  - [x] 3.2.2: Gerar alertas se houver divergências de valor, unidade de medida ou nomes de exames.
  - [x] 3.2.3: Tarefa Concluída
- [x] **Tarefa 3.3: Relatório de Auditoria**
  - [x] 3.3.1: Desenvolver exportação do relatório de auditoria em `data/exames/auditoria/auditoria_valores_{paciente_sanitizado}_{timestamp}.md`.
  - [x] 3.3.2: Tarefa Concluída
- [x] Sprint 3 Concluída

---

## Sprint 4: Painel e Orquestração (Dashboard Interativo)
**Objetivo:** Criar a interface visual no Streamlit (`dashboard.py`), integrando a exibição analítica com o acionador em tempo real das rotinas do crawler e parser.

- [x] **Tarefa 4.1: Ajustes da Interface Visual e CSS Premium**
  - [x] 4.1.1: Estruturar o visual Dark Mode Premium com estilizações CSS customizadas para os componentes do Streamlit.
  - [x] 4.1.2: Tarefa Concluída
- [x] **Tarefa 4.2: Implementação dos Filtros Dinâmicos**
  - [x] 4.2.1: Integrar os filtros na barra lateral: Paciente (inicia selecionando o primeiro disponível na base de dados), Médico, Laboratório, Datas e Componentes.
  - [x] 4.2.2: Implementar lógica de reatividade para recalcular as métricas e atualizar a tabela com base nos filtros selecionados.
  - [x] 4.2.3: Tarefa Concluída
- [x] **Tarefa 4.3: Gráfico de Evolução Histórica (Eixo Duplo)**
  - [x] 4.3.1: Desenvolver gráfico de linha temporal interativo com Plotly.
  - [x] 4.3.2: Implementar suporte a eixo Y secundário (dual-axis) para exibir componentes com escalas/unidades diferentes na mesma janela temporal.
  - [x] 4.3.3: Tarefa Concluída
- [x] **Tarefa 4.4: Botão de Sincronização em Tempo Real**
  - [x] 4.4.1: Implementar botão "🔄 Atualizar Exames" no dashboard.
  - [x] 4.4.2: Vincular o clique do botão à chamada em cadeia: `crawler.py` ➔ `pdf_processor.py` ➔ `data_extractor.py` ➔ `auditoria.py`.
  - [x] 4.4.3: Implementar limpeza de cache (`st.cache_data.clear()`) e recarga automática da tela (`st.rerun()`).
  - [x] 4.4.4: Tarefa Concluída
- [x] Sprint 4 Concluída

---

## Sprint 5: Homologação e Testes Finais
**Objetivo:** Validar o projeto completo sob diferentes cenários de carga de dados e múltiplos usuários.

- [x] **Tarefa 5.1: Testes de Integração com Múltiplos Pacientes**
  - [x] 5.1.1: Cadastrar mais de um paciente no arquivo `.env` para validar o isolamento e agregação correta de dados no CSV.
  - [x] 5.1.2: Tarefa Concluída
- [x] **Tarefa 5.2: Validação de Concorrência e Tratamento de Exceções**
  - [x] 5.2.1: Testar falhas na conexão de rede durante o crawler e assegurar que a base de dados CSV e seus backups permaneçam intactos.
  - [x] 5.2.2: Documentar o fluxo final de setup no `README.md`.
  - [x] 5.2.3: Tarefa Concluída
- [x] Sprint 5 Concluída

---

## Sprint 6: Painel Inteligente & Segurança (Autenticação e Presets)
**Objetivo:** Implementar o fluxo de autenticação e autorização por perfis de acesso (roles) com credenciais do `config.ini`, juntamente com botões de filtros clínicos rápidos (Presets) no dashboard.

- [x] **Tarefa 6.1: Sistema de Autenticação na Inicialização (Login)**
  - [x] 6.1.1: Desenvolver a interface visual de login no topo do aplicativo utilizando o `st.session_state` do Streamlit.
  - [x] 6.1.2: Implementar validador de credenciais que lê os dados dos pacientes na seção `[Pacientes]` do [config.ini](../config.ini).
  - [x] 6.1.3: Bloquear toda a visualização do painel e qualquer fluxo de atualização caso a sessão de login não esteja ativa.
- [x] **Tarefa 6.2: Controle de Acesso e Privacidade por Perfil (Role)**
  - [x] 6.2.1: Ler o campo `"role"` de cada paciente no [config.ini](../config.ini).
  - [x] 6.2.2: Se a role for `"admin"`, dar acesso ao selectbox contendo todos os pacientes disponíveis nos resultados tabulados.
  - [x] 6.2.3: Se a role for normal (ou não definida), travar e desabilitar o selectbox para exibir estritamente os exames do próprio usuário logado, garantindo o sigilo dos dados clínicos.
- [x] **Tarefa 6.3: Filtros Rápidos de Combinação (Presets Clínicos)**
  - [x] 6.3.1: Criar botões na barra lateral com as seguintes combinações médicas mapeadas:
    - **Controle de Diabetes:** `["Glicose em Jejum", "Hemoglobina Glicada (HbA1c)", "Glicemia Média Estimada"]`
    - **Função Renal:** `["Ureia", "Creatinina Sérica", "Ácido Úrico"]`
    - **Função Hepática:** `["TGO (AST)", "TGP (ALT)", "Gama Gt", "Fosfatase Alcalina"]`
    - **Perfil Lipídico:** `["Colesterol Total", "Colesterol HDL", "Triglicerídeos"]`
    - **Hemograma Completo:** Todos os exames contendo prefixo `Hemograma - ` ou `Leucograma - `
    - **Hormônios & Tireoide:** `["TSH Ultra Sensível", "T4 Livre", "25-Hidroxivitamina D"]`
    - **PSA (Saúde Masculina):** `["Psa Total Ultra Sensível"]`
  - [x] 6.3.2: Implementar reatividade: ao selecionar um preset, aplicar os componentes na multiseleção de exames e recarregar os dados do gráfico interativo Plotly dinamicamente.
- [x] **Tarefa 6.4: Homologação da Nova Camada**
  - [x] 6.4.1: Executar a suíte de testes em `tests/run_tests.py` e expandir casos de validação para a lógica de autenticação e visibilidade de paciente por role.
- [x] Sprint 6 Concluída

---

## Sprint 7: Logging Estruturado, Reset & Qualidade de Auditoria
**Objetivo:** Implementar telemetria robusta por loguru, script completo de reset e correções fundamentais de regressão nos mapeamentos do auditor de PDF.

- [x] **Tarefa 7.1: Telemetria e Logging Centralizado**
  - [x] 7.1.1: Configurar logger unificado com `loguru` em `app/logger.py`.
  - [x] 7.1.2: Redirecionar logs estruturados com rotação diária para `_temp/pipeline.log`.
  - [x] 7.1.3: Adicionar medição de tempo por etapas do pipeline.
- [x] **Tarefa 7.2: Script do Orquestrador de Reset**
  - [x] 7.2.1: Criar script interativo `resetall.ps1` com confirmação e logs coloridos.
- [x] **Tarefa 7.3: Tratamento de Status na Inicialização**
  - [x] 7.3.1: Exibir status e progresso do pipeline via `st.status` no painel principal.
- [x] **Tarefa 7.4: Resolução de Bugs de Mapeamento de Termos de PDF**
  - [x] 7.4.1: Corrigir o mapeamento de termos do PDF para "GLICOSE EM JEJUM" (vs "GLICOSE JEJUM").
  - [x] 7.4.2: Adicionar busca contextual em 2 níveis e suporte a novos aliases.
- [x] **Tarefa 7.5: Suíte de Testes da Auditoria**
  - [x] 7.5.1: Implementar suíte com 29 testes automáticos em `tests/test_auditoria.py` e integrá-la à suíte geral.
- [x] Sprint 7 Concluída

---

## Sprint 8: Otimização de Layout, Sincronização Visual & Segurança
**Objetivo:** Otimizar e compactar visualmente os componentes do painel Streamlit e Plotly e consolidar a segurança de dados do repositório.

- [x] **Tarefa 8.1: Otimização e Compactação dos Cards de Métricas**
  - [x] 8.1.1: Desenvolver visual dos cards com fontes comprimidas e entrelinhas otimizado.
  - [x] 8.1.2: Limitar altura vertical máxima em `380px` com scroll Webkit personalizado de `4px`.
- [x] **Tarefa 8.2: Sincronização Dinâmica de Cores (Gráfico ➔ Cards)**
  - [x] 8.2.1: Definir `cor_map` global compartilhado.
  - [x] 8.2.2: Sincronizar dinamicamente a cor da fonte e da borda esquerda de cada card com a linha do gráfico Plotly.
- [x] **Tarefa 8.3: Resolução de Bugs de Exibição de Dados**
  - [x] 8.3.1: Corrigir ordenação cronológica de "Última Coleta" por `Data Formatada` no lugar de string alfabética.
  - [x] 8.3.2: Implementar algoritmo dinâmico de distanciamento de texto (`textposition`) para evitar sobreposições de anotações no Plotly em pontos coincidentes.
- [x] **Tarefa 8.4: Anonimização de Dados e Higienização de Repositório**
  - [x] 8.4.1: Criar mockup 100% anonimizado em `_docs/dashboard_mockup.png` sob o nome de "Lucas Silva".
  - [x] 8.4.2: Limpar relatórios médicos MD e screenshots de dados reais de exames fora da pasta `data/`.
- [x] Sprint 8 Concluída
