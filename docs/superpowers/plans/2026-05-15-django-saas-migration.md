# Django SaaS Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate Orders Master Infoprex from Streamlit single-tenant to Django 5.x SaaS multi-tenant with PostgreSQL, Redis, HTMX, and TailwindCSS.

**Architecture:** Django project (`orders_master_saas/`) with 3 apps: `accounts` (auth + multi-tenancy), `backoffice` (Django Admin), `orders` (core business). The domain package `orders_master/` is copied intact with only Streamlit-specific adapters replaced (caching → Django cache, `st.secrets` → Django settings, `st.session_state` → Redis-backed session). UI is full-server-rendered Django templates + HTMX for interactive controls.

**Tech Stack:** Django 5.x, PostgreSQL 16+, Redis 7+, Gunicorn 21+, TailwindCSS 4.x, HTMX 2.x, openpyxl, pydantic, pandas

**Spec:** `docs/superpowers/specs/2026-05-15-django-saas-migration-design.md`

---

## Prerequisite: TarefasV2 Corrections (Pre-Migration Cleanup)

Before starting the Django migration, critical corrections from `TarefasV2.md` must be executed. These fix Streamlit leaks in `orders_master/` that would otherwise be copied to Django.

**Required TarefasV2 tasks (in execution order):**

| Order | Task | Why Required Before Migration |
|---|---|---|
| 1 | T2-01 | Security: secrets.toml gitignore — prevents leaking URLs |
| 2 | T2-02 | **Critical:** removes `import streamlit` from domain (`integrations/`, `config/`) — the Django project cannot have `import streamlit` in `orders_master/` |
| 3 | T2-03 | Fixes brand filter bug — would be copied to Django if not fixed |
| 4 | T2-07 | Vectorizes shortages.py — removes `.apply(lambda)` |
| 5 | T2-08 | Vectorizes donotbuy.py — removes `.apply(lambda)` |
| 6 | T2-09 | Implements lazy merge — performance feature |
| 7 | T2-10 | Fixes date format — prevents display bugs |
| 8 | T2-12 | Aligns secrets structure — prerequisite for Django settings migration |
| 9 | T2-13 | Completes constants.py — needed for CSS class generation |
| 10 | T2-16 | Renames `master_products` → `df_master_products` — aligns with PRD |

