# TarefasV2 — Plano de Optimização e Correcção

> **Data:** 2026-05-08
> **Base:** Análise exaustiva de 30 divergências entre PRD v2 e implementação real
> **Critério:** Cada tarefa está classificada por prioridade e veredicto (corrigir código vs actualizar PRD)

---

## Convenções

- **Veredicto CC** = Código Correcto, actualizar PRD
- **Veredicto PC** = PRD Correcto, corrigir Código
- **Veredicto AM** = Ambos precisam de ajuste Mútuo
- Cada tarefa tem: veredicto, ficheiros afectados, descrição, critério de aceitação

---

## FASE 1 — Segurança e Arquitectura (Prioridade ALTA)

### T2-01 — Mover secrets.toml para .gitignore e criar template

- **Veredicto:** PC (PRD Correcto, corrigir Código)
- **Divergência:** #12
- **Ficheiros afectados:**
  - `.streamlit/secrets.toml` → remover do git tracking
  - `.streamlit/secrets.toml.example` → criar novo
  - `.gitignore` → adicionar entradas
  - `.env.example` → preencher com template

**Descrição:**

O ficheiro `.streamlit/secrets.toml` contém URLs reais das Google Sheets commitadas no repositório. Isto viola NFR-S1 e o critério de aceitação do PRD §8.14.

**Acções:**

1. Criar `.streamlit/secrets.toml.example` com a estrutura correcta (secção `[google_sheets]` conforme PRD §6.3.4):
   ```toml
   # .streamlit/secrets.toml.example
   # Copiar para .streamlit/secrets.toml e preencher com URLs reais
   
   [google_sheets]
   shortages_url = "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/pub?output=xlsx"
   donotbuy_url  = "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/pub?output=xlsx"
   ```

2. Adicionar ao `.gitignore`:
   ```
   .streamlit/secrets.toml
   .env
   ```

3. Preencher `.env.example` com:
   ```
   # Variáveis de ambiente para integrações Google Sheets
   # Usadas como fallback quando st.secrets não está disponível
   SHORTAGES_URL=
   DONOTBUY_URL=
   ```

4. Remover `.streamlit/secrets.toml` do tracking do git (mantendo o ficheiro local com `git rm --cached`).

**Critério de aceitação:** `git check-ignore .streamlit/secrets.toml .env` devolve ambos; o ficheiro `.example` está commitado com template preenchido.

---

### T2-02 — Remover import streamlit do domínio (integrations)

- **Veredicto:** PC (PRD Correcto, corrigir Código)
- **Divergência:** #11, #24
- **Ficheiros afectados:**
  - `orders_master/integrations/shortages.py`
  - `orders_master/integrations/donotbuy.py`
  - `orders_master/app_services/session_service.py` (possível refactoring)

**Descrição:**

O package `orders_master/integrations/` importa e usa `streamlit` de duas formas problemáticas:
1. `st.cache_data` como decorator de cache
2. `st.sidebar.warning()` para renderizar UI directamente do domínio

A regra arquitectural ADR-002 exige zero `import streamlit` em `orders_master/`.

**Acções:**

1. **Extrair lógica de cache** para um módulo `orders_master/integrations/cache_helpers.py` que:
   - Tenta `from streamlit import cache_data` com `try/except ImportError`
   - Fornece um decorator no-op como fallback
   - `shortages.py` e `donotbuy.py` importam de `cache_helpers` em vez de `import streamlit`

2. **Remover `st.sidebar.warning()`** de `shortages.py:44`. Em vez de renderizar UI no domínio:
   - `fetch_shortages_db()` já devolve DataFrame vazio em caso de falha
   - Mover a exibição do aviso para `ui/main_area.py` que verifica se o DataFrame de shortages está vazio e exibe `st.sidebar.warning()`
   - Alternativamente: `fetch_shortages_db()` pode retornar também um flag/erro que a UI consome

3. **Verificar** que `grep -r "import streamlit" orders_master/` devolve zero matches.

**Critério de aceitação:** `grep -r "import streamlit" orders_master/` devolve 0 resultados; os testes unitários de integrações continuam a passar.

---

### T2-03 — Corrigir filtro de marcas no recalc_service (ADR-013)

- **Veredicto:** PC (PRD Correcto, corrigir Código)
- **Divergência:** #17
- **Ficheiros afectados:**
  - `orders_master/app_services/recalc_service.py`

**Descrição:**

