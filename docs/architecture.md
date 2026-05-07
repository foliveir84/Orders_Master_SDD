# Orders Master Infoprex — Arquitectura do Sistema

Este documento descreve a estrutura interna do sistema, o fluxo de dados principal e as decisões técnicas que guiaram a implementação. Destina-se a mantenedores e desenvolvedores que necessitam de compreender o interior do sistema para o modificar, estender ou depurar.

---

## 1. Visão Geral da Arquitectura

O sistema segue uma **arquitectura em camadas** com separação rígida entre três camadas:

1. **Camada de Apresentação** (`app.py` + `ui/`) — Contém toda a lógica de renderização Streamlit. Não contém lógica de negócio.
2. **Camada de Aplicação** (`orders_master/app_services/`) — Orquestra os casos de uso, coordenando a camada de domínio. Não contém regras de negócio puras mas coordena a sua execução.
3. **Camada de Domínio** (`orders_master/` excepto `app_services/`) — Contém toda a lógica de negócio pura, validações, cálculos e transformações de dados. **Nenhum módulo de domínio importa `streamlit` directamente** (apenas com guarded imports para caching).

A regra fundamental das dependências: **todas apontam para dentro**. A Apresentação depende da Aplicação; a Aplicação depende do Domínio; o Domínio não depende de ninguém acima dele.

---

## 2. Estrutura de Directorias

```
Orders_Master_SDD/
├── app.py                              # Entry-point Streamlit (thin, ~96 linhas)
├── pyproject.toml                       # Configuração do projecto (deps, ruff, black, mypy, pytest)
├── requirements.txt                     # Dependências de runtime (pinadas)
├── requirements-dev.txt                # Dependências de desenvolvimento
├── .gitignore
├── .env.example                        # Template vazio para variáveis de ambiente
├── .pre-commit-config.yaml             # Hooks de pré-commit
├── .streamlit/
│   └── secrets.toml                    # URLs Google Sheets (NÃO commitado)
├── .github/
│   └── workflows/
│       └── ci.yml                      # Pipeline CI (lint + type check + testes)
├── config/                             # Ficheiros de configuração editáveis em produção
│   ├── laboratorios.json               # Nome do Lab → [códigos CLA]
│   ├── localizacoes.json               # Termo de pesquisa → Alias da farmácia
│   └── presets.yaml                    # Presets de pesos (Conservador/Padrão/Agressivo)
├── orders_master/                       # ===== CAMADA DE DOMÍNIO =====
│   ├── __init__.py
│   ├── constants.py                    # Columns, GroupLabels, Weights, Highlight, Limits
│   ├── schemas.py                      # Schemas pydantic de validação de DataFrames
│   ├── exceptions.py                   # Hierarquia de excepções tipadas + FileError
│   ├── logger.py                       # Logging central (rotativo + session filter)
│   ├── secrets_loader.py              # get_secret() hierárquico (st.secrets → env → .env)
│   ├── ingestion/                      # --- Parsers de ficheiros de entrada ---
│   │   ├── __init__.py
│   │   ├── infoprex_parser.py          # parse_infoprex_file() — parser principal
│   │   ├── codes_txt_parser.py        # parse_codes_txt() — lista de CNPs
│   │   ├── brands_parser.py           # parse_brands_csv() — CSVs de marcas
│   │   └── encoding_fallback.py       # try_read_with_fallback_encodings()
│   ├── aggregation/
│   │   ├── __init__.py
│   │   └── aggregator.py             # aggregate(), build_master_products(), reorder_columns()
│   ├── business_logic/                # --- Regras de negócio puras ---
│   │   ├── __init__.py
│   │   ├── averages.py               # weighted_average(), select_window(), load_presets()
│   │   ├── proposals.py              # compute_base_proposal(), compute_shortage_proposal()
│   │   ├── cleaners.py               # clean_designation_vectorized(), remove_zombie_rows/agg()
│   │   └── price_validation.py       # flag_price_anomalies()
│   ├── integrations/                  # --- Fontes externas ---
│   │   ├── __init__.py
│   │   ├── shortages.py              # fetch_shortages_db(), merge_shortages()
│   │   └── donotbuy.py               # fetch_donotbuy_list(), merge_donotbuy()
│   ├── config/                        # --- Loaders de configuração ---
│   │   ├── __init__.py
│   │   ├── labs_loader.py            # LabsConfig (pydantic), load_labs()
│   │   ├── locations_loader.py       # LocationsConfig (pydantic), load_locations(), map_location()
│   │   ├── presets_loader.py         # load_presets_config() (validação YAML)
│   │   └── validate.py              # CLI: python -m orders_master.config.validate <ficheiro>
│   ├── formatting/                    # --- Formatação condicional ---
│   │   ├── __init__.py
│   │   ├── rules.py                  # HighlightRule dataclass + lista RULES (fonte única de verdade)
│   │   ├── web_styler.py             # build_styler() — Pandas Styler
│   │   └── excel_formatter.py       # build_excel() — openpyxl + nome dinâmico
│   └── app_services/                  # ===== CAMADA DE APLICAÇÃO =====
│       ├── __init__.py
│       ├── session_state.py           # SessionState dataclass, ScopeContext, FileInventoryEntry
│       ├── session_service.py         # process_orders_session() — pipeline pesado
│       └── recalc_service.py          # recalculate_proposal() — pipeline leve
├── ui/                                # ===== CAMADA DE APRESENTAÇÃO =====
│   ├── __init__.py
│   ├── sidebar.py                     # render_sidebar() — 4 blocos + botão Processar
│   ├── main_area.py                   # render_main() — layout vertical 14 componentes
│   ├── scope_bar.py                   # render_scope_summary() — barra métrica horizontal
│   └── file_inventory.py             # render_file_inventory() — tabela de ficheiros
├── tests/                             # ===== TESTES =====
│   ├── conftest.py                    # Fixtures partilhadas
│   ├── unit/                          # Testes unitários (sem rede, sem ficheiros >1KB)
│   ├── integration/                   # Testes de integração (pipeline completo)
│   └── performance/                   # Benchmarks de performance
├── scratch/                           # Scripts temporários de exploração
├── agents/                            # Documentação de agentes IA usados no desenvolvimento
└── docs/                              # Documentação do projecto
```