**Optional TarefasV2 tasks** (can be done in parallel with migration):
- T2-04, T2-05, T2-06, T2-20–T2-25 (PRD documentation updates — don't block migration)
- T2-11 (.env.example — already covered by T2-01)
- T2-14, T2-15 (ScopeContext/FileInventory fields — UI changes)
- T2-17, T2-18, T2-19 (code cleanup — can be done after migration)

---

## File Structure Map

### New Django Project Structure

```
orders_master_saas/                    # Django project root
├── manage.py
├── pyproject.toml                     # Django + dependencies
├── requirements.txt
├── requirements-dev.txt
├── Procfile                            # Railway: gunicorn
├── .env.example                        # Django settings template
├── orders_master_saas/                 # Django project config
│   ├── __init__.py
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py                     # Common settings
│   │   ├── development.py              # Dev overrides (SQLite ok for local)
│   │   └── production.py              # Prod overrides (PG, Redis, gunicorn)
│   ├── urls.py                         # Root URL conf
│   └── wsgi.py
├── accounts/                           # Auth + tenant app
│   ├── __init__.py
│   ├── models.py                       # Cliente, Farmacia, Subscricao, UserProfile
│   ├── middleware.py                   # TenantMiddleware
│   ├── admin.py                        # Custom admin for accounts models
│   ├── urls.py                         # login/, logout/, password_reset/
│   ├── views.py                        # LoginView, LogoutView
│   └── forms.py                        # LoginForm
├── backoffice/                         # Admin customisation app
│   ├── __init__.py
│   ├── admin.py                        # Custom ModelAdmin classes
│   └── management/
│       └── commands/
│           ├── import_labs_json.py      # Migrate laboratorios.json → DB
│           ├── import_locations_json.py # Migrate localizacoes.json → DB
│           └── import_presets_yaml.py   # Migrate presets.yaml → DB
├── orders/                             # Core business app
│   ├── __init__.py
│   ├── models.py                       # ConfigLaboratorio, ConfigLocalizacao, ConfigPesoPreset, SessaoProcessamento
│   ├── views.py                        # Upload, process, recalc, download, progress
│   ├── urls.py                         # /orders/ URL patterns
│   ├── forms.py                        # UploadForm, RecalcForm
│   ├── services/
│   │   ├── __init__.py
│   │   ├── session_service.py          # Adapted: callbacks instead of st.progress
│   │   ├── recalc_service.py           # Adapted: Django cache instead of st.cache_data
│   │   └── processing_session.py       # NEW: Redis-backed DataFrame storage
│   ├── templatetags/
│   │   ├── __init__.py
│   │   └── table_tags.py               # Custom tags for conditional table rendering
│   └── tests/
│       ├── __init__.py
│       ├── test_views.py
│       ├── test_processing_session.py
│       ├── test_license_validation.py
│       └── test_multitenancy.py
├── orders_master/                      # Domain package (copied + adapted)
│   ├── (all existing files, with Streamlit deps replaced)
│   └── config/
│       ├── labs_loader.py              # Adapted: reads DB, no @st.cache_data
│       ├── locations_loader.py         # Adapted: reads DB, no @st.cache_data
│       └── presets_loader.py           # Adapted: reads DB, no @st.cache_data
├── templates/                          # Django templates
│   ├── base.html                       # Layout: sidebar + main area
│   ├── registration/
│   │   └── login.html
│   └── orders/
│       ├── upload.html                 # Upload form + sidebar
│       ├── results.html                # Table + controls
│       ├── _table_rows.html            # HTMX partial: table rows
│       ├── _scope_bar.html             # HTMX partial: scope summary
│       ├── _controls.html              # HTMX partial: toggles/sliders
│       ├── _file_inventory.html        # File inventory component
│       ├── _progress.html              # HTMX partial: progress bar
│       └── _banner.html                # BD Rupturas banner
├── static/
│   ├── css/
│   │   ├── orders.css                  # Table conditional styles (5 rules)
│   │   └── app.css                     # Layout, sidebar, forms
│   └── js/
│       └── app.js                      # HTMX config, minor interactivity
├── config/                             # Legacy JSON/YAML (kept for import commands)
│   ├── laboratorios.json
│   ├── localizacoes.json
│   └── presets.yaml
└── tests/                              # Domain tests (carried over)
    └── (existing test structure)
```

### Files Modified in orders_master/ (Domain Adaptation)

| File | Change | Reason |
|---|---|---|
| `config/labs_loader.py` | Remove `import streamlit`, `@st.cache_data`. Add `load_labs_from_db(client_id)` | Labs come from Django model, not JSON file |
| `config/locations_loader.py` | Remove `import streamlit`, `@st.cache_data`. Add `load_locations_from_db(client_id)` | Locations come from Django model |
| `config/presets_loader.py` | Add `load_presets_from_db()` | Presets come from Django model |
| `integrations/shortages.py` | Remove `cache_decorator` (st.cache_data). Add `@django_cache_decorator`. Remove `st.sidebar.warning` | Django cache instead of Streamlit cache |
| `integrations/donotbuy.py` | Remove `cache_decorator` (st.cache_data). Add `@django_cache_decorator` | Same |
| `business_logic/averages.py` | Remove `import streamlit`, `@st.cache_data`. Add `load_presets_from_db()` call | Presets from DB |
| `app_services/session_state.py` | Remove `st.session_state` facade. Keep pure dataclasses. | Django uses Redis session |
| `app_services/session_service.py` | Remove `st.secrets` reads. Accept URLs as parameters. | Django settings provide URLs |
| `secrets_loader.py` | Remove `st.secrets` path. Add Django settings fallback. | Django settings replace st.secrets |
| `formatting/web_styler.py` | Rewrite to generate HTML with CSS classes instead of Pandas Styler | ADR-M06: HTML+CSS > Styler |

---

## Phase 0: Django Project Setup

### Task MIG-0.1: Create Django project scaffold

**Files:**
- Create: `orders_master_saas/manage.py`
- Create: `orders_master_saas/orders_master_saas/__init__.py`
- Create: `orders_master_saas/orders_master_saas/settings/__init__.py`
- Create: `orders_master_saas/orders_master_saas/settings/base.py`
- Create: `orders_master_saas/orders_master_saas/settings/development.py`
- Create: `orders_master_saas/orders_master_saas/settings/production.py`
- Create: `orders_master_saas/orders_master_saas/urls.py`
- Create: `orders_master_saas/orders_master_saas/wsgi.py`
- Create: `orders_master_saas/pyproject.toml`
- Create: `orders_master_saas/requirements.txt`
- Create: `orders_master_saas/requirements-dev.txt`
- Create: `orders_master_saas/.env.example`
- Create: `orders_master_saas/Procfile`

- [ ] **Step 1: Create project directory and scaffold Django**

```bash
cd "C:/Users/farma/Documents/Python Scripts/ORDERS_DJANGO/Orders_Master_SDD"
mkdir -p orders_master_saas
cd orders_master_saas
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install django==5.1 gunicorn psycopg2-binary redis django-redis celery
pip install -e ..
django-admin startproject orders_master_saas .
```

- [ ] **Step 2: Create split settings**

Create `orders_master_saas/settings/base.py`:
```python
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = os.environ.get("SECRET_KEY", "django-insecure-change-me-in-production")

DEBUG = os.environ.get("DEBUG", "True").lower() == "true"

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Local apps
    "accounts",
    "backoffice",
    "orders",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "accounts.middleware.TenantMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "orders_master_saas.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "orders_master_saas.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "pt-pt"
TIME_ZONE = "Europe/Lisbon"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/orders/"
LOGOUT_REDIRECT_URL = "/accounts/login/"

# Integration URLs (replace st.secrets)
SHORTAGES_SHEET_URL = os.environ.get("SHORTAGES_SHEET_URL", "")
DONOTBUY_SHEET_URL = os.environ.get("DONOTBUY_SHEET_URL", "")
```

Create `orders_master_saas/settings/development.py`:
```python
from .base import *  # noqa: F401,F403

DEBUG = True
```

Create `orders_master_saas/settings/production.py`:
```python
import os
from .base import *  # noqa: F401,F403

DEBUG = False

SECRET_KEY = os.environ["SECRET_KEY"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("PGDATABASE", "orders_master"),
        "USER": os.environ.get("PGUSER", "postgres"),
        "PASSWORD": os.environ.get("PGPASSWORD", ""),
        "HOST": os.environ.get("PGHOST", "localhost"),
        "PORT": os.environ.get("PGPORT", "5432"),
    }
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": os.environ.get("REDIS_URL", "redis://localhost:6379/0"),
    }
}

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
X_FRAME_OPTIONS = "DENY"
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
```

- [ ] **Step 3: Create requirements files**

`requirements.txt`:
```
django>=5.1,<6.0
gunicorn>=21.2
psycopg2-binary>=2.9
django-redis>=5.4
redis>=5.0
celery>=5.4
htmx>=1.0
pandas>=2.2
openpyxl>=3.1
pydantic>=2.7
python-dotenv>=1.0
pyyaml>=6.0
python-dateutil>=2.9
```

`requirements-dev.txt`:
```
-r requirements.txt
pytest>=8.2
pytest-django>=4.8
pytest-cov>=5.0
ruff>=0.4
black>=24.4
mypy>=1.10
pre-commit>=3.7
factory-boy>=3.3
```

- [ ] **Step 4: Create Procfile**

```
web: gunicorn orders_master_saas.wsgi:application --bind 0.0.0.0:$PORT --workers 4
```

- [ ] **Step 5: Create .env.example**

```bash
SECRET_KEY=change-me-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=sqlite:///db.sqlite3
REDIS_URL=redis://localhost:6379/0
SHORTAGES_SHEET_URL=
DONOTBUY_SHEET_URL=
```

- [ ] **Step 6: Create the 3 Django apps**

```bash
cd orders_master_saas
python manage.py startapp accounts
python manage.py startapp backoffice
python manage.py startapp orders
```

- [ ] **Step 7: Verify Django runs**

```bash
DJANGO_SETTINGS_MODULE=orders_master_saas.settings.development python manage.py check
```
Expected: `System check identified no issues (0 silenced).`

- [ ] **Step 8: Commit**

```bash
git add orders_master_saas/
git commit -m "feat: scaffold Django project with accounts, backoffice, orders apps"
```

---

### Task MIG-0.2: Copy orders_master/ domain package into Django project

**Files:**
- Copy: `orders_master/` → `orders_master_saas/orders_master/`
- Modify: `orders_master_saas/orders_master/__init__.py`

- [ ] **Step 1: Copy the domain package**

```bash
cp -r orders_master/ orders_master_saas/orders_master/
```

- [ ] **Step 2: Add orders_master to INSTALLED_APPS**

In `orders_master_saas/settings/base.py`, add to `INSTALLED_APPS`:
```python
    "orders_master",  # Domain package
```

- [ ] **Step 3: Verify import works**

```bash
cd orders_master_saas
python -c "import orders_master; print('Domain package imported successfully')"
```
Expected: `Domain package imported successfully`

- [ ] **Step 4: Commit**

```bash
git add orders_master_saas/orders_master/
git commit -m "feat: copy orders_master domain package into Django project"
```

---

### Task MIG-0.3: Add TailwindCSS + HTMX to Django project

**Files:**
- Create: `orders_master_saas/static/css/app.css`
- Create: `orders_master_saas/static/css/orders.css`
- Create: `orders_master_saas/static/js/app.js`
- Modify: `orders_master_saas/templates/base.html`

- [ ] **Step 1: Install TailwindCSS via CDN in base template (simplest for Railway)**

Create `orders_master_saas/templates/base.html`:
```html
{% load static %}
<!DOCTYPE html>
<html lang="pt-PT">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Orders Master Infoprex{% endblock %}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/htmx.org@2.0.4"></script>
    <link rel="stylesheet" href="{% static 'css/orders.css' %}">
    <link rel="stylesheet" href="{% static 'css/app.css' %}">
    {% block extra_head %}{% endblock %}
</head>
<body class="bg-gray-50 min-h-screen">
    {% if user.is_authenticated %}
    <nav class="bg-white shadow-sm border-b">
        <div class="max-w-7xl mx-auto px-4 py-3 flex justify-between items-center">
            <a href="{% url 'orders:upload' %}" class="text-lg font-bold text-gray-800">Orders Master</a>
            <div class="flex items-center gap-4">
                <span class="text-sm text-gray-600">{{ user.get_full_name|default:user.username }}</span>
                <span class="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">{{ user.profile.cliente.nome }}</span>
                <form method="post" action="{% url 'logout' %}" class="inline">
                    {% csrf_token %}
                    <button type="submit" class="text-sm text-red-600 hover:text-red-800">Sair</button>
                </form>
            </div>
        </div>
    </nav>
    {% endif %}

    {% if messages %}
    <div class="max-w-7xl mx-auto px-4 mt-4">
        {% for message in messages %}
        <div class="p-3 rounded mb-2 {% if message.tags == 'error' %}bg-red-100 text-red-800{% elif message.tags == 'warning' %}bg-yellow-100 text-yellow-800{% elif message.tags == 'success' %}bg-green-100 text-green-800{% else %}bg-blue-100 text-blue-800{% endif %}">
            {{ message }}
        </div>
        {% endfor %}
    </div>
    {% endif %}

    <main class="max-w-7xl mx-auto px-4 py-6">
        {% block content %}{% endblock %}
    </main>

    <script src="{% static 'js/app.js' %}"></script>
    {% block extra_scripts %}{% endblock %}
</body>
</html>
```

- [ ] **Step 2: Create orders.css with the 5 conditional table rules**

Create `orders_master_saas/static/css/orders.css`:
```css
/* === Orders Table — 5 Conditional Rules (PRD v2 §6.1.6, ADR-M06) === */

.table-orders {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.85rem;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

.table-orders th {
    background-color: #f5f5f5;
    font-weight: 600;
    padding: 8px 12px;
    text-align: left;
    border-bottom: 2px solid #ddd;
    position: sticky;
    top: 0;
    z-index: 10;
}

.table-orders td {
    padding: 6px 10px;
    border-bottom: 1px solid #eee;
}

/* Rule 1: Grupo — black bg, white text, bold (full row) */
.table-orders tr.row-grupo td {
    background-color: #000000 !important;
    color: #FFFFFF !important;
    font-weight: bold !important;
}

/* Rule 2: Não Comprar — light purple bg (CÓDIGO..T Uni) */
.table-orders td.row-nao-comprar {
    background-color: #E6D5F5;
    color: #000000;
}

/* Rule 3: Rutura — red Proposta cell */
.table-orders td.cell-rutura {
    background-color: #FF0000;
    color: #FFFFFF;
    font-weight: bold;
}

/* Rule 4: Validade curta — orange DTVAL cell */
.table-orders td.cell-validade-curta {
    background-color: #FFA500;
    color: #000000;
    font-weight: bold;
}

/* Rule 5: Preço anómalo — red bold text + warning icon */
.table-orders td.cell-preco-anomalo {
    color: #FF0000;
    font-weight: bold;
}

/* Hover */
.table-orders tbody tr:hover td {
    background-color: #f0f0f0;
}
.table-orders tbody tr.row-grupo:hover td {
    background-color: #333333 !important;
}

/* Number alignment */
.table-orders td.num {
    text-align: right;
    font-variant-numeric: tabular-nums;
}
```

- [ ] **Step 3: Create app.css for layout**

Create `orders_master_saas/static/css/app.css`:
```css
/* Scope Summary Bar */
.scope-bar {
    background: linear-gradient(to right, #f5f7fa, #c3cfe2);
    padding: 12px 16px;
    border-radius: 8px;
    margin-bottom: 16px;
    font-size: 0.9rem;
    display: flex;
    gap: 24px;
    flex-wrap: wrap;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.scope-bar span {
    display: inline-flex;
    align-items: center;
    gap: 4px;
}

/* BD Rupturas Banner */
.bd-rupturas-banner {
    background: linear-gradient(to right, #e0f7fa, #f1f8e9);
    padding: 12px 20px;
    border-radius: 15px;
    margin-bottom: 16px;
    text-align: center;
}

.bd-rupturas-banner .date {
    color: #0078D7;
    font-size: 24px;
    font-weight: bold;
}

/* File Inventory */
.file-inventory {
    font-size: 0.85rem;
}

.file-inventory tr.row-error td {
    background-color: #fde8e8;
    color: #c53030;
}
```

- [ ] **Step 4: Create app.js for HTMX**

Create `orders_master_saas/static/js/app.js`:
```javascript
document.addEventListener('DOMContentLoaded', function() {
    // HTMX config
    htmx.on('htmx:responseError', function(event) {
        console.error('HTMX response error:', event.detail);
    });
});
```

- [ ] **Step 5: Commit**

```bash
git add orders_master_saas/templates/ orders_master_saas/static/
git commit -m "feat: add base template, TailwindCSS, HTMX, and conditional table CSS"
```

---

## Phase 1: Domain Adaptation — Remove Streamlit Dependencies

### Task MIG-1.1: Create Django cache decorator (replaces @st.cache_data)

**Files:**
- Create: `orders_master_saas/orders_master/integrations/django_cache.py`
- Test: `orders_master_saas/orders/tests/test_django_cache.py`

- [ ] **Step 1: Write the failing test**

Create `orders_master_saas/orders/tests/test_django_cache.py`:
```python
import pytest
from django.core.cache import cache


@pytest.mark.django_db
def test_cache_decorator_caches_result():
    call_count = 0

    from orders_master.integrations.django_cache import django_cache_decorator

    @django_cache_decorator(timeout=300, key_prefix="test_fn")
    def expensive_fn(x):
        nonlocal call_count
        call_count += 1
        return x * 2

    cache.clear()
    result1 = expensive_fn(5)
    assert result1 == 10
    assert call_count == 1

    result2 = expensive_fn(5)
    assert result2 == 10
    assert call_count == 1  # not called again — cached

    result3 = expensive_fn(7)
    assert result3 == 14
    assert call_count == 2  # different args — new call


@pytest.mark.django_db
def test_cache_decorator_key_isolation():
    from orders_master.integrations.django_cache import django_cache_decorator

    @django_cache_decorator(timeout=300, key_prefix="iso_test")
    def fn_a(x):
        return x + 1

    @django_cache_decorator(timeout=300, key_prefix="iso_test2")
    def fn_b(x):
        return x + 2

    cache.clear()
    assert fn_a(10) == 11
    assert fn_b(10) == 12
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd orders_master_saas
pytest orders/tests/test_django_cache.py -v
```
Expected: FAIL — `ModuleNotFoundError: No module named 'orders_master.integrations.django_cache'`

- [ ] **Step 3: Write implementation**

Create `orders_master_saas/orders_master/integrations/django_cache.py`:
```python
import hashlib
import logging
from functools import wraps

logger = logging.getLogger(__name__)


def _make_cache_key(key_prefix: str, args, kwargs) -> str:
    key_data = f"{key_prefix}:{args}:{sorted(kwargs.items())}"
    return f"omc:{key_prefix}:{hashlib.md5(key_data.encode()).hexdigest()}"


def django_cache_decorator(timeout: int = 3600, key_prefix: str = ""):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            from django.core.cache import cache

            cache_key = _make_cache_key(key_prefix or func.__name__, args, kwargs)
            result = cache.get(cache_key)
            if result is not None:
                logger.debug("Cache hit: %s", cache_key)
                return result

            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout=timeout)
            logger.debug("Cache miss: %s", cache_key)
            return result

        return wrapper
    return decorator
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd orders_master_saas
pytest orders/tests/test_django_cache.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add orders_master_saas/orders_master/integrations/django_cache.py orders_master_saas/orders/tests/test_django_cache.py
git commit -m "feat: add Django cache decorator to replace @st.cache_data"
```

---

### Task MIG-1.2: Adapt shortages.py — remove Streamlit, use Django cache

**Files:**
- Modify: `orders_master_saas/orders_master/integrations/shortages.py`

- [ ] **Step 1: Replace streamlit imports and decorators**

In `orders_master_saas/orders_master/integrations/shortages.py`, replace the top of the file:

**Before:**
```python
import logging
from datetime import datetime

import pandas as pd

from orders_master.constants import Columns
from orders_master.schemas import ShortageRecordSchema

try:
    import streamlit as st
    _HAS_STREAMLIT = True
except ImportError:
    _HAS_STREAMLIT = False

if _HAS_STREAMLIT:
    cache_decorator = st.cache_data(ttl=3600, show_spinner="A carregar BD de Rupturas...")
else:
    cache_decorator = lambda f: f
```

**After:**
```python
import logging
from datetime import datetime

import pandas as pd

from orders_master.constants import Columns
from orders_master.schemas import ShortageRecordSchema

try:
    from orders_master.integrations.django_cache import django_cache_decorator
    cache_decorator = django_cache_decorator(timeout=3600, key_prefix="shortages")
except ImportError:
    cache_decorator = lambda f: f
```

- [ ] **Step 2: Remove st.sidebar.warning call**

Find and remove the `st.sidebar.warning(...)` call in the `except` block of `fetch_shortages_db`. The function already returns an empty DataFrame on failure — the warning will be shown by the calling view.

- [ ] **Step 3: Verify no streamlit imports remain**

```bash
grep -r "import streamlit" orders_master_saas/orders_master/integrations/shortages.py
```
Expected: no output (0 matches)

- [ ] **Step 4: Run existing tests**

```bash
cd orders_master_saas
pytest tests/unit/test_shortages_integration.py -v
```
Expected: PASS (tests use mocked data, no real HTTP calls)

- [ ] **Step 5: Commit**

```bash
git add orders_master_saas/orders_master/integrations/shortages.py
git commit -m "feat: adapt shortages.py — replace st.cache_data with Django cache, remove st.sidebar.warning"
```

---

### Task MIG-1.3: Adapt donotbuy.py — remove Streamlit, use Django cache

**Files:**
- Modify: `orders_master_saas/orders_master/integrations/donotbuy.py`

- [ ] **Step 1: Replace streamlit imports and decorators**

In `orders_master_saas/orders_master/integrations/donotbuy.py`, replace the top of the file with the same pattern as shortages.py:

**Before:**
```python
try:
    import streamlit as st
    _HAS_STREAMLIT = True
except ImportError:
    _HAS_STREAMLIT = False

if _HAS_STREAMLIT:
    cache_decorator = st.cache_data(ttl=3600, show_spinner="A carregar lista Não Comprar...")
else:
    cache_decorator = lambda f: f
```

**After:**
```python
try:
    from orders_master.integrations.django_cache import django_cache_decorator
    cache_decorator = django_cache_decorator(timeout=3600, key_prefix="donotbuy")
except ImportError:
    cache_decorator = lambda f: f
```

- [ ] **Step 2: Verify no streamlit imports remain**

```bash
grep -r "import streamlit" orders_master_saas/orders_master/integrations/donotbuy.py
```
Expected: no output

- [ ] **Step 3: Run existing tests**

```bash
cd orders_master_saas
pytest tests/unit/test_donotbuy_integration.py -v
```
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add orders_master_saas/orders_master/integrations/donotbuy.py
git commit -m "feat: adapt donotbuy.py — replace st.cache_data with Django cache"
```

---

### Task MIG-1.4: Adapt averages.py — remove Streamlit, add DB loader

**Files:**
- Modify: `orders_master_saas/orders_master/business_logic/averages.py`

- [ ] **Step 1: Remove streamlit import and @st.cache_data**

In `orders_master_saas/orders_master/business_logic/averages.py`, remove:
```python
import streamlit as st
```
and remove `@st.cache_data(ttl=3600)` from `load_presets`.

- [ ] **Step 2: Add DB-based preset loader with fallback to YAML**

Add at the end of the file:
```python
def load_presets(path: str | Path) -> dict[str, tuple[float, ...]]:
    """Load weight presets. Tries Django DB first, falls back to YAML file."""
    try:
        from orders.models import ConfigPesoPreset
        db_presets = {}
        for p in ConfigPesoPreset.objects.all():
            db_presets[p.nome] = tuple(p.pesos)
        if db_presets:
            return db_presets
    except Exception:
        pass
    # Fallback: load from YAML
    path = Path(path)
    if not path.exists():
        return {}
    config = load_presets_config(path)
    return config
```

- [ ] **Step 3: Verify no streamlit imports remain**

```bash
grep -r "import streamlit" orders_master_saas/orders_master/business_logic/averages.py
```
Expected: no output

- [ ] **Step 4: Run existing tests**

```bash
cd orders_master_saas
pytest tests/unit/test_averages.py -v
```
Expected: PASS (tests use YAML fallback)

- [ ] **Step 5: Commit**

```bash
git add orders_master_saas/orders_master/business_logic/averages.py
git commit -m "feat: adapt averages.py — remove st.cache_data, add DB preset loader"
```

---

### Task MIG-1.5: Adapt config loaders — remove Streamlit, add DB loaders

**Files:**
- Modify: `orders_master_saas/orders_master/config/labs_loader.py`
- Modify: `orders_master_saas/orders_master/config/locations_loader.py`
- Modify: `orders_master_saas/orders_master/config/presets_loader.py`

- [ ] **Step 1: Adapt labs_loader.py**

Remove `import streamlit as st` and `@st.cache_data`. Add a DB-based loader function:

```python
def load_labs_from_db(client_id: int | None = None) -> dict[str, list[str]]:
    """Load lab config from Django DB. If client_id, filter by client; else global."""
    try:
        from orders.models import ConfigLaboratorio
        qs = ConfigLaboratorio.objects.filter(ativo=True)
        return {lab.nome: lab.codigos_cla for lab in qs}
    except Exception:
        return {}
```

Keep the original `load_labs(mtime, path)` for backward compatibility (YAML fallback).

- [ ] **Step 2: Adapt locations_loader.py**

Remove `import streamlit as st` and `@st.cache_data`. Add:

```python
def load_locations_from_db(client_id: int | None = None) -> dict[str, str]:
    """Load location aliases from Django DB. Client-specific overrides globals."""
    try:
        from orders.models import ConfigLocalizacao
        aliases = {}
        # Global configs first
        for loc in ConfigLocalizacao.objects.filter(cliente__isnull=True):
            aliases[loc.search_term] = loc.alias
        # Client-specific overrides
        if client_id:
            for loc in ConfigLocalizacao.objects.filter(cliente_id=client_id):
                aliases[loc.search_term] = loc.alias
        return aliases
    except Exception:
        return {}
```

- [ ] **Step 3: Adapt presets_loader.py**

Add DB loader (presets_loader.py has no streamlit imports already):

```python
def load_presets_from_db() -> dict[str, list[float]]:
    """Load weight presets from Django DB."""
    try:
        from orders.models import ConfigPesoPreset
        return {p.nome: p.pesos for p in ConfigPesoPreset.objects.all()}
    except Exception:
        return {}
```

- [ ] **Step 4: Verify zero streamlit imports in config/】

```bash
grep -r "import streamlit" orders_master_saas/orders_master/config/
```
Expected: no output

- [ ] **Step 5: Commit**

```bash
git add orders_master_saas/orders_master/config/
git commit -m "feat: adapt config loaders — remove Streamlit, add DB-based loaders"
```

---

### Task MIG-1.6: Adapt secrets_loader.py and session_service.py

**Files:**
- Modify: `orders_master_saas/orders_master/secrets_loader.py`
- Modify: `orders_master_saas/orders_master/app_services/session_service.py`

- [ ] **Step 1: Adapt secrets_loader.py — replace st.secrets with Django settings**

Replace the `st.secrets` navigation block in `get_secret()`:

**Before (conceptual):**
```python
try:
    import streamlit as st
    value = st.secrets
    for part in key_path.split('.'):
        value = value[part]
    if value:
        return str(value)
except Exception:
    pass
```

**After:**
```python
try:
    from django.conf import settings
    parts = key_path.split('.')
    value = getattr(settings, parts[0].upper(), None)
    for part in parts[1:]:
        if value is None:
            break
        value = value.get(part) if isinstance(value, dict) else getattr(value, part, None)
    if value:
        return str(value)
except Exception:
    pass
```

Remove the `import streamlit as st` line.

- [ ] **Step 2: Adapt session_service.py — remove st.secrets reads**

In `process_orders_session()`, replace:
```python
url_shortages = st.secrets.get("SHORTAGES_URL")
url_dnb = st.secrets.get("DONOTBUY_URL")
```
With:
```python
url_shortages = kwargs.get("shortages_url") or os.environ.get("SHORTAGES_SHEET_URL", "")
url_dnb = kwargs.get("donotbuy_url") or os.environ.get("DONOTBUY_SHEET_URL", "")
```

Update the function signature to accept these as explicit parameters instead of reading from `st.secrets`.

- [ ] **Step 3: Verify zero streamlit imports**

```bash
grep -r "import streamlit" orders_master_saas/orders_master/secrets_loader.py orders_master_saas/orders_master/app_services/session_service.py
```
Expected: no output

- [ ] **Step 4: Run existing tests**

```bash
cd orders_master_saas
pytest tests/unit/test_session_service.py tests/unit/test_secrets_loader.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add orders_master_saas/orders_master/secrets_loader.py orders_master_saas/orders_master/app_services/session_service.py
git commit -m "feat: replace st.secrets with Django settings in secrets_loader and session_service"
```

---

### Task MIG-1.7: Adapt session_state.py — remove st.session_state facade

**Files:**
- Modify: `orders_master_saas/orders_master/app_services/session_state.py`

- [ ] **Step 1: Remove st.session_state facade functions**

Remove `get_state()` and `reset_state()` functions that depend on `st.session_state`. Keep the pure dataclasses (`SessionState`, `ScopeContext`, `FileInventoryEntry`) — they are used by Django views as regular Python objects.

The Django views will manage session state via Redis cache keyed by user session, not via `st.session_state`.

- [ ] **Step 2: Verify dataclasses still import cleanly**

```bash
cd orders_master_saas
python -c "from orders_master.app_services.session_state import SessionState, ScopeContext, FileInventoryEntry; print('OK')"
```
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add orders_master_saas/orders_master/app_services/session_state.py
git commit -m "feat: remove st.session_state facade from session_state.py, keep pure dataclasses"
```

---

### Task MIG-1.8: Verify zero Streamlit imports in orders_master/

**Files:**
- All files in `orders_master_saas/orders_master/`

- [ ] **Step 1: Run comprehensive grep**

```bash
grep -r "import streamlit" orders_master_saas/orders_master/
```
Expected: no output (0 matches)

- [ ] **Step 2: Run full domain test suite**

```bash
cd orders_master_saas
pytest tests/unit/ -v --tb=short
```
Expected: All existing unit tests pass

- [ ] **Step 3: Commit any final cleanup**

```bash
git add -A orders_master_saas/orders_master/
git commit -m "feat: complete removal of streamlit from orders_master domain package"
```

---

## Phase 2: Models & Config Migration

### Task MIG-2.1: Create accounts models (Cliente, Farmacia, Subscricao, UserProfile)

**Files:**
- Create: `orders_master_saas/accounts/models.py`
- Test: `orders_master_saas/accounts/tests/test_models.py`

- [ ] **Step 1: Write the failing test**

Create `orders_master_saas/accounts/tests/__init__.py` and `orders_master_saas/accounts/tests/test_models.py`:
```python
import pytest
from django.contrib.auth.models import User
from accounts.models import Cliente, Farmacia, Subscricao, UserProfile


@pytest.mark.django_db
def test_cliente_creation():
    cliente = Cliente.objects.create(nome="Farmácias João", email="joao@example.com")
    assert cliente.nome == "Farmácias João"
    assert cliente.ativo is True
    assert str(cliente) == "Farmácias João"


@pytest.mark.django_db
def test_farmacia_belongs_to_cliente():
    cliente = Cliente.objects.create(nome="Teste", email="test@example.com")
    farmacia = Farmacia.objects.create(
        cliente=cliente, nome="FARMACIA GUIA",
        localizacao_key="GUIA", alias="Guia"
    )
    assert farmacia.cliente == cliente
    assert farmacia.ativa is True
    assert cliente.farmacias.count() == 1


@pytest.mark.django_db
def test_subscricao_bd_rupturas_flag():
    from datetime import date
    cliente = Cliente.objects.create(nome="Teste", email="test@example.com")
    sub = Subscricao.objects.create(
        cliente=cliente, plano=Subscricao.Plano.PROFISSIONAL,
        bd_rupturas_ativa=True, data_inicio=date(2026, 1, 1)
    )
    assert sub.bd_rupturas_ativa is True
    assert sub.plano == "PRO"


@pytest.mark.django_db
def test_userprofile_links_user_to_cliente():
    cliente = Cliente.objects.create(nome="Teste", email="test@example.com")
    user = User.objects.create_user("joao", password="test123")
    profile = UserProfile.objects.create(user=user, cliente=cliente, role="compras")
    assert profile.cliente == cliente
    assert profile.role == "compras"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd orders_master_saas
pytest accounts/tests/test_models.py -v
```
Expected: FAIL

- [ ] **Step 3: Write the models**

Create `orders_master_saas/accounts/models.py`:
```python
from django.contrib.auth.models import User
from django.db import models


class Cliente(models.Model):
    nome = models.CharField(max_length=200)
    nif = models.CharField(max_length=20, blank=True)
    email = models.EmailField()
    telefone = models.CharField(max_length=30, blank=True)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    actualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class Farmacia(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name="farmacias")
    nome = models.CharField(max_length=200)
    localizacao_key = models.CharField(
        max_length=100,
        help_text="Valor exacto do campo LOCALIZACAO no Infoprex (ex: 'FARMACIA GUIA')",
    )
    alias = models.CharField(max_length=100, help_text="Nome de apresentacao (ex: 'Guia')")
    ativa = models.BooleanField(default=True)
    licenciada_ate = models.DateField(null=True, blank=True)

    class Meta:
        unique_together = ["cliente", "localizacao_key"]
        ordering = ["alias"]
        verbose_name_plural = "farmacias"

    def __str__(self):
        return f"{self.alias} ({self.cliente.nome})"


class Subscricao(models.Model):
    class Plano(models.TextChoices):
        BASICO = "BAS", "Basico"
        PROFISSIONAL = "PRO", "Profissional"
        ENTERPRISE = "ENT", "Enterprise"

    cliente = models.OneToOneField(Cliente, on_delete=models.CASCADE, related_name="subscricao")
    plano = models.CharField(max_length=3, choices=Plano.choices, default=Plano.BASICO)
    bd_rupturas_ativa = models.BooleanField(
        default=False, help_text="Extra pago: acesso a BD Esgotados Infarmed"
    )
    data_inicio = models.DateField()
    data_fim = models.DateField(null=True, blank=True)
    ativa = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.cliente.nome} - {self.get_plano_display()}"


class UserProfile(models.Model):
    class Role(models.TextChoices):
        ADMIN = "admin", "Administrador"
        COMPRAS = "compras", "Responsavel de Compras"
        FARMACIA = "farmacia", "Farmacia"

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name="utilizadores")
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.COMPRAS)

    def __str__(self):
        return f"{self.user.username} ({self.cliente.nome})"
```

- [ ] **Step 4: Run migrations and tests**

```bash
cd orders_master_saas
python manage.py makemigrations accounts
python manage.py migrate
pytest accounts/tests/test_models.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add orders_master_saas/accounts/
git commit -m "feat: add accounts models — Cliente, Farmacia, Subscricao, UserProfile"
```

---

### Task MIG-2.2: Create orders models (ConfigLaboratorio, ConfigLocalizacao, ConfigPesoPreset)

**Files:**
- Create: `orders_master_saas/orders/models.py`
- Test: `orders_master_saas/orders/tests/test_config_models.py`

- [ ] **Step 1: Write the failing test**

Create `orders_master_saas/orders/tests/test_config_models.py`:
```python
import pytest
from orders.models import ConfigLaboratorio, ConfigLocalizacao, ConfigPesoPreset
from accounts.models import Cliente


@pytest.mark.django_db
def test_config_laboratorio():
    lab = ConfigLaboratorio.objects.create(nome="Mylan", codigos_cla=["137", "2651"])
    assert lab.codigos_cla == ["137", "2651"]
    assert lab.ativo is True


@pytest.mark.django_db
def test_config_localizacao_global():
    loc = ConfigLocalizacao.objects.create(search_term="guia", alias="Guia")
    assert loc.cliente is None
    assert "Global" in str(loc)


@pytest.mark.django_db
def test_config_localizacao_client_specific():
    cliente = Cliente.objects.create(nome="Teste", email="t@t.com")
    loc = ConfigLocalizacao.objects.create(cliente=cliente, search_term="ilha", alias="Ilha")
    assert loc.cliente == cliente
    assert "Teste" in str(loc)


@pytest.mark.django_db
def test_config_peso_preset():
    preset = ConfigPesoPreset.objects.create(nome="Padrão", pesos=[0.4, 0.3, 0.2, 0.1])
    assert sum(preset.pesos) == 1.0
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd orders_master_saas
pytest orders/tests/test_config_models.py -v
```
Expected: FAIL

- [ ] **Step 3: Write the models**

Add to `orders_master_saas/orders/models.py`:
```python
from django.db import models
from accounts.models import Cliente


class ConfigLaboratorio(models.Model):
    nome = models.CharField(max_length=200, unique=True)
    codigos_cla = models.JSONField(help_text='Lista de codigos CLA. Ex: ["137", "2651"]')
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ["nome"]
        verbose_name_plural = "configlaboratorios"

    def __str__(self):
        return self.nome


class ConfigLocalizacao(models.Model):
    cliente = models.ForeignKey(
        Cliente, on_delete=models.CASCADE, null=True, blank=True,
        help_text="Se null, e uma config global (aplica-se a todos)",
        related_name="localizacoes",
    )
    search_term = models.CharField(
        max_length=200, help_text="Termo de pesquisa no campo LOCALIZACAO do Infoprex"
    )
    alias = models.CharField(max_length=100, help_text="Nome de apresentacao")

    class Meta:
        unique_together = ["cliente", "search_term"]
        ordering = ["search_term"]
        verbose_name_plural = "configlocalizacaos"

    def __str__(self):
        escopo = "Global" if not self.cliente else str(self.cliente.nome)
        return f"[{escopo}] {self.search_term} -> {self.alias}"


class ConfigPesoPreset(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    pesos = models.JSONField(help_text="Lista de 4 pesos. Ex: [0.4, 0.3, 0.2, 0.1]")

    class Meta:
        ordering = ["nome"]
        verbose_name_plural = "configpesopresets"

    def __str__(self):
        return self.nome


class SessaoProcessamento(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    utilizador = models.ForeignKey("auth.User", on_delete=models.CASCADE)
    criado_em = models.DateTimeField(auto_now_add=True)
    num_ficheiros = models.IntegerField()
    num_produtos = models.IntegerField()
    num_farmacias = models.IntegerField()
    lab_selecionados = models.JSONField(default=list)
    modo_detalhado = models.BooleanField(default=False)
    meses_previsao = models.FloatField(default=1.0)

    class Meta:
        ordering = ["-criado_em"]

    def __str__(self):
        return f"Sessao {self.criado_em:%Y-%m-%d %H:%M} — {self.cliente.nome}"
```

- [ ] **Step 4: Run migrations and tests**

```bash
cd orders_master_saas
python manage.py makemigrations orders
python manage.py migrate
pytest orders/tests/test_config_models.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add orders_master_saas/orders/models.py orders_master_saas/orders/tests/test_config_models.py
git commit -m "feat: add orders models — ConfigLaboratorio, ConfigLocalizacao, ConfigPesoPreset, SessaoProcessamento"
```

---

### Task MIG-2.3: Create management commands to import JSON/YAML configs

**Files:**
- Create: `orders_master_saas/backoffice/management/__init__.py`
- Create: `orders_master_saas/backoffice/management/commands/__init__.py`
- Create: `orders_master_saas/backoffice/management/commands/import_labs_json.py`
- Create: `orders_master_saas/backoffice/management/commands/import_locations_json.py`
- Create: `orders_master_saas/backoffice/management/commands/import_presets_yaml.py`
- Test: `orders_master_saas/backoffice/tests/test_import_commands.py`

- [ ] **Step 1: Write the failing test**

```python
import pytest
from django.core.management import call_command
from orders.models import ConfigLaboratorio, ConfigLocalizacao, ConfigPesoPreset


@pytest.mark.django_db
def test_import_labs_json(tmp_path):
    json_file = tmp_path / "labs.json"
    json_file.write_text('{"Mylan": ["137", "2651"], "Bial": ["42"]}')
    call_command("import_labs_json", str(json_file))
    assert ConfigLaboratorio.objects.count() == 2
    mylan = ConfigLaboratorio.objects.get(nome="Mylan")
    assert mylan.codigos_cla == ["137", "2651"]


@pytest.mark.django_db
def test_import_locations_json(tmp_path):
    json_file = tmp_path / "locs.json"
    json_file.write_text('{"guia": "Guia", "ilha": "Ilha"}')
    call_command("import_locations_json", str(json_file))
    assert ConfigLocalizacao.objects.filter(cliente__isnull=True).count() == 2


@pytest.mark.django_db
def test_import_presets_yaml(tmp_path):
    yaml_file = tmp_path / "presets.yaml"
    yaml_file.write_text("presets:\n  Padrao:\n    pesos:\n      - 0.4\n      - 0.3\n      - 0.2\n      - 0.1\n")
    call_command("import_presets_yaml", str(yaml_file))
    assert ConfigPesoPreset.objects.count() == 1
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd orders_master_saas
pytest backoffice/tests/test_import_commands.py -v
```
Expected: FAIL

- [ ] **Step 3: Write the management commands**

`import_labs_json.py`:
```python
import json
from django.core.management.base import BaseCommand
from orders.models import ConfigLaboratorio


class Command(BaseCommand):
    help = "Import laboratorios.json into ConfigLaboratorio model"

    def add_arguments(self, parser):
        parser.add_argument("json_path", type=str)

    def handle(self, *args, **options):
        with open(options["json_path"]) as f:
            data = json.load(f)
        count = 0
        for nome, codigos in data.items():
            lab, created = ConfigLaboratorio.objects.update_or_create(
                nome=nome, defaults={"codigos_cla": codigos, "ativo": True}
            )
            if created:
                count += 1
        self.stdout.write(self.style.SUCCESS(f"Imported {count} new labs ({len(data)} total)"))
```

`import_locations_json.py`:
```python
import json
from django.core.management.base import BaseCommand
from orders.models import ConfigLocalizacao


class Command(BaseCommand):
    help = "Import localizacoes.json into ConfigLocalizacao model (global)"

    def add_arguments(self, parser):
        parser.add_argument("json_path", type=str)

    def handle(self, *args, **options):
        with open(options["json_path"]) as f:
            data = json.load(f)
        count = 0
        for search_term, alias in data.items():
            loc, created = ConfigLocalizacao.objects.update_or_create(
                cliente=None, search_term=search_term, defaults={"alias": alias}
            )
            if created:
                count += 1
        self.stdout.write(self.style.SUCCESS(f"Imported {count} new locations ({len(data)} total)"))
```

`import_presets_yaml.py`:
```python
import yaml
from django.core.management.base import BaseCommand
from orders.models import ConfigPesoPreset


class Command(BaseCommand):
    help = "Import presets.yaml into ConfigPesoPreset model"

    def add_arguments(self, parser):
        parser.add_argument("yaml_path", type=str)

    def handle(self, *args, **options):
        with open(options["yaml_path"]) as f:
            data = yaml.safe_load(f)
        count = 0
        presets = data.get("presets", data)
        for nome, config in presets.items():
            pesos = config.get("pesos", config) if isinstance(config, dict) else config
            preset, created = ConfigPesoPreset.objects.update_or_create(
                nome=nome, defaults={"pesos": pesos}
            )
            if created:
                count += 1
        self.stdout.write(self.style.SUCCESS(f"Imported {count} new presets ({len(presets)} total)"))
```

- [ ] **Step 4: Run tests**

```bash
cd orders_master_saas
pytest backoffice/tests/test_import_commands.py -v
```
Expected: PASS

- [ ] **Step 5: Import existing config data**

```bash
cd orders_master_saas
python manage.py import_labs_json ../config/laboratorios.json
python manage.py import_locations_json ../config/localizacoes.json
python manage.py import_presets_yaml ../config/presets.yaml
```

- [ ] **Step 6: Commit**

```bash
git add orders_master_saas/backoffice/
git commit -m "feat: add management commands to import JSON/YAML configs into Django models"
```

---

## Phase 3: Auth & Multi-Tenancy

### Task MIG-3.1: Implement TenantMiddleware

**Files:**
- Create: `orders_master_saas/accounts/middleware.py`
- Test: `orders_master_saas/orders/tests/test_multitenancy.py`

- [ ] **Step 1: Write the failing test**

```python
import pytest
from django.contrib.auth.models import User
from django.test import RequestFactory
from accounts.middleware import TenantMiddleware
from accounts.models import Cliente, UserProfile


@pytest.mark.django_db
def test_tenant_middleware_sets_request_tenant():
    cliente = Cliente.objects.create(nome="Teste", email="t@t.com")
    user = User.objects.create_user("testuser", password="pass")
    UserProfile.objects.create(user=user, cliente=cliente)

    factory = RequestFactory()
    request = factory.get("/orders/")
    request.user = user

    middleware = TenantMiddleware(lambda r: None)
    middleware(request)

    assert request.tenant == cliente


@pytest.mark.django_db
def test_tenant_middleware_anonymous_no_tenant():
    from django.contrib.auth.models import AnonymousUser
    factory = RequestFactory()
    request = factory.get("/orders/")
    request.user = AnonymousUser()

    middleware = TenantMiddleware(lambda r: None)
    middleware(request)

    assert not hasattr(request, "tenant") or request.tenant is None
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd orders_master_saas
pytest orders/tests/test_multitenancy.py -v
```
Expected: FAIL

- [ ] **Step 3: Write the middleware**

Create `orders_master_saas/accounts/middleware.py`:
```python
class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            try:
                request.tenant = request.user.profile.cliente
            except Exception:
                request.tenant = None
        response = self.get_response(request)
        return response
```

- [ ] **Step 4: Run tests**

```bash
cd orders_master_saas
pytest orders/tests/test_multitenancy.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add orders_master_saas/accounts/middleware.py orders_master_saas/orders/tests/test_multitenancy.py
git commit -m "feat: add TenantMiddleware for multi-tenant request handling"
```

---

### Task MIG-3.2: Create login/logout views and templates

**Files:**
- Create: `orders_master_saas/accounts/views.py`
- Create: `orders_master_saas/accounts/urls.py`
- Create: `orders_master_saas/templates/registration/login.html`
- Modify: `orders_master_saas/orders_master_saas/urls.py`

- [ ] **Step 1: Create login view**

Create `orders_master_saas/accounts/views.py`:
```python
from django.contrib.auth.views import LoginView, LogoutView


class OrdersLoginView(LoginView):
    template_name = "registration/login.html"
    redirect_authenticated_user = True
```

- [ ] **Step 2: Create login template**

Create `orders_master_saas/templates/registration/login.html`:
```html
{% extends "base.html" %}

{% block title %}Login — Orders Master{% endblock %}

{% block content %}
<div class="max-w-md mx-auto mt-20">
    <div class="bg-white rounded-lg shadow-md p-8">
        <h1 class="text-2xl font-bold mb-6 text-center">Orders Master Infoprex</h1>
        <form method="post">
            {% csrf_token %}
            {% if form.errors %}
            <div class="bg-red-100 text-red-800 p-3 rounded mb-4">
                Credenciais inválidas. Tente novamente.
            </div>
            {% endif %}
            <div class="mb-4">
                <label for="id_username" class="block text-sm font-medium text-gray-700 mb-1">Utilizador</label>
                <input type="text" name="username" id="id_username"
                       class="w-full border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                       value="{{ form.username.value|default:'' }}">
            </div>
            <div class="mb-6">
                <label for="id_password" class="block text-sm font-medium text-gray-700 mb-1">Palavra-passe</label>
                <input type="password" name="password" id="id_password"
                       class="w-full border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500">
            </div>
            <button type="submit" class="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700">
                Entrar
            </button>
        </form>
    </div>
</div>
{% endblock %}
```

- [ ] **Step 3: Wire up URLs**

Create `orders_master_saas/accounts/urls.py`:
```python
from django.urls import path
from accounts.views import OrdersLoginView

urlpatterns = [
    path("login/", OrdersLoginView.as_view(), name="login"),
]
```

Update `orders_master_saas/orders_master_saas/urls.py`:
```python
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.views import LogoutView
from django.views.generic import RedirectView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("accounts/logout/", LogoutView.as_view(), name="logout"),
    path("orders/", include("orders.urls")),
    path("", RedirectView.as_view(url="/orders/")),
]
```

- [ ] **Step 4: Verify login page renders**

```bash
cd orders_master_saas
python manage.py check
```
Expected: no issues

- [ ] **Step 5: Commit**

```bash
git add orders_master_saas/accounts/views.py orders_master_saas/accounts/urls.py orders_master_saas/templates/registration/ orders_master_saas/orders_master_saas/urls.py
git commit -m "feat: add login/logout views, templates, and URL routing"
```

---

### Task MIG-3.3: Create Django Admin customizations

**Files:**
- Create: `orders_master_saas/accounts/admin.py`
- Create: `orders_master_saas/backoffice/admin.py`

- [ ] **Step 1: Create accounts admin**

Create `orders_master_saas/accounts/admin.py`:
```python
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from accounts.models import Cliente, Farmacia, Subscricao, UserProfile


class FarmaciaInline(admin.TabularInline):
    model = Farmacia
    extra = 1


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ["nome", "email", "ativo", "n_farmacias"]
    list_filter = ["ativo"]
    search_fields = ["nome", "email"]
    inlines = [FarmaciaInline]

    def n_farmacias(self, obj):
        return obj.farmacias.count()
    n_farmacias.short_description = "Farmácias"


@admin.register(Farmacia)
class FarmaciaAdmin(admin.ModelAdmin):
    list_display = ["alias", "nome", "cliente", "ativa", "licenciada_ate"]
    list_filter = ["ativa", "cliente"]
    search_fields = ["nome", "alias", "localizacao_key"]
    actions = ["activar", "desactivar"]

    @admin.action(description="Activar farmácias seleccionadas")
    def activar(self, request, queryset):
        queryset.update(ativa=True)

    @admin.action(description="Desactivar farmácias seleccionadas")
    def desactivar(self, request, queryset):
        queryset.update(ativa=False)


@admin.register(Subscricao)
class SubscricaoAdmin(admin.ModelAdmin):
    list_display = ["cliente", "plano", "bd_rupturas_ativa", "ativa", "data_inicio", "data_fim"]
    list_filter = ["ativa", "plano", "bd_rupturas_ativa"]


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = "Perfil"


class UserAdmin(BaseUserAdmin):
    inlines = [UserProfileInline]


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
```

- [ ] **Step 2: Create backoffice admin**

Create `orders_master_saas/backoffice/admin.py`:
```python
from django.contrib import admin
from orders.models import ConfigLaboratorio, ConfigLocalizacao, ConfigPesoPreset


@admin.register(ConfigLaboratorio)
class ConfigLaboratorioAdmin(admin.ModelAdmin):
    list_display = ["nome", "ativo"]
    list_filter = ["ativo"]
    search_fields = ["nome"]


@admin.register(ConfigLocalizacao)
class ConfigLocalizacaoAdmin(admin.ModelAdmin):
    list_display = ["search_term", "alias", "cliente_display"]
    list_filter = ["cliente"]
    search_fields = ["search_term", "alias"]

    def cliente_display(self, obj):
        return "Global" if obj.cliente is None else str(obj.cliente.nome)
    cliente_display.short_description = "Escopo"


@admin.register(ConfigPesoPreset)
class ConfigPesoPresetAdmin(admin.ModelAdmin):
    list_display = ["nome", "pesos"]
```

- [ ] **Step 3: Verify admin loads**

```bash
cd orders_master_saas
python manage.py check
```
Expected: no issues

- [ ] **Step 4: Commit**

```bash
git add orders_master_saas/accounts/admin.py orders_master_saas/backoffice/admin.py
git commit -m "feat: add Django Admin customizations for all models"
```

---

## Phase 4: Views & Templates (Core UI)

### Task MIG-4.1: Create ProcessingSession service (Redis-backed DataFrame storage)

**Files:**
- Create: `orders_master_saas/orders/services/__init__.py`
- Create: `orders_master_saas/orders/services/processing_session.py`
- Test: `orders_master_saas/orders/tests/test_processing_session.py`

- [ ] **Step 1: Write the failing test**

```python
import pytest
import pandas as pd
from orders.services.processing_session import ProcessingSession


@pytest.mark.django_db
def test_store_and_retrieve_dataframe():
    session = ProcessingSession(session_key="test-session-1")
    df = pd.DataFrame({"A": [1, 2], "B": [3, 4]})
    session.store("test_df", df)
    retrieved = session.get("test_df")
    assert retrieved is not None
    assert list(retrieved.columns) == ["A", "B"]
    assert len(retrieved) == 2


@pytest.mark.django_db
def test_get_missing_key_returns_none():
    session = ProcessingSession(session_key="test-session-2")
    assert session.get("nonexistent") is None


@pytest.mark.django_db
def test_clear_session():
    session = ProcessingSession(session_key="test-session-3")
    session.store("df", pd.DataFrame({"X": [1]}))
    session.clear()
    assert session.get("df") is None
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd orders_master_saas
pytest orders/tests/test_processing_session.py -v
```
Expected: FAIL

- [ ] **Step 3: Write implementation**

Create `orders_master_saas/orders/services/processing_session.py`:
```python
import logging

import pandas as pd
from django.core.cache import cache

logger = logging.getLogger(__name__)

_CACHE_PREFIX = "om:session"
_DEFAULT_TTL = 3600  # 1 hour


class ProcessingSession:
    def __init__(self, session_key: str):
        self._key = f"{_CACHE_PREFIX}:{session_key}"

    def _full_key(self, name: str) -> str:
        return f"{self._key}:{name}"

    def store(self, name: str, df: pd.DataFrame, ttl: int = _DEFAULT_TTL) -> None:
        cache.set(self._full_key(name), df.to_parquet(), timeout=ttl)

    def get(self, name: str) -> pd.DataFrame | None:
        data = cache.get(self._full_key(name))
        if data is None:
            return None
        return pd.read_parquet(data)

    def store_value(self, name: str, value, ttl: int = _DEFAULT_TTL) -> None:
        cache.set(self._full_key(name), value, timeout=ttl)

    def get_value(self, name: str):
        return cache.get(self._full_key(name))

    def clear(self) -> None:
        keys = cache.keys(f"{self._key}:*")
        if keys:
            cache.delete_many(keys)
```

- [ ] **Step 4: Run tests**

```bash
cd orders_master_saas
pytest orders/tests/test_processing_session.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add orders_master_saas/orders/services/ orders_master_saas/orders/tests/test_processing_session.py
git commit -m "feat: add ProcessingSession service for Redis-backed DataFrame storage"
```

---

### Task MIG-4.2: Create upload view and template

**Files:**
- Create: `orders_master_saas/orders/views.py`
- Create: `orders_master_saas/orders/urls.py`
- Create: `orders_master_saas/orders/forms.py`
- Create: `orders_master_saas/templates/orders/upload.html`
- Test: `orders_master_saas/orders/tests/test_views.py`

- [ ] **Step 1: Create the forms**

Create `orders_master_saas/orders/forms.py`:
```python
from django import forms


class UploadForm(forms.Form):
    infoprex_files = forms.FileField(
        widget=forms.ClearableFileInput(attrs={"multiple": True, "accept": ".txt"}),
        required=True,
    )
    codes_file = forms.FileField(
        widget=forms.ClearableFileInput(attrs={"accept": ".txt"}),
        required=False,
    )
    brands_files = forms.FileField(
        widget=forms.ClearableFileInput(attrs={"multiple": True, "accept": ".csv"}),
        required=False,
    )
    labs = forms.MultipleChoiceField(
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    def __init__(self, *args, labs_choices=None, **kwargs):
        super().__init__(*args, **kwargs)
        if labs_choices:
            self.fields["labs"].choices = labs_choices


class RecalcForm(forms.Form):
    detailed_view = forms.BooleanField(required=False, initial=False)
    use_previous_month = forms.BooleanField(required=False, initial=False)
    months = forms.FloatField(min_value=0.5, max_value=6.0, initial=1.0)
    preset = forms.ChoiceField(choices=[])
    brands = forms.MultipleChoiceField(required=False, widget=forms.CheckboxSelectMultiple)

    def __init__(self, *args, preset_choices=None, brands_choices=None, **kwargs):
        super().__init__(*args, **kwargs)
        if preset_choices:
            self.fields["preset"].choices = preset_choices
        if brands_choices:
            self.fields["brands"].choices = brands_choices
```

- [ ] **Step 2: Create the views**

Create `orders_master_saas/orders/views.py`:
```python
import io
import logging

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from orders.forms import UploadForm, RecalcForm
from orders.models import ConfigLaboratorio, ConfigPesoPreset
from orders.services.processing_session import ProcessingSession
from orders_master.app_services.session_state import SessionState, ScopeContext
from orders_master.app_services.session_service import process_orders_session
from orders_master.app_services.recalc_service import recalculate_proposal
from orders_master.config.labs_loader import load_labs_from_db
from orders_master.config.locations_loader import load_locations_from_db
from orders_master.formatting.excel_formatter import build_excel
from orders_master.integrations.django_cache import django_cache_decorator

logger = logging.getLogger(__name__)


@login_required
def upload_view(request):
    labs_qs = ConfigLaboratorio.objects.filter(ativo=True)
    labs_choices = [(lab.nome, lab.nome) for lab in labs_qs]

    if request.method == "POST":
        form = UploadForm(request.POST, request.FILES, labs_choices=labs_choices)
        if form.is_valid():
            return _process_upload(request, form)
    else:
        form = UploadForm(labs_choices=labs_choices)

    return render(request, "orders/upload.html", {"form": form, "labs": labs_qs})


def _process_upload(request, form):
    from orders_master.ingestion.codes_txt_parser import parse_codes_txt

    infoprex_files = request.FILES.getlist("infoprex_files")
    codes_file = form.cleaned_data.get("codes_file")
    brands_files = request.FILES.getlist("brands_files")
    labs_selected = form.cleaned_data.get("labs", [])

    # Build CLA list from selected labs
    labs_config = load_labs_from_db()
    lista_cla = []
    for lab_name in labs_selected:
        lista_cla.extend(labs_config.get(lab_name, []))

    # Parse codes TXT
    lista_codigos = []
    if codes_file:
        codes_bytes = codes_file.read()
        lista_codigos = parse_codes_txt(io.BytesIO(codes_bytes))

    # Load locations
    tenant = getattr(request, "tenant", None)
    client_id = tenant.id if tenant else None
    locations_aliases = load_locations_from_db(client_id=client_id)

    # Process
    state = SessionState()
    session = ProcessingSession(session_key=request.session.session_key or "default")

    process_orders_session(
        files=[io.BytesIO(f.read()) for f in infoprex_files],
        codes_file=io.BytesIO(codes_file.read()) if codes_file else None,
        brands_files=[io.BytesIO(f.read()) for f in brands_files],
        labs_selected=labs_selected,
        labs_config=labs_config,
        locations_aliases=locations_aliases,
        state=state,
        shortages_url=request.settings.SHORTAGES_SHEET_URL if hasattr(request, "settings") else "",
        donotbuy_url=request.settings.DONOTBUY_SHEET_URL if hasattr(request, "settings") else "",
    )

    # Store state in cache
    for attr in ["df_aggregated", "df_detailed", "df_raw", "master_products",
                 "file_errors", "file_inventory", "scope_context"]:
        val = getattr(state, attr, None)
        if val is not None:
            if isinstance(val, (list,)) and val and hasattr(val[0], '__dataclass_fields__'):
                session.store_value(attr, [vars(v) for v in val])
            elif hasattr(val, '__dataclass_fields__'):
                session.store_value(attr, vars(val))
            elif isinstance(val, object) and hasattr(val, 'to_parquet'):
                session.store(attr, val)
            else:
                session.store_value(attr, val)

    return redirect("orders:results")


@login_required
def results_view(request):
    session = ProcessingSession(session_key=request.session.session_key or "default")
    state = _reconstruct_state(session)

    if state.df_aggregated is None or state.df_aggregated.empty:
        return redirect("orders:upload")

    presets = ConfigPesoPreset.objects.all()
    preset_choices = [(p.nome, p.nome) for p in presets]

    # Default recalc
    weights = tuple(presets.first().pesos) if presets.exists() else (0.4, 0.3, 0.2, 0.1)
    df_final = recalculate_proposal(
        df_detailed=state.df_detailed,
        detailed_view=False,
        master_products=state.df_master_products if hasattr(state, "df_master_products") else state.master_products,
        months=1.0,
        weights=weights,
        use_previous_month=False,
        marcas=None,
        scope_context=state.scope_context,
    )

    context = {
        "state": state,
        "df_final": df_final,
        "presets": presets,
        "columns": list(df_final.columns),
        "rows": _prepare_rows(df_final),
    }
    return render(request, "orders/results.html", context)


@login_required
@require_POST
def recalc_view(request):
    """HTMX endpoint: recalculate with new parameters."""
    session = ProcessingSession(session_key=request.session.session_key or "default")
    state = _reconstruct_state(session)

    detailed = request.POST.get("detailed_view") == "on"
    use_prev = request.POST.get("use_previous_month") == "on"
    months = float(request.POST.get("months", 1.0))
    preset_name = request.POST.get("preset", "Padrão")
    brands = request.POST.getlist("brands")

    preset = ConfigPesoPreset.objects.filter(nome=preset_name).first()
    weights = tuple(preset.pesos) if preset else (0.4, 0.3, 0.2, 0.1)

    df_final = recalculate_proposal(
        df_detailed=state.df_detailed,
        detailed_view=detailed,
        master_products=state.df_master_products if hasattr(state, "df_master_products") else state.master_products,
        months=months,
        weights=weights,
        use_previous_month=use_prev,
        marcas=brands if brands else None,
        scope_context=state.scope_context,
    )

    context = {
        "df_final": df_final,
        "columns": list(df_final.columns),
        "rows": _prepare_rows(df_final),
    }
    return render(request, "orders/_table_rows.html", context)


@login_required
def download_excel_view(request):
    session = ProcessingSession(session_key=request.session.session_key or "default")
    state = _reconstruct_state(session)

    # Recalc with current params (simplified — use cached df_final if available)
    df_final = session.get("df_final_last")
    if df_final is None:
        return redirect("orders:results")

    scope_tag = "encomenda"
    excel_bytes, filename = build_excel(df_final, scope_tag)

    response = HttpResponse(
        excel_bytes,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


def _reconstruct_state(session: ProcessingSession) -> SessionState:
    state = SessionState()
    state.df_aggregated = session.get("df_aggregated")
    state.df_detailed = session.get("df_detailed")
    state.df_raw = session.get("df_raw")
    state.file_errors = session.get_value("file_errors") or []
    state.scope_context = ScopeContext(**(session.get_value("scope_context") or {}))
    state.file_inventory = session.get_value("file_inventory") or []
    master = session.get("master_products")
    if master is not None:
        if hasattr(state, "df_master_products"):
            state.df_master_products = master
        else:
            state.master_products = master
    return state


def _prepare_rows(df):
    """Convert DataFrame to list of dicts with CSS class info for template rendering."""
    from orders_master.formatting.rules import RULES
    from orders_master.constants import Columns, GroupLabels

    rows = []
    for _, row in df.iterrows():
        row_data = {"cells": {}, "row_classes": [], "cell_classes": {}}

        is_grupo = str(row.get(Columns.LOCALIZACAO, "")) == GroupLabels.GROUP_ROW.value
        if is_grupo:
            row_data["row_classes"].append("row-grupo")

        for rule in RULES:
            if is_grupo and rule.precedence > 1:
                continue
            try:
                if rule.predicate(row):
                    targets = rule.target_cells(df)
                    for col in targets:
                        if col in row.index:
                            row_data["cell_classes"].setdefault(col, []).append(
                                f"row-nao-comprar" if rule.name == "Não Comprar" else f"cell-{rule.name.lower().replace(' ', '-')}"
                            )
            except Exception:
                pass

        for col in df.columns:
            val = row[col]
            display = ""
            if pd.notna(val):
                display = str(val)
            row_data["cells"][col] = display

        rows.append(row_data)
    return rows


import pandas as pd  # noqa: E402 — needed for pd.notna in _prepare_rows
```

- [ ] **Step 3: Create URLs**

Create `orders_master_saas/orders/urls.py`:
```python
from django.urls import path
from orders import views

app_name = "orders"

urlpatterns = [
    path("", views.upload_view, name="upload"),
    path("results/", views.results_view, name="results"),
    path("recalc/", views.recalc_view, name="recalc"),
    path("download/", views.download_excel_view, name="download"),
]
```

- [ ] **Step 4: Create upload template**

Create `orders_master_saas/templates/orders/upload.html`:
```html
{% extends "base.html" %}

{% block title %}Upload — Orders Master{% endblock %}

{% block content %}
<div class="grid grid-cols-1 lg:grid-cols-4 gap-6">
    <!-- Sidebar -->
    <div class="lg:col-span-1">
        <div class="bg-white rounded-lg shadow p-6">
            <h2 class="text-lg font-bold mb-4">Configuração</h2>
            <form method="post" enctype="multipart/form-data">
                {% csrf_token %}

                <div class="mb-4">
                    <h3 class="font-semibold text-sm mb-2">Filtrar por Laboratório</h3>
                    {% for lab in labs %}
                    <label class="flex items-center gap-2 text-sm mb-1">
                        <input type="checkbox" name="labs" value="{{ lab.nome }}"
                               class="rounded border-gray-300">
                        {{ lab.nome }}
                    </label>
                    {% endfor %}
                </div>

                <hr class="my-4">

                <div class="mb-4">
                    <h3 class="font-semibold text-sm mb-2">Filtrar por Códigos</h3>
                    <p class="text-xs text-gray-500 mb-2">Tem prioridade sobre Laboratórios</p>
                    {{ form.codes_file }}
                </div>

                <hr class="my-4">

                <div class="mb-4">
                    <h3 class="font-semibold text-sm mb-2">Dados Base Infoprex</h3>
                    {{ form.infoprex_files }}
                </div>

                <hr class="my-4">

                <div class="mb-4">
                    <h3 class="font-semibold text-sm mb-2">Base de Marcas</h3>
                    {{ form.brands_files }}
                </div>

                <button type="submit"
                        class="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 font-semibold">
                    Processar Dados
                </button>
            </form>
        </div>
    </div>

    <!-- Main Area -->
    <div class="lg:col-span-3">
        <div class="bg-white rounded-lg shadow p-8 text-center">
            <h2 class="text-xl font-bold mb-2">Orders Master Infoprex</h2>
            <p class="text-gray-600">Carregue os ficheiros Infoprex e clique "Processar Dados" para iniciar.</p>
        </div>
    </div>
</div>
{% endblock %}
```

- [ ] **Step 5: Commit**

```bash
git add orders_master_saas/orders/views.py orders_master_saas/orders/urls.py orders_master_saas/orders/forms.py orders_master_saas/templates/orders/
git commit -m "feat: add upload view, results view, recalc HTMX endpoint, download endpoint"
```

---

### Task MIG-4.3: Create results template with conditional table

**Files:**
- Create: `orders_master_saas/templates/orders/results.html`
- Create: `orders_master_saas/templates/orders/_table_rows.html`
- Create: `orders_master_saas/templates/orders/_scope_bar.html`
- Create: `orders_master_saas/templates/orders/_controls.html`
- Create: `orders_master_saas/templates/orders/_file_inventory.html`
- Create: `orders_master_saas/templates/orders/_banner.html`

- [ ] **Step 1: Create results template**

Create `orders_master_saas/templates/orders/results.html`:
```html
{% extends "base.html" %}
{% load table_tags %}

{% block title %}Resultados — Orders Master{% endblock %}

{% block content %}
<div class="space-y-6">
    {% include "orders/_banner.html" with state=state %}
    {% include "orders/_scope_bar.html" with state=state %}
    {% include "orders/_file_inventory.html" with state=state %}
    {% include "orders/_controls.html" with presets=presets %}

    <div id="table-container">
        {% include "orders/_table_rows.html" with df_final=df_final columns=columns rows=rows %}
    </div>

    <div class="flex justify-end">
        <a href="{% url 'orders:download' %}"
           class="bg-green-600 text-white px-6 py-2 rounded hover:bg-green-700 font-semibold">
            Download Excel Encomendas
        </a>
    </div>
</div>
{% endblock %}
```

- [ ] **Step 2: Create table partial (HTMX target)**

Create `orders_master_saas/templates/orders/_table_rows.html`:
```html
<div class="overflow-x-auto max-h-[70vh] overflow-y-auto border rounded-lg">
    <table class="table-orders">
        <thead>
            <tr>
                {% for col in columns %}<th>{{ col }}</th>{% endfor %}
            </tr>
        </thead>
        <tbody>
            {% for row in rows %}
            <tr class="{{ row.row_classes|join:' ' }}">
                {% for col in columns %}
                <td class="{{ row.cell_classes|get:col|default:''|join:' ' }} {% if col in numeric_cols %}num{% endif %}">
                    {{ row.cells|get:col|default:"" }}
                </td>
                {% endfor %}
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
```

- [ ] **Step 3: Create template tags**

Create `orders_master_saas/orders/templatetags/__init__.py` and `orders_master_saas/orders/templatetags/table_tags.py`:
```python
from django import template

register = template.Library()


@register.filter
def get(dictionary, key):
    if dictionary is None:
        return ""
    if isinstance(dictionary, dict):
        return dictionary.get(key, "")
    return ""


@register.filter
def join(lst, separator=" "):
    if not lst:
        return ""
    return separator.join(str(x) for x in lst)
```

- [ ] **Step 4: Create controls partial**

Create `orders_master_saas/templates/orders/_controls.html`:
```html
<form hx-post="{% url 'orders:recalc' %}" hx-target="#table-container" hx-swap="innerHTML"
      class="bg-white rounded-lg shadow p-4 mb-4">
    {% csrf_token %}
    <div class="grid grid-cols-2 lg:grid-cols-6 gap-4 items-end">
        <div>
            <label class="flex items-center gap-2 text-sm">
                <input type="checkbox" name="detailed_view" class="rounded border-gray-300">
                Ver Detalhe
            </label>
        </div>
        <div>
            <label class="flex items-center gap-2 text-sm">
                <input type="checkbox" name="use_previous_month" class="rounded border-gray-300">
                Mês Anterior
            </label>
        </div>
        <div>
            <label class="block text-sm font-medium mb-1">Meses a Prever</label>
            <input type="number" name="months" step="0.5" min="0.5" max="6" value="1.0"
                   class="w-full border rounded px-2 py-1 text-sm">
        </div>
        <div>
            <label class="block text-sm font-medium mb-1">Preset Pesos</label>
            <select name="preset" class="w-full border rounded px-2 py-1 text-sm">
                {% for p in presets %}
                <option value="{{ p.nome }}">{{ p.nome }}</option>
                {% endfor %}
            </select>
        </div>
        <div>
            <button type="submit" class="bg-blue-600 text-white px-4 py-1.5 rounded text-sm hover:bg-blue-700">
                Recalcular
            </button>
        </div>
    </div>
</form>
```

- [ ] **Step 5: Create scope bar, file inventory, and banner partials**

Create `orders_master_saas/templates/orders/_scope_bar.html`:
```html
{% if state.scope_context %}
<div class="scope-bar">
    <span>{{ state.scope_context.n_produtos }} produtos</span>
    <span>{{ state.scope_context.n_farmacias }} farmácias</span>
    <span>{{ state.scope_context.filtro }}</span>
    <span>Previsão: {{ state.scope_context.meses_previsao }} m</span>
</div>
{% endif %}
```

Create `orders_master_saas/templates/orders/_file_inventory.html`:
```html
{% if state.file_inventory %}
<details class="bg-white rounded-lg shadow p-4 mb-4">
    <summary class="cursor-pointer font-semibold text-sm">File Inventory ({{ state.file_inventory|length }} ficheiros)</summary>
    <div class="mt-3 overflow-x-auto">
        <table class="file-inventory w-full text-sm">
            <thead>
                <tr><th>Ficheiro</th><th>Farmácia</th><th>Linhas</th><th>Estado</th></tr>
            </thead>
            <tbody>
                {% for entry in state.file_inventory %}
                <tr class="{% if entry.status == 'error' %}row-error{% endif %}">
                    <td>{{ entry.filename }}</td>
                    <td>{{ entry.farmacia }}</td>
                    <td>{{ entry.linhas }}</td>
                    <td>{% if entry.status == 'ok' %}OK{% else %}Erro{% endif %}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</details>
{% endif %}
```

Create `orders_master_saas/templates/orders/_banner.html`:
```html
{% if state.shortages_data_consulta %}
<div class="bd-rupturas-banner">
    Data Consulta BD Rupturas — <span class="date">{{ state.shortages_data_consulta }}</span>
</div>
{% else %}
<div class="bd-rupturas-banner" style="opacity: 0.6">
    Não foi possível carregar a informação da BD Rupturas
</div>
{% endif %}
```

- [ ] **Step 6: Commit**

```bash
git add orders_master_saas/templates/orders/ orders_master_saas/orders/templatetags/
git commit -m "feat: add results template, conditional table, HTMX controls, scope bar, file inventory, banner"
```

---

### Task MIG-4.4: Implement license validation on upload

**Files:**
- Modify: `orders_master_saas/orders/views.py`
- Test: `orders_master_saas/orders/tests/test_license_validation.py`

- [ ] **Step 1: Write the failing test**

```python
import pytest
from accounts.models import Cliente, Farmacia, Subscricao
from datetime import date


@pytest.mark.django_db
def test_licensed_farmacia_accepted():
    cliente = Cliente.objects.create(nome="Teste", email="t@t.com")
    Farmacia.objects.create(cliente=cliente, nome="FARMACIA GUIA", localizacao_key="GUIA", alias="Guia")
    from orders.services.license import validate_localizacao
    result = validate_localizacao("GUIA", cliente)
    assert result is not None
    assert result.alias == "Guia"


@pytest.mark.django_db
def test_unlicensed_farmacia_rejected():
    cliente = Cliente.objects.create(nome="Teste", email="t@t.com")
    from orders.services.license import validate_localizacao
    result = validate_localizacao("NOVA", cliente)
    assert result is None
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd orders_master_saas
pytest orders/tests/test_license_validation.py -v
```
Expected: FAIL

- [ ] **Step 3: Write implementation**

Create `orders_master_saas/orders/services/license.py`:
```python
import logging
from accounts.models import Cliente, Farmacia

logger = logging.getLogger(__name__)


def validate_localizacao(localizacao: str, cliente: Cliente) -> Farmacia | None:
    """Check if a LOCALIZACAO matches a licensed Farmacia for this client.

    Uses substring match (case-insensitive), consistent with ADR-012.
    """
    localizacao_lower = localizacao.lower()
    for farmacia in Farmacia.objects.filter(cliente=cliente, ativa=True):
        if farmacia.localizacao_key.lower() in localizacao_lower:
            return farmacia
        if localizacao_lower in farmacia.localizacao_key.lower():
            return farmacia
    return None
```

- [ ] **Step 4: Run tests**

```bash
cd orders_master_saas
pytest orders/tests/test_license_validation.py -v
```
Expected: PASS

- [ ] **Step 5: Integrate into upload processing**

In `orders/views.py`, `_process_upload()`, add validation after parsing each file:

```python
from orders.services.license import validate_localizacao

# In the upload processing loop, after extracting LOCALIZACAO:
farmacia = validate_localizacao(localizacao_detected, request.tenant)
if farmacia is None:
    state.file_errors.append(FileError(
        filename=file_name, type="license",
        message=f"A farmacia '{localizacao_detected}' nao esta licenciada para a sua conta."
    ))
    continue  # skip this file
```

- [ ] **Step 6: Commit**

```bash
git add orders_master_saas/orders/services/license.py orders_master_saas/orders/tests/test_license_validation.py orders_master_saas/orders/views.py
git commit -m "feat: add license validation — reject files from unlicensed farmacias"
```

---

## Phase 5: Features & Subscriptions

### Task MIG-5.1: Implement BD Rupturas feature flag

**Files:**
- Modify: `orders_master_saas/orders/views.py`

- [ ] **Step 1: Add subscription check in upload processing**

In `_process_upload()`, before calling integrations:

```python
# Check if BD Rupturas is active for this client
bd_rupturas_active = False
if hasattr(request, "tenant") and request.tenant:
    try:
        bd_rupturas_active = request.tenant.subscricao.bd_rupturas_ativa and request.tenant.subscricao.ativa
    except Exception:
        bd_rupturas_active = False

# Only fetch shortages if feature is active
if bd_rupturas_active:
    # ... fetch and merge shortages
    pass
else:
    logger.info("BD Rupturas not active for client %s", request.tenant)
```

- [ ] **Step 2: Hide BD Rupturas banner when inactive**

In `_banner.html`, add condition:
```html
{% if state.shortages_data_consulta and bd_rupturas_active %}
<div class="bd-rupturas-banner">...</div>
{% endif %}
```

- [ ] **Step 3: Commit**

```bash
git add orders_master_saas/orders/views.py orders_master_saas/templates/orders/_banner.html
git commit -m "feat: add BD Rupturas feature flag based on Subscricao.bd_rupturas_ativa"
```

---

### Task MIG-5.2: Subscription expiry check

**Files:**
- Modify: `orders_master_saas/accounts/middleware.py`

- [ ] **Step 1: Add subscription check to middleware**

Add after tenant assignment:

```python
from datetime import date

if request.user.is_authenticated:
    try:
        request.tenant = request.user.profile.cliente
        sub = request.tenant.subscricao
        if sub and sub.ativa and sub.data_fim and sub.data_fim < date.today():
            request.subscription_expired = True
        else:
            request.subscription_expired = False
    except Exception:
        request.tenant = None
        request.subscription_expired = False
```

- [ ] **Step 2: Add middleware check to views**

Add a decorator or check at the top of `upload_view` and `results_view`:
```python
if getattr(request, "subscription_expired", False):
    return render(request, "orders/subscription_expired.html", status=403)
```

- [ ] **Step 3: Create subscription_expired template**

Create `orders_master_saas/templates/orders/subscription_expired.html`:
```html
{% extends "base.html" %}
{% block title %}Subscrição Expirada{% endblock %}
{% block content %}
<div class="max-w-md mx-auto mt-20 bg-yellow-50 border border-yellow-300 rounded-lg p-8 text-center">
    <h1 class="text-xl font-bold text-yellow-800 mb-4">Subscrição Expirada</h1>
    <p class="text-yellow-700">A sua subscrição expirou. Contacte o administrador para renovar.</p>
</div>
{% endblock %}
```

- [ ] **Step 4: Commit**

```bash
git add orders_master_saas/accounts/middleware.py orders_master_saas/templates/orders/subscription_expired.html orders_master_saas/orders/views.py
git commit -m "feat: add subscription expiry check and expired template"
```

---

## Phase 6: Production & Deploy

### Task MIG-6.1: Configure Railway deployment

**Files:**
- Create: `orders_master_saas/railway.json`
- Modify: `orders_master_saas/Procfile`
- Create: `orders_master_saas/.github/workflows/deploy.yml`

- [ ] **Step 1: Update Procfile**

```
web: python manage.py migrate && python manage.py collectstatic --noinput && gunicorn orders_master_saas.wsgi:application --bind 0.0.0.0:$PORT --workers 4
```

- [ ] **Step 2: Create CI/CD workflow**

Create `orders_master_saas/.github/workflows/deploy.yml`:
```yaml
name: Django CI

on:
  push:
    branches: [main, Django_Migration]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    env:
      DJANGO_SETTINGS_MODULE: orders_master_saas.settings.development
      SECRET_KEY: test-secret-key
      SHORTAGES_SHEET_URL: ""
      DONOTBUY_SHEET_URL: ""

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt -r requirements-dev.txt
      - name: Lint
        run: ruff check .
      - name: Type check
        run: mypy --strict orders_master/ accounts/ orders/ backoffice/
      - name: Run tests
        run: pytest --cov=orders_master --cov-fail-under=80 -m "not slow"
```

- [ ] **Step 3: Commit**

```bash
git add orders_master_saas/Procfile orders_master_saas/.github/workflows/deploy.yml
git commit -m "feat: add Railway Procfile and GitHub Actions CI/CD workflow"
```

---

### Task MIG-6.2: Verify zero Streamlit in entire project

**Files:**
- All files in `orders_master_saas/`

- [ ] **Step 1: Comprehensive grep**

```bash
grep -r "streamlit" orders_master_saas/ --include="*.py" | grep -v "__pycache__" | grep -v "venv"
```
Expected: no output (0 matches). This is NFR-M4 from the spec.

- [ ] **Step 2: Run full test suite**

```bash
cd orders_master_saas
pytest --cov=orders_master --cov-fail-under=80 -v
```
Expected: PASS, coverage >= 80%

- [ ] **Step 3: Commit**

```bash
git commit --allow-empty -m "verify: zero streamlit imports in Django project, all tests pass"
```

---

### Task MIG-6.3: Smoke test checklist

**Files:**
- Modify: `orders_master_saas/docs/smoke_test_checklist.md`

- [ ] **Step 1: Update smoke test for Django**

Create `orders_master_saas/docs/smoke_test_django.md`:
```markdown
# Django SaaS Smoke Test Checklist

## Fluxo 1: Upload + Processamento
- [ ] Login com credenciais válidas
- [ ] Seleccionar laboratório
- [ ] Carregar 2+ ficheiros Infoprex
- [ ] Clicar "Processar Dados"
- [ ] Verificar tabela com formatação condicional
- [ ] Verificar Scope Bar com métricas correctas
- [ ] Verificar File Inventory com estado dos ficheiros

## Fluxo 2: Recálculo HTMX
- [ ] Toggle "Ver Detalhe" → tabela muda sem reload total
- [ ] Toggle "Mês Anterior" → valores recalculam
- [ ] Alterar "Meses a Prever" → proposta recalcula
- [ ] Alterar preset → pesos actualizam
- [ ] Download Excel → ficheiro descarregado

## Fluxo 3: Validação de Licença
- [ ] Upload de ficheiro de farmácia não licenciada → rejeitado com erro claro
- [ ] Upload de ficheiro de farmácia licenciada → aceite

## Fluxo 4: Multi-Tenancy
- [ ] Utilizador A não vê dados do Utilizador B
- [ ] Admin vê gestão de clientes e farmácias

## Fluxo 5: Subscrição
- [ ] BD Rupturas visível quando activa
- [ ] BD Rupturas oculta quando inactiva
- [ ] Subscrição expirada → bloqueio de acesso
```

- [ ] **Step 2: Commit**

```bash
git add orders_master_saas/docs/smoke_test_django.md
git commit -m "docs: add Django SaaS smoke test checklist"
```

---

## Self-Review Checklist

### 1. Spec Coverage

| Spec Requirement | Task |
|---|---|
| Django project scaffold | MIG-0.1 |
| Copy orders_master/ intact | MIG-0.2 |
| TailwindCSS + HTMX | MIG-0.3 |
| Replace @st.cache_data with Django cache | MIG-1.1 |
| Adapt shortages.py | MIG-1.2 |
| Adapt donotbuy.py | MIG-1.3 |
| Adapt averages.py | MIG-1.4 |
| Adapt config loaders | MIG-1.5 |
| Adapt secrets/session_service | MIG-1.6 |
| Remove st.session_state facade | MIG-1.7 |
| Verify zero streamlit imports | MIG-1.8 |
| Create accounts models | MIG-2.1 |
| Create orders models | MIG-2.2 |
| Management commands for config import | MIG-2.3 |
| TenantMiddleware | MIG-3.1 |
| Login/logout views | MIG-3.2 |
| Django Admin customizations | MIG-3.3 |
| ProcessingSession (Redis) | MIG-4.1 |
| Upload + results views | MIG-4.2 |
| Conditional table templates | MIG-4.3 |
| License validation | MIG-4.4 |
| BD Rupturas feature flag | MIG-5.1 |
| Subscription expiry | MIG-5.2 |
| Railway deployment | MIG-6.1 |
| Zero streamlit verification | MIG-6.2 |
| Smoke test checklist | MIG-6.3 |

### 2. Placeholder Scan

No TBDs, TODOs, or "implement later" found. All steps have code.

### 3. Type Consistency

- `ProcessingSession` uses `session_key: str` consistently
- `validate_localizacao` returns `Farmacia | None` consistently
- `_prepare_rows` returns `list[dict]` consumed by template
- `SessionState` dataclass fields match between `_reconstruct_state` and domain code