O filtro de marcas no `recalc_service.py:53-55` tem dois bugs:

1. **Não preserva a linha Grupo explicitamente** — o PRD ADR-13 exige `mask_keep = (df['LOCALIZACAO'] == 'Grupo') | (df['MARCA'].isin(marcas))`. O código actual filtra por CNPs válidos, o que pode excluir linhas Grupo.

2. **Não faz DROP da coluna MARCA** antes de chamar `weighted_average()` — a coluna MARCA permanece no DataFrame quando a âncora posicional `T Uni` é usada, violando o invariante ADR-004.

**Acções:**

Substituir o bloco de filtro de marcas em `recalc_service.py` por:

```python
# 1. Filtrar pelas marcas seleccionadas (preservando linha Grupo - ADR-013)
if marcas:
    mask_keep = (
        (df_work[Columns.LOCALIZACAO] == GroupLabels.GROUP_ROW)
        | (df_work[Columns.MARCA].isin(marcas))
    )
    df_work = df_work[mask_keep].copy()

# 2. DROP imediato da coluna MARCA (invariante posicional ADR-004)
if Columns.MARCA in df_work.columns:
    df_work = df_work.drop(columns=[Columns.MARCA])
```

**Critério de aceitação:** Na vista detalhada filtrada por marca, a linha `Grupo` está sempre presente; a coluna `MARCA` não existe quando `weighted_average()` é chamada; testes `test_aggregator.py` e `test_recalc_service.py` passam.

---

## FASE 2 — Actualizações ao PRD (Prioridade ALTA)

### T2-04 — Actualizar ADR-010: ThreadPool em vez de ProcessPool

- **Veredicto:** CC (Código Correcto, actualizar PRD)
- **Divergência:** #3
- **Ficheiros afectados:** `prd.md`

**Descrição:**

O ADR-010 rejeita `ThreadPoolExecutor` argumentando que o GIL impede paralelismo. Na realidade, `pd.read_csv` liberta o GIL durante I/O (o bottleneck real), e `ThreadPoolExecutor` é a escolha correcta porque:
- Evita overhead de serialização inter-processo (DataFrames grandes)
- Funciona correctamente com objectos Streamlit (`UploadedFile` não é picklável)
- O bottleneck é I/O de ficheiros, não CPU

**Acções:**

1. Actualizar ADR-010 no PRD:
   - **Decisão:** `ThreadPoolExecutor` com `max_workers = min(cpu_count, len(files), 8)`
   - **Alternativas consideradas:** `ProcessPoolExecutor` — rejeitado porque (a) `UploadedFile` do Streamlit não é picklável, (b) overhead de serialização de DataFrames grandes, (c) o GIL é libertado durante I/O (`pd.read_csv` usa C-extensions)
   - **Consequências:** (+) sem overhead de serialização; (+) compatível com objectos Streamlit; (−) paralelismo limitado a I/O-bound tasks

2. Actualizar §8.11 para usar `ThreadPoolExecutor` em vez de `ProcessPoolExecutor`.

3. Actualizar §3.3 P9 para o mesmo.

**Critério de aceitação:** Pesquisa por `ProcessPoolExecutor` no PRD devolve zero resultados.

---

### T2-05 — Actualizar PRD: Integrações no pipeline pesado

- **Veredicto:** CC (Código Correcto, actualizar PRD)
- **Divergência:** #5
- **Ficheiros afectados:** `prd.md`

**Descrição:**

O PRD §3.1 especifica que `recalculate_proposal()` integra com `fetch_shortages()` e `fetch_donotbuy()`. A implementação correcta faz o merge no pipeline pesado (`session_service`) uma vez, e o recálculo opera sobre os dados já merged. Isto é mais eficiente porque:
- Evita re-merge a cada slider change
- O `@st.cache_data(ttl=3600)` já gere a frescura dos dados
- TimeDelta é recalculado no fetch (dentro do cache)

**Acções:**

1. Actualizar PRD §3.1 fluxo principal para documentar:
   - Passo 2: `process_orders_session()` coordena ingestão + agregação + **integrações** (shortages e donotbuy)
   - Passo 3: `recalculate_proposal()` lê do `SessionState`, aplica business_logic (propostas, médias), NÃO chama integrações

2. Actualizar PRD §5.6.2 para clarificar que as integrações correm no pipeline pesado.

3. Documentar `df_raw` como campo de `SessionState` no §4.1.8.

