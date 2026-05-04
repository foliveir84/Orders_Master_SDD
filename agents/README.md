# Agentes de IA — Orders Master Infoprex

Equipa de agentes especializados para o desenvolvimento do projecto Orders Master Infoprex. Cada agente tem um dominio de responsabilidade claro, alinhado com a arquitectura em camadas do projecto e com o conhecimento especifico necessario.

Todos os agentes de implementacao tecnica utilizam o **MCP server context7** para consultar documentacao actualizada das tecnologias da stack antes de escrever codigo.

---

## Indice de Agentes

| Agente | Ficheiro | Dominio | Camada |
|---|---|---|---|
| Backend Streamlit Engineer | [`backend-streamlit.md`](backend-streamlit.md) | Logica de dominio, servicos de aplicacao, integracoes | Domain + Application |
| Frontend Streamlit Engineer | [`frontend-streamlit.md`](frontend-streamlit.md) | Interface de utilizador, componentes visuais | Presentation |
| Data Analyst & Pandas Specialist | [`data-analyst.md`](data-analyst.md) | Pipeline de dados, performance, operacoes vectorizadas | Domain (dados) |
| Especialista de Dominio Farmaceutico | [`pharmacy-domain-expert.md`](pharmacy-domain-expert.md) | Regras de negocio, Infarmed, Sifarma, farmacias PT | Negocio |
| Testing & QA Engineer | [`testing-qa.md`](testing-qa.md) | Testes unitarios, integracao, cobertura, CI | Qualidade |

---

## Quando Usar Cada Agente

### Backend Streamlit Engineer
**Usar quando:**
- Implementar modulos da pasta `orders_master/` (ingestao, agregacao, logica de negocio, integracoes, formatacao, configuracao)
- Criar ou alterar `app_services/` (session_service, recalc_service, session_state)
- Implementar `constants.py`, `schemas.py`, `exceptions.py`, `logger.py`
- Trabalhar com integracoes externas (Google Sheets BD Esgotados, Lista Nao Comprar)
- Implementar cache com invalidacao por `mtime`
- Exportacao Excel com formatacao condicional

**Nao usar quando:** a tarefa envolve componentes de UI Streamlit, ou e puramente sobre performance de DataFrames.

---

### Frontend Streamlit Engineer
**Usar quando:**
- Criar ou alterar `app.py` ou qualquer ficheiro em `ui/`
- Implementar a sidebar (4 blocos: labs, codigos, infoprex, marcas)
- Implementar a area principal (tabela, toggles, sliders, download button)
- Criar componentes visuais (Scope Summary Bar, File Inventory, banners)
- Implementar barra de progresso na ingestao
- Trabalhar com `st.session_state`, widgets, e layouts Streamlit

**Nao usar quando:** a tarefa envolve logica de negocio, calculos sobre DataFrames, ou integracoes externas.

---

### Data Analyst & Pandas Specialist
**Usar quando:**
- Optimizar operacoes de I/O (`pd.read_csv` com `usecols`, encoding, dtypes)
- Converter `.apply(lambda ...)` para operacoes vectorizadas
- Implementar ou rever a funcao `aggregate()` (groupby, merge, pivot)
- Implementar calculo de media ponderada vectorizado (`.dot()`)
- Optimizar uso de memoria (dtypes, reduzir footprint)
- Resolver problemas de performance em pipelines de dados
- Implementar limpeza vectorizada de designacoes
- Rever merges multi-chave (BD Esgotados, Nao Comprar)

**Nao usar quando:** a tarefa e sobre UI, ou requer validacao de regras de negocio farmaceuticas.

---

### Especialista de Dominio Farmaceutico
**Usar quando:**
- Validar se a formula de proposta esta correcta para o contexto farmaceutico
- Rever regras de negocio (zombies, codigos locais, prioridade TXT vs labs)
- Esclarecer duvidas sobre o ecossistema farmaceutico portugues (Infarmed, Sifarma, CNP, CLA)
- Definir edge cases de negocio (ruptura com TimeDelta negativo, produto sem vendas com stock)
- Validar modelo de dados contra a realidade do Infoprex
- Rever designacoes de produtos farmaceuticos (Title Case, acentos, asteriscos)
- Confirmar semantica da lista "Nao Comprar" e da BD Esgotados
- Rever presets de pesos da media ponderada

**Nao usar quando:** a tarefa e puramente tecnica (performance, arquitectura, UI).

---

### Testing & QA Engineer
**Usar quando:**
- Escrever testes unitarios para modulos de dominio
- Escrever testes de integracao (pipeline completo)
- Criar fixtures de teste (DataFrames minimos, ficheiros de amostra)
- Configurar CI pipeline (GitHub Actions com ruff, mypy, pytest)
- Medir e melhorar cobertura de testes (target >= 80%)
- Escrever benchmarks de performance (vectorizado vs apply)
- Validar invariantes arquitecturais (ancoragem T Uni, paridade Web-Excel, sort-key)

**Nao usar quando:** a tarefa e sobre implementacao de features (so testes de features).

---

## Fluxo de Trabalho Recomendado

Para implementar uma nova feature ou corrigir um bug, recomenda-se a seguinte ordem:

```
1. Especialista Farmaceutico  →  Validar regras de negocio e edge cases
        |
        v
2. Data Analyst              →  Definir o pipeline de dados e operacoes
        |
        v
3. Backend Engineer          →  Implementar logica de dominio e servicos
        |
        v
4. Frontend Engineer         →  Implementar interface de utilizador
        |
        v
5. Testing & QA              →  Escrever testes e validar cobertura
```

Para tarefas que tocam apenas uma camada, usa o agente correspondente directamente.

---

## Stack do Projecto (Referencia Rapida)

| Tecnologia | Versao | Uso |
|---|---|---|
| Python | 3.11+ | Linguagem principal |
| Streamlit | >= 1.30 | Framework UI web |
| Pandas | 2.x | Manipulacao de dados |
| Pydantic | v2 | Schema validation |
| openpyxl | - | Exportacao Excel |
| pytest | - | Testes |
| pytest-cov | - | Cobertura |
| ruff | - | Linting |
| mypy | - | Type checking |
| black | - | Formatting |
| python-dateutil | - | Datas (relativedelta) |
| concurrent.futures | stdlib | Parsing paralelo |

---

## Arquitectura (Visao Geral)

```
Presentation (app.py + ui/)     →  Frontend Streamlit Engineer
        |
        v
Application (app_services/)     →  Backend Streamlit Engineer
        |
        v
Domain (orders_master/)         →  Backend Engineer + Data Analyst
        |
        v
External (Google Sheets, JSON)  →  Backend Engineer
```

Todas as dependencias apontam para dentro: `UI -> app_services -> domain`. Nunca ao contrario. O dominio **nunca** importa `streamlit`.
