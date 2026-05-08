# Todolist — Prompts para Execução de Tarefas T2

> **Data:** 2026-05-08
> **Contexto obrigatório:** Antes de executar qualquer tarefa, lê integralmente `prd.md` e `TarefasV2.md` para compreender o modelo de dados, arquitectura, e ADRs relevantes.
> **Convenção:** Cada prompt abaixo está pronto para ser copiado e dado a um agente. O agente deve ler os ficheiros de contexto indicados, implementar a tarefa, e verificar os critérios de aceitação.

---

## FASE 1 — Segurança e Arquitectura (Prioridade ALTA)

### T2-01 — Mover secrets.toml para .gitignore e criar template

**Prompt:**

```
Lê os ficheiros `prd.md` e `TarefasV2.md` na raiz do projecto para obter todo o contexto arquitectural e de negócio.

Executa a tarefa T2-01 do `TarefasV2.md`: Mover secrets.toml para .gitignore e criar template.

Contexto: O ficheiro `.streamlit/secrets.toml` contém URLs reais das Google Sheets commitadas no repositório, violando NFR-S1 (PRD §7.2) e o critério de aceitação do PRD §8.14. O PRD §6.3.4 define a estrutura esperada do secrets.toml com secção `[google_sheets]`.

Acções a executar:
1. Cria `.streamlit/secrets.toml.example` com a estrutura correcta (secção `[google_sheets]` conforme PRD §6.3.4):
   ```toml
   # .streamlit/secrets.toml.example
   # Copiar para .streamlit/secrets.toml e preencher com URLs reais

   [google_sheets]
   shortages_url = "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/pub?output=xlsx"
   donotbuy_url  = "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/pub?output=xlsx"
   ```

2. Adiciona ao `.gitignore`:
   ```
   .streamlit/secrets.toml
   .env
   ```

3. Preenche `.env.example` com:
   ```
   # Variáveis de ambiente para integrações Google Sheets
   # Usadas como fallback quando st.secrets não está disponível
   SHORTAGES_URL=
   DONOTBUY_URL=
   ```

4. Remove `.streamlit/secrets.toml` do tracking do git (mantendo o ficheiro local): `git rm --cached .streamlit/secrets.toml`

Critérios de aceitação a verificar no final:
- `git check-ignore .streamlit/secrets.toml .env` devolve ambos
- O ficheiro `.streamlit/secrets.toml.example` está commitado com template preenchido
- O `.env.example` contém as variáveis SHORTAGES_URL e DONOTBUY_URL
- O `.gitignore` contém `.streamlit/secrets.toml` e `.env`
```

---

### T2-02 — Remover import streamlit do domínio (integrations)

**Prompt:**

```
Lê os ficheiros `prd.md` e `TarefasV2.md` na raiz do projecto para obter todo o contexto arquitectural e de negócio.

Executa a tarefa T2-02 do `TarefasV2.md`: Remover import streamlit do domínio (integrations).

Contexto: O package `orders_master/integrations/` importa e usa `streamlit` de duas formas problemáticas: (1) `st.cache_data` como decorator de cache, (2) `st.sidebar.warning()` para renderizar UI directamente do domínio. A regra arquitectural ADR-002 (PRD §3.3 P1, §8.1) exige zero `import streamlit` em `orders_master/`. Lê também `orders_master/integrations/shortages.py`, `orders_master/integrations/donotbuy.py`, e `ui/main_area.py` para entender o uso actual.

Acções a executar:
1. Cria `orders_master/integrations/cache_helpers.py` que:
   - Tenta `from streamlit import cache_data` com `try/except ImportError`
   - Fornece um decorator no-op como fallback (decorator que retorna a função inalterada)
   - Exporta `cache_decorator` que pode ser usado por shortages.py e donotbuy.py

2. Substitui em `shortages.py` e `donotbuy.py` o `import streamlit as st` / `st.cache_data` por importação de `cache_helpers`

3. Remove `st.sidebar.warning()` de `shortages.py`. Em vez de renderizar UI no domínio:
   - `fetch_shortages_db()` já devolve DataFrame vazio em caso de falha
   - Move a exibição do aviso para `ui/main_area.py` que verifica se o DataFrame de shortages está vazio e exibe `st.sidebar.warning()`

4. Verifica que `grep -r "import streamlit" orders_master/` devolve zero matches.

Critérios de aceitação a verificar no final:
- `grep -r "import streamlit" orders_master/` devolve 0 resultados
- Os testes unitários de integrações continuam a passar (`pytest tests/unit/test_shortages_integration.py tests/unit/test_donotbuy_integration.py -v`)
- O aviso de falha de ligação continua visível na UI quando o fetch falha
```

---

### T2-03 — Corrigir filtro de marcas no recalc_service (ADR-013)

**Prompt:**