4. Documentar campos extra: `last_brands_selection`, `shortages_data_consulta`.

**Critério de aceitação:** Nenhuma referência a `recalculate_proposal()` chamando integrações; `df_raw` documentado no modelo de dados.

---

### T2-06 — Actualizar PRD: Re-agregação deliberada no recalc

- **Veredicto:** CC (Código Correcto, actualizar PRD)
- **Divergência:** #25, #26
- **Ficheiros afectados:** `prd.md`

**Descrição:**

O `recalculate_proposal()` opera sobre `df_detailed` (raw por loja, persistido em SessionState), calcula Media/Proposta, e re-agrega via `aggregate()`. O PRD §3.1 sugere que o recálculo opera sobre DataFrames já agregados.

A implementação actual é deliberadamente mais simples: ao re-agregar, garante-se que nunca há desalinhamento entre dados raw e agregados. O custo é aceitável para os volumes do projecto (<500ms para re-agregar).

**Acções:**

1. Actualizar PRD §3.1 passo 3 para documentar que `recalculate_proposal()`:
   - Recebe `df_detailed` (raw por loja) do SessionState
   - Calcula média ponderada e propostas
   - Re-agrega com `aggregate(detailed=...)` para obtenção dos DataFrames finais
   - NÃO chama integrações (dados de integração já persistem em `df_detailed`)

2. Adicionar nota em §3.3 P4 justificando o trade-off: simplicidade de implementação vs. performance marginal.

**Critério de aceitação:** O fluxo de `recalculate_proposal()` está correctamente documentado no PRD.

---

## FASE 3 — Correcções Funcionais de Código (Prioridade MÉDIA)

### T2-07 — Vectorizar .apply(lambda) em shortages.py (ADR-011)

- **Veredicto:** PC (PRD Correcto, corrigir Código)
- **Divergência:** #18
- **Ficheiros afectados:** `orders_master/integrations/shortages.py`

**Descrição:**

A linha `shortages.py:61-63` usa `.apply(lambda)` para calcular TimeDelta, violando ADR-011.

**Acções:**

Substituir:
```python
df[Columns.TIME_DELTA] = (df["Data prevista para reposição"].dt.date - today).apply(
    lambda x: x.days if pd.notnull(x) else pd.NA
)
```

Por versão vectorizada:
```python
delta = df["Data prevista para reposição"].dt.date - today
df[Columns.TIME_DELTA] = pd.NA
valid_mask = delta.notna()
df.loc[valid_mask, Columns.TIME_DELTA] = delta[valid_mask].apply(lambda x: getattr(x, 'days', pd.NA))
```

Ou, se os deltas forem `timedelta` objects:
```python
delta = df["Data prevista para reposição"] - pd.Timestamp(today)
df[Columns.TIME_DELTA] = delta.dt.days.where(delta.notna(), pd.NA)
```

**Critério de aceitação:** `grep -r "\.apply.*lambda" orders_master/integrations/shortages.py` devolve zero; testes existentes passam; resultado numérico idêntico.

---

### T2-08 — Vectorizar .apply(lambda) em donotbuy.py (ADR-011)

- **Veredicto:** PC (PRD Correcto, corrigir Código)
- **Divergência:** #19
- **Ficheiros afectados:** `orders_master/integrations/donotbuy.py`

**Descrição:**

A linha `donotbuy.py:49-51` usa `.apply(lambda)` para mapear localizações. A função `map_location` tem lógica de substring matching que não é trivialmente vectorizável com Pandas puro, mas pode ser optimizada.

**Acções:**

Opção A — Pre-computar mapeamento e usar `.map()`:
```python
# Pre-computar todos os mapeamentos únicos
unique_farmacias = df["FARMACIA"].dropna().unique()
mapping_dict = {name: map_location(str(name), aliases) for name in unique_farmacias}
df["FARMACIA"] = df["FARMACIA"].map(mapping_dict).fillna("")
```

Opção B — Usar `np.vectorize`:
```python
vmap = np.vectorize(lambda x: map_location(str(x), aliases) if pd.notna(x) else "")
df["FARMACIA"] = vmap(df["FARMACIA"].values)
```

Escolher Opção A por ser mais eficiente (evita chamadas repetidas para o mesmo input).

**Critério de aceitação:** `grep -r "\.apply.*lambda" orders_master/integrations/donotbuy.py` devolve zero; testes existentes passam; resultado idêntico.

---

### T2-09 — Implementar lazy merge (codigos_visible) no session_service

