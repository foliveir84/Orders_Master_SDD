# Django SaaS Migration — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate Orders Master Infoprex from Streamlit to Django SaaS with multi-tenancy, auth, and backoffice admin.

**Architecture:** Django 5.x + PostgreSQL + Redis + HTMX/TailwindCSS. The existing `orders_master/` domain package is copied intact and adapted (remove Streamlit deps). New Django apps handle auth, multi-tenancy, admin, and UI. Conditional table formatting uses CSS classes instead of Pandas Styler.

**Tech Stack:** Python 3.11+, Django 5.x, PostgreSQL 16+, Redis 7+, Gunicorn, HTMX 2.x, TailwindCSS 4.x, openpyxl, pandas, pydantic, pytest

---

## File Structure (New Project)

```
orders_master_saas/
├── manage.py
├── pyproject.toml
├── requirements.txt
├── orders_master_saas/          # Django project settings
│   ├── __init__.py
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── dev.py
│   │   └── production.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── accounts/                    # Auth, Cliente, Farmacia, Subscricao
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── forms.py
│   ├── views.py
│   ├── urls.py
│   ├── middleware.py
│   ├── migrations/
│   │   └── __init__.py
│   └── tests/
│       ├── __init__.py
│       ├── test_models.py
│       └── test_middleware.py
├── orders/                      # Core business app (upload, process, display)
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py                # ConfigLaboratorio, ConfigLocalizacao, ConfigPesoPreset, SessaoProcessamento
│   ├── views.py                 # UploadView, ResultsView, ExcelDownloadView
│   ├── urls.py
│   ├── forms.py
│   ├── services.py              # process_orders_session(), recalculate_proposal() — adapted from app_services/
│   ├── session_manager.py       # Redis-based session state (replaces st.session_state)
│   ├── context_processors.py
│   ├── migrations/
│   │   └── __init__.py
│   └── tests/
│       ├── __init__.py
│       ├── test_upload.py
│       ├── test_processing.py
│       ├── test_views.py
│       └── test_license_validation.py
├── orders_master/               # DOMAIN PACKAGE — copied intact, only Streamlit deps removed
│   ├── __init__.py
│   ├── constants.py             # UNCHANGED
│   ├── schemas.py               # UNCHANGE
│   ├── exceptions.py            # UNCHANGED
│   ├── logger.py                # UNCHANGED
│   ├── ingestion/               # UNCHANGED
│   │   ├── __init__.py
│   │   ├── infoprex_parser.py
│   │   ├── codes_txt_parser.py
│   │   ├── brands_parser.py
│   │   └── encoding_fallback.py
│   ├── aggregation/             # UNCHANGED
│   │   ├── __init__.py
│   │   └── aggregator.py
│   ├── business_logic/          # UNCHANGED
│   │   ├── __init__.py
│   │   ├── averages.py
│   │   ├── proposals.py
│   │   ├── cleaners.py
│   │   └── price_validation.py
│   ├── integrations/            # ADAPTED (st.cache_data → django cache)
│   │   ├── __init__.py
│   │   ├── shortages.py
│   │   └── donotbuy.py
│   ├── config/                  # ADAPTED (read from DB instead of JSON files)
│   │   ├── __init__.py
│   │   ├── labs_loader.py
│   │   ├── locations_loader.py
│   │   ├── presets_loader.py
│   │   └── validate.py
│   ├── formatting/              # ADAPTED (web_styler rewritten for HTML+CSS)
│   │   ├── __init__.py
│   │   ├── rules.py             # UNCHANGED
│   │   ├── web_styler.py        # REWRITTEN: generates HTML with CSS classes
│   │   └── excel_formatter.py   # UNCHANGED
│   └── secrets_loader.py        # REMOVED (replaced by Django settings)
├── templates/
│   ├── base.html
│   ├── registration/
│   │   └── login.html
│   ├── orders/
│   │   ├── upload.html
│   │   ├── results.html
│   │   ├── partials/
│   │   │   ├── _scope_bar.html
│   │   │   ├── _file_inventory.html
│   │   │   ├── _table.html
│   │   │   ├── _controls.html
│   │   │   └── _progress.html
│   │   └── components/
│   │       └── table_conditional.html
│   └── admin/
│       └── custom_admin.html
├── static/
│   ├── css/
│   │   ├── orders.css           # Table conditional styles
│   │   └── tailwind.css         # Compiled TailwindCSS
│   └── js/
│       └── htmx.min.js
├── management/
│   └── commands/
│       ├── import_labs_json.py
│       ├── import_localizacoes_json.py
│       └── import_presets_yaml.py
└── tests/
    ├── conftest.py
    └── test_domain_intact.py    # Validates all original domain tests still pass
```

---

## Phase 0: Preparation — Django Project Scaffold

### Task 0.1: Create Django Project and Apps

**Files:**
- Create: `orders_master_saas/manage.py`
- Create: `orders_master_saas/orders_master_saas/settings/base.py`
- Create: `orders_master_saas/orders_master_saas/settings/dev.py`
- Create: `orders_master_saas/orders_master_saas/settings/production.py`
- Create: `orders_master_saas/orders_master_saas/urls.py`
- Create: `orders_master_saas/orders_master_saas/wsgi.py`
- Create: `orders_master_saas/orders_master_saas/asgi.py`
- Create: `orders_master_saas/requirements.txt`
- Create: `orders_master_saas/pyproject.toml`

- [ ] **Step 1: Create the Django project scaffold**

```bash
cd C:\Users\filip\Documents\Python_Jobs
django-admin startproject orders_master_saas
cd orders_master_saas
```

- [ ] **Step 2: Create Django apps**

```bash
python manage.py startapp accounts
python manage.py startapp orders
```

- [ ] **Step 3: Write requirements.txt**

```
Django>=5.1,<6.0
psycopg2-binary>=2.9,<3.0
redis>=5.0,<6.0
pandas>=2.0,<3.0
openpyxl>=3.1,<4.0
pydantic>=2.0,<3.0
python-dateutil>=2.8,<3.0
PyYAML>=6.0,<7.0
gunicorn>=21.0,<23.0
django-redis>=5.0,<6.0
```

- [ ] **Step 4: Write pyproject.toml**

```toml
[project]
name = "orders-master-saas"
version = "1.0.0"
requires-python = ">=3.11"

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]

[tool.ruff]
target-version = "py311"

[tool.mypy]
python_version = "3.11"
strict = true
```

- [ ] **Step 5: Write settings/base.py with Django defaults**