```
Lê os ficheiros `prd.md` e `TarefasV2.md` na raiz do projecto para obter todo o contexto arquitectural e de negócio.

Executa a tarefa T2-03 do `TarefasV2.md`: Corrigir filtro de marcas no recalc_service (ADR-013).

Contexto: O PRD §5.5.5 (Isolamento Matemático) define a ordem obrigatória: (1) filtrar marcas preservando linha Grupo, (2) DROP imediato da coluna MARCA, (3) só depois calcular médias/propostas. O ADR-004 (PRD §3.3 P3) exige que a coluna MARCA não exista quando a âncora posicional `T Uni` é usada. Lê `orders_master/app_services/recalc_service.py`, `orders_master/constants.py` (para `Columns` e `GroupLabels`), e `orders_master/aggregation/aggregator.py` para entender o fluxo actual.

Acções a executar:
Substitui o bloco de filtro de marcas em `recalc_service.py` por:

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

Critérios de aceitação a verificar no final:
- Na vista detalhada filtrada por marca, a linha `Grupo` está sempre presente
- A coluna `MARCA` não existe quando `weighted_average()` é chamada
- Testes `pytest tests/unit/test_aggregator.py tests/unit/test_recalc_service.py -v` passam
```

---

## FASE 2 — Actualizações ao PRD (Prioridade ALTA)

### T2-04 — Actualizar ADR-010: ThreadPool em vez de ProcessPool

**Prompt:**

```
Lê os ficheiros `prd.md` e `TarefasV2.md` na raiz do projecto para obter todo o contexto arquitectural e de negócio.

Executa a tarefa T2-04 do `TarefasV2.md`: Actualizar ADR-010 no PRD — ThreadPool em vez de ProcessPool.

Contexto: O código usa `ThreadPoolExecutor` (correcto, porque `pd.read_csv` liberta o GIL durante I/O e `UploadedFile` do Streamlit não é picklável), mas o PRD ADR-010 rejeita `ThreadPoolExecutor` e recomenda `ProcessPoolExecutor`. Lê `prd.md` (secções §3.3 P9, §8.11, e §10 ADR-010) e `orders_master/app_services/session_service.py` para confirmar o estado actual.

Acções a executar:
1. Actualiza ADR-010 no PRD §10:
   - **Decisão:** `ThreadPoolExecutor` com `max_workers = min(cpu_count, len(files), 8)`
   - **Alternativas consideradas:** `ProcessPoolExecutor` — rejeitado porque (a) `UploadedFile` do Streamlit não é picklável, (b) overhead de serialização de DataFrames grandes, (c) o GIL é libertado durante I/O (`pd.read_csv` usa C-extensions)
   - **Consequências:** (+) sem overhead de serialização; (+) compatível com objectos Streamlit; (−) paralelismo limitado a I/O-bound tasks

2. Actualiza §8.11 para usar `ThreadPoolExecutor` em vez de `ProcessPoolExecutor`.

3. Actualiza §3.3 P9 para o mesmo.

Critérios de aceitação a verificar no final:
- Pesquisa por `ProcessPoolExecutor` no PRD devolve zero resultados
- ADR-010 reflecte a decisão correcta de usar ThreadPoolExecutor
```

---

### T2-05 — Actualizar PRD: Integrações no pipeline pesado

**Prompt:**

```
Lê os ficheiros `prd.md` e `TarefasV2.md` na raiz do projecto para obter todo o contexto arquitectural e de negócio.

Executa a tarefa T2-05 do `TarefasV2.md`: Actualizar PRD — Integrações no pipeline pesado.

Contexto: O PRD §3.1 fluxo principal diz que `recalculate_proposal()` integra com `fetch_shortages()` e `fetch_donotbuy()`. Na realidade, as integrações correm no pipeline pesado (`session_service`) uma vez, e o recálculo opera sobre dados já merged. Isto é mais eficiente. Lê `prd.md` (§3.1, §4.1.8, §5.6.2), `orders_master/app_services/session_service.py`, e `orders_master/app_services/recalc_service.py` para confirmar.

Acções a executar:
1. Actualiza PRD §3.1 fluxo principal para documentar:
   - Passo 2: `process_orders_session()` coordena ingestão + agregação + **integrações** (shortages e donotbuy)
   - Passo 3: `recalculate_proposal()` lê do `SessionState`, aplica business_logic (propostas, médias), NÃO chama integrações

2. Actualiza PRD §5.6.2 para clarificar que as integrações correm no pipeline pesado.

3. Documenta `df_raw` como campo de `SessionState` no §4.1.8.

4. Documenta campos extra: `last_brands_selection`, `shortages_data_consulta`.

Critérios de aceitação a verificar no final:
- Nenhuma referência a `recalculate_proposal()` chamando integrações no PRD
- `df_raw` documentado no modelo de dados §4.1.8
- `last_brands_selection` e `shortages_data_consulta` documentados
```

---

### T2-06 — Actualizar PRD: Re-agregação deliberada no recalc

**Prompt:**