- **Veredicto:** PC (PRD Correcto, corrigir Código)
- **Divergência:** #28
- **Ficheiros afectados:** `orders_master/app_services/session_service.py`

**Descrição:**

O PRD §8.10 especifica lazy merge — passar `codigos_visible` para `fetch_shortages_db()` para filtrar a sheet antes do merge. A função já suporta o parâmetro mas não é utilizado.

**Acções:**

Em `session_service.py`, na chamada a `fetch_shortages_db`, adicionar:

```python
codigos_visible = set(df_full[Columns.CODIGO].unique()) if not df_full.empty else None
df_shortages = fetch_shortages_db(url_shortages, codigos_visible=codigos_visible)
```

**Critério de aceitação:** Quando o filtro de códigos contém 10 códigos, a sheet de shortages é filtrada antes do merge; os resultados são idênticos ao comportamento anterior.

---

### T2-10 — Corrigir formato da data no banner BD Rupturas

- **Veredicto:** PC (PRD Correcto, corrigir Código)
- **Divergência:** #29
- **Ficheiros afectados:** `orders_master/app_services/session_service.py`

**Descrição:**

`session_service.py:81` guarda a data da consulta como `str(df_shortages["Data da Consulta"].iloc[0])`, que pode produzir `"2026-04-15 00:00:00"` em vez de `"2026-04-15"`.

**Acções:**

Substituir:
```python
state.shortages_data_consulta = str(df_shortages["Data da Consulta"].iloc[0])
```

Por:
```python
data_consulta = df_shortages["Data da Consulta"].iloc[0]
if pd.notna(data_consulta):
    try:
        state.shortages_data_consulta = pd.Timestamp(data_consulta).strftime("%Y-%m-%d")
    except Exception:
        state.shortages_data_consulta = str(data_consulta)
else:
    state.shortages_data_consulta = None
```

**Critério de aceitação:** `shortages_data_consulta` está sempre no formato `YYYY-MM-DD` ou `None`.

---

### T2-11 — Preencher .env.example com template

- **Veredicto:** PC (PRD Correcto, corrigir Código)
- **Divergência:** #13
- **Ficheiros afectados:** `.env.example`

**Descrição:**

O `.env.example` está vazio (0 bytes). Deve conter as variáveis de ambiente necessárias.

**Acções:**

Preencher `.env.example` com:
```bash
# Variáveis de ambiente para Orders Master Infoprex
# Copiar para .env e preencher com URLs reais

# Google Sheet - BD Esgotados (Infarmed)
SHORTAGES_URL=

# Google Sheet - Produtos Não Comprar
DONOTBUY_URL=
```

**Critério de aceitação:** O ficheiro contém todas as variáveis necessárias com comentários explicativos.

---

### T2-12 — Alinhar estrutura do secrets.toml com PRD

- **Veredicto:** AM (Ambos precisam de ajuste)
- **Divergência:** #9
- **Ficheiros afectados:**
  - `.streamlit/secrets.toml` → reestruturar com secção `[google_sheets]`
  - `orders_master/secrets_loader.py` → actualizar navegação de keys
  - `orders_master/app_services/session_service.py` → passar a usar `secrets_loader.py`
  - `prd.md` → já actualizado em T2-04? Não — alinhar nomes de chaves

**Descrição:**

O PRD §8.14 e §6.3.4 usam `st.secrets["google_sheets"]["shortages_url"]` (secção aninhada), mas o código usa `st.secrets.get("SHORTAGES_URL")` (top-level plano). O `secrets_loader.py` existe mas não é utilizado pelo pipeline principal.

**Acções:**

1. Reestruturar `secrets.toml.example` (já criado em T2-01) para usar secção `[google_sheets]`:
   ```toml
   [google_sheets]
   shortages_url = "https://docs.google.com/..."
   donotbuy_url  = "https://docs.google.com/..."
   ```

2. Mover `secrets_loader.py` de `orders_master/secrets_loader.py` para `orders_master/config/secrets_loader.py`.

3. Actualizar `secrets_loader.py` para suportar navegação por `key_path` com secções:
   ```python
   def get_secret(key_path: str, env_var: str | None = None) -> str | None:
       # 1. st.secrets com navegação por pontos
       # 2. Variável de ambiente
       # 3. .env fallback
   ```

4. Actualizar `session_service.py` para usar `get_secret("google_sheets.shortages_url", "SHORTAGES_URL")` em vez de `st.secrets.get("SHORTAGES_URL")`.

