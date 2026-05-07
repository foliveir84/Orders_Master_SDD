# Divergências entre PRD v2 e a Implementação Real

> **Data:** 2026-05-08
> **PRD de referência:** `prd.md` (v2.0, 2026-05-04)
> **Código analisado:** `Orders_Master_SDD/` (estado actual do repositório)

Este documento cruza sistematicamente cada afirmação do PRD com o código real, identificando três categorias de divergência:

1. **PRD diz, código não faz** — especificação presente no PRD mas ausente na implementação.
2. **Código faz, PRD não diz** — funcionalidade existente no código mas não documentada no PRD.
3. **Desvio de lógica de negócio** — ambas as partes existem mas divergem em comportamento, assinatura ou semântica.

---

## Índice

- [1. Ficheiros e Estrutura de Directorias](#1-ficheiros-e-estrutura-de-directorias)
- [2. Componentes UI Ausentes](#2-componentes-ui-ausentes)
- [3. ProcessPoolExecutor vs ThreadPoolExecutor](#3-processpoolexecutor-vs-threadpoolexecutor)
- [4. SessionState — Campos Divergentes](#4-sessionstate--campos-divergentes)
- [5. Recalc Service vs Session Service — Responsabilidade de Integrações](#5-recalc-service-vs-session-service--responsabilidade-de-integrações)
- [6. Regras de Formatação — 4 vs 5](#6-regras-de-formatação--4-vs-5)
- [7. Schemas — DetailedRowSchema](#7-schemas--detailedrowschema)
- [8. PriceAnomalyWarning — Definido mas Nunca Emitido](#8-priceanomalywarning--definido-mas-nunca-emitido)
- [9. Secrets Loader — Localização e Hierarquia](#9-secrets-loader--localização-e-hierarquia)
- [10. Encoding Fallback — on_bad_lines vs errors](#10-encoding-fallback--on_bad_lines-vs-errors)
- [11. Integrações — St.sidebar.warning no Domínio](#11-integrações--stsidebarwarning-no-domínio)
- [12. .streamlit/secrets.toml — Conteúdo Real vs Template](#12-streamlitsecretstoml--conteúdo-real-vs-template)
- [13. .env.example — Ficheiro Vazio](#13-envexample--ficheiro-vazio)
- [14. Ficheiros de Configuração Extra Não Listados no PRD](#14-ficheiros-de-configuração-extra-não-listados-no-prd)
- [15. secrets_loader.py — Localização Fora de config/](#15-secrets_loaderpy--localização-fora-de-config)
- [16. Testes — Ficheiros Presentes vs PRD](#16-testes--ficheiros-presentes-vs-prd)
- [17. Filtro de Marcas — Lógica Divergente no recalc_service](#17-filtro-de-marcas--lógica-divergente-no-recalc_service)
- [18. Shortages — TimeDelta com .apply(lambda) vs Vectorizado](#18-shortages--timedelta-com-applylambda-vs-vectorizado)
- [19. DonotBuy — .apply(lambda) em FARMACIA mapping](#19-donotbuy--applylambda-em-farmacia-mapping)
- [20. DonotBuy — Merge Sempre `detailed=True`](#20-donotbuy--merge-sempre-detailedtrue)
- [21. ScopeContext — Campos Divergentes](#21-scopecontext--campos-divergentes)
- [22. FileInventoryEntry — Campos Divergentes](#22-fileinventoryentry--campos-divergentes)
- [23. Constants — Campos Ausentes](#23-constants--campos-ausentes)
- [24. Integrations — import streamlit no Domínio](#24-integrations--import-streamlit-no-domínio)
- [25. Aggregate — Assinatura sem master_products no recalc_service?](#25-aggregate--assinatura-sem-master_products-no-recalc_service)
- [26. Recalc Service — Re-Agrega em Cada Recálculo](#26-recalc-service--re-agrega-em-cada-recálculo)
- [27. Session Service — Init de Colunas de Integração em df_raw](#27-session-service--init-de-colunas-de-integração-em-df_raw)
- [28. Lazy Merge — codigos_visible Ignorado no session_service](#28-lazy-merge--codigos_visible-ignorado-no-session_service)
- [29. Banner BD Rupturas — Formato da Data](#29-banner-bd-rupturas--formato-da-data)
- [30. Resumo Quantitativo](#30-resumo-quantitativo)

---

## 1. Ficheiros e Estrutura de Directorias

**PRD §3.4** define a estrutura completa do projecto. Comparação com o código real:

| Caminho no PRD | Existe? | Notas |
|---|---|---|
| `app.py` | ✔ | |
| `pyproject.toml` | ✔ | |
| `requirements.txt` | ✔ | |
| `README.md` | ✔ | |
| `.gitignore` | ✔ | |
| `.streamlit/secrets.toml` | ✔ | Contém URLs reais (ver secção 12) |
| `config/laboratorios.json` | ✔ | |
| `config/localizacoes.json` | ✔ | |
| `config/presets.yaml` | ✔ | |
| `orders_master/constants.py` | ✔ | Campos ausentes (ver secção 23) |
| `orders_master/schemas.py` | ✔ | Tem `DetailedRowSchema` (ver secção 7) |
| `orders_master/logger.py` | ✔ | |
| `orders_master/ingestion/__init__.py` | ✔ | |
| `orders_master/ingestion/infoprex_parser.py` | ✔ | |
| `orders_master/ingestion/codes_txt_parser.py` | ✔ | |
| `orders_master/ingestion/brands_parser.py` | ✔ | |
| `orders_master/ingestion/encoding_fallback.py` | ✔ | |
| `orders_master/aggregation/aggregator.py` | ✔ | |
| `orders_master/business_logic/averages.py` | ✔ | |
| `orders_master/business_logic/proposals.py` | ✔ | |
| `orders_master/business_logic/cleaners.py` | ✔ | |
| `orders_master/business_logic/price_validation.py` | ✔ | |
| `orders_master/integrations/shortages.py` | ✔ | |
| `orders_master/integrations/donotbuy.py` | ✔ | |
| `orders_master/config/labs_loader.py` | ✔ | |
| `orders_master/config/locations_loader.py` | ✔ | |
| `orders_master/formatting/rules.py` | ✔ | |
| `orders_master/formatting/web_styler.py` | ✔ | |
| `orders_master/formatting/excel_formatter.py` | ✔ | |
| `orders_master/app_services/session_state.py` | ✔ | |
| `orders_master/app_services/session_service.py` | ✔ | |
| `orders_master/app_services/recalc_service.py` | ✔ | |
| `ui/sidebar.py` | ✔ | |
| `ui/main_area.py` | ✔ | |
| `ui/scope_bar.py` | ✔ | |
| `ui/file_inventory.py` | ✔ | |
| **`ui/alerts.py`** | ✘ | Ver secção 2 |
| **`ui/documentation.py`** | ✘ | Ver secção 2 |
| `tests/conftest.py` | ✔ | |
| `tests/unit/test_column_ordering.py` | ✔ | (existe, contrário ao que pensámos inicialmente) |
| `tests/unit/test_web_excel_parity.py` | ✔ | (existe, PRD §8.13 lista-o) |
| `tests/fixtures/` | ✔ | (parcial) |
| `tests/integration/test_full_pipeline.py` | ✔ | |
| `tests/integration/test_boundary_year.py` | ✔ | |

**Ficheiros no código NÃO listados no PRD §3.4:**

| Ficheiro | Fora do PRD |
|---|---|
| `orders_master/config/validate.py` | PRD §8.15 menciona `python -m orders_master.config.validate` mas a estrutura §3.4 não lista o ficheiro |
| `orders_master/config/presets_loader.py` | Totalmente ausente do PRD §3.4 |
| `orders_master/secrets_loader.py` | Ausente da estrutura; o PRD §8.14 menciona função `get_secret()` mas não localiza o módulo |
| `tests/unit/test_session_state.py` | Não listado na tabela de testes do PRD §8.13 |
| `tests/unit/test_session_service.py` | Não listado |
| `tests/unit/test_secrets_loader.py` | Não listado |
| `tests/unit/test_schemas.py` | Não listado |
| `tests/unit/test_rules.py` | Não listado |
| `tests/unit/test_recalc_service.py` | Não listado |
| `tests/unit/test_process_session.py` | Não listado |
| `tests/unit/test_logger.py` | Não listado |
| `tests/performance/` (3 ficheiros) | PRD §7.1 menciona `tests/performance/` mas apenas lista `test_ingestion_benchmark.py`; código tem 3 ficheiros |
| `tests/integration/test_pipeline_e2e.py` | Não listado no PRD |

---

## 2. Componentes UI Ausentes

**PRD §3.4 e §3.2** especificam dois módulos de UI que não existem no código:

| Módulo PRD | Responsabilidade PRD | Realidade no Código |
|---|---|---|
| `ui/alerts.py` | `render_errors_and_warnings()` — exibe erros (st.error) e avisos (st.warning) ao utilizador | Lógica integrada em `ui/main_area.py` inline |
| `ui/documentation.py` | `render_help_expander()` — expander "ℹ️ Documentação e Workflow" | Lógica integrada em `ui/main_area.py` inline |

**Impacto:** Violação da separação de responsabilidades por componente prevista no PRD. O `main_area.py` acumula lógica de 3 componentes (main + alerts + documentation).

---

## 3. ProcessPoolExecutor vs ThreadPoolExecutor

**PRD §3.3 P9, §8.11, ADR-010:**

> `ProcessPoolExecutor` com `max_workers = min(cpu_count, len(files))`. Cada worker devove um DataFrame independente.

**PRD ADR-010 — textualmente:**

> `ThreadPoolExecutor` — **rejeitado**; GIL torna o parsing (CPU-bound) não-paralelo.

**Código real** (`session_service.py:4,158`):

```python
from concurrent.futures import ThreadPoolExecutor
# ...
with ThreadPoolExecutor(max_workers=max_workers) as executor:
```

**Divergência:** A implementação usa exactamente a alternativa que o ADR-010 rejeitou, com a justificação invertida. O código até comenta "Usar ThreadPoolExecutor para paralelismo I/O + GIL-releasing pandas operations" — reconhecendo implicitamente que a razão original de rejeição (GIL) é mitigada pelo facto de `pd.read_csv` libertar o GIL durante I/O.

**Impacto:** Funcionalmente funciona (porque Pandas liberta o GIL no I/O), mas diverge do ADR-010 documentado. O PRD deve ser actualizado ou o código revertido.

---

## 4. SessionState — Campos Divergentes

**PRD §4.1.8** define os campos de `SessionState`:

| Campo PRD | Tipo PRD | No Código? | Tipo Código | Divergência |
|---|---|---|---|---|
| `df_aggregated` | `pd.DataFrame` | ✔ | `pd.DataFrame` | — |
| `df_detailed` | `pd.DataFrame` | ✔ | `pd.DataFrame` | — |
| `df_master_products` | `pd.DataFrame` | ✔ (nome diferente) | `master_products` | PRD usa `df_master_products`; código usa `master_products` |
| `last_labs_selection` | `list[str] \| None` | ✔ | `list[str] \| None` | — |
| `last_codes_file_name` | `str \| None` | ✔ | `str \| None` | — |
| `file_errors` | `list[FileError]` | ✔ | `list[FileError]` | — |
| `invalid_codes` | `list[str]` | ✔ | `list[str]` | — |
| `file_inventory` | `list[FileInventoryEntry]` | ✔ | `list[FileInventoryEntry]` | — |
| `scope_context` | `ScopeContext` | ✔ | `ScopeContext` | — |
| — | — | ✔ | `df_raw: pd.DataFrame` | **Extra no código** — DataFrame bruto pós-ingestão, pré-agregação |
| — | — | ✔ | `last_brands_selection: list[str]` | **Extra no código** — última selecção de marcas |
| — | — | ✔ | `shortages_data_consulta: str \| None` | **Extra no código** — data da consulta da BD Rupturas |

**Notas:**

- `df_raw` é um campo significativo: o `recalc_service` trabalha sobre `df_detailed` (que já é agregado) em vez do raw, mas o `session_service` armazena o DataFrame completo pós-ingestão, com colunas de integrações já merged. Isto contradiz o fluxo do PRD §3.1 onde "recalcular_proposal() lê do SessionState" (implícito: usa aggregated/detailed já prontos).
- `last_brands_selection` não é mencionado no PRD, mas é necessário para detectar filtros obsoletos de marcas (extensão de US-11).
- `shortages_data_consulta` alimenta o banner "Data Consulta BD Rupturas" (PRD §6.2.3), mas não está documentado no §4.1.8.

---

## 5. Recalc Service vs Session Service — Responsabilidade de Integrações

**PRD §3.1 — Fluxo Principal:**

> A cada interacção subsequente (slider, toggle, filtro marca): `app_services.recalculate_proposal()` lê do `SessionState`, aplica `business_logic`, **integra com `integrations.fetch_shortages()` e `integrations.fetch_donotbuy()`**, devolve DataFrame final.

**Código real:**

- **`session_service.py:66-91`** chama `fetch_shortages_db()`, `merge_shortages()`, `fetch_donotbuy_list()` e `merge_donotbuy()` no pipeline pesado (Processar Dados).
- **`recalc_service.py`** NÃO chama integrações nenhuma. Apenas: filtro marcas → média ponderada → proposta base → proposta rutura → agregação.

**Divergência crítica:** As integrações correm no pipeline pesado (session_service), não no pipeline leve (recalc_service). Isto significa que:

1. Os dados de rutura e "não comprar" são mergeados **uma vez** no processamento inicial e persistem no `df_raw` / `df_detailed`.
2. Quando o utilizador muda o slider ou toggle, o `recalculate_proposal` opera sobre DataFrames que **já têm** TimeDelta, DIR, DPR, DATA_OBS injectados.
3. O PRD especifica que as integrações devem correr **em cada recálculo** (o que faria sentido para actualizações de cache, mas penaliza performance).

**Impacto positivo:** A implementação é mais eficiente — os merges pesados correm apenas uma vez. O TimeDelta é recalculado no fetch (dentro do `@st.cache_data(ttl=3600)`), o que é consistente com o requisito de recalcular contra `datetime.now()`.

**Impacto negativo:** Se a Google Sheet for actualizada durante a sessão do utilizador, o recálculo NÃO vai buscar os novos dados (porque o `st.cache_data` apenas expira após TTL de 3600s, independentemente de o recalc_service chamar ou não a integração).

---

## 6. Regras de Formatação — 4 vs 5

**PRD §3.2 — `formatting/rules.py`:**

> Encapsula as **4 regras visuais** (grupo, não comprar, rutura, validade).

**PRD §6.1.6 — Tabela de Regras:**

Lista 5 regras, incluindo a regra 5 "price_anomaly → ícone ⚠️".

**Código real** (`rules.py:66-132`): define exactamente **5 regras** na lista `RULES`:

| # | Nome | Precedência |
|---|---|---|
| 1 | Grupo | 1 |
| 2 | Não Comprar | 2 |
| 3 | Rutura | 3 |
| 4 | Validade Curta | 4 |
| 5 | Preço Anómalo | 5 |

**Divergência textual:** O PRD §3.2 diz "4 regras visuais" mas o §6.1.6 lista 5, e o código define 5. O §3.2 está desactualizado — provavelmente escrito antes de a regra de preço anómalo ser adicionada como regra de formatação (era originalmente apenas um `UserWarning`, §5.6.1).

---

## 7. Schemas — DetailedRowSchema

**PRD §3.2 — schemas.py:**

> Define os schemas tipados: `InfoprexRowSchema`, `AggregatedRowSchema`, `ShortageRowSchema`, `DoNotBuyRowSchema`, `BrandRowSchema`.

O PRD NÃO menciona `DetailedRowSchema` na lista de §3.2, mas **descreve a entidade DetailedRow em §4.1.3** com campos e validações.

**Código real** (`schemas.py:70-88`): `DetailedRowSchema` **existe** com `required_columns` listando `CÓDIGO`, `DESIGNAÇÃO`, `LOCALIZACAO`, `PVP_Médio`, `P.CUSTO`, `T Uni`, `STOCK`.

**Divergência:** O PRD §3.2 omite `DetailedRowSchema` da lista de schemas, apesar de a entidade existir no modelo de dados (§4.1.3) e existir no código. Provável lapso de redacção.

---

## 8. PriceAnomalyWarning — Definido mas Nunca Emitido

**PRD §5.6.1 — Taxonomia de Erros:**

> `PriceAnomalyWarning(UserWarning)` — Preço fora de faixa normal. Visibilidade: Marcado silenciosamente com flag + ícone na UI.

**Código real:**

- `exceptions.py:24` define `PriceAnomalyWarning(UserWarning)`.
- Um `grep` por `PriceAnomalyWarning` em todo o código só retorna a definição — **nunca é emitido** via `warnings.warn()`.
- `price_validation.py` marca `price_anomaly = True` na coluna booleana, mas não emite o `UserWarning`.
- `rules.py` regra 5 consome a coluna `price_anomaly` para formatação visual, sem usar o `Warning`.

**Divergência:** A classe `PriceAnomalyWarning` é código morto. O PRD diz "visibilidade: marcado silenciosamente com flag + ícone na UI" — o "silenciosamente" sugere que não emitir via `warnings.warn()` é aceitável, mas a classe definida em §5.6.1 torna-se órfã.

---

## 9. Secrets Loader — Localização e Hierarquia

**PRD §8.14 — Hierarquia de lookup:**

1. `st.secrets["google_sheets"]["shortages_url"]` / `["donotbuy_url"]`
2. Variáveis de ambiente `SHORTAGES_SHEET_URL` / `DONOTBUY_SHEET_URL`
3. Fallback para `.env`

**Código real** (`secrets_loader.py`):

1. `st.secrets` com navegação por `key_path` (ex: `"google_sheets.shortages_url"`)
2. Variável de ambiente derivada automaticamente (`key_path.replace(".", "_").upper()`)
3. `.env` via `load_dotenv()` (carregado no import do módulo)

**Divergências:**

- **localização do secrets.toml difere:** O PRD §8.14 usa `st.secrets["google_sheets"]["shortages_url"]` (seccção aninhada), mas o `secrets.toml` real tem chaves planas `SHORTAGES_URL` / `DONOTBUY_URL` no top-level. O `session_service.py:72,84` lê com `st.secrets.get("SHORTAGES_URL")` (top-level), não `st.secrets["google_sheets"]["shortages_url"]`.
- **localização do módulo:** `secrets_loader.py` está em `orders_master/secrets_loader.py` (raiz do package), não dentro de `orders_master/config/` onde o PRD implicitamente o colocaria (§3.4 não o lista).
- **uso inconsistente:** `session_service.py` não usa `secrets_loader.py` — acede a `st.secrets` directamente. A função `get_secret()` não é invocada em lado nenhum do pipeline principal.

---

## 10. Encoding Fallback — on_bad_lines vs errors

**PRD §5.1.2 — Fallback de Encoding:**

> Se todos falharem → `raise InfoprexEncodingError(...)`

**TASK-09 notes** referem `errors='strict'` para a tentativa de detecção de encoding.

**Código real** (`encoding_fallback.py:45`):

```python
on_bad_lines="error",  # Levanta erro se houver linhas mal formadas
```

**Divergência:** Usa `on_bad_lines="error"` em vez de `errors='strict'`. A semântica é diferente:
- `on_bad_lines` controla o que fazer com linhas mal formatadas no CSV (schema de colunas).
- `errors` controla o que fazer com bytes não decodificáveis no encoding.

O PRD §4.3.1 tabela de validação indica que colunas estruturais ausentes devem causar `InfoprexSchemaError`, mas `on_bad_lines="error"` pode causar um `ParserError` genérico antes de se chegar à validação de schema. O código faz um `except Exception: continue` no loop de encodings, o que mascara este erro e tenta o encoding seguinte — potencialmente lendo o ficheiro com o encoding errado se linhas malformadas forem específicas de um encoding.

---

## 11. Integrações — St.sidebar.warning no Domínio

**PRD §8.1 — Regra de Arquitectura:**

> `orders_master/` sem qualquer `import streamlit` nos módulos de domínio.
> Critério de aceitação: `grep -r "import streamlit" orders_master/` devolve zero matches.

**Código real:**

- `integrations/shortages.py:12` → `import streamlit as st`
- `integrations/shortages.py:44` → `st.sidebar.warning("⚠️ Ligação ao Google Sheets falhou.")`
- `integrations/donotbuy.py:12` → `import streamlit as st` (usado no `cache_decorator`)
- Ambos usam `st.cache_data` como decorator.

**Divergência:** O package de integrações, teoricamente parte do domínio (§3.1 diagrama coloca-o em `Domain`), importa e usa Streamlit. Isto quebra a regra de arquitectura ADR-002. A mitigação é o `try/except ImportError` que permite funcionar sem Streamlit em testes, mas não deixa de ser uma violação.

---

## 12. .streamlit/secrets.toml — Conteúdo Real vs Template

**PRD §6.3.4:**

```toml
[google_sheets]
shortages_url = "https://docs.google.com/.../pub?output=xlsx"
donotbuy_url  = "https://docs.google.com/.../pub?output=xlsx"
```

**PRD §8.14:**

> `.streamlit/secrets.toml.example` commitado (template).
> `.streamlit/secrets.toml` **no `.gitignore`**.

**Código real** (`secrets.toml`):

```toml
SHORTAGES_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT53W00IxszrUzX8iTpV7y27zpeDQ_p1EbP07hqutlU864A6qaGvfIhQOzzm-Y1wrYZLRAvphteNMqY/pub?output=xlsx"
DONOTBUY_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQpVF4Akv5OCgavLp8tSbjxYwuRlV2Td_JEnzw8zIhinDWrqlsL-173ks9aJtCWrlr-yokfEboAOSWL/pub?output=xlsx"
```

**Divergências múltiplas:**

1. **URLs reais commitadas** — o ficheiro contém URLs reais das Google Sheets, não um template `.example`. Viola NFR-S1 e o critério de aceitação do §8.14.
2. **Estrutura plana vs seccção aninhada** — o PRD usa `[google_sheets]` como secção TOML; o código usa chaves top-level `SHORTAGES_URL`.
3. **Nome das chaves diverge** — PRD: `shortages_url` / `donotbuy_url`; código: `SHORTAGES_URL` / `DONOTBUY_URL`.
4. **Falta `.toml.example`** — não existe `.streamlit/secrets.toml.example` no repositório.

---

## 13. .env.example — Ficheiro Vazio

**PRD §8.14:**

> `.env.example` commitado; `.env` no `.gitignore`.

**Código real:** `.env.example` existe mas tem **0 bytes** — está completamente vazio. Um novo developer não saberia que variáveis de ambiente definir.

**Divergência:** O PRD implica (e as TASK-02 notes sugerem) que o `.env.example` deve conter um template com as variáveis necessárias (pelo menos `SHORTAGES_URL` e `DONOTBUY_URL`).

---

## 14. Ficheiros de Configuração Extra Não Listados no PRD

**PRD §3.4** não lista os seguintes ficheiros que existem em `orders_master/config/`:

| Ficheiro | Função | Razão da Omissão |
|---|---|---|
| `orders_master/config/validate.py` | CLI de validação offline de JSONs (PRD §8.15 menciona o comando `python -m orders_master.config.validate` mas não lista o ficheiro na estrutura) | Provavelmente esquecido na lista de §3.4 |
| `orders_master/config/presets_loader.py` | Carregamento e validação do `presets.yaml` (PRD §8.4 menciona presets mas não lista este módulo) | Provavelmente esquecido na lista de §3.4 |

---

## 15. secrets_loader.py — Localização Fora de config/

**PRD §3.4** — a directoria `orders_master/config/` contém `labs_loader.py` e `locations_loader.py`.

**Código real:** `orders_master/secrets_loader.py` está na **raiz** do package `orders_master/`, não dentro de `config/`.

**Divergência:** Inconsistência organizativa — outros loaders de configuração (`labs_loader`, `locations_loader`, `presets_loader`) estão em `config/`, mas o secrets loader está fora. Não há justificação no PRD.

---

## 16. Testes — Ficheiros Presentes vs PRD

**PRD §8.13** lista 17 ficheiros de teste obrigatórios. O código tem 23 ficheiros de teste na directoria `tests/`.

**Testes no PRD mas com nome diferente ou ausentes:**

| PRD | Código | Nota |
|---|---|---|
| `tests/unit/test_column_ordering.py` | ✔ Presente | |
| `tests/unit/test_web_excel_parity.py` | ✔ Presente | |

**Testes extras no código (não listados no PRD §8.13):**

| Ficheiro | Cobre |
|---|---|
| `tests/unit/test_session_state.py` | SessionState dataclass e façade |
| `tests/unit/test_session_service.py` | Pipeline pesado |
| `tests/unit/test_secrets_loader.py` | Secrets hierarchy |
| `tests/unit/test_schemas.py` | Schemas pydantic |
| `tests/unit/test_rules.py` | HighlightRule e RULES |
| `tests/unit/test_recalc_service.py` | Pipeline leve |
| `tests/unit/test_process_session.py` | Possível duplicado com test_session_service |
| `tests/unit/test_logger.py` | Configuração de logging |
| `tests/performance/test_recalc_benchmark.py` | NFR-P2 |
| `tests/performance/test_parallel_parsing_benchmark.py` | NFR-P5 |
| `tests/performance/test_parallel_benchmark.py` | Possível duplicado |
| `tests/integration/test_pipeline_e2e.py` | E2E alternativo |

**Divergência:** O código tem mais testes do que o PRD exige — positivo em termos de cobertura, mas indica que a lista do PRD é incompleta.

---

## 17. Filtro de Marcas — Lógica Divergente no recalc_service

**PRD §5.5.5 — Isolamento Matemático (ordem obrigatória):**

1. Filtrar pelas marcas seleccionadas (incluindo preservar linha Grupo).
2. DROP imediato da coluna MARCA.
3. Só depois calcular médias/propostas.

**Código real** (`recalc_service.py:53-55`):

```python
if marcas:
    valid_cnps = master_products[master_products[Columns.MARCA].isin(marcas)][Columns.CODIGO]
    df_work = df_work[df_work[Columns.CODIGO].isin(valid_cnps)]
```

**Divergências:**

1. **Não preserva a linha Grupo explicitamente** (PRD ADR-13 exige `mask_keep = (df['LOCALIZACAO'] == 'Grupo') | ...`). O código filtra por CNPs válidos, o que indirectamente pode excluir linhas Grupo se nenhum dos códigos associados a marcas seleccionadas estiver na vista detalhada. Como a linha Grupo tem `CÓDIGO` válido, ela pode sobreviver, mas apenas se o `CÓDIGO` do Grupo estiver em `valid_cnps`.
2. **Não faz DROP da coluna MARCA** antes de chamar `weighted_average()`. A coluna MARCA pode estar presente no DataFrame quando a âncora `T Uni` é usada, violando o invariante posicional (ADR-004). O facto de o filtro filtrar antes de chamar `aggregate()` (que faz o merge com master_products) mitiga parcialmente, mas a coluna MARCA pode propagar-se.
3. **Filtra contra master_products em vez de df_work** — o PRD §5.5.4 diz que as opções vêm de `df_aggregated['MARCA']` (dataset já filtrado), não do master. O código filtra `master_products` para obter CNPs, o que inclui marcas de produtos que podem não estar no contexto actual.

---

## 18. Shortages — TimeDelta com .apply(lambda) vs Vectorizado

**PRD §3.3 P10, ADR-011:**

> Nenhuma função de domínio usa `.apply` com lambdas Python sobre séries/DataFrames.

**Código real** (`shortages.py:61-63`):

```python
df[Columns.TIME_DELTA] = (df["Data prevista para reposição"].dt.date - today).apply(
    lambda x: x.days if pd.notnull(x) else pd.NA
)
```

**Divergência:** Usa `.apply(lambda)` para calcular `TimeDelta`. Versão vectorizada:

```python
delta = df["Data prevista para reposição"].dt.date - today
df[Columns.TIME_DELTA] = delta.where(delta.notna(), pd.NA).map(lambda x: x.days)
```

Ou usando `.dt.days` se os timedeltas estiverem num `TimedeltaIndex`. O `.apply(lambda)` viola explicitamente ADR-011.

---

## 19. DonotBuy — .apply(lambda) em FARMACIA mapping

**Código real** (`donotbuy.py:49-51`):

```python
df["FARMACIA"] = df["FARMACIA"].apply(
    lambda x: map_location(str(x), aliases) if pd.notna(x) else ""
)
```

**Divergência:** Outro `.apply(lambda)` no domínio, violando ADR-011. Alternativa vectorizada não trivial porque `map_location` é uma função custom com lógica de matching por substring, mas poderia ser vectorizada com `.map()` e um dicionário pré-computado.

---

## 20. DonotBuy — Merge Sempre `detailed=True`

**PRD §6.2.2** — duas modalidades de merge conforme a vista:

| Vista | Chaves de merge |
|---|---|
| Agrupada | `('CÓDIGO', 'CNP')` com dedup por CNP |
| Detalhada | `(['CÓDIGO', 'LOCALIZACAO'], ['CNP', 'FARMACIA'])` |

**Código real** (`session_service.py:89`):

```python
df_full = merge_donotbuy(df_full, df_dnb, detailed=True)
```

**Divergência:** O `session_service` chama `merge_donotbuy` com `detailed=True` **no DataFrame raw** (antes da agregação). Isto é semanticamente correcto porque o `df_full` antes da agregação contém `LOCALIZACAO` por loja. No entanto, o PRD especifica que o merge acontece **no recálculo** (em `recalculate_proposal`), não no processamento inicial. A implementação escolheu fazer o merge mais granular (por loja) no raw e depois preservar a coluna `DATA_OBS` durante a agregação — o que é mais eficiente mas diverge do fluxo descrito no PRD.

---

## 21. ScopeContext — Campos Divergentes

**PRD §8.7 — ScopeContext:**

```python
@dataclass
class ScopeContext:
    n_produtos: int
    n_farmacias: int
    filtro_descricao: str
    janela_meses: str
    preset_pesos: str
    meses_previsao: float
    modo_vista: str
```

**Código real** (`session_state.py:9-19`):

```python
@dataclass(slots=True)
class ScopeContext:
    n_produtos: int = 0
    n_farmacias: int = 0
    descricao_filtro: str = ""
    primeiro_mes: str = ""
    ultimo_mes: str = ""
    ano_range: str = ""
    meses: float = 0.0
    modo: str = ""
```

**Divergências:**

| Campo PRD | Campo Código | Diferença |
|---|---|---|
| `filtro_descricao` | `descricao_filtro` | Nome invertido |
| `janela_meses` | `primeiro_mes` + `ultimo_mes` + `ano_range` | PRD usa 1 campo composto; código usa 3 campos |
| `preset_pesos` | — | **Ausente no código** — não rastreia o preset activo |
| `meses_previsao` | `meses` | Nome diferente |
| `modo_vista` | `modo` | Nome diferente |

A decomposição de `janela_meses` em 3 campos dá mais flexibilidade de formatação, mas o campo `preset_pesos` está ausente, impedindo que o scope bar mostre o preset activo como o PRD exige.

---

## 22. FileInventoryEntry — Campos Divergentes

**PRD §8.8 — FileInventoryEntry:**

```python
@dataclass
class FileInventoryEntry:
    filename: str
    farmacia: str | None
    linhas: int
    data_max: datetime | None
    anomalias_preco: int
    status: Literal["ok", "error"]
    error_message: str | None
```

**Código real** (`session_state.py:23-33`):

```python
@dataclass(slots=True)
class FileInventoryEntry:
    filename: str
    farmacia: str = ""
    n_linhas: int = 0
    duv_max: str = ""
    avisos: str = ""
    status: str = "ok"
    error_message: str = ""
```

**Divergências:**

| Campo PRD | Campo Código | Diferença |
|---|---|---|
| `farmacia: str \| None` | `farmacia: str = ""` | PRD permite None; código usa string vazia |
| `linhas` | `n_linhas` | Nome diferente |
| `data_max: datetime \| None` | `duv_max: str = ""` | PRD usa datetime; código usa string formatada |
| `anomalias_preco: int` | — | **Ausente no código** — não rastreia contagem |
| — | `avisos: str = ""` | **Extra no código** — campo de texto livre para avisos gerais |

O campo `anomalias_preco` está ausente, apesar de o PRD §8.8 e §8.5 exigirem que o File Inventory mostre a contagem de anomalias de preço. O código compensa parcialmente concatenando a contagem no campo `avisos` (`session_service.py:143-144`).

---

## 23. Constants — Campos Ausentes

**PRD §8.2** lista constantes que devem existir em `constants.py`:

**Presentes no código:**

- `Columns` (StrEnum) — ✔ todos os campos listados no PRD
- `GroupLabels` — ✔
- `Weights` — ✔ (PADRAO, CONSERVADOR, AGRESSIVO)
- `Highlight` — ✔ parcial (ver abaixo)
- `Limits` — ✔ parcial (ver abaixo)

**Campos ausentes no código `Highlight`:**

- `NAO_COMPRAR_FG` — PRD define `#000000`; código não tem
- `RUTURA_FG` — PRD define `#FFFFFF`; código não tem
- `VALIDADE_FG` — PRD define `#000000`; código não tem

Os valores estão hardcoded em `rules.py` via `Font(color=...)` em vez de referenciados a partir de `constants.py`.

**Campos ausentes no código `Limits`:**

| Constante PRD | Valor PRD | No código? |
|---|---|---|
| `STYLER_MAX_ELEMENTS` | `1_000_000` | ✘ Ausente |
| `CODIGO_LOCAL_PREFIX` | `'1'` | ✘ Ausente |
| `MESES_COUNT` | `15` | ✘ Ausente |
| `MEDIA_WINDOW` | `4` | ✘ Ausente (existe `MEDIA_WINDOW_SIZE = 4` — nome ligeiramente diferente) |
| `VALIDADE_ALERT_MONTHS` | `4` | ✘ Existe como `VALIDADE_ALERTA_MESES = 4` |

O código adiciona `MESES_PREVISAO_DEFAULT = 1.0` que não está no PRD.

---

## 24. Integrations — import streamlit no Domínio

**Já coberto na secção 11**, mas merece destaque pela gravidade:

| Ficheiro | Linha | Uso Streamlit |
|---|---|---|
| `integrations/shortages.py` | 12, 14, 44 | `import streamlit as st`, `st.cache_data`, `st.sidebar.warning` |
| `integrations/donotbuy.py` | 12, 14 | `import streamlit as st`, `st.cache_data` |

O PRD §8.1 exige:

> `grep -r "import streamlit" orders_master/` devolve zero matches.

O módulo `shortages.py` vai mais longe ao chamar `st.sidebar.warning()` de dentro do domínio — não apenas usa Streamlit para caching, mas para **renderizar UI**. Isto é uma violação dupla da separação arquitectural.

---

## 25. Aggregate — Assinatura sem master_products no recalc_service?

**PRD §5.3.3 — Assinatura:**

```python
def aggregate(df, detailed: bool, master_products: pd.DataFrame) -> pd.DataFrame:
```

**Código real** (`recalc_service.py:72`):

```python
df_agg = aggregate(df_work, detailed_view, master_products)
```

A assinatura está correcta. No entanto, o PRD especifica que o `recalc_service` deve receber `df_aggregated` e `df_detailed` do `SessionState` (já agregados) e calcular apenas propostas, não re-agregar. O código re-agrega a cada recálculo, passando o `df_work` (que já inclui MEDIA e PROPOSTA calculadas) através do motor de agregação.

**Divergência:** O `recalculate_proposal` faz re-agregação em vez de operar directamente sobre os DataFrames agregados. O aggregator foi modificado para somar `MEDIA` e `PROPOSTA`, mas isto significa que a agregação corre duas vezes: uma no `session_service` e outra no `recalc_service`. O PRD §3.3 P4 não contempla este "duplo aggregate".

---

## 26. Recalc Service — Re-Agrega em Cada Recálculo

**PRD §3.1 — Fluxo Principal:**

> Processar Dados → session_service (parse + aggregate + integrations) → SessionState
> Interação UI → recalculate_proposal (lê SessionState, aplica business_logic, devolve DataFrame)

**Código real** (`recalc_service.py:62-72`):

```python
df_work[Columns.MEDIA] = weighted_average(df_work, weights, use_previous_month)
df_work = compute_base_proposal(df_work, months)
df_work = compute_shortage_proposal(df_work)
df_agg = aggregate(df_work, detailed_view, master_products)
```

O `recalculate_proposal` opera sobre `df_detailed` (o DataFrame já processado por loja), **adiciona** colunas de cálculo, e depois **re-agrega**. Isto difere do fluxo PRD que diz que o recálculo opera sobre DataFrames "já em SessionState" e apenas recalcula propostas.

**Diferença prática:** O recálculo no código é mais pesado do que o PRD especifica, porque re-corre o motor de agregação. Se o PRD pretendesse optimização, os DataFrames agregados já estariam em SessionState e o recálculo apenas actualizaria a coluna Proposta.

---

## 27. Session Service — Init de Colunas de Integração em df_raw

**Código real** (`session_service.py:62-64`):

```python
for col in [Columns.DIR, Columns.DPR, Columns.DATA_OBS, Columns.TIME_DELTA]:
    if col not in df_full.columns:
        df_full[col] = pd.NA
```

**Divergência:** O código inicializa colunas de integração com `pd.NA` no DataFrame bruto mesmo quando as integrações falharam ou as URLs estavam vazias. Isto garante que a formatação visual nunca quebra por falta de colunas (porque `rules.py` verifica `pd.notna()` nos predicates). O PRD não documenta esta prática defensiva — implica que as colunas só existem se o merge acontecer (§4.1.4, §4.1.5).

**Impacto:** Positivo (robustez), mas diverge do modelo de dados do PRD.

---

## 28. Lazy Merge — codigos_visible Ignorado no session_service

**PRD §8.10 — Lazy Merge:**

> O chamador (em `recalc_service`) passa o conjunto de `CÓDIGO` presentes em `df_aggregated` / `df_detailed`.

**Código real** (`session_service.py:74`):

```python
df_shortages = fetch_shortages_db(url_shortages)
```

**Divergência:** O `session_service` chama `fetch_shortages_db()` sem passar `codigos_visible`. A função suporta o parâmetro (shortages.py:27), mas não é utilizado na invocação principal. Isto significa que a BD inteira é carregada em todos os cenários, mesmo quando o filtro é de 10 produtos. O lazy merge do PRD não é aplicado no pipeline pesado.

---

## 29. Banner BD Rupturas — Formato da Data

**PRD §6.2.3:**

> Valor: primeiro `Data da Consulta` da sheet de Esgotados, formatado `YYYY-MM-DD`. Se a integração falhar: `"Não foi possível carregar a INFO"`.

**Código real** (`session_service.py:81`):

```python
state.shortages_data_consulta = str(df_shortages["Data da Consulta"].iloc[0])
```

**Divergência:** O valor é guardado como string bruta do que vem da sheet, sem formatar para `YYYY-MM-DD`. O formato final depende de como o Pandas faz `str()` do tipo na coluna, que pode ser `"2026-04-15 00:00:00"` em vez de `"2026-04-15"`. Sem formatação explícita `.strftime('%Y-%m-%d')`, o resultado é imprevisível.

---

## 30. Resumo Quantitativo

| Categoria | Contagem |
|---|---|
| **PRD diz, código não faz** | 8 |
| **Código faz, PRD não diz** | 7 |
| **Desvio de lógica/nome/semântica** | 15 |
| **Total de divergências** | **30** |

### Detalhe por gravidade:

| # | Divergência | Gravidade | Acção sugerida |
|---|---|---|---|
| 3 | ProcessPool → ThreadPool | **Alta** | Actualizar ADR-010 ou rever para ProcessPool |
| 5 | Integrações no pipeline pesado vs leve | **Alta** | Clarificar no PRD qual pipeline chama integrações |
| 11/24 | `import streamlit` no domínio | **Alta** | Mover `st.sidebar.warning` para UI; extrair cache decorator |
| 12 | URLs reais no secrets.toml | **Alta** | Mover para .gitignore, criar .example |
| 17 | Filtro marcas sem preservar Grupo | **Média** | Implementar ADR-013 explícito |
| 28 | Lazy merge não aplicado | **Média** | Passar `codigos_visible` no session_service |
| 25/26 | Re-agregação no recalc | **Média** | Documentar ou refactoring para evitar duplo aggregate |
| 18/19 | `.apply(lambda)` no domínio | **Média** | Vectorizar (ADR-011) |
| 21 | ScopeContext sem `preset_pesos` | **Baixa** | Adicionar campo |
| 22 | FileInventoryEntry sem `anomalias_preco` | **Baixa** | Adicionar campo dedicado |
| 23 | Constants incompletos | **Baixa** | Adicionar campos em falta |
| 6 | "4 regras" vs 5 no §3.2 | **Baixa** | Actualizar texto do PRD |
| 7 | DetailedRowSchema não listado em §3.2 | **Baixa** | Adicionar à lista |
| 8 | PriceAnomalyWarning órfão | **Baixa** | Remover ou usar |
| 9 | Secrets loader inconsistente | **Baixa** | Alinhar estrutura/nomes |
| 10 | on_bad_lines vs errors | **Baixa** | Clarificar semântica |
| 13 | .env.example vazio | **Baixa** | Preencher template |
| 14/15 | Ficheiros não listados no PRD | **Baixa** | Adicionar à estrutura §3.4 |
| 27 | Init de colunas de integração | **Informativo** | Documentar prática defensiva |
| 29 | Formato data banner | **Baixa** | Adicionar `.strftime('%Y-%m-%d')` |
| 20 | Merge donotbuy sempre detailed | **Informativo** | Correcto no contexto, mas documentar |
| 2 | UI alerts.py / documentation.py | **Baixa** | Extrair de main_area.py |
| 4 | SessionState campos extra | **Informativo** | Documentar no PRD |