### Notas sobre a estrutura

- **`config/` no root** (não dentro de `orders_master/`) — Permite que utilizadores não-técnicos editem os JSONs sem navegar em estrutura Python.
- **`.streamlit/secrets.toml`** — Localização standard do Streamlit. Está no `.gitignore` — nunca deve ser commitado.
- **`tests/`** separado em `unit/`, `integration/` e `performance/` — Unit não requer rede; integration pode usar fixtures maiores; performance mede tempos de execução.
- **`pyproject.toml`** em vez de `setup.py` — Standard moderno Python para configuração de projecto.

---

## 3. Fluxo de Dados Principal

O sistema tem dois pipelines distintos com naturezas muito diferentes:

### 3.1 Pipeline Pesado — `process_orders_session()`

Executado **uma única vez** quando o utilizador clica no botão "🚀 Processar Dados". Processa ficheiros que podem ter 30MB cada. O resultado é armazenado em `SessionState` para uso posterior.

```
┌──────────────────────────────────────────────────────────────────┐
│                    SIDEBAR (render_sidebar)                       │
│  Bloco 1: Multiselect Laboratórios                               │
│  Bloco 2: Upload ficheiro TXT de códigos                          │
│  Bloco 3: Upload ficheiros Infoprex (.txt)                        │
│  Bloco 4: Upload CSVs de marcas (opcional)                        │
│  Botão:  🚀 Processar Dados                                      │
└──────────────┬───────────────────────────────────────────────────┘
               │ selection (SidebarSelection)
               ▼
┌──────────────────────────────────────────────────────────────────┐
│              app.py (main)                                        │
│  • reset_state()                                                  │
│  • st.progress(0) → callback                                      │
│  • process_orders_session(files, codes, brands, labs, aliases)   │
└──────────────┬───────────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────────┐
│         session_service.process_orders_session()                  │
│                                                                    │
│  1. Parse codes_txt → lista_codigos (se ficheiro TXT presente)   │
│  2. Ou: mapear labs_selected → lista_cla via laboratorios.json   │
│  3. ThreadPoolExecutor: parse_infoprex_file() por cada ficheiro  │
│     • try_read_with_fallback_encodings (utf-16 → utf-8 → latin1) │
│     • Filtrar por localização (DUV máxima)                        │
│     • Filtrar por CLA ou CNP                                      │
│     • Inverter V14..V0 → colunas de mês nomeadas                  │
│     • Renomear CPR→CÓDIGO, NOM→DESIGNAÇÃO, etc.                  │
│     • Mapear localizações via map_location()                       │
│     • flag_price_anomalies()                                       │
│     • Erros capturados em FileError (não abortivos)               │
│  4. pd.concat(dfs válidos)                                        │
│  5. Integrar BD Rupturas: fetch_shortages_db → merge_shortages    │
│  6. Integrar Não Comprar: fetch_donotbuy_list → merge_donotbuy   │
│  7. parse_brands_csv() + build_master_products()                  │
│  8. aggregate(df, detailed=False) → df_aggregated                 │
│  9. aggregate(df, detailed=True) → df_detailed                    │
│ 10. Popular SessionState (DataFrames, file_inventory, scope)     │
│ 11. progress_callback(1.0) → barra vazia                         │
└──────────────┬───────────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────────┐
│                    SessionState (st.session_state)                 │
│  • df_raw (DataFrame detalhado pós-ingestão + integrações)       │
│  • df_aggregated (1 linha por produto)                            │
│  • df_detailed (N linhas por produto + linha Grupo)              │
│  • master_products (CÓDIGO → DESIGNAÇÃO canónica + MARCA)       │
│  • file_errors, file_inventory, scope_context                    │
└──────────────────────────────────────────────────────────────────┘
```