**Critério de aceitação:** `secrets_loader.py` é o único ponto de acesso a secrets; `session_service.py` não importa `streamlit` directamente para secrets; testes continuam a passar.

---

## FASE 4 — Correcções de Constants e Dataclasses (Prioridade MÉDIA)

### T2-13 — Completar constants.py com campos em falta

- **Veredicto:** PC (PRD Correcto, corrigir Código)
- **Divergência:** #23
- **Ficheiros afectados:**
  - `orders_master/constants.py`
  - `orders_master/formatting/rules.py` (refactor para usar constants)

**Descrição:**

O PRD §8.2 define constantes que não existem no código ou têm nomes diferentes. Os valores de foreground do `Highlight` estão hardcoded em `rules.py` em vez de referenciados a partir de `constants.py`.

**Acções:**

1. Adicionar a `Highlight` em `constants.py`:
   ```python
   NAO_COMPRAR_FG = '#000000'
   RUTURA_FG = '#FFFFFF'
   VALIDADE_FG = '#000000'
   ```

2. Adicionar a `Limits` em `constants.py`:
   ```python
   STYLER_MAX_ELEMENTS = 1_000_000
   CODIGO_LOCAL_PREFIX = '1'
   MESES_COUNT = 15
   ```

3. Renomear `MEDIA_WINDOW_SIZE` para `MEDIA_WINDOW` (alinhar com PRD).

4. Refactor `rules.py` para usar `Highlight.NAO_COMPRAR_FG`, `Highlight.RUTURA_FG`, `Highlight.VALIDADE_FG` em vez de valores hardcoded.

**Critério de aceitação:** `grep -r "#000000\|#FFFFFF\|#FF0000" orders_master/formatting/rules.py` devolve apenas referências a constants; testes passam.

---

### T2-14 — Adicionar campo preset_pesos ao ScopeContext

- **Veredicto:** PC (PRD Correcto, corrigir Código)
- **Divergência:** #21
- **Ficheiros afectados:**
  - `orders_master/app_services/session_state.py`
  - `ui/scope_bar.py`
  - `orders_master/app_services/recalc_service.py`

**Descrição:**

O PRD §8.7 exige que o Scope Summary Bar mostre o preset activo (ex: "Padrão", "Conservador"). O `ScopeContext` no código não tem campo `preset_pesos`.

**Acções:**

1. Adicionar campo a `ScopeContext`:
   ```python
   preset_pesos: str = ""  # ex: "Padrão", "Conservador", "Agressivo", "Custom"
   ```

2. Actualizar `recalc_service.py` para popular o campo quando o scope_context é actualizado.

3. Actualizar `ui/scope_bar.py` para exibir o preset.

**Critério de aceitação:** O Scope Summary Bar mostra o preset activo; o campo está presente no dataclass.

---

### T2-15 — Adicionar campo anomalias_preco ao FileInventoryEntry

- **Veredicto:** PC (PRD Correcto, corrigir Código)
- **Divergência:** #22
- **Ficheiros afectados:**
  - `orders_master/app_services/session_state.py`
  - `orders_master/app_services/session_service.py`
  - `ui/file_inventory.py`

**Descrição:**

O PRD §8.8 exige que o File Inventory mostre a contagem de anomalias de preço por ficheiro. O código compensa concatenando no campo `avisos`, mas deveria ter um campo dedicado.

**Acções:**

1. Adicionar campo a `FileInventoryEntry`:
   ```python
   anomalias_preco: int = 0
   ```

2. Actualizar `session_service.py:140-144` para popular o campo dedicado em vez de concatenar em `avisos`.

3. Actualizar `ui/file_inventory.py` para exibir a contagem de anomalias como coluna separada.

**Critério de aceitação:** O File Inventory mostra coluna "Anomalias preço" com contagem numérica; o campo `avisos` deixa de conter informação de anomalias.

---

### T2-16 — Alinhar nomes de campos SessionState com PRD

- **Veredicto:** PC (PRD Correcto, corrigir Código)
- **Divergência:** #4
- **Ficheiros afectados:**
  - `orders_master/app_services/session_state.py`
  - Todos os ficheiros que referenciam `master_products` (deve passar a `df_master_products`)

**Descrição:**

O PRD §4.1.8 usa `df_master_products` mas o código usa `master_products`. Além disso, faltam documentar `df_raw`, `last_brands_selection` e `shortages_data_consulta`.

