# Checkpoint de Sessão para o Gemini (Handoff)

Este arquivo serve como resumo de progresso e contexto técnico para que o próximo agente IA possa retomar as melhorias do projeto sem precisar reler todo o histórico de conversas.

---

## 📍 Estado Atual do Projeto

O projeto é um pipeline estruturado e automatizado de extração e visualização de dados clínicos:
1. **Instalação:** Automatizada no Windows via [`setup.ps1`](setup.ps1) e executada via [`run.ps1`](run.ps1) (Streamlit).
2. **Reset:** [`resetall.ps1`](resetall.ps1) apaga todos os dados gerados (PDFs, MDs, CSVs, auditorias, logs) para reiniciar do zero.
3. **Configurações:** Migradas com sucesso do antigo `.env` para o [`config.ini`](config.ini) (e o exemplo seguro [`config.ini_example`](config.ini_example)). Mapeia URLs de login e credenciais/laboratórios de múltiplos pacientes em formato JSON dict.
4. **Segurança de Dados (Crucial):** Todos os dados confidenciais estão localizados na pasta `data/` e em `data/exames/auditoria/`, ambas ignoradas no [`.gitignore`](.gitignore). **Nenhum dado real de exames ou nomes de pacientes deve ser incluído no repositório de códigos.**

---

## 🛠️ Arquitetura dos Módulos