**Ponto-chave:** Os DataFrames `df_raw`, `df_aggregated` e `df_detailed` ficam em memória (via `st.session_state`) e **não são recalculados** quando o utilizador muda os controlos da UI. Isto é fundamental para a performance — o parsing de ficheiros de 30MB é dispendioso.

### 3.2 Pipeline Leve — `recalculate_proposal()`

Executado a **cada interacção** do utilizador com os controlos (slider, toggles, filtro de marca, preset de pesos). Opera exclusivamente sobre DataFrames já em memória, sem tocar em ficheiros. O objectivo é completar em menos de 500ms.

```
┌──────────────────────────────────────────────────────────────────┐
│            UI Controls (main_area.py)                             │
│  • Toggle "Ver Detalhe"  → detailed_view                         │
│  • Toggle "Mês Anterior" → use_previous_month                    │
│  • Slider "Meses a Prever" → months                              │
│  • Selectbox "Preset de Pesos" → weights                         │
│  • Multiselect "Filtrar por Marca" → marcas                      │
└──────────────┬───────────────────────────────────────────────────┘
               │ parâmetros
               ▼
┌──────────────────────────────────────────────────────────────────┐
│         recalc_service.recalculate_proposal()                     │
│                                                                    │
│  1. Filtrar por marcas (se seleccionadas) via master_products    │
│  2. Limpar colunas de cálculo prévio (Media, Proposta)           │
│  3. weighted_average(df, weights, use_previous_month) → Media    │
│  4. compute_base_proposal(df, months) → Proposta base            │
│  5. compute_shortage_proposal(df) → sobrescreve Proposta se TimeDelta presente │
│  6. aggregate(df, detailed_view, master_products) →vista final  │
│  7. Actualizar ScopeContext                                       │
└──────────────┬───────────────────────────────────────────────────┘
               │ df_final
               ▼
┌──────────────────────────────────────────────────────────────────┐
│              Renderização                                          │
│  • build_styler(df_final) → st.dataframe()  (vista web)         │
│  • build_excel(df_final, scope_tag) → st.download_button()     │
└──────────────────────────────────────────────────────────────────┘
```