**Acções:**

1. Renomear `SessionState.master_products` para `SessionState.df_master_products` (alinhar com PRD).

2. Adicionar `df_raw`, `last_brands_selection`, `shortages_data_consulta` à documentação do PRD como campos válidos (T2-05 já cobre isto parcialmente).

3. Actualizar todas as referências a `state.master_products` e `st.session_state["orders_master_state"].master_products` em todo o código.

**Critério de aceitação:** `grep -r "\.master_products" orders_master/ ui/` devolve zero resultados; campo `df_master_products` está presente; testes passam.

---

## FASE 5 — Limpeza Menor de Código (Prioridade BAIXA)

### T2-17 — Remover PriceAnomalyWarning (código morto)

- **Veredicto:** PC (PRD Correcto, corrigir Código)
- **Divergência:** #8
- **Ficheiros afectados:**
  - `orders_master/exceptions.py`
  - `orders_master/business_logic/price_validation.py`
  - Qualquer teste que referencie `PriceAnomalyWarning`

**Descrição:**

`PriceAnomalyWarning(UserWarning)` é definida em `exceptions.py:24` mas nunca é emitida via `warnings.warn()`. A coluna booleana `price_anomaly` e a regra 5 em `rules.py` tratam da funcionalidade. A classe é código morto.

**Acções:**

1. Remover `class PriceAnomalyWarning(UserWarning)` de `exceptions.py`.

2. Verificar se algum teste referencia `PriceAnomalyWarning` e actualizar.

3. Verificar se o PRD §5.6.1 deve ser actualizado para reflectir que a anomalia é marcada apenas via flag booleana, não via `UserWarning`.

**Critério de aceitação:** `grep -r "PriceAnomalyWarning" orders_master/` devolve zero; testes passam.

---

### T2-18 — Corrigir encoding_fallback.py (on_bad_lines e errors)

- **Veredicto:** AM (Ambos precisam de ajuste)
- **Divergência:** #10
- **Ficheiros afectados:** `orders_master/ingestion/encoding_fallback.py`

**Descrição:**

O código usa `on_bad_lines="error"` mas o PRD/TASK-09 referem `errors='strict'`. São parâmetros diferentes:
- `on_bad_lines` controla linhas mal formatadas no CSV
- `errors` controla bytes não decodificáveis no encoding

Ambos deviam ser configurados explicitamente.

**Acções:**

1. Adicionar `errors='strict'` ao `pd.read_csv()` para forçar falha se o encoding tiver bytes inválidos (em vez de `except Exception: continue` comer tudo).

2. Mudar `on_bad_lines` de `"error"` para `"skip"` — linhas mal formatadas devem ser ignoradas silenciosamente (consistente com o comportamento de `brands_parser.py` que usa `on_bad_lines='skip'`). Isto evita que um ficheiro com uma linha corrompida faça falhar todo o parsing.

3. Actualizar PRD §5.1.2 para documentar ambos os parâmetros.

**Critério de aceitação:** `encoding_fallback.py` usa `errors='strict'` e `on_bad_lines='skip'`; linhas mal formatadas são saltadas; bytes inválidos causam `InfoprexEncodingError`.

---

### T2-19 — Extrair componentes UI alerts.py e documentation.py de main_area.py

- **Veredicto:** PC (PRD Correcto, corrigir Código)
- **Divergência:** #2
- **Ficheiros afectados:**
  - `ui/main_area.py` → refactor
  - `ui/alerts.py` → criar novo
  - `ui/documentation.py` → criar novo

**Descrição:**

O PRD §3.2 e §3.4 especificam dois módulos UI separados: `ui/alerts.py` com `render_errors_and_warnings()` e `ui/documentation.py` com `render_help_expander()`. A lógica está integrada em `main_area.py`.

**Acções:**

1. Criar `ui/alerts.py` com função `render_errors_and_warnings(state: SessionState)` que exibe `st.error()` para cada erro e `st.warning()` para filtros obsoletos.

2. Criar `ui/documentation.py` com função `render_help_expander()` que exibe o expander "ℹ️ Documentação e Workflow".

3. Refactor `main_area.py` para importar e chamar estas funções em vez de ter lógica inline.

**Critério de aceitação:** Ambos os ficheiros existem; `main_area.py` reduz linhas; funcionalidade não muda.

---

## FASE 6 — Actualizações de Documentação do PRD (Prioridade BAIXA)