```
Lê os ficheiros `prd.md` e `TarefasV2.md` na raiz do projecto para obter todo o contexto arquitectural e de negócio.

Executa a tarefa T2-06 do `TarefasV2.md`: Actualizar PRD — Re-agregação deliberada no recalc.

Contexto: O `recalculate_proposal()` opera sobre `df_detailed` (raw por loja, persistido em SessionState), calcula Media/Proposta, e re-agrega via `aggregate()`. O PRD §3.1 sugere que o recálculo opera sobre DataFrames já agregados. A implementação actual é deliberadamente mais simples: ao re-agregar, garante-se que nunca há desalinhamento. Lê `prd.md` (§3.1, §3.3 P4) e `orders_master/app_services/recalc_service.py` para confirmar.

Acções a executar:
1. Actualiza PRD §3.1 passo 3 para documentar que `recalculate_proposal()`:
   - Recebe `df_detailed` (raw por loja) do SessionState
   - Calcula média ponderada e propostas
   - Re-agrega com `aggregate(detailed=...)` para obtenção dos DataFrames finais
   - NÃO chama integrações (dados de integração já persistem em `df_detailed`)

2. Adiciona nota em §3.3 P4 justificando o trade-off: simplicidade de implementação vs. performance marginal (custo <500ms para re-agregar, aceitável para os volumes do projecto).

Critérios de aceitação a verificar no final:
- O fluxo de `recalculate_proposal()` está correctamente documentado no PRD §3.1
- §3.3 P4 inclui nota sobre o trade-off
```

---

## FASE 3 — Correcções Funcionais de Código (Prioridade MÉDIA)

### T2-07 — Vectorizar .apply(lambda) em shortages.py (ADR-011)

**Prompt:**

```
Lê os ficheiros `prd.md` e `TarefasV2.md` na raiz do projecto para obter todo o contexto arquitectural e de negócio.

Executa a tarefa T2-07 do `TarefasV2.md`: Vectorizar .apply(lambda) em shortages.py (ADR-011).

Contexto: O ADR-011 (PRD §3.3 P10) proíbe `.apply` com lambdas Python sobre séries/DataFrames. A linha `shortages.py:61-63` usa `.apply(lambda)` para calcular TimeDelta. Lê `orders_master/integrations/shortages.py` e `orders_master/constants.py` para entender o código actual.

Acções a executar:
Substitui o bloco `.apply(lambda)` em `shortages.py` por versão vectorizada. Se os deltas forem `timedelta` objects:

```python
delta = df["Data prevista para reposição"] - pd.Timestamp(today)
df[Columns.TIME_DELTA] = delta.dt.days.where(delta.notna(), pd.NA)
```

Caso contrário, usa alternativa com `.dt.date`:

```python
delta = df["Data prevista para reposição"].dt.date - today
df[Columns.TIME_DELTA] = pd.NA
valid_mask = delta.notna()
df.loc[valid_mask, Columns.TIME_DELTA] = delta[valid_mask].apply(lambda x: getattr(x, 'days', pd.NA))
```

Critérios de aceitação a verificar no final:
- `grep "\.apply.*lambda" orders_master/integrations/shortages.py` devolve zero
- `pytest tests/unit/test_shortages_integration.py -v` passa
- Resultado numérico idêntico ao comportamento anterior
```

---

### T2-08 — Vectorizar .apply(lambda) em donotbuy.py (ADR-011)

**Prompt:**

```
Lê os ficheiros `prd.md` e `TarefasV2.md` na raiz do projecto para obter todo o contexto arquitectural e de negócio.

Executa a tarefa T2-08 do `TarefasV2.md`: Vectorizar .apply(lambda) em donotbuy.py (ADR-011).

Contexto: O ADR-011 (PRD §3.3 P10) proíbe `.apply` com lambdas Python. A linha `donotbuy.py:49-51` usa `.apply(lambda)` para mapear localizações via `map_location()`. Lê `orders_master/integrations/donotbuy.py`, `orders_master/config/locations_loader.py` e `orders_master/constants.py` para entender o função `map_location`.

Acções a executar:
Usa Opção A — Pre-computar mapeamento e usar `.map()` (mais eficiente, evita chamadas repetidas para o mesmo input):

```python
unique_farmacias = df["FARMACIA"].dropna().unique()
mapping_dict = {name: map_location(str(name), aliases) for name in unique_farmacias}
df["FARMACIA"] = df["FARMACIA"].map(mapping_dict).fillna("")
```

Critérios de aceitação a verificar no final:
- `grep "\.apply.*lambda" orders_master/integrations/donotbuy.py` devolve zero
- `pytest tests/unit/test_donotbuy_integration.py -v` passa
- Resultado idêntico ao comportamento anterior
```

---

### T2-09 — Implementar lazy merge (codigos_visible) no session_service

**Prompt:**