**Ponto-chave:** O `recalculate_proposal` **não relê ficheiros** — trabalha sobre `state.df_raw` já em memória. Isto permite que as interacções com toggles e sliders sejam instantâneas.

---

## 4. De Onde Vêm os Dados, Como São Processados, Para Onde Vão

### Origens de dados

| Fonte | Formato | Mecanismo de entrada | Obrigatório? |
|---|---|---|---|
| Ficheiros Infoprex | `.txt` (UTF-16 ou UTF-8, separador Tab) | Upload manual via sidebar (Bloco 3) | **Sim** — é o dado base |
| Lista de CNPs | `.txt` (um CNP por linha) | Upload manual via sidebar (Bloco 2) | Não — opcional, tem prioridade sobre Laboratórios |
| Laboratórios | `config/laboratorios.json` | Configuração estática (editável sem restart) | Não — opcional, para filtrar por CLA |
| CSVs de Marcas | `.csv` (separador `;`, colunas COD/MARCA) | Upload manual via sidebar (Bloco 4) | Não — opcional, para filtro de UI |
| BD Esgotados Infarmed | Google Sheet (XLSX via URL pública) | `st.secrets["SHORTAGES_URL"]` | Não — integração falha graciosamente |
| Lista Não Comprar | Google Sheet (XLSX via URL pública) | `st.secrets["DONOTBUY_URL"]` | Não — integração falha graciosamente |
| Mapeamento de farmácias | `config/localizacoes.json` | Configuração estática | **Sim** — para mapear `LOCALIZACAO` |
| Presets de pesos | `config/presets.yaml` | Configuração estática | Não — tem defaults hardcoded |

### Transformações principais

1. **Ingestão** (`ingestion/infoprex_parser.py`):
   - Fallback de encoding (utf-16 → utf-8 → latin1).
   - Filtragem por localização: se o ficheiro contém dados de múltiplas localizações, apenas a com `DUV` (data de última venda) mais recente é mantida.
   - Filtragem por CLA (código de laboratório) ou por lista de CNPs (prioridade ao TXT).
   - Inversão cronológica: as colunas `V14, V13, ..., V0` do Infoprex são invertidas para que o mês mais antigo fique à esquerda e o mais recente à direita.
   - Renomeação de colunas para nomes em Português (`CPR` → `CÓDIGO`, `NOM` → `DESIGNAÇÃO`, `SAC` → `STOCK`, `PCU` → `P.CUSTO`).
   - Cálculo de `T Uni` (total de unidades vendidas = soma das 15 colunas de vendas).
   - Mapeamento de localizações via `map_location()` com word-boundary matching.
   - Detecção de anomalias de preço (`flag_price_anomalies`).
   - Códigos não-numéricos são descartados e registados.

2. **Agregação** (`aggregation/aggregator.py`):
   - Descarte de códigos locais (prefixo '1').
   - Remoção de zombies individuais (`STOCK == 0 AND T Uni == 0`).
   - Cálculo de médias de preço (PVP, P.CUSTO) excluindo anomalias.
   - Groupby soma para vendas e stock.
   - Injecção de designações canónicas e MARCA via master_products.
   - Remoção de zombies agregados (códigos cujo stock e vendas total são zero).
   - Na vista detalhada: adição de linhas `Grupo` (sumário por produto).
   - Ordenação determinística via `_sort_key` (desacoplado do rótulo 'Grupo').
   - Reordenação de colunas para a ordem canónica.

3. **Cálculo de Propostas** (`business_logic/proposals.py` + `averages.py`):
   - Média ponderada de 4 meses com pesos configuráveis, usando indexação posicional via âncora `T Uni`.
   - Toggle "Mês Anterior": desloca a janela uma posição para a esquerda (ignora o mês corrente incompleto).
   - Proposta base: `round(Media × meses_previsao − STOCK)`. Propostas negativas são mantidas (stock excedente = informação).
   - Proposta rutura: quando `TimeDelta` está presente (produto em rutura), sobrescreve com `round((Media / 30) × TimeDelta − STOCK)`.

