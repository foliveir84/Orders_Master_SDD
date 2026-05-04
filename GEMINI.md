# Project Overview
**Orders Master Infoprex** is an internal web application designed for community pharmacies. It consolidates sales export files from the Sifarma/Infoprex module to generate multi-store order proposals. It applies deterministic aggregation rules, weighted averages on sales history, and adjusts for out-of-stock products (via the official Infarmed database) and collaborative "Do Not Buy" lists. 

## Main Technologies
- **Language:** Python 3.11+
- **Frontend Framework:** Streamlit (≥ 1.30)
- **Data Processing:** Pandas
- **Data Validation:** Pydantic
- **Export:** Openpyxl (Excel)
- **Testing & Quality:** Pytest, Ruff, Black, Mypy, Pre-commit

## Architecture
The project strictly follows a layered architecture to ensure domain logic remains isolated and highly testable:
- **Presentation Layer:** `app.py` (entry-point) and `ui/` directory. Contains all Streamlit-specific code.
- **Application Layer:** `orders_master/app_services/`. Orchestrates data ingestion, aggregation, and state management.
- **Domain Layer:** `orders_master/` directory (excluding `app_services/`). Contains pure business logic, parsing (`ingestion/`), calculation (`business_logic/`, `aggregation/`), configuration loading, formatting rules, schemas, and constants. This layer **must not** contain any `import streamlit` statements.
- **Configuration:** External configurations (e.g., laboratories, locations, presets) are stored in the `config/` directory as JSON and YAML files.

# Building and Running

## Setup
1. Create and activate a virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt -r requirements-dev.txt
   ```
3. Set up pre-commit hooks:
   ```bash
   pre-commit install
   ```

## Execution
Run the Streamlit application:
```bash
streamlit run app.py
```

## Testing and Linting
- **Tests:** Run the test suite using pytest.
  ```bash
  pytest
  ```
- **Linting & Formatting:** Ensure code quality using ruff and black.
  ```bash
  ruff check .
  black .
  ```
- **Type Checking:** Verify types using mypy.
  ```bash
  mypy --strict orders_master/
  ```

# Development Conventions

1. **Vectorized Operations (Performance):** Strictly use Pandas vectorized operations (e.g., `.str.replace`, `np.where`, `pd.cut`). The use of `.apply(lambda...)` is explicitly forbidden in domain functions due to severe performance degradation.
2. **Typed Boundaries & Schemas:** Data schemas (defined in `orders_master/schemas.py` via Pydantic) are used to validate DataFrames exclusively at the system's boundaries (e.g., parsing, inputs from UI). Hot loops rely on the established contract to avoid runtime validation overhead.
3. **Exception Handling:** Bare `except:` clauses are prohibited. All captured exceptions must be explicitly typed and logged. The system employs "Defensive Parsing"—if one file fails during ingestion, the error is logged and collected (`file_errors`), and processing continues for the remaining files.
4. **Positional Addressing:** Month columns in the Infoprex data have dynamic names. All calculations involving months must use an offset relative to the static `T Uni` column anchor (e.g., `index_of('T Uni') - N`).
5. **Single Source of Truth (SSOT) for Formatting:** Visual highlighting rules (e.g., Out of stock, Do Not Buy) are defined once as dataclasses in `orders_master/formatting/rules.py` and are consumed by both the web renderer (`web_styler.py`) and the Excel exporter (`excel_formatter.py`).
6. **Logging:** Use the centralized logger defined in `orders_master/logger.py`. Do not use `print()` in production code. Use appropriate semantic log levels (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`).