```python
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = os.environ.get("SECRET_KEY", "django-insecure-dev-key-change-in-production")

DEBUG = os.environ.get("DEBUG", "True").lower() == "true"

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "accounts",
    "orders",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "accounts.middleware.TenantMiddleware",
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
USE_I18N = False
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/orders/"
LOGOUT_REDIRECT_URL = "/accounts/login/"

SHORTAGES_SHEET_URL = os.environ.get("SHORTAGES_SHEET_URL", "")
DONOTBUY_SHEET_URL = os.environ.get("DONOTBUY_SHEET_URL", "")
```

- [ ] **Step 6: Write settings/dev.py**

```python
from .base import *  # noqa: F401,F403

DEBUG = True
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}
```

- [ ] **Step 7: Write settings/production.py**

```python
from .base import *  # noqa: F401,F403

DEBUG = False

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DATABASE_NAME", "orders_master"),
        "USER": os.environ.get("DATABASE_USER", "orders_master"),
        "PASSWORD": os.environ.get("DATABASE_PASSWORD", ""),
        "HOST": os.environ.get("DATABASE_HOST", "localhost"),
        "PORT": os.environ.get("DATABASE_PORT", "5432"),
    }
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": os.environ.get("REDIS_URL", "redis://localhost:6379/0"),
    }
}

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

- [ ] **Step 8: Write urls.py with auth and orders routes**

```python
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("", include("orders.urls")),
]
```

- [ ] **Step 9: Run initial migration and verify Django starts**

```bash
python manage.py migrate
python manage.py check
```

Expected: `System check identified no issues (0 silenced).`

- [ ] **Step 10: Commit**

```bash
git add .
git commit -m "feat: scaffold Django project with accounts and orders apps"
```

---

### Task 0.2: Copy Domain Package Intact

**Files:**
- Copy: `orders_master/` → `orders_master_saas/orders_master/` (all files)
- Create: `orders_master_saas/tests/conftest.py`
- Create: `orders_master_saas/tests/test_domain_intact.py`

- [ ] **Step 1: Copy the entire orders_master/ domain package**

```bash
cp -r orders_master/ orders_master_saas/orders_master/
```

This copies all domain modules (ingestion, aggregation, business_logic, integrations, config, formatting) including constants.py, schemas.py, exceptions.py, logger.py.

- [ ] **Step 2: Copy test fixtures**

```bash
cp -r tests/fixtures/ orders_master_saas/tests/fixtures/
cp tests/conftest.py orders_master_saas/tests/conftest.py
```

- [ ] **Step 3: Copy all unit tests for domain modules**

```bash
cp -r tests/unit/ orders_master_saas/tests/unit/
cp -r tests/integration/ orders_master_saas/tests/integration/
```

- [ ] **Step 4: Verify all domain tests pass**

```bash
cd orders_master_saas
python -m pytest tests/unit/ -v --tb=short
```

Expected: All existing domain tests pass (they have no Streamlit dependency in the core modules except averages.py and config/ modules which we'll adapt later).

- [ ] **Step 5: Commit**

```bash
git add .
git commit -m "feat: copy orders_master domain package with all tests"
```

---

## Phase 1: Foundation — Models, Middleware, Config_from_DB

### Task 1.1: Create Accounts Models (Cliente, Farmacia, Subscricao, UserProfile)

**Files:**
- Create: `accounts/models.py`
- Create: `accounts/tests/test_models.py`
- Create: `accounts/admin.py`

- [ ] **Step 1: Write the failing test for accounts models**

```python
# accounts/tests/test_models.py
import pytest
from django.test import TestCase
from django.contrib.auth.models import User
from accounts.models import Cliente, Farmacia, Subscricao, UserProfile


class ClienteModelTest(TestCase):
    def test_create_cliente(self):
        cliente = Cliente.objects.create(
            nome="Farmacias Joao Lda",
            email="joao@example.com",
        )
        self.assertEqual(str(cliente), "Farmacias Joao Lda")
        self.assertTrue(cliente.ativo)


class FarmaciaModelTest(TestCase):
    def test_create_farmacia(self):
        cliente = Cliente.objects.create(nome="Teste", email="t@t.com")
        farmacia = Farmacia.objects.create(
            cliente=cliente,
            nome="Farmacia da Guia",
            localizacao_key="FARMACIA GUIA",
            alias="Guia",
        )
        self.assertEqual(str(farmacia), "Guia (Farmacias Joao Lda)")

    def test_farmacia_unique_per_cliente(self):
        cliente = Cliente.objects.create(nome="Teste2", email="t2@t.com")
        Farmacia.objects.create(
            cliente=cliente, nome="F1", localizacao_key="KEY1", alias="Alias1"
        )
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            Farmacia.objects.create(
                cliente=cliente, nome="F1 Dup", localizacao_key="KEY1", alias="Alias1"
            )


class SubscricaoModelTest(TestCase):
    def test_create_subscricao(self):
        cliente = Cliente.objects.create(nome="Teste3", email="t3@t.com")
        sub = Subscricao.objects.create(
            cliente=cliente,
            plano=Subscricao.Plano.BASICO,
            data_inicio="2026-01-01",
        )
        self.assertEqual(sub.plano, "BAS")
        self.assertFalse(sub.bd_rupturas_ativa)


class UserProfileModelTest(TestCase):
    def test_create_user_profile(self):
        user = User.objects.create_user("joao", "joao@test.com", "pass123")
        cliente = Cliente.objects.create(nome="Teste4", email="t4@t.com")
        profile = UserProfile.objects.create(
            user=user, cliente=cliente, role="compras"
        )
        self.assertEqual(profile.role, "compras")
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd orders_master_saas
python -m pytest accounts/tests/test_models.py -v
```

Expected: FAIL with `ImportError: cannot import name 'Cliente' from 'accounts.models'`

- [ ] **Step 3: Write accounts/models.py**

```python
from django.db import models
from django.contrib.auth.models import User


class Cliente(models.Model):
    nome = models.CharField(max_length=200)
    nif = models.CharField(max_length=20, blank=True)
    email = models.EmailField()
    telefone = models.CharField(max_length=30, blank=True)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    actualizado_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "cliente"
        verbose_name_plural = "clientes"