4. **Integrações** (`integrations/`):
   - Esgotados: left join por `CÓDIGO`, injecta `DIR`, `DPR`, `TimeDelta`. TimeDelta é recalculado dinamicamente contra `datetime.now()`. Falha graciosamente (DataFrame vazio com schema preservado).
   - Não Comprar: merge dual-mode. Detalhada: por `(CÓDIGO, LOCALIZACAO)`. Agrupada: deduplica por CNP, merge por `CÓDIGO`. Injecta `DATA_OBS`.

### Destinos de dados

| Destino | Formato | Mecanismo |
|---|---|---|
| Vista web (tabela interactiva) | Pandas Styler com CSS | `st.dataframe(build_styler(df_final))` |
| Ficheiro Excel | `.xlsx` (openpyxl) | `st.download_button(build_excel(df_final))` |
| Nenhum — estado não é persistido | — | Cada sessão é independente |

---

## 5. Decisões Técnicas Importantes

### 5.1 Arquitectura em 3 Camadas (ADR-002)

**Problema:** O código original misturava Streamlit com Pandas numa teia impossível de testar isoladamente.

**Decisão:** Dependências apontam para dentro (`UI → services → domain`). Nenhum módulo de domínio importa `streamlit` directamente (apenas `st.cache_data` com guarded imports quando necessário). Isto torna toda a lógica de negócio testável com `pytest` puro, sem dependência do runtime Streamlit.

### 5.2 Single Source of Truth para Regras de Formatação (ADR-003)

**Problema:** As regras visuais (grupo preto, não comprar roxo, rutura vermelho, validade laranja, preço anómalo) corriam o risco de divergir entre o Styler web e o formatter Excel.

**Decisão:** `formatting/rules.py` define cada regra como uma `HighlightRule` dataclass com `predicate`, `target_cells`, `css_web`, `excel_fill` e `excel_font`. Ambos os renderers (`web_styler.py` e `excel_formatter.py`) consomem a mesma lista `RULES`. Acrescentar uma regra nova exige uma só alteração em `rules.py`.

A lista `RULES` no código actual contém 5 regras, por ordem de precedência:

| Precedência | Nome | Condição | Alvo visual | Cor |
|---|---|---|---|---|
| 1 | Grupo | `LOCALIZACAO == 'Grupo'` | Todas as colunas | Fundo preto, texto branco, bold |
| 2 | Não Comprar | `DATA_OBS` não-NaN | De `CÓDIGO` até `T Uni` | Fundo roxo claro `#E6D5F5` |
| 3 | Rutura | `DIR` não-NaN | Apenas coluna `Proposta` | Fundo vermelho `#FF0000`, texto branco, bold |
| 4 | Validade Curta | Meses até expiração ≤ 4 | Apenas coluna `DTVAL` | Fundo laranja `#FFA500`, bold |
| 5 | Preço Anómalo | `price_anomaly == True` | Coluna PVP/PVP_Médio | Texto vermelho, bold, prefixo ⚠️ |

Para a linha Grupo (precedência 1), as regras 2-5 não são aplicadas — garantindo que o fundo preto nunca é sobreposto.

### 5.3 Indexação Posicional via Âncora `T Uni` (ADR-004)

**Problema:** Os nomes dos meses (JAN, FEV, ...) são dinâmicos — dependem da data de venda mais recente detectada no ficheiro Infoprex. Hardcoding de nomes cria bugs sazonais.

**Decisão:** Qualquer cálculo sobre meses usa `index_of('T Uni') − N`. O contrato é: entre `T Uni − 5` e `T Uni − 1` têm de estar exclusivamente colunas de vendas. A coluna `MARCA` e qualquer metadata são dropadas antes de cálculos posicionais.

### 5.4 Aggregate-Once + Recalculate-In-Memory (ADR-005)