```
Lê os ficheiros `prd.md` e `TarefasV2.md` na raiz do projecto para obter todo o contexto arquitectural e de negócio.

Executa a tarefa T2-09 do `TarefasV2.md`: Implementar lazy merge (codigos_visible) no session_service.

Contexto: O PRD §8.10 especifica lazy merge — o chamador passa `codigos_visible` para `fetch_shortages_db()` para filtrar a sheet antes do merge, reduzindo o volume de dados. A função já suporta o parâmetro mas não é utilizada. Lê `orders_master/app_services/session_service.py` e `orders_master/integrations/shortages.py` para confirmar.

Acções a executar:
Em `session_service.py`, na chamada a `fetch_shortages_db`, adiciona:

```python
codigos_visible = set(df_full[Columns.CODIGO].unique()) if not df_full.empty else None
df_shortages = fetch_shortages_db(url_shortages, codigos_visible=codigos_visible)
```

Nota: certifica-te de que `Columns.CODIGO` está importado de `orders_master.constants`.

Critérios de aceitação a verificar no final:
- Quando o filtro de códigos contém 10 códigos, a sheet de shortages é filtrada antes do merge
- Os resultados são idênticos ao comportamento anterior (sem lazy filter)
- `pytest tests/unit/test_shortages_integration.py tests/unit/test_session_service.py -v` passa
```

---

### T2-10 — Corrigir formato da data no banner BD Rupturas

**Prompt:**

```
Lê os ficheiros `prd.md` e `TarefasV2.md` na raiz do projecto para obter todo o contexto arquitectural e de negócio.

Executa a tarefa T2-10 do `TarefasV2.md`: Corrigir formato da data no banner BD Rupturas.

Contexto: O PRD §6.2.3 exige que a data da consulta da BD Rupturas seja formatada `YYYY-MM-DD`. O código actual usa `str()` que pode produzir `"2026-04-15 00:00:00"`. Lê `orders_master/app_services/session_service.py` (linha ~81) para confirmar.

Acções a executar:
Substitui:
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

Critérios de aceitação a verificar no final:
- `shortages_data_consulta` está sempre no formato `YYYY-MM-DD` ou `None`
- `pytest tests/unit/test_session_service.py -v` passa
```

---

### T2-11 — Preencher .env.example com template

**Prompt:**

```
Lê os ficheiros `prd.md` e `TarefasV2.md` na raiz do projecto para obter todo o contexto arquitectural e de negócio.

Executa a tarefa T2-11 do `TarefasV2.md`: Preencher .env.example com template.

Contexto: O `.env.example` está vazio (0 bytes). Deve conter as variáveis de ambiente necessárias para as integrações com Google Sheets. O PRD §8.14 especifica que as variáveis são usadas como fallback quando `st.secrets` não está disponível. Nota: esta tarefa é dependente de T2-01 (que também mexe no `.env.example`). Se T2-01 já foi executada, verifica se o `.env.example` já está preenchido; caso contrário, preenche-o.

Acções a executar:
Preenche `.env.example` com:
```
# Variáveis de ambiente para Orders Master Infoprex
# Copiar para .env e preencher com URLs reais

# Google Sheet - BD Esgotados (Infarmed)
SHORTAGES_URL=

# Google Sheet - Produtos Não Comprar
DONOTBUY_URL=
```

Critérios de aceitação a verificar no final:
- O ficheiro contém todas as variáveis necessárias (SHORTAGES_URL, DONOTBUY_URL)
- Comentários explicativos estão presentes
```

---

### T2-12 — Alinhar estrutura do secrets.toml com PRD

**Prompt:**

```
Lê os ficheiros `prd.md` e `TarefasV2.md` na raiz do projecto para obter todo o contexto arquitectural e de negócio.

Executa a tarefa T2-12 do `TarefasV2.md`: Alinhar estrutura do secrets.toml com PRD.

Contexto: O PRD §8.14 e §6.3.4 usam `st.secrets["google_sheets"]["shortages_url"]` (secção aninhada), mas o código usa `st.secrets.get("SHORTAGES_URL")` (top-level plano). O `secrets_loader.py` existe mas não é utilizado pelo pipeline principal. Esta tarefa é dependente de T2-01 (secrets.gitignore) e T2-02 (remover streamlit do domínio). Lê `orders_master/secrets_loader.py`, `orders_master/app_services/session_service.py`, `prd.md` (§8.14, §6.3.4), e o `.streamlit/secrets.toml.example` (criado em T2-01).

Acções a executar:
1. Reestrutura `secrets.toml.example` (já criado em T2-01) para usar secção `[google_sheets]`:
   ```toml
   [google_sheets]
   shortages_url = "https://docs.google.com/..."
   donotbuy_url  = "https://docs.google.com/..."
   ```

2. Move `secrets_loader.py` de `orders_master/secrets_loader.py` para `orders_master/config/secrets_loader.py`.

3. Actualiza `secrets_loader.py` para suportar navegação por `key_path` com secções:
   ```python
   def get_secret(key_path: str, env_var: str | None = None) -> str | None:
       # 1. st.secrets com navegação por pontos (ex: "google_sheets.shortages_url")
       # 2. Variável de ambiente (env_var ou derivada de key_path)
       # 3. .env fallback
   ```

4. Actualiza `session_service.py` para usar `get_secret("google_sheets.shortages_url", "SHORTAGES_URL")` em vez de `st.secrets.get("SHORTAGES_URL")`.

5. Actualiza todos os imports que referenciem `orders_master.secrets_loader`.

Critérios de aceitação a verificar no final:
- `secrets_loader.py` é o único ponto de acesso a secrets
- `session_service.py` não importa `streamlit` directamente para secrets
- `grep -r "from orders_master.secrets_loader" orders_master/ ui/` devolve zero (caminho antigo)
- `grep -r "from orders_master.config.secrets_loader" orders_master/ ui/` devolve resultados (novo caminho)
- `pytest tests/unit/test_secrets_loader.py -v` passa
```