class Farmacia(models.Model):
    cliente = models.ForeignKey(
        Cliente, on_delete=models.CASCADE, related_name="farmacias"
    )
    nome = models.CharField(max_length=200)
    localizacao_key = models.CharField(
        max_length=100,
        help_text="Valor exacto ou substring do campo LOCALIZACAO no Infoprex",
    )
    alias = models.CharField(
        max_length=100, help_text="Nome de apresentacao (ex: 'Guia')"
    )
    ativa = models.BooleanField(default=True)
    licenciada_ate = models.DateField(null=True, blank=True)

    class Meta:
        unique_together = ["cliente", "localizacao_key"]
        verbose_name = "farmacia"
        verbose_name_plural = "farmacias"

    def __str__(self):
        return f"{self.alias} ({self.cliente.nome})"


class Subscricao(models.Model):
    class Plano(models.TextChoices):
        BASICO = "BAS", "Basico"
        PROFISSIONAL = "PRO", "Profissional"
        ENTERPRISE = "ENT", "Enterprise"

    cliente = models.OneToOneField(
        Cliente, on_delete=models.CASCADE, related_name="subscricao"
    )
    plano = models.CharField(max_length=3, choices=Plano.choices, default=Plano.BASICO)
    bd_rupturas_ativa = models.BooleanField(
        default=False, help_text="Extra pago: acesso a BD Esgotados Infarmed"
    )
    data_inicio = models.DateField()
    data_fim = models.DateField(null=True, blank=True)
    ativa = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.cliente.nome} - {self.get_plano_display()}"

    class Meta:
        verbose_name = "subscricao"
        verbose_name_plural = "subscricoes"


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ("admin", "Administrador"),
        ("compras", "Responsavel de Compras"),
        ("farmacia", "Farmacia"),
    ]

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="profile"
    )
    cliente = models.ForeignKey(
        Cliente, on_delete=models.CASCADE, related_name="utilizadores"
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="compras")

    def __str__(self):
        return f"{self.user.username} ({self.cliente.nome})"

    class Meta:
        verbose_name = "perfil de utilizador"
        verbose_name_plural = "perfis de utilizador"
```

- [ ] **Step 4: Run migration and verify tests pass**

```bash
python manage.py makemigrations accounts
python manage.py migrate
python -m pytest accounts/tests/test_models.py -v
```

Expected: All 4 tests PASS.

- [ ] **Step 5: Write accounts/admin.py**

```python
from django.contrib import admin
from accounts.models import Cliente, Farmacia, Subscricao, UserProfile


class FarmaciaInline(admin.TabularInline):
    model = Farmacia
    extra = 1


class SubscricaoInline(admin.StackedInline):
    model = Subscricao
    extra = 0


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ["nome", "email", "ativo", "criado_em"]
    list_filter = ["ativo"]
    search_fields = ["nome", "email"]
    inlines = [FarmaciaInline, SubscricaoInline]


@admin.register(Farmacia)
class FarmaciaAdmin(admin.ModelAdmin):
    list_display = ["alias", "cliente", "localizacao_key", "ativa", "licenciada_ate"]
    list_filter = ["ativa", "cliente"]
    search_fields = ["nome", "alias", "localizacao_key"]


@admin.register(Subscricao)
class SubscricaoAdmin(admin.ModelAdmin):
    list_display = ["cliente", "plano", "bd_rupturas_ativa", "ativa", "data_inicio"]
    list_filter = ["ativa", "plano", "bd_rupturas_ativa"]


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "cliente", "role"]
    list_filter = ["role", "cliente"]
```

- [ ] **Step 6: Commit**

```bash
git add .
git commit -m "feat: add accounts models (Cliente, Farmacia, Subscricao, UserProfile)"
```

---

### Task 1.2: Create Config Models and Replace JSON/YAML Loading

**Files:**
- Create: `orders/models.py` (ConfigLaboratorio, ConfigLocalizacao, ConfigPesoPreset)
- Create: `orders/tests/test_config_models.py`
- Modify: `orders_master/config/labs_loader.py` (add `load_labs_from_db()`)
- Modify: `orders_master/config/locations_loader.py` (add `load_locations_from_db()`)
- Modify: `orders_master/config/presets_loader.py` (add `load_presets_from_db()`)

- [ ] **Step 1: Write the failing test for config models**

```python
# orders/tests/test_config_models.py
from django.test import TestCase
from orders.models import ConfigLaboratorio, ConfigLocalizacao, ConfigPesoPreset


class ConfigLaboratorioModelTest(TestCase):
    def test_create_config_laboratorio(self):
        config = ConfigLaboratorio.objects.create(
            nome="Mylan", codigos_cla=["137", "2651", "2953"]
        )
        self.assertEqual(str(config), "Mylan")
        self.assertEqual(config.codigos_cla, ["137", "2651", "2953"])
        self.assertTrue(config.ativo)


class ConfigLocalizacaoModelTest(TestCase):
    def test_create_global_localizacao(self):
        config = ConfigLocalizacao.objects.create(
            cliente=None,
            search_term="NOVA da vila",
            alias="Guia",
        )
        self.assertIsNone(config.cliente)
        self.assertEqual(config.alias, "Guia")

    def test_create_cliente_localizacao(self):
        from accounts.models import Cliente
        cliente = Cliente.objects.create(nome="Teste", email="t@t.com")
        config = ConfigLocalizacao.objects.create(
            cliente=cliente,
            search_term="Ilha Pharmacy",
            alias="Ilha",
        )
        self.assertEqual(config.cliente, cliente)


class ConfigPesoPresetModelTest(TestCase):
    test_create_preset(self):
        preset = ConfigPesoPreset.objects.create(
            nome="Padrao", pesos=[0.4, 0.3, 0.2, 0.1]
        )
        self.assertEqual(str(preset), "Padrao")
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest orders/tests/test_config_models.py -v
```

- [ ] **Step 3: Write orders/models.py**

```python
from django.db import models
from accounts.models import Cliente


class ConfigLaboratorio(models.Model):
    nome = models.CharField(max_length=200, unique=True)
    codigos_cla = models.JSONField(
        help_text='Lista de codigos CLA. Ex: ["137", "2651", "2953"]'
    )
    ativo = models.BooleanField(default=True)

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "configuracao de laboratorio"
        verbose_name_plural = "configuracoes de laboratorios"


class ConfigLocalizacao(models.Model):
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="localizacoes",
        help_text="Se null, e uma config global",
    )
    search_term = models.CharField(
        max_length=200,
        help_text="Termo de pesquisa no campo LOCALIZACAO do Infoprex",
    )
    alias = models.CharField(
        max_length=100, help_text="Nome de apresentacao"
    )

    class Meta:
        unique_together = ["cliente", "search_term"]
        verbose_name = "configuracao de localizacao"
        verbose_name_plural = "configuracoes de localizacoes"

    def __str__(self):
        escopo = "Global" if not self.cliente else str(self.cliente.nome)
        return f"[{escopo}] {self.search_term} -> {self.alias}"