**Problema:** Se cada movimento de slider reprocessasse ficheiros de 30MB, a UX seria inaceitável (segundos a minutos de espera).

**Decisão:** `process_orders_session()` é pesado e corre só quando o utilizador clica `Processar Dados`. Todo o resto (slider, toggle, filtros de marca) invoca apenas `recalculate_proposal()`, que trabalha sobre DataFrames já em `SessionState`. Esta separação garante interacções sub-segundo.

### 5.5 Caching por `mtime` (ADR-006)

**Problema:** Ficheiros JSON editáveis em produção (`laboratorios.json`, `localizacoes.json`) exigem recarregamento sem restart do servidor.

**Decisão:** Funções como `load_labs(mtime)` e `load_locations(mtime)` recebem `mtime` como argumento; o chamador obtém `os.path.getmtime(path)`. O `@st.cache_data` usa este valor como chave — qualquer edição ao ficheiro produz novo `mtime` → cache miss → recarregamento automático. Para aplicar: basta o utilizador recarregar a página (F5) após editar o ficheiro.

### 5.6 Parsing Defensivo com Recolha de Erros (ADR-007)

**Problema:** Um ficheiro corrompido não deve derrubar o processamento dos outros.

**Decisão:** O loop de ingestão faz `try/except` com excepções tipadas (`InfoprexEncodingError`, `InfoprexSchemaError`, `Exception` genérica). Regista os erros por ficheiro num `FileError` (NamedTuple imutável) e continua. Os ficheiros válidos são processados normalmente. Os erros são exibidos na UI via expander, não como stack trace.

### 5.7 Sort-Key Auxiliar (ADR-008)

**Problema:** O uso de prefixos como `'Zgrupo_Total'` para forçar ordenação alfabética misturava identidade semântica com mecânica de ordenação.

**Decisão:** Na agregação, acrescenta-se uma coluna `_sort_key ∈ {0, 1}` (0 para linhas de detalhe, 1 para linha `Grupo`). A ordenação é `[DESIGNAÇÃO, CÓDIGO, _sort_key, LOCALIZACAO]`. A coluna `_sort_key` é descartada antes da renderização. O rótulo exibido é `'Grupo'` desde o início.

### 5.8 Parallel Parsing com ThreadPoolExecutor (ADR-010)

**Problema:** Com 4-5 ficheiros de 30MB, o parsing sequencial é linear no número de ficheiros.

**Decisão:** `ThreadPoolExecutor` com `max_workers = min(len(files), os.cpu_count(), 8)`. Usa threads (não processos) porque as operações de I/O e operações Pandas que libertam o GIL beneficiam suficientemente de paralelismo com threads. O merge é feito sequencialmente após todos terminarem.

**Nota:** O PRD original mencionava `ProcessPoolExecutor` mas a implementação usa `ThreadPoolExecutor`. Isto é deliberado — o parsing Pandas com `pd.read_csv` liberta o GIL durante operações de I/O, e o overhead de serialização inter-processo do `ProcessPoolExecutor` seria contraproducente para DataFrames.

### 5.9 Operações Vectorizadas Apenas (ADR-011)

**Problema:** `.apply(lambda ...)` em `clean_designation` é 5-10× mais lento que `.str` vectorizado.

**Decisão:** Nenhuma função de domínio usa `.apply` com lambdas Python sobre colunas em loops quentes. A limpeza de strings passa por `.str.normalize`, `.str.replace`, etc. A excepção é `convert_code` no `infoprex_parser.py` que usa `.apply()` para converter códigos — aceitável porque corre apenas uma vez por coluna durante o parsing.

### 5.10 Validação de Preços (Anomalias)

O módulo `price_validation.py` marca linhas com preços inválidos (`P.CUSTO ≤ 0`, `PVP ≤ 0`, ou `PVP < P.CUSTO`). Estas linhas são:

- **Excluídas** do cálculo de médias de preço na agregação (médias de PVP/P.CUSTO usam apenas linhas com `price_anomaly == False`).
- **Sinalizadas visualmente** com texto vermelho e prefixo ⚠️ na coluna PVP.
- Se todos os preços de um grupo forem anómalos, o sistema usa o primeiro preço disponível como fallback.