---

## FASE 4 — Correcções de Constants e Dataclasses (Prioridade MÉDIA)

### T2-13 — Completar constants.py com campos em falta

**Prompt:**

```
Lê os ficheiros `prd.md` e `TarefasV2.md` na raiz do projecto para obter todo o contexto arquitectural e de negócio.

Executa a tarefa T2-13 do `TarefasV2.md`: Completar constants.py com campos em falta.

Contexto: O PRD §8.2 define constantes que não existem no código ou têm nomes diferentes. Os valores de foreground do `Highlight` estão hardcoded em `rules.py` em vez de referenciados a partir de `constants.py`. Lê `orders_master/constants.py` e `orders_master/formatting/rules.py` para ver o estado actual.

Acções a executar:
1. Adiciona a `Highlight` em `constants.py`:
   ```python
   NAO_COMPRAR_FG = '#000000'
   RUTURA_FG = '#FFFFFF'
   VALIDADE_FG = '#000000'
   ```

2. Adiciona a `Limits` em `constants.py`:
   ```python
   STYLER_MAX_ELEMENTS = 1_000_000
   CODIGO_LOCAL_PREFIX = '1'
   MESES_COUNT = 15
   ```

3. Renomeia `MEDIA_WINDOW_SIZE` para `MEDIA_WINDOW` (alinhar com PRD).

4. Refactor `rules.py` para usar `Highlight.NAO_COMPRAR_FG`, `Highlight.RUTURA_FG`, `Highlight.VALIDADE_FG` em vez de valores hardcoded.

Critérios de aceitação a verificar no final:
- `grep "#000000\|#FFFFFF\|#FF0000" orders_master/formatting/rules.py` devolve apenas referências a constants
- `pytest tests/unit/ -v` passa
```

---

### T2-14 — Adicionar campo preset_pesos ao ScopeContext

**Prompt:**

```
Lê os ficheiros `prd.md` e `TarefasV2.md` na raiz do projecto para obter todo o contexto arquitectural e de negócio.

Executa a tarefa T2-14 do `TarefasV2.md`: Adicionar campo preset_pesos ao ScopeContext.

Contexto: O PRD §8.7 exige que o Scope Summary Bar mostre o preset activo (ex: "Padrão", "Conservador", "Agressivo", "Custom"). O `ScopeContext` no código não tem campo `preset_pesos`. Lê `orders_master/app_services/session_state.py`, `ui/scope_bar.py`, e `orders_master/app_services/recalc_service.py` para entender o fluxo actual.

Acções a executar:
1. Adiciona campo a `ScopeContext`:
   ```python
   preset_pesos: str = ""  # ex: "Padrão", "Conservador", "Agressivo", "Custom"
   ```

2. Actualiza `recalc_service.py` para popular o campo quando o scope_context é actualizado (recebe o nome do preset seleccionado como parâmetro).

3. Actualiza `ui/scope_bar.py` para exibir o preset (por ex: "Preset: Padrão").

Critérios de aceitação a verificar no final:
- O Scope Summary Bar mostra o preset activo
- O campo `preset_pesos` está presente no dataclass `ScopeContext`
- `pytest tests/unit/test_session_state.py tests/unit/test_recalc_service.py -v` passa
```

---

### T2-15 — Adicionar campo anomalias_preco ao FileInventoryEntry

**Prompt:**

```
Lê os ficheiros `prd.md` e `TarefasV2.md` na raiz do projecto para obter todo o contexto arquitectural e de negócio.

Executa a tarefa T2-15 do `TarefasV2.md`: Adicionar campo anomalias_preco ao FileInventoryEntry.

Contexto: O PRD §8.8 exige que o File Inventory mostre a contagem de anomalias de preço por ficheiro. O código compensa concatenando no campo `avisos`, mas deveria ter um campo dedicado. Lê `orders_master/app_services/session_state.py`, `orders_master/app_services/session_service.py`, e `ui/file_inventory.py`.

Acções a executar:
1. Adiciona campo a `FileInventoryEntry`:
   ```python
   anomalias_preco: int = 0
   ```

2. Actualiza `session_service.py` (~linha 140-144) para popular o campo dedicado em vez de concatenar em `avisos`.

3. Actualiza `ui/file_inventory.py` para exibir a contagem de anomalias como coluna separada.

Critérios de aceitação a verificar no final:
- O File Inventory mostra coluna "Anomalias preço" com contagem numérica
- O campo `avisos` deixa de conter informação de anomalias
- `pytest tests/unit/test_session_state.py tests/unit/test_session_service.py -v` passa
```

---

### T2-16 — Alinhar nomes de campos SessionState com PRD

**Prompt:**