* **[`crawler.py`](app/crawler.py):** Efetua login e baixa PDFs usando o motor dinâmico **[D4vinci/Scrapling](https://github.com/D4vinci/Scrapling)**.
* **[`pdf_processor.py`](app/pdf_processor.py):** Converte incrementalmente PDFs brutos para Markdown (`.md`).
* **[`data_extractor.py`](app/data_extractor.py):** Parseia os markdowns e salva em arquivos CSV individuais por paciente (`results-*.csv`).
* **[`data_extractor_reference.py`](app/data_extractor_reference.py):** Extrai unidades e valores de referência (VR) do exame mais recente aplicando metadados do paciente (`config.ini`).
* **[`auditoria.py`](app/auditoria.py):** Abre os PDFs brutos originais (via `pdfplumber`), confronta as amostras e exporta relatórios de qualidade em `data/exames/auditoria/`. Auditoria configurada para **100% dos registros** (`AUDIT_SAMPLE_PERCENTAGE = 1.0`).
* **[`auditoria_reference.py`](app/auditoria_reference.py):** Faz validação cruzada alfanumérica contínua das referências extraídas confrontando diretamente com o PDF original.
* **[`logger.py`](app/logger.py):** Logger centralizado com `loguru` — saída colorida no console + arquivo rotativo em `_temp/pipeline.log`. Mede tempo de cada etapa do pipeline.
* **[`dashboard.py`](app/dashboard.py):** Interface Dark Mode Streamlit com gráficos Plotly de eixo duplo, cartões de resumo integrados com referências do paciente, tela de login (RBAC), presets clínicos e botão de atualização em lote. Pipeline de startup roda **uma única vez por processo** via `@st.cache_resource`.

---

## 📈 Sprint 7 — 100% Concluída ✅

1. **Sistema de logging com loguru:**
   - Saída colorida no console (DEBUG/INFO/SUCCESS/WARNING/ERROR)
   - Arquivo rotativo em `_temp/pipeline.log` (rotação diária, retenção 7 dias)
   - Tempo de execução monitorado por etapa (Scraping / Conversão / Extração / Auditoria) e total
   - Integrado em todos os módulos: `crawler.py`, `pdf_processor.py`, `data_extractor.py`, `auditoria.py`, `dashboard.py`

2. **Script `resetall.ps1`:**
   - Apaga todos os dados gerados com confirmação interativa e saída colorida
   - Documentado no README com tabela de scripts utilitários

3. **Tela de loading de startup:**
   - Substitui a mensagem crua `Running _run_startup_once()` por um `st.status` com progresso por etapa
   - Pipeline de startup executa apenas uma vez por processo usando `@st.cache_resource(show_spinner=False)` + dict mutável como flag

4. **Correção crítica de qualidade de auditoria:**
   - **Bug:** `auditoria.py` buscava `"GLICOSE EM JEJUM"` no PDF, mas o PDF contém `"GLICOSE JEJUM"` (sem "EM") — causava 3 falsos negativos
   - **Fix:** Adicionado mapeamento `"GLICOSE EM JEJUM": ["GLICOSE JEJUM", "GLICOSE"]` e revisado todos os mapeamentos do dict
   - **Busca em 2 níveis:** Nível 1 Estrita (termo + valor na mesma linha, alta confiança) → Nível 2 Contextual (na página, sinalizado no relatório)
   - **Auditoria 100%:** `AUDIT_SAMPLE_PERCENTAGE = 1.0` em `config.ini` (obrigatório para dados médicos)
   - Novos aliases cobertos: `INSULINA BASAL`, `COLESTEROL NAO-HDL`, `25-HIDROXIVITAMINA D`, `VITAMINA D (25-HIDROXI)`

5. **Testes unitários de auditoria (`tests/test_auditoria.py`):**
   - **29 testes** cobrindo `TestAuditoriaMapping` e `TestGetPdfSearchTermsDirect`
   - Garante regressão zero para o bug histórico `GLICOSE EM JEJUM` vs `GLICOSE JEJUM`
   - Testa todo mapeamento alias→PDF para cada exame conhecido
   - Roda via `python tests/run_tests.py` junto com a suíte completa (29/29 ✅)

---

## 📋 Regra de Manutenção — Mapeamento Auditoria

> **SEMPRE que `data_extractor.py` criar um novo alias em `examen_alias()`, adicionar o termo original do PDF em `auditoria.py → get_pdf_search_terms() → mappings`.**
>
> Exemplo: alias `"Glicose em Jejum"` ← PDF `"GLICOSE JEJUM"` → mapping `"GLICOSE EM JEJUM": ["GLICOSE JEJUM"]`

---

## 📈 Sprint 8 — 100% Concluída ✅

1. **Otimização de Layout e Compactação:**
   - Cards de métricas compactados verticalmente (reduzindo fontes, padding e margins) para alinhar perfeitamente à altura do gráfico.
   - Limitação de altura máxima (`max-height: 380px`) com scroll vertical personalizado (Webkit Scrollbar de 4px) na lista de cards.
2. **Cores Sincronizadas (Gráfico ➔ Cards):**
   - Cores das fontes e da borda esquerda de cada card sincronizadas dinamicamente à cor da linha do exame correspondente no Plotly.
3. **Resolução de Bugs de Exibição:**
   - **Ordenação de Datas:** Correção no cálculo de "Última Coleta" ordenando por `Data Formatada` (data real/ISO) em vez de string `Data Exame` (alfabético).
   - **Sobreposição no Plotly:** Posicionamento dinâmico de texto (`textposition`) que reposiciona anotações para cima (`top center`) ou para baixo (`bottom center`) quando os pontos de dados coincidem na mesma data.
4. **Segurança de Dados e Anonimização:**
   - Criação de mockup 100% anonimizado em [`_docs/dashboard_mockup.png`](_docs/dashboard_mockup.png) sob o nome fictício "Lucas Silva".
   - Remoção de arquivos temporários de dados sensíveis fora da pasta `data/` (como relatórios md de auditoria antigos e prints de telas reais em `_docs/`).

---

## 📈 Sprint 9 — 100% Concluída ✅

1. **Extração e Auditoria de Referências Dinâmicas:**
   - **Extrator (`data_extractor_reference.py`):** Mapeia apenas o PDF/Markdown mais recente e extrai os valores de referência (VR) e a unidade de cada exame.
   - **Metadados Clínicos:** Lê `data_nascimento` e `sexo` do paciente a partir do `config.ini` e calcula a idade exata no dia do exame, selecionando no texto do VR apenas a regra (adulta/infantil, masculina/feminina) correspondente a ele em `Referencia_Paciente_Especifico`.
   - **Auditoria (`auditoria_reference.py`):** Realiza comparação alfanumérica contínua (100% tolerante a quebras de diagramação do PDF original) validando as referências extraídas (100% de sucesso atingido na validação do laudo recente do Célio).
   - **Suíte de Testes:** 4 testes unitários adicionados em `tests/test_references.py` e integrados à suíte global.
2. **Exibição Dinâmica no Dashboard:**
   - O dashboard Streamlit integra a etapa de referências no pipeline de startup e no botão de recarga da Sidebar.
   - Os cards de resumo exibem a referência filtrada do paciente na terceira linha (ex: `Ref: 60 a 99 mg/dL`).
   - A tabela detalhada exibe a referência adaptada ao perfil do paciente.

---

## 📈 Próximas Ideias

1. Alertas preditivos no dashboard para valores fora do intervalo de referência (highlight em vermelho/amarelo nos gráficos e cards)
2. Suporte a novos portais de laboratório além do Pretti
3. Testes unitários de auditoria (`tests/test_auditoria.py`) para garantir regressão zero quando novos exames forem adicionados

---

## 📈 Sprint 10 — Em Andamento 🔄

### Suporte a Tema Claro/Escuro Dinâmico no Dashboard

1. **CSS Responsivo ao Tema Nativo do Streamlit:**
   - Substituídas as cores fixas hardcoded (ex: `#0f1116`, `#161920`) por variáveis CSS nativas do Streamlit: `var(--background-color)`, `var(--text-color)`, `var(--secondary-background-color)`.
   - Afeta: classe `.main`, `.stAppHeader`, `.stSidebar`, e seletores `h1, h2, h3`.
   - Resultado: navbar e fundo agora respondem corretamente ao tema selecionado (claro/escuro) nas configurações nativas do Streamlit. ✅

2. **Detecção Dinâmica de `tema_is_dark`:**
   - Substituído o valor fixo `tema_is_dark = True` por lógica de detecção via `pd_st.config.get_option("theme.base")` com fallback para `pd_st.get_option("theme.base")`.
   - Objetivo: alternar cores das linhas de referência no Plotly (amarelo no dark, vermelho no light) e cores de grid/hover do gráfico automaticamente.
   - **⚠️ Pendente:** Quando o tema é o padrão do sistema (sem seção `[theme]` definida no `config.toml`), `get_option("theme.base")` retorna `None`, fazendo o fallback cair em `True` (dark). Isso causa a linha de referência permanecer amarela mesmo no tema claro.

3. **Ordem dos Filtros na Sidebar:** ✅
   - Filtro "Exame / Componente" reposicionado logo abaixo do filtro "Médico".

4. **Linhas de Referência Dual-tema:** ✅ (código implementado, detecção pendente)
   - Dark: `rgba(253, 224, 71, 0.85)` (amarelo)
   - Light: `rgba(239, 68, 68, 0.85)` (vermelho)

### ⚠️ Problema Conhecido — Detecção do Tema Padrão

> `pd_st.config.get_option("theme.base")` retorna `None` quando nenhum tema está explicitamente definido no `config.toml` (o usuário usa o padrão do Streamlit ou alterna via UI sem salvar).
>
> **Possível fix:** Usar JavaScript injetado via `pd_st.components.v1.html` para ler `document.body.getAttribute('data-theme')` ou o valor de background do body e retornar via `st.query_params`. Alternativa: pedir ao usuário que defina `[theme]` com `base = "dark"` ou `base = "light"` no `.streamlit/config.toml`.