### T2-20 — Actualizar PRD §3.2: "4 regras" → "5 regras"

- **Veredicto:** CC (Código Correcto, actualizar PRD)
- **Divergência:** #6
- **Ficheiros afectados:** `prd.md`

**Descrição:**

O PRD §3.2 diz "4 regras visuais" mas o §6.1.6 lista 5 regras e o código define 5. O §3.2 está desactualizado.

**Acções:**

Actualizar §3.2 tabela de `formatting/rules.py` de:
> Encapsula as **4 regras visuais** (grupo, não comprar, rutura, validade).

Para:
> Encapsula as **5 regras visuais** (grupo, não comprar, rutura, validade, preço anómalo).

**Critério de aceitação:** Pesquisa por "4 regras" no PRD devolve zero resultados.

---

### T2-21 — Adicionar DetailedRowSchema à lista de §3.2

- **Veredicto:** CC (Código Correcto, actualizar PRD)
- **Divergência:** #7
- **Ficheiros afectados:** `prd.md`

**Descrição:**

O PRD §3.2 lista 5 schemas mas omite `DetailedRowSchema`, que existe no código e é descrito em §4.1.3.

**Acções:**

Actualizar §3.2 tabela de schemas de:
> `orders_master/schemas.py` | Domínio — Contratos | Define os schemas tipados (pydantic): `InfoprexRowSchema`, `AggregatedRowSchema`, `ShortageRowSchema`, `DoNotBuyRowSchema`, `BrandRowSchema`.

Para:
> `orders_master/schemas.py` | Domínio — Contratos | Define os schemas tipados (pydantic): `InfoprexRowSchema`, `AggregatedRowSchema`, `DetailedRowSchema`, `ShortageRowSchema`, `DoNotBuyRowSchema`, `BrandRowSchema`.

**Critério de aceitação:** `DetailedRowSchema` aparece na lista de §3.2.

---

### T2-22 — Adicionar ficheiros em falta à estrutura §3.4

- **Veredicto:** CC (Código Correcto, actualizar PRD)
- **Divergência:** #14
- **Ficheiros afectados:** `prd.md`

**Descrição:**

Os seguintes ficheiros existem no código mas não estão na árvore de directorias do PRD §3.4:
- `orders_master/config/validate.py`
- `orders_master/config/presets_loader.py`
- `orders_master/secrets_loader.py` (deve ser movido para `orders_master/config/` na T2-12)

**Acções:**

Adicionar à árvore de §3.4:
```
│   ├── config/
│   │   ├── __init__.py
│   │   ├── labs_loader.py
│   │   ├── locations_loader.py
│   │   ├── presets_loader.py          # NOVO
│   │   ├── secrets_loader.py          # NOVO (após T2-12)
│   │   └── validate.py               # NOVO
│   └── secrets_loader.py              # MOVER para config/ na T2-12
```

**Critério de aceitação:** Todos os ficheiros de código existentes estão listados na árvore §3.4.

---

### T2-23 — Documentar init defensivo de colunas de integração

- **Veredicto:** CC (Código Correcto, actualizar PRD)
- **Divergência:** #27
- **Ficheiros afectados:** `prd.md`

**Descrição:**

O código inicializa colunas de integração (`DIR`, `DPR`, `DATA_OBS`, `TimeDelta`) com `pd.NA` no DataFrame bruto, mesmo quando as integrações falharam. Esta prática defensiva garante que a formatação nunca quebra por KeyError. O PRD não documenta este comportamento.

**Acções:**

Adicionar nota ao PRD §4.1.7 (entidade FinalProposalRow) ou §5.6.2:

> **Nota defensiva:** O pipeline inicializa as colunas de integração (`DIR`, `DPR`, `DATA_OBS`, `TimeDelta`) com `pd.NA` no DataFrame bruto, independentemente de as integrações terem sucesso. Isto garante que as regras de formatação (§6.1.6) nunca falham por KeyError, utilizando `pd.notna()` nos predicates.

**Critério de aceitação:** A prática defensiva está documentada no PRD.

---

### T2-24 — Documentar merge donotbuy sempre detailed=True

- **Veredicto:** CC (Código Correcto, actualizar PRD)
- **Divergência:** #20
- **Ficheiros afectados:** `prd.md`

**Descrição:**