```
Lê os ficheiros `prd.md` e `TarefasV2.md` na raiz do projecto para obter todo o contexto arquitectural e de negócio.

Executa a tarefa T2-16 do `TarefasV2.md`: Alinhar nomes de campos SessionState com PRD.

Contexto: O PRD §4.1.8 usa `df_master_products` mas o código usa `master_products`. Esta é uma renomeação transversal com impacto em múltiplos ficheiros. Executa com cuidado: primeiro identifica TODAS as referências, depois substitui uma a uma. Lê `orders_master/app_services/session_state.py`, e depois usa `grep -r "master_products" orders_master/ ui/` para encontrar todas as referências.

Acções a executar:
1. Renomeia `SessionState.master_products` para `SessionState.df_master_products` (alinhar com PRD).

2. Actualiza TODAS as referências a `state.master_products` e `st.session_state["orders_master_state"].master_products` em todo o código (orders_master/ e ui/).

3. Verifica se há referências em testes e actualiza também.

Critérios de aceitação a verificar no final:
- `grep -r "\.master_products" orders_master/ ui/` devolve zero resultados
- Campo `df_master_products` está presente em `SessionState`
- `pytest tests/ -v` passa (todos os testes, não apenas unit)
```

---

## FASE 5 — Limpeza Menor de Código (Prioridade BAIXA)

### T2-17 — Remover PriceAnomalyWarning (código morto)

**Prompt:**

```
Lê os ficheiros `prd.md` e `TarefasV2.md` na raiz do projecto para obter todo o contexto arquitectural e de negócio.

Executa a tarefa T2-17 do `TarefasV2.md`: Remover PriceAnomalyWarning (código morto).

Contexto: `PriceAnomalyWarning(UserWarning)` é definida em `exceptions.py` mas nunca é emitida via `warnings.warn()`. A coluna booleana `price_anomaly` e a regra 5 em `rules.py` tratam da funcionalidade. Lê `orders_master/exceptions.py`, `orders_master/business_logic/price_validation.py`, e faz `grep -r "PriceAnomalyWarning" orders_master/ tests/`.

Acções a executar:
1. Remove `class PriceAnomalyWarning(UserWarning)` de `exceptions.py`.

2. Verifica se algum teste referencia `PriceAnomalyWarning` e actualiza/remova.

3. Verifica se o PRD §5.6.1 tem referência a `PriceAnomalyWarning` como classe emitida — se sim, actualiza para reflectir que a anomalia é marcada apenas via flag booleana.

Critérios de aceitação a verificar no final:
- `grep -r "PriceAnomalyWarning" orders_master/` devolve zero
- `pytest tests/ -v` passa
```

---

### T2-18 — Corrigir encoding_fallback.py (on_bad_lines e errors)

**Prompt:**

```
Lê os ficheiros `prd.md` e `TarefasV2.md` na raiz do projecto para obter todo o contexto arquitectural e de negócio.

Executa a tarefa T2-18 do `TarefasV2.md`: Corrigir encoding_fallback.py (on_bad_lines e errors).

Contexto: O código usa `on_bad_lines="error"` mas o PRD/TASK-09 referem `errors='strict'`. São parâmetros diferentes: `on_bad_lines` controla linhas mal formatadas no CSV; `errors` controla bytes não decodificáveis no encoding. Lê `orders_master/ingestion/encoding_fallback.py` e `prd.md` §5.1.2.

Acções a executar:
1. Adiciona `errors='strict'` ao `pd.read_csv()` para forçar falha se o encoding tiver bytes inválidos (em vez de `except Exception: continue` comer tudo).

2. Muda `on_bad_lines` de `"error"` para `"skip"` — linhas mal formatadas devem ser ignoradas silenciosamente (consistente com `brands_parser.py` que usa `on_bad_lines='skip'`). Isto evita que um ficheiro com uma linha corrompida faça falhar todo o parsing.

3. Actualiza PRD §5.1.2 para documentar ambos os parâmetros.

Critérios de aceitação a verificar no final:
- `encoding_fallback.py` usa `errors='strict'` e `on_bad_lines='skip'`
- Linhas mal formatadas são saltadas
- Bytes inválidos causam `InfoprexEncodingError`
- `pytest tests/unit/test_encoding_fallback.py -v` passa
```

---

### T2-19 — Extrair componentes UI alerts.py e documentation.py de main_area.py

**Prompt:**

```
Lê os ficheiros `prd.md` e `TarefasV2.md` na raiz do projecto para obter todo o contexto arquitectural e de negócio.

Executa a tarefa T2-19 do `TarefasV2.md`: Extrair componentes UI alerts.py e documentation.py de main_area.py.

Contexto: O PRD §3.2 e §3.4 especificam dois módulos UI separados: `ui/alerts.py` com `render_errors_and_warnings()` e `ui/documentation.py` com `render_help_expander()`. A lógica está integrada em `main_area.py`. Lê `ui/main_area.py` para identificar as secções a extrair.

Acções a executar:
1. Cria `ui/alerts.py` com função `render_errors_and_warnings(state: SessionState)` que exibe `st.error()` para cada erro e `st.warning()` para filtros obsoletos.

2. Cria `ui/documentation.py` com função `render_help_expander()` que exibe o expander "ℹ️ Documentação e Workflow".

3. Refactor `main_area.py` para importar e chamar estas funções em vez de ter lógica inline.

Critérios de aceitação a verificar no final:
- Ambos os ficheiros (`ui/alerts.py` e `ui/documentation.py`) existem
- `main_area.py` reduz linhas
- Funcionalidade não muda (tabela, avisos, expander continuam visíveis)
- `pytest tests/ -v` passa
```