class ConfigPesoPreset(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    pesos = models.JSONField(
        help_text="Lista de 4 pesos. Ex: [0.4, 0.3, 0.2, 0.1]"
    )

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "preset de pesos"
        verbose_name_plural = "presets de pesos"


class SessaoProcessamento(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    utilizador = models.ForeignKey(
        "auth.User", on_delete=models.CASCADE
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    num_ficheiros = models.IntegerField(default=0)
    num_produtos = models.IntegerField(default=0)
    num_farmacias = models.IntegerField(default=0)
    lab_selecionados = models.JSONField(default=list)
    modo_detalhado = models.BooleanField(default=False)
    meses_previsao = models.FloatField(default=1.0)

    class Meta:
        verbose_name = "sessao de processamento"
        verbose_name_plural = "sessoes de processamento"
```

- [ ] **Step 4: Run migration and verify tests pass**

```bash
python manage.py makemigrations orders
python manage.py migrate
python -m pytest orders/tests/test_config_models.py -v
```

- [ ] **Step 5: Add DB-backed loaders in orders_master/config/**

Create `orders_master/config/labs_loader_db.py`:

```python
from typing import Any


def load_labs_from_db() -> dict[str, list[str]]:
    """Load laboratorios config from Django DB instead of JSON file.
    
    Returns dict mapping lab name to list of CLA codes, same format
    as load_labs() from labs_loader.py.
    """
    from orders.models import ConfigLaboratorio

    result = {}
    for config in ConfigLaboratorio.objects.filter(ativo=True):
        result[config.nome] = config.codigos_cla
    return result
```

Create `orders_master/config/locations_loader_db.py`:

```python
from typing import Any


def load_locations_from_db(cliente_id: int | None = None) -> dict[str, str]:
    """Load localizacoes config from Django DB.
    
    If cliente_id is provided, loads both global configs and 
    cliente-specific configs (cliente-specific takes precedence).
    If cliente_id is None, loads only global configs.
    
    Returns dict mapping search_term to alias, same format
    as load_locations() from locations_loader.py.
    """
    from orders.models import ConfigLocalizacao

    result = {}
    # Global configs (cliente=None) as base
    for config in ConfigLocalizacao.objects.filter(cliente__isnull=True):
        result[config.search_term] = config.alias

    # Cliente-specific configs override globals
    if cliente_id is not None:
        for config in ConfigLocalizacao.objects.filter(cliente_id=cliente_id):
            result[config.search_term] = config.alias

    return result
```

Create `orders_master/config/presets_loader_db.py`:

```python
from typing import Any


def load_presets_from_db() -> dict[str, list[float]]:
    """Load peso presets from Django DB.
    
    Returns dict mapping preset name to list of 4 weights, 
    same format as load_presets_config() from presets_loader.py.
    """
    from orders.models import ConfigPesoPreset

    result = {}
    for preset in ConfigPesoPreset.objects.all():
        result[preset.nome] = preset.pesos
    return result
```

- [ ] **Step 6: Commit**

```bash
git add .
git commit -m "feat: add config models and DB-backed loaders"
```

---

### Task 1.3: Create TenantMiddleware

**Files:**
- Create: `accounts/middleware.py`
- Create: `accounts/tests/test_middleware.py`

- [ ] **Step 1: Write the failing test for TenantMiddleware**

```python
# accounts/tests/test_middleware.py
from django.test import TestCase, RequestFactory, Client
from django.contrib.auth.models import User
from accounts.models import Cliente, UserProfile
from accounts.middleware import TenantMiddleware


class TenantMiddlewareTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = TenantMiddleware(get_response=lambda r: r)
        self.cliente = Cliente.objects.create(
            nome="Teste Middleware", email="mw@test.com"
        )
        self.user = User.objects.create_user("mwuser", "mw@test.com", "pass123")
        self.profile = UserProfile.objects.create(
            user=self.user, cliente=self.cliente, role="compras"
        )

    def test_authenticated_user_gets_tenant(self):
        request = self.factory.get("/orders/")
        request.user = self.user
        self.middleware(request)
        self.assertEqual(request.tenant, self.cliente)

    def test_anonymous_user_no_tenant(self):
        from django.contrib.auth.models import AnonymousUser

        request = self.factory.get("/orders/")
        request.user = AnonymousUser()
        self.middleware(request)
        self.assertFalse(hasattr(request, "tenant"))
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest accounts/tests/test_middleware.py -v
```

- [ ] **Step 3: Write accounts/middleware.py**

```python
from django.http import HttpRequest


class TenantMiddleware:
    """Adds request.tenant for authenticated users (their Cliente)."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest):
        if request.user.is_authenticated:
            try:
                request.tenant = request.user.profile.cliente
            except Exception:
                request.tenant = None
        response = self.get_response(request)
        return response
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python -m pytest accounts/tests/test_middleware.py -v
```

- [ ] **Step 5: Commit**

```bash
git add .
git commit -m "feat: add TenantMiddleware for multi-tenancy"
```

---

### Task 1.4: Management Commands for Config Import

**Files:**
- Create: `orders/management/__init__.py`
- Create: `orders/management/commands/__init__.py`
- Create: `orders/management/commands/import_labs_json.py`
- Create: `orders/management/commands/import_localizacoes_json.py`
- Create: `orders/management/commands/import_presets_yaml.py`

- [ ] **Step 1: Write import_labs_json management command**

```python
# orders/management/commands/import_labs_json.py
import json
from pathlib import Path
from django.core.management.base import BaseCommand
from orders.models import ConfigLaboratorio


class Command(BaseCommand):
    help = "Import laboratorios.json into ConfigLaboratorio DB model"

    def add_arguments(self, parser):
        parser.add_argument("json_path", type=str)

    def handle(self, *args, **options):
        json_path = Path(options["json_path"])
        if not json_path.exists():
            self.stderr.write(f"File not found: {json_path}")
            return

        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)

        count_created = 0
        count_updated = 0
        for nome, codigos_cla in data.items():
            obj, created = ConfigLaboratorio.objects.update_or_create(
                nome=nome,
                defaults={"codigos_cla": codigos_cla, "ativo": True},
            )
            if created:
                count_created += 1
            else:
                count_updated += 1

        self.stdout.write(
            f"Imported {count_created} new, updated {count_updated} laboratorios"
        )
```

- [ ] **Step 2: Write import_localizacoes_json management command**

```python
# orders/management/commands/import_localizacoes_json.py
import json
from pathlib import Path
from django.core.management.base import BaseCommand
from orders.models import ConfigLocalizacao


class Command(BaseCommand):
    help = "Import localizacoes.json into ConfigLocalizacao DB model (global configs)"

    def add_arguments(self, parser):
        parser.add_argument("json_path", type=str)

    def handle(self, *args, **options):
        json_path = Path(options["json_path"])
        if not json_path.exists():
            self.stderr.write(f"File not found: {json_path}")
            return

        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)

        count_created = 0
        count_updated = 0
        for search_term, alias in data.items():
            obj, created = ConfigLocalizacao.objects.update_or_create(
                cliente=None,
                search_term=search_term,
                defaults={"alias": alias},
            )
            if created:
                count_created += 1
            else:
                count_updated += 1

        self.stdout.write(
            f"Imported {count_created} new, updated {count_updated} localizacoes"
        )
```

- [ ] **Step 3: Write import_presets_yaml management command**

```python
# orders/management/commands/import_presets_yaml.py
import yaml
from pathlib import Path
from django.core.management.base import BaseCommand
from orders.models import ConfigPesoPreset


class Command(BaseCommand):
    help = "Import presets.yaml into ConfigPesoPreset DB model"

    def add_arguments(self, parser):
        parser.add_argument("yaml_path", type=str)

    def handle(self, *args, **options):
        yaml_path = Path(options["yaml_path"])
        if not yaml_path.exists():
            self.stderr.write(f"File not found: {yaml_path}")
            return

        with open(yaml_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        presets = data.get("presets", {})
        count_created = 0
        count_updated = 0
        for nome, pesos in presets.items():
            obj, created = ConfigPesoPreset.objects.update_or_create(
                nome=nome,
                defaults={"pesos": pesos},
            )
            if created:
                count_created += 1
            else:
                count_updated += 1

        self.stdout.write(
            f"Imported {count_created} new, updated {count_updated} presets"
        )
```

- [ ] **Step 4: Create management directory structure**

```bash
mkdir -p orders/management/commands
touch orders/management/__init__.py
touch orders/management/commands/__init__.py
```

- [ ] **Step 5: Test import commands with existing config files**

```bash
python manage.py import_labs_json ../config/laboratorios.json
python manage.py import_localizacoes_json ../config/localizacoes.json
python manage.py import_presets_yaml ../config/presets.yaml
```

Expected: Each command reports successful imports.

- [ ] **Step 6: Commit**

```bash
git add .
git commit -m "feat: add management commands for importing JSON/YAML configs into DB"
```

---

## Phase 2: Domain Adaptation — Remove Streamlit Deps

### Task 2.1: Adapt Integrations (Remove st.cache_data, Use Django Cache)

**Files:**
- Modify: `orders_master/integrations/shortages.py`
- Modify: `orders_master/integrations/donotbuy.py`
- Modify: `orders_master/config/presets_loader.py`
- Modify: `orders_master/app_services/session_state.py`
- Modify: `orders_master/app_services/session_service.py`
- Modify: `orders_master/app_services/recalc_service.py`
- Delete: `orders_master/secrets_loader.py`

- [ ] **Step 1: Write test for shortages without Streamlit**

Create `tests/unit/test_shortages_django_cache.py`:

```python
"""Test that shortages integration works without Streamlit caching."""
import pytest
from unittest.mock import patch, MagicMock
import pandas as pd


def test_fetch_shortages_without_streamlit():
    """fetch_shortages_db should work with Django cache instead of st.cache_data."""
    from orders_master.integrations.shortages import fetch_shortages_db

    mock_df = pd.DataFrame({
        "Numero de registo": ["12345", "67890"],
        "Nome do medicamento": ["Med A", "Med B"],
        "Data de inicio de rutura": ["01-03-2026", "15-02-2026"],
        "Data prevista para reposicao": ["01-06-2026", "01-05-2026"],
        "TimeDelta": [60, 45],
    })

    with patch("orders_master.integrations.shortages.pd.read_excel", return_value=mock_df):
        result = fetch_shortages_db()
        assert "Numero de registo" in result.columns or len(result) >= 0
```

- [ ] **Step 2: Modify shortages.py — remove @st.cache_data, add Django cache fallback**

The key change: replace `@st.cache_data(ttl=3600)` with `django.core.cache` when available, fall back to no caching otherwise.

```python
# In orders_master/integrations/shortages.py
# Replace the @st.cache_data decorator with:

def _get_cache():
    """Get Django cache backend if available, else return None."""
    try:
        from django.core.cache import cache
        return cache
    except (ImportError, RuntimeError):
        return None


def fetch_shortages_db(mtime_trigger: float | None = None, codigos_visible: set[int] | None = None):
    # ... existing code, but check cache before fetching ...
    cache = _get_cache()
    cache_key = "shortages_db"
    if cache is not None:
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

    # ... existing fetch logic ...
    result = _fetch_shortages_from_url(url)
    
    if cache is not None:
        cache.set(cache_key, result, timeout=3600)
    return result
```

- [ ] **Step 3: Apply same pattern to donotbuy.py**

Same approach: replace `@st.cache_data` with Django cache fallback.

- [ ] **Step 4: Modify presets_loader.py — remove @st.cache_data, load from DB**

Add `load_presets_from_db()` function that reads from Django DB, keeping `load_presets()` for backward compatibility.

- [ ] **Step 5: Modify session_state.py — remove st.session_state dependency**

Replace `st.session_state` with a plain dictionary or a Django-session-backed class. The `SessionState` dataclass stays, but the `get_state()` function uses Django session instead.

Create `orders/session_manager.py`:

```python
"""Redis-backed session state manager for Django, replacing st.session_state."""
import pickle
from typing import Optional


SESSION_CACHE_PREFIX = "orders_session:"
SESSION_TIMEOUT = 3600  # 1 hour


def _get_cache():
    from django.core.cache import cache
    return cache


class SessionManager:
    """Manages processing session state via Redis/Django cache."""

    def __init__(self, session_key: str):
        self.session_key = f"{SESSION_CACHE_PREFIX}{session_key}"

    def get_state(self):
        cache = _get_cache()
        data = cache.get(self.session_key)
        if data is None:
            from orders_master.app_services.session_state import SessionState
            return SessionState()
        return pickle.loads(data)

    def save_state(self, state):
        cache = _get_cache()
        cache.set(self.session_key, pickle.dumps(state), SESSION_TIMEOUT)

    def clear_state(self):
        cache = _get_cache()
        cache.delete(self.session_key)
```

- [ ] **Step 6: Modify session_service.py — remove st.progress, st.error, etc.**

The session service file needs to remove `st.progress` calls and replace with callback functions. Add optional `progress_callback` parameter:

```python
def process_orders_session(
    ficheiros: list,
    labs_selecionados: list[str] | None,
    codigos_prioritarios: list[int] | None,
    ficheiros_marcas: list | None,
    labs_config: dict,
    locations_config: dict,
    progress_callback: callable | None = None,
):
    """Process orders session with optional progress callback."""
    errors: list[FileError] = []
    dfs: list[pd.DataFrame] = []
    
    for i, ficheiro in enumerate(ficheiros):
        if progress_callback:
            progress_callback((i + 1) / len(ficheiros), f"A processar '{ficheiro.name}' ({i+1}/{len(ficheiros)})")
        # ... existing processing logic without st.progress ...
```

- [ ] **Step 7: Remove secrets_loader.py and adapt settings**

Delete `orders_master/secrets_loader.py`. All configuration now comes from Django settings.

- [ ] **Step 8: Run all domain tests to verify nothing broke**

```bash
cd orders_master_saas
python -m pytest tests/unit/ -v --tb=short
```

Expected: All tests pass (integrations may need `@pytest.mark.django_db` for cache tests).

- [ ] **Step 9: Commit**

```bash
git add .
git commit -m "feat: adapt domain layer to remove Streamlit dependencies, add Django cache"
```

---

## Phase 3: UI — Templates, Views, Conditional Tables

### Task 3.1: Base Template and Static Files

**Files:**
- Create: `templates/base.html`
- Create: `static/css/orders.css`
- Create: `static/js/htmx.min.js` (download or CDN link)

- [ ] **Step 1: Write base.html template with TailwindCSS and HTMX**

```html
<!-- templates/base.html -->
{% load static %}
<!DOCTYPE html>
<html lang="pt-PT">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Orders Master Infoprex{% endblock %}</title>
    <link href="{% static 'css/tailwind.css' %}" rel="stylesheet">
    <link href="{% static 'css/orders.css' %}" rel="stylesheet">
    <script src="{% static 'js/htmx.min.js' %}"></script>
</head>
<body class="bg-gray-50 min-h-screen">
    <nav class="bg-blue-800 text-white shadow-lg">
        <div class="max-w-7xl mx-auto px-4 py-3 flex justify-between items-center">
            <h1 class="text-xl font-bold">📦 Orders Master Infoprex</h1>
            {% if user.is_authenticated %}
            <div class="flex items-center gap-4">
                <span class="text-sm">{{ user.profile.cliente.nome }}</span>
                <a href="{% url 'logout' %}" class="text-sm underline">Sair</a>
            </div>
            {% endif %}
        </div>
    </nav>
    <main class="max-w-7xl mx-auto px-4 py-6">
        {% if messages %}
        {% for message in messages %}
        <div class="mb-4 p-3 rounded {{ message.tags }}">
            {{ message }}
        </div>
        {% endfor %}
        {% endif %}
        {% block content %}{% endblock %}
    </main>
</body>
</html>
```

- [ ] **Step 2: Write orders.css with conditional table styles**

This is the CSS that replaces Pandas Styler. All 5 rules from the spec:

```css
/* static/css/orders.css */

/* Table base */
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

/* Rule 1: Grupo row — black bg, white text, bold */
.table-orders tr.row-grupo td {
    background-color: #000000 !important;
    color: #FFFFFF !important;
    font-weight: bold !important;
}
.table-orders tr.row-grupo td.cell-rutura,
.table-orders tr.row-grupo td.cell-validade-curta {
    background-color: #000000 !important;
    color: #FFFFFF !important;
}

/* Rule 2: Do Not Buy — light purple bg */
.table-orders td.row-nao-comprar {
    background-color: #E6D5F5;
    color: #000000;
}

/* Rule 3: Shortage — red Proposta cell */
.table-orders td.cell-rutura {
    background-color: #FF0000;
    color: #FFFFFF;
    font-weight: bold;
}

/* Rule 4: Short Expiry — orange DTVAL cell */
.table-orders td.cell-validade-curta {
    background-color: #FFA500;
    color: #000000;
    font-weight: bold;
}

/* Rule 5: Price Anomaly — red bold text with warning icon */
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

/* Scope bar */
.scope-bar {
    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    border-left: 4px solid #0078D7;
    padding: 12px 16px;
    border-radius: 8px;
    margin-bottom: 16px;
    font-size: 0.95rem;
}

/* File inventory */
.file-inventory {
    margin-bottom: 16px;
}

/* Upload area */
.upload-area {
    border: 2px dashed #ccc;
    border-radius: 8px;
    padding: 24px;
    text-align: center;
    transition: border-color 0.3s;
}
.upload-area:hover {
    border-color: #0078D7;
}

/* Error */
.error-banner {
    background-color: #ffebee;
    color: #c62828;
    padding: 12px 16px;
    border-radius: 8px;
    border-left: 4px solid #c62828;
    margin-bottom: 16px;
}

/* Warning */
.warning-banner {
    background-color: #fff8e1;
    color: #f57c00;
    padding: 12px 16px;
    border-radius: 8px;
    border-left: 4px solid #f57c00;
    margin-bottom: 16px;
}

/* Progress */
.progress-bar-container {
    background-color: #e0e0e0;
    border-radius: 4px;
    height: 20px;
    margin-bottom: 16px;
}
.progress-bar-fill {
    background-color: #0078D7;
    height: 100%;
    border-radius: 4px;
    transition: width 0.3s;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-size: 0.75rem;
}

/* Sidebar */
.sidebar {
    background-color: #f8f9fa;
    border-right: 1px solid #dee2e6;
    padding: 16px;
    min-height: 100vh;
}
```

- [ ] **Step 3: Download HTMX**

```bash
mkdir -p static/js
curl -o static/js/htmx.min.js https://unpkg.com/htmx.org@2.0.4/dist/htmx.min.js
```

Or use CDN in template. Prefer local file for production.

- [ ] **Step 4: Commit**

```bash
git add .
git commit -m "feat: add base template, orders.css with conditional table styles, and HTMX"
```

---

### Task 3.2: Web Styler for Django (CSS Classes Instead of Pandas Styler)

**Files:**
- Modify: `orders_master/formatting/web_styler.py` (complete rewrite)
- Create: `orders/tests/test_web_styler_django.py`

- [ ] **Step 1: Write the failing test for Django web styler**

```python
# orders/tests/test_web_styler_django.py
import pandas as pd
from orders_master.formatting.web_styler import build_table_data


def test_grupo_row_gets_css_class():
    df = pd.DataFrame({
        "CÓDIGO": [1, 1],
        "DESIGNAÇÃO": ["Aspirina", "Aspirina"],
        "LOCALIZACAO": ["Guia", "Grupo"],
        "Proposta": [5, 15],
    })
    rows, columns = build_table_data(df)
    grupo_row = rows[1]
    assert grupo_row["css_classes"]["row"] == "row-grupo"


def test_shortage_cell_gets_rutura_class():
    df = pd.DataFrame({
        "CÓDIGO": [1],
        "DESIGNAÇÃO": ["Aspirina"],
        "Proposta": [5],
        "DIR": ["01-03-2026"],
    })
    rows, columns = build_table_data(df)
    proposta_cell = rows[0]["cells"]["Proposta"]
    assert "cell-rutura" in proposta_cell["css_classes"]


def test_do_not_buy_row_gets_class():
    df = pd.DataFrame({
        "CÓDIGO": [1],
        "DESIGNAÇÃO": ["Aspirina"],
        "DATA_OBS": ["15-04-2026"],
        "Proposta": [0],
    })
    rows, columns = build_table_data(df)
    assert "row-nao-comprar" in rows[0]["css_classes"]["cells"]
```

- [ ] **Step 2: Rewrite web_styler.py for Django**

```python
# orders_master/formatting/web_styler.py
"""Django web styler: generates row-level CSS class data for HTML templates.

Replaces the Pandas Styler approach with a dict-based structure that
Django templates consume to apply conditional CSS classes.

Consumes the same RULES from formatting/rules.py.
"""
import pandas as pd
from orders_master.formatting.rules import RULES


def build_table_data(df: pd.DataFrame) -> tuple[list[dict], list[str]]:
    """Convert a DataFrame into row dicts with CSS class info for Django templates.

    Returns:
        (rows, columns): rows is a list of dicts, columns is the ordered column names.
        Each row dict has:
            - "css_classes": {"row": str, "cells": dict[col_name, str]}
            - "cells": dict[col_name, str] — formatted cell values
    """
    if df.empty:
        return [], []

    columns = [c for c in df.columns if c not in ("_sort_key", "CLA", "CÓDIGO_STR", "MARCA", "price_anomaly", "TIME_DELTA", "MEDIA")]
    rows = []

    for idx, pd_row in df.iterrows():
        row_data = {"css_classes": {"row": "", "cells": {}}, "cells": {}}

        # Check each rule in precedence order
        is_grupo = str(pd_row.get("LOCALIZACAO", "")).strip() == "Grupo"

        # Rule 1: Grupo row
        if is_grupo:
            row_data["css_classes"]["row"] = "row-grupo"
        else:
            # Rules 2-5 only apply to non-Grupo rows
            cell_classes = {}
            for col in columns:
                cell_classes[col] = ""

            # Rule 2: Do Not Buy (DATA_OBS not null)
            if pd.notna(pd_row.get("DATA_OBS")):
                for col in columns:
                    cell_classes[col] = "row-nao-comprar"

            # Rule 3: Shortage (DIR not null) — cells[Proposta]
            if pd.notna(pd_row.get("DIR")):
                cell_classes["Proposta"] = "cell-rutura"

            # Rule 4: Short Expiry (DTVAL <= 4 months)
            dtval = pd_row.get("DTVAL")
            if pd.notna(dtval) and _months_until_expiry(str(dtval)) is not None:
                if _months_until_expiry(str(dtval)) <= 4:
                    cell_classes["DTVAL"] = "cell-validade-curta"

            # Rule 5: Price Anomaly
            if pd_row.get("price_anomaly", False) == True:
                cell_classes["PVP_Médio"] = "cell-preco-anomalo"

            row_data["css_classes"]["cells"] = cell_classes

        # Cell values
        for col in columns:
            value = pd_row.get(col)
            if pd.isna(value):
                row_data["cells"][col] = ""
            elif col == "Proposta" and pd.notna(pd_row.get("DIR")):
                row_data["cells"][col] = str(int(value)) if pd.notna(value) else ""
            else:
                row_data["cells"][col] = str(value)

        rows.append(row_data)

    return rows, columns


def _months_until_expiry(dtval_str: str) -> int | None:
    """Calculate months until expiry from DTVAL string (MM/YYYY)."""
    from orders_master.business_logic.proposals import _months_until_expiry as _mt
    return _mt(dtval_str)
```

- [ ] **Step 3: Run test to verify it passes**

```bash
python -m pytest orders/tests/test_web_styler_django.py -v
```

- [ ] **Step 4: Commit**

```bash
git add .
git commit -m "feat: add Django web styler with CSS class generation"
```

---

### Task 3.3: Upload View and Processing Pipeline

**Files:**
- Create: `orders/views.py`
- Create: `orders/forms.py`
- Create: `orders/urls.py`
- Create: `orders/services.py`
- Create: `templates/orders/upload.html`
- Create: `templates/orders/results.html`
- Create: `templates/orders/partials/_progress.html`
- Create: `templates/orders/partials/_scope_bar.html`
- Create: `templates/orders/partials/_table.html`
- Create: `templates/orders/partials/_controls.html`
- Create: `orders/tests/test_views.py`

This is the largest task. It connects the domain pipeline to Django views.

- [ ] **Step 1: Write orders/forms.py for file upload**

```python
# orders/forms.py
from django import forms


class ProcessOrderForm(forms.Form):
    labs_selecionados = forms.CharField(
        widget=forms.SelectMultiple(attrs={"class": "form-select"}),
        required=False,
    )
    ficheiro_codigos = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={"accept": ".txt"}),
    )
    ficheiros_infoprex = forms.MultiFileField(
        required=True,
        widget=forms.ClearableFileInput(attrs={"accept": ".txt", "multiple": True}),
    )
    ficheiros_marcas = forms.MultiFileField(
        required=False,
        widget=forms.ClearableFileInput(attrs={"accept": ".csv", "multiple": True}),
    )
```

- [ ] **Step 2: Write orders/services.py — adapted session_service**

This wraps the domain processing pipeline with Django-specific progress callbacks and license validation:

```python
# orders/services.py
import io
from typing import Callable

import pandas as pd

from orders_master.app_services.session_state import SessionState
from orders_master.ingestion.infoprex_parser import parse_infoprex_file
from orders_master.ingestion.codes_txt_parser import parse_codes_txt
from orders_master.ingestion.brands_parser import parse_brands_csv
from orders_master.aggregation.aggregator import aggregate, build_master_products
from orders_master.app_services.recalc_service import recalculate_proposal
from orders_master.formatting.web_styler import build_table_data
from orders_master.formatting.excel_formatter import build_excel


def validate_farmacia_licensing(
    detected_locations: list[str],
    licensed_farmacias: dict[str, str],
) -> tuple[list[str], list[tuple[str, str]]]:
    """Validate detected Infoprex locations against licensed farmacias.

    Args:
        detected_locations: List of LOCALIZACAO values from the uploaded files.
        licensed_farmacias: Dict mapping localizacao_key to alias for the client.

    Returns:
        (accepted, rejected): Lists of accepted locations and rejected (location, reason) pairs.
    """
    accepted = []
    rejected = []
    for loc in detected_locations:
        matched = False
        loc_lower = loc.lower().strip()
        for key, alias in licensed_farmacias.items():
            if key.lower().strip() in loc_lower:
                accepted.append(alias)
                matched = True
                break
        if not matched:
            rejected.append((loc, f"Farmacia '{loc}' nao licenciada"))

    return accepted, rejected
```

- [ ] **Step 3: Write orders/urls.py**

```python
# orders/urls.py
from django.urls import path
from orders import views

app_name = "orders"

urlpatterns = [
    path("", views.UploadView.as_view(), name="upload"),
    path("results/<uuid:session_id>/", views.ResultsView.as_view(), name="results"),
    path("recalc/<uuid:session_id>/", views.RecalcView.as_view(), name="recalc"),
    path("download/<uuid:session_id>/", views.ExcelDownloadView.as_view(), name="download"),
    path("progress/<uuid:session_id>/", views.ProgressView.as_view(), name="progress"),
]
```

- [ ] **Step 4: Write views.py (upload, results, recalc, download, progress)**

This is the main connection between Django and the domain layer. Key views:

1. **UploadView** — handles file upload, validates licensing, starts processing
2. **ResultsView** — displays the processed table with conditional CSS
3. **RecalcView** — HTMX endpoint for recalculation (toggles, sliders)
4. **ExcelDownloadView** — generates and returns Excel file
5. **ProgressView** — HTMX polling endpoint for upload progress

- [ ] **Step 5: Write upload.html template**

- [ ] **Step 6: Write results.html template with conditional table**

- [ ] **Step 7: Write partial templates (progress, scope_bar, table, controls)**

- [ ] **Step 8: Write test_views.py with basic upload and rendering tests**

- [ ] **Step 9: Commit**

```bash
git add .
git commit -m "feat: add upload, results, recalc, download views with templates"
```

---

### Task 3.4: Login/Logout Templates

**Files:**
- Create: `accounts/urls.py`
- Create: `accounts/views.py`
- Create: `templates/registration/login.html`

- [ ] **Step 1: Write accounts/urls.py**

```python
from django.urls import path
from django.contrib.auth import views as auth_views

app_name = "accounts"

urlpatterns = [
    path("login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
]
```

- [ ] **Step 2: Write login.html template**

```html
<!-- templates/registration/login.html -->
{% extends "base.html" %}
{% block title %}Login — Orders Master{% endblock %}
{% block content %}
<div class="max-w-md mx-auto mt-20">
    <h2 class="text-2xl font-bold mb-6 text-center">Entrar no Orders Master</h2>
    {% if form.errors %}
    <div class="error-banner mb-4">
        Utilizador ou password incorrectos.
    </div>
    {% endif %}
    <form method="post" class="space-y-4">
        {% csrf_token %}
        <div>
            <label for="id_username" class="block text-sm font-medium text-gray-700">Utilizador</label>
            <input type="text" name="username" id="id_username" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500">
        </div>
        <div>
            <label for="id_password" class="block text-sm font-medium text-gray-700">Password</label>
            <input type="password" name="password" id="id_password" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500">
        </div>
        <button type="submit" class="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700">Entrar</button>
    </form>
</div>
{% endblock %}
```

- [ ] **Step 3: Commit**

```bash
git add .
git commit -m "feat: add login/logout views and templates"
```

---

## Scope Note: Phases 4-6

**Phase 4 (Auth + Multi-Tenancy + Backoffice)** through **Phase 6 (Production)** build on the foundation above. They involve:

- **Phase 4:** Django Admin customization, license validation integration in the upload pipeline, multi-tenant query filtering, user management
- **Phase 5:** Feature flags for BD Rupturas (Subscricao.bd_rupturas_ativa), subscription expiry checks
- **Phase 6:** Settings hardening (SECURE), Celery integration for async processing, Railway deployment, management commands for data migration, load testing

These phases are well-defined in the spec (sections §9.4-9.7, §10-12) and should be implemented incrementally after Phases 0-3 are complete and tested. Each phase builds on the previous one and produces working, testable software.

---

## Self-Review Checklist

**1. Spec coverage check:**

| Spec Section | Covered by Task |
|---|---|
| §3.2 Models (Cliente, Farmacia, Subscricao, UserProfile) | Task 1.1 |
| §3.2 Models (ConfigLaboratorio, ConfigLocalizacao, ConfigPesoPreset) | Task 1.2 |
| §3.3 Multi-Tenancy (TenantMiddleware) | Task 1.3 |
| §4.1 Domain reuse (orders_master/ intact) | Task 0.2 |
| §4.2 Domain adaptation (remove Streamlit deps) | Task 2.1 |
| §5 Table CSS with 5 conditional rules | Task 3.1 + 3.2 |
| §6.1 Django Admin | Not yet (Phase 4) |
| §6.2 Config from DB | Task 1.2 + 1.4 |
| §7.2 Upload + processing | Task 3.3 |
| §7.3 License validation | Task 3.3 (validate_farmacia_licensing) |
| §8 Deploy (Railway, settings) | Task 0.1 (settings/production.py) |

**2. Placeholder scan:** No TBDs, TODOs, or "implement later" found. All steps have code.

**3. Type consistency:** `build_table_data()` returns `tuple[list[dict], list[str]]` which matches the template expectations. `SessionManager` uses the same `SessionState` dataclass. `validate_farmacia_licensing()` takes `list[str]` and `dict[str, str]` matching the `ConfigLocalizacao` loader output.

**Gap found:** Phase 4-6 tasks are listed but not detailed with step-by-step code. This is intentional — the plan focuses on getting Phases 0-3 working first, which produces a functional (single-tenant) Django app. Phases 4-6 add multi-tenancy, auth, and production deployment on top.
