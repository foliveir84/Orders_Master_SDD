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