---

## FASE 6 — Actualizações de Documentação do PRD (Prioridade BAIXA)

### T2-20 — Actualizar PRD §3.2: "4 regras" → "5 regras"

**Prompt:**

```
Lê os ficheiros `prd.md` e `TarefasV2.md` na raiz do projecto para obter todo o contexto arquitectural e de negócio.

Executa a tarefa T2-20 do `TarefasV2.md`: Actualizar PRD §3.2 — "4 regras" → "5 regras".

Contexto: O PRD §3.2 diz "4 regras visuais" mas o §6.1.6 lista 5 regras e o código define 5 (incluindo preço anómalo). Lê `prd.md` §3.2 (tabela de `formatting/rules.py`) e `orders_master/formatting/rules.py`.

Acções a executar:
Actualiza §3.2 tabela de `formatting/rules.py` de:
> Encapsula as **4 regras visuais** (grupo, não comprar, rutura, validade).

Para:
> Encapsula as **5 regras visuais** (grupo, não comprar, rutura, validade, preço anómalo).

Critérios de aceitação a verificar no final:
- Pesquisa por "4 regras" no PRD devolve zero resultados
- A tabela de `rules.py` em §3.2 menciona "5 regras visuais"
```

---

### T2-21 — Adicionar DetailedRowSchema à lista de §3.2

**Prompt:**

```
Lê os ficheiros `prd.md` e `TarefasV2.md` na raiz do projecto para obter todo o contexto arquitectural e de negócio.

Executa a tarefa T2-21 do `TarefasV2.md`: Adicionar DetailedRowSchema à lista de §3.2.

Contexto: O PRD §3.2 lista 5 schemas mas omite `DetailedRowSchema`, que existe no código (`schemas.py:70-88`) e é descrito em §4.1.3. Lê `prd.md` §3.2 e `orders_master/schemas.py`.

Acções a executar:
Actualiza §3.2 tabela de schemas de:
> `orders_master/schemas.py` | Domínio — Contratos | Define os schemas tipados (pydantic): `InfoprexRowSchema`, `AggregatedRowSchema`, `ShortageRowSchema`, `DoNotBuyRowSchema`, `BrandRowSchema`.

Para:
> `orders_master/schemas.py` | Domínio — Contratos | Define os schemas tipados (pydantic): `InfoprexRowSchema`, `AggregatedRowSchema`, `DetailedRowSchema`, `ShortageRowSchema`, `DoNotBuyRowSchema`, `BrandRowSchema`.

Critérios de aceitação a verificar no final:
- `DetailedRowSchema` aparece na lista de §3.2
```

---

### T2-22 — Adicionar ficheiros em falta à estrutura §3.4

**Prompt:**

```
Lê os ficheiros `prd.md` e `TarefasV2.md` na raiz do projecto para obter todo o contexto arquitectural e de negócio.

Executa a tarefa T2-22 do `TarefasV2.md`: Adicionar ficheiros em falta à estrutura §3.4.

Contexto: Os seguintes ficheiros existem no código mas não estão na árvore de directorias do PRD §3.4: `orders_master/config/validate.py`, `orders_master/config/presets_loader.py`, e `orders_master/secrets_loader.py` (deve ser movido para `orders_master/config/` na T2-12). Lê `prd.md` §3.4 e verifica os ficheiros existentes em `orders_master/config/`.

Acções a executar:
Adiciona à árvore de §3.4:
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

Nota: Se T2-12 já foi executada, `secrets_loader.py` já estará em `config/` — nesse caso, remove a entrada `└── secrets_loader.py` da raiz e garante que apenas a entrada `config/secrets_loader.py` existe.

Critérios de aceitação a verificar no final:
- Todos os ficheiros de código existentes estão listados na árvore §3.4
- `orders_master/config/validate.py`, `orders_master/config/presets_loader.py`, e `orders_master/config/secrets_loader.py` aparecem na árvore
```

---

### T2-23 — Documentar init defensivo de colunas de integração

**Prompt:**