---

## 6. Detalhes de Componentes Chave

### 6.1 `SessionState` — Façade Tipada

A dataclass `SessionState` em `app_services/session_state.py` serve como façade tipada sobre `st.session_state`. Isto resolve o problema do `st.session_state` ser um dicionário sem tipagem — o `SessionState` fornece campos tipados, valores por defeito e é testável fora do Streamlit.

O acesso é feito via `get_state()` que faz lazy-init em `st.session_state` caso o Streamlit esteja disponível, ou devolve uma instância fresh caso contrário (útil para testes unitários).

### 6.2 `map_location()` — Matching com Ancoragem

A função `map_location()` em `config/locations_loader.py` implementa um matching em três níveis:

1. **Match exacto** (case-insensitive) — se o nome da farmácia coincide exactamente com um termo.
2. **Word boundary** (`\b` + regex-escaped term + `\b`) — se o termo aparece como palavra completa dentro do nome. Exemplo: `"ilha"` faz match em `"Farmácia da Ilha"` mas NÃO em `"Farmácia Vilha"`.
3. **Fallback** — `name.title()` se nenhum match.

Se múltiplos termos fazem match, o primeiro vence e um warning é registado.

### 6.3 `aggregate()` — Motor Único

A função `aggregate()` em `aggregation/aggregator.py` é o motor de agregação único que serve tanto a vista agrupada como a detalhada. O parâmetro `detailed: bool` controla o comportamento:

- `detailed=False`: 1 linha por `CÓDIGO`, vendas somadas, preços como média.
- `detailed=True`: N linhas por `CÓDIGO` (uma por loja) + 1 linha `'Grupo'` com total.

A mesma função é usada tanto no pipeline pesado (`session_service`) como no pipeline leve (`recalc_service`), garantindo consistência.

### 6.4 `build_master_products()` — Designações Canónicas

A função `build_master_products()` constrói uma tabela de referência que mapeia cada `CÓDIGO` à sua designação mais frequente (limpa via `clean_designation_vectorized`). Se CSVs de marcas forem fornecidos, a coluna `MARCA` é injectada via merge. Esta tabela é usada pela agregação para garantir que todas as linhas do mesmo produto usam a mesma designação, mesmo que fontes diferentes as reportem de forma distinta.

---

## 7. Ficheiros de Configuração — Schema e Validação

### `laboratorios.json`

Schema pydantic: `LabsConfig(RootModel[dict[str, list[str]]])` com validação:

- Chaves: mínimo 2 caracteres, primeira letra maiúscula.
- Valores: strings alfanuméricos, máximo 10 caracteres.
- Duplicados em CLA: dedup automático com warning.
- CLA em múltiplos labs: warning.

### `localizacoes.json`

Schema pydantic: `LocationsConfig(RootModel[dict[str, str]])` com validação:

- Termos de pesquisa: mínimo 3 caracteres (para evitar matches frágeis).

### `presets.yaml`

Estrutura: `presets: { Nome: [peso1, peso2, peso3, peso4] }`. Validação:

- Lista de exactamente 4 pesos.
- Soma ≈ 1.0 (tolerância ±0.001).

---

## 8. Logging e Observabilidade

O sistema usa logging centralizado (`orders_master/logger.py`) com:

- **SessionFilter**: injecta um `session_id` (UUID4) em cada log record, permitindo rastrear todos os eventos de uma sessão.
- **TimedRotatingFileHandler**: rotação diária, 7 backups, ficheiro `logs/orders_master.log`.
- **StreamHandler**: output para stdout (nível INFO).
- **Logger especializado**: `orders_master` em nível DEBUG (mais verboso que o root).
- **Decorador `@timed`**: mede e regista o tempo de execução de funções ao nível DEBUG.

Formato: `YYYY-MM-DD HH:MM:SS | LEVEL | session_id | module | message`