O código faz `merge_donotbuy(df_full, df_dnb, detailed=True)` no DataFrame raw (pré-agregação), que é semanticamente correcto porque o raw tem `LOCALIZACAO` por loja. O PRD §6.2.2 especifica duas modalidades de merge (agrupada e detalhada), mas na prática só a detalhada é usada no pipeline pesado.

**Acções:**

Actualizar PRD §6.2.2 para clarificar:

> No pipeline pesado (`process_orders_session`), o merge com "Não Comprar" é sempre executado com `detailed=True` no DataFrame raw (pré-agregação), que contém `LOCALIZACAO` por loja. A coluna `DATA_OBS` resultante é preservada durante a agregação, estando disponível tanto na vista agrupada (após dedup por CNP) como na detalhada.

**Critério de aceitação:** PRD documenta correctamente como o merge donotbuy é executado na prática.

---

### T2-25 — Documentar campos extra do SessionState

- **Veredicto:** CC (Código Correcto, actualizar PRD)
- **Divergência:** #4
- **Ficheiros afectados:** `prd.md`

**Descrição:**

O código tem 3 campos em `SessionState` não documentados no PRD §4.1.8: `df_raw`, `last_brands_selection`, `shortages_data_consulta`.

**Acções:**

Adicionar ao PRD §4.1.8 tabela:

| Campo | Tipo | Descrição |
|---|---|---|
| `df_raw` | `pd.DataFrame` | DataFrame bruto pós-ingestão com integrações merged. Usado como input pelo recalc_service. |
| `last_brands_selection` | `list[str]` | Última selecção de marcas. Usado para detectar filtros obsoletos. |
| `shortages_data_consulta` | `str \| None` | Data da consulta da BD de Rupturas para exibição no banner. |

**Critério de aceitação:** Todos os campos do SessionState implementado estão documentados no PRD §4.1.8.

---

## Resumo de Dependências entre Tarefas

```
T2-01 (secrets.toml) ← independente
T2-02 (remover streamlit domínio) ← independente
T2-03 (filtro marcas) ← independente
T2-04 (actualizar ADR-010 PRD) ← independente
T2-05 (actualizar PRD integrações) ← independente
T2-06 (actualizar PRD re-agregação) ← independente
T2-07 (vectorizar shortages) ← independente
T2-08 (vectorizar donotbuy) ← independente
T2-09 (lazy merge) ← pode ser feito antes/depois de T2-02
T2-10 (formato data banner) ← independente
T2-11 (.env.example) ← dependente de T2-01 (criar .example ao mesmo tempo)
T2-12 (alinhar secrets) ← dependente de T2-01 e T2-02
T2-13 (constants) ← independente
T2-14 (scope context) ← independente
T2-15 (file inventory) ← independente
T2-16 (renomear master_products) ← impacto transversal, fazer com cuidado
T2-17 (remover PriceAnomalyWarning) ← independente
T2-18 (encoding fallback) ← independente
T2-19 (extrair UI components) ← independente
T2-20—T2-25 (PRD updates) ← todas independentes entre si
```

## Ordem de Execução Recomendada

| Ordem | Tarefa | Prioridade | Veredicto |
|---|---|---|---|
| 1 | T2-01 | ALTA | PC |
| 2 | T2-02 | ALTA | PC |
| 3 | T2-03 | ALTA | PC |
| 4 | T2-07 | MÉDIA | PC |
| 5 | T2-08 | MÉDIA | PC |
| 6 | T2-09 | MÉDIA | PC |
| 7 | T2-10 | MÉDIA | PC |
| 8 | T2-11 | MÉDIA | PC |
| 9 | T2-12 | MÉDIA | PC |
| 10 | T2-13 | MÉDIA | PC |
| 11 | T2-14 | MÉDIA | PC |
| 12 | T2-15 | MÉDIA | PC |
| 13 | T2-16 | MÉDIA | PC |
| 14 | T2-17 | BAIXA | PC |
| 15 | T2-18 | BAIXA | AM |
| 16 | T2-18 | BAIXA | PC |
| 17 | T2-19 | BAIXA | PC |
| 18 | T2-04 | ALTA | CC |
| 19 | T2-05 | ALTA | CC |
| 20 | T2-06 | ALTA | CC |
| 21 | T2-20 | BAIXA | CC |
| 22 | T2-21 | BAIXA | CC |
| 23 | T2-22 | BAIXA | CC |
| 24 | T2-23 | BAIXA | CC |
| 25 | T2-24 | BAIXA | CC |
| 25 | T2-25 | BAIXA | CC |