```
Lê os ficheiros `prd.md` e `TarefasV2.md` na raiz do projecto para obter todo o contexto arquitectural e de negócio.

Executa a tarefa T2-23 do `TarefasV2.md`: Documentar init defensivo de colunas de integração.

Contexto: O código inicializa colunas de integração (`DIR`, `DPR`, `DATA_OBS`, `TimeDelta`) com `pd.NA` no DataFrame bruto, mesmo quando as integrações falharam. Esta prática defensiva garante que a formatação nunca quebra por KeyError. O PRD não documenta este comportamento. Lê `prd.md` §4.1.7 e §5.6.2, e `orders_master/app_services/session_service.py` para confirmar.

Acções a executar:
Adiciona nota ao PRD §4.1.7 (entidade FinalProposalRow) ou §5.6.2:

> **Nota defensiva:** O pipeline inicializa as colunas de integração (`DIR`, `DPR`, `DATA_OBS`, `TimeDelta`) com `pd.NA` no DataFrame bruto, independentemente de as integrações terem sucesso. Isto garante que as regras de formatação (§6.1.6) nunca falham por KeyError, utilizando `pd.notna()` nos predicates.

Critérios de aceitação a verificar no final:
- A prática defensiva está documentada no PRD
```

---

### T2-24 — Documentar merge donotbuy sempre detailed=True

**Prompt:**

```
Lê os ficheiros `prd.md` e `TarefasV2.md` na raiz do projecto para obter todo o contexto arquitectural e de negócio.

Executa a tarefa T2-24 do `TarefasV2.md`: Documentar merge donotbuy sempre detailed=True.

Contexto: O código faz `merge_donotbuy(df_full, df_dnb, detailed=True)` no DataFrame raw (pré-agregação), que é semanticamente correcto porque o raw tem `LOCALIZACAO` por loja. O PRD §6.2.2 especifica duas modalidades, mas na prática só a detalhada é usada no pipeline pesado. Lê `prd.md` §6.2.2 e `orders_master/app_services/session_service.py`.

Acções a executar:
Actualiza PRD §6.2.2 para clarificar:

> No pipeline pesado (`process_orders_session`), o merge com "Não Comprar" é sempre executado com `detailed=True` no DataFrame raw (pré-agregação), que contém `LOCALIZACAO` por loja. A coluna `DATA_OBS` resultante é preservada durante a agregação, estando disponível tanto na vista agrupada (após dedup por CNP) como na detalhada.

Critérios de aceitação a verificar no final:
- PRD documenta correctamente como o merge donotbuy é executado na prática
```

---

### T2-25 — Documentar campos extra do SessionState

**Prompt:**

```
Lê os ficheiros `prd.md` e `TarefasV2.md` na raiz do projecto para obter todo o contexto arquitectural e de negócio.

Executa a tarefa T2-25 do `TarefasV2.md`: Documentar campos extra do SessionState.

Contexto: O código tem 3 campos em `SessionState` não documentados no PRD §4.1.8: `df_raw`, `last_brands_selection`, `shortages_data_consulta`. Lê `prd.md` §4.1.8 e `orders_master/app_services/session_state.py` para confirmar.

Acções a executar:
Adiciona ao PRD §4.1.8 tabela:

| Campo | Tipo | Descrição |
|---|---|---|
| `df_raw` | `pd.DataFrame` | DataFrame bruto pós-ingestão com integrações merged. Usado como input pelo recalc_service. |
| `last_brands_selection` | `list[str]` | Última selecção de marcas. Usado para detectar filtros obsoletos. |
| `shortages_data_consulta` | `str \| None` | Data da consulta da BD de Rupturas para exibição no banner. |

Critérios de aceitação a verificar no final:
- Todos os campos do SessionState implementado estão documentados no PRD §4.1.8
- Os 3 campos extra estão presentes na tabela
```

---

## Ordem de Execução e Dependências

| Ordem | Tarefa | Prioridade | Veredicto | Depende de |
|---|---|---|---|---|
| 1 | T2-01 | ALTA | PC | — |
| 2 | T2-02 | ALTA | PC | — |
| 3 | T2-03 | ALTA | PC | — |
| 4 | T2-07 | MÉDIA | PC | — |
| 5 | T2-08 | MÉDIA | PC | — |
| 6 | T2-09 | MÉDIA | PC | T2-02 (opcional) |
| 7 | T2-10 | MÉDIA | PC | — |
| 8 | T2-11 | MÉDIA | PC | T2-01 |
| 9 | T2-12 | MÉDIA | AM | T2-01, T2-02 |
| 10 | T2-13 | MÉDIA | PC | — |
| 11 | T2-14 | MÉDIA | PC | — |
| 12 | T2-15 | MÉDIA | PC | — |
| 13 | T2-16 | MÉDIA | PC | — |
| 14 | T2-17 | BAIXA | PC | — |
| 15 | T2-18 | BAIXA | AM | — |
| 16 | T2-19 | BAIXA | PC | — |
| 17 | T2-04 | ALTA | CC | — |
| 18 | T2-05 | ALTA | CC | — |
| 19 | T2-06 | ALTA | CC | — |
| 20 | T2-20 | BAIXA | CC | — |
| 21 | T2-21 | BAIXA | CC | — |
| 22 | T2-22 | BAIXA | CC | T2-12 (para saber se secrets_loader moveu) |
| 23 | T2-23 | BAIXA | CC | — |
| 24 | T2-24 | BAIXA | CC | — |
| 25 | T2-25 | BAIXA | CC | — |