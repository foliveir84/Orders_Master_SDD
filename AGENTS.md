# AGENTS.md

## What This Project Is

Orders Master Infoprex — a Streamlit app that consolidates pharmacy sales data (Infoprex files) into multi-store order proposals. Currently migrating to Django SaaS (see `docs/superpowers/specs/2026-05-15-django-saas-migration-design.md`).

## Commands

```bash
# Run the app
streamlit run app.py

# Run all tests
pytest

# Run tests with coverage (CI requires >= 80% on orders_master/)
pytest --cov=orders_master --cov-fail-under=80 -m "not slow"

# Run a single test file
pytest tests/unit/test_aggregator.py -v

# Lint + format + typecheck (run in this order)
ruff check .
black .
mypy --strict orders_master/

# Run all pre-commit hooks
pre-commit run --all-files
```

## Architecture 

**Strict layered  architecture — dependency arrows point inward only:**

```
app.py + ui/  →  app_services/  →  domain (orders_master/*)
(Presentation)    (Application)      (Business Logic)
```

- `orders_master/` is the domain layer. **No `import streamlit` allowed** (guarded imports for caching are the sole exception).
- `ui/` and `app.py` are the only Streamlit-touching modules.
- `orders_master/app_services/` orchestrates domain calls; it uses `st.session_state` (guarded) and `st.progress` via callbacks.

**Streamlit leaks in domain code** (must be removed in Django migration):
- `orders_master/config/labs_loader.py` — `@st.cache_data`
- `orders_master/config/locations_loader.py` — `import streamlit`
- `orders_master/config/presets_loader.py` — `@st.cache_data`
- `orders_master/integrations/shortages.py` — `@st.cache_data`
- `orders_master/integrations/donotbuy.py` — `@st.cache_data`
- `orders_master/business_logic/averages.py` — `@st.cache_data` on `load_presets()`
- `orders_master/app_services/session_state.py` — `st.session_state` facade
- `orders_master/app_services/session_service.py` — `st.progress` via callback

## Conventions

- **Vectorized operations only** — `.apply(lambda...)` is forbidden in `orders_master/`. Use `.str` methods, `np.where`, etc.
- **Positional month addressing** — month columns have dynamic names (JAN, FEV, etc.). Always use `index_of('T Uni') - N`. Never hardcode month names.
- **Formatting SSOT** — all conditional visual rules (Grupo black, Nao Comprar purple, Rutura red, Validade orange, Preco Anomalo) are defined once in `orders_master/formatting/rules.py` as `HighlightRule` dataclasses. Both `web_styler.py` and `excel_formatter.py` consume the same `RULES` list.
- **No `print()`** in production — pre-commit hook blocks it in `orders_master/`. Use `logger = logging.getLogger(__name__)`.
- **No bare `except:`** — always use explicit exception types.
- **Config files** are in `config/` (project root, not inside `orders_master/`) so non-technical users can edit them without navigating Python packages.

## Key Domain Entry Points

- `parse_infoprex_file()` in `orders_master/ingestion/infoprex_parser.py` — main file parser
- `aggregate()` in `orders_master/aggregation/aggregator.py` — unified aggregation (grouped + detailed)
- `recalculate_proposal()` in `orders_master/app_services/recalc_service.py` — lightweight recalc on toggle/slider changes
- `process_orders_session()` in `orders_master/app_services/session_service.py` — heavy pipeline orchestration
- `build_styler()` + `build_excel()` in `orders_master/formatting/` — web and Excel rendering from shared rules

## Config Files

- `config/laboratorios.json` — Lab name → CLA codes mapping. Mtime-based cache invalidation.
- `config/localizacoes.json` — Substring search term → display alias. Min 3 chars per search_term (ADR-012).
- `config/presets.yaml` — Weight presets (Conservador/Padrao/Agressivo).
- `.streamlit/secrets.toml` — Google Sheets URLs for BD Rupturas and Nao Comprar. **Never committed** (pre-commit hook blocks it).

## Django Migration Status

The project is being migrated from Streamlit to Django SaaS. See:
- **Spec:** `docs/superpowers/specs/2026-05-15-django-saas-migration-design.md`
- **Plan:** `docs/superpowers/plans/2026-05-15-django-saas-migration.md`

The domain package (`orders_master/`) will be copied intact to the new Django project, with only Streamlit-specific code adapted (caching → Django cache, `st.session_state` → Redis, `st.progress` → callbacks).

## CI

GitHub Actions (`.github/workflows/ci.yml`):
1. Lint: `ruff check .`
2. Format: `black --check .`
3. Typecheck: `mypy --strict orders_master/`
4. Tests: `pytest --cov=orders_master --cov-fail-under=80 -m "not slow"`