# PRD — Migracao Orders Master Infoprex para Django SaaS

> **Versao:** 1.0  
> **Data:** 2026-05-15  
> **Estado:** Rascunho  
> **Baseado em:** PRD v2 (Orders_Master_SDD/prd.md)  
> **Framework alvo:** Django 5.x + PostgreSQL + HTMX/TailwindCSS  
> **Deploy alvo:** Railway  

---

## Indice P

- [PRD — Migracao Orders Master Infoprex para Django SaaS](#prd--migracao-orders-master-infoprex-para-django-saas)
  - [Indice P](#indice-p)
  - [1. Visao e Objectivos da Migracao](#1-visao-e-objectivos-da-migracao)
    - [1.1 Proposta de Valor](#11-proposta-de-valor)
    - [1.2 Objectivos Mensuraveis](#12-objectivos-mensuraveis)
    - [1.3 Fora de Ambito (exclusoes)](#13-fora-de-ambito-exclusoes)
  - [2. Justificacao da Escolha: Django vs Flask vs Streamlit](#2-justificacao-da-escolha-django-vs-flask-vs-streamlit)
  - [3. Arquitectura do Sistema SaaS](#3-arquitectura-do-sistema-saas)
    - [3.1 Diagrama de Arquitectura](#31-diagrama-de-arquitectura)
    - [3.2 Modelos de Dados (Django ORM)](#32-modelos-de-dados-django-orm)
      - [Cliente](#cliente)
      - [Farmacia](#farmacia)
      - [Subscricao](#subscricao)
      - [ConfigLaboratorio (config global, editavel via admin)](#configlaboratorio-config-global-editavel-via-admin)
      - [ConfigLocalizacao (config por cliente + global)](#configlocalizacao-config-por-cliente--global)
      - [ConfigPesoPreset (config global)](#configpesopreset-config-global)
      - [SessaoProcessamento (log de sessoes, opcional na Fase 5)](#sessaoprocessamento-log-de-sessoes-opcional-na-fase-5)
      - [User (extendido via relacao)](#user-extendido-via-relacao)
    - [3.3 Multi-Tenancy](#33-multi-tenancy)
    - [3.4 Autenticacao e Licenciamento](#34-autenticacao-e-licenciamento)
    - [3.5 Validacao por Infoprex](#35-validacao-por-infoprex)
  - [4. Migracao da Camada de Dominio](#4-migracao-da-camada-de-dominio)
    - [4.1 O Que Se Reaproveita Integramente](#41-o-que-se-reaproveita-integramente)
    - [4.2 O Que Necessita de Adaptacao](#42-o-que-necessita-de-adaptacao)
    - [4.3 O Que Se Reescreve](#43-o-que-se-reescreve)
  - [5. UI Django — Tabelas Condicionais](#5-ui-django--tabelas-condicionais)
    - [5.1 Regras de Formatacao (Paridade com PRD v2)](#51-regras-de-formatacao-paridade-com-prd-v2)
    - [5.2 Implementacao CSS das Tabelas](#52-implementacao-css-das-tabelas)
    - [5.3 HTML das Tabelas](#53-html-das-tabelas)
  - [6. Backoffice de Administracao](#6-backoffice-de-administracao)
    - [6.1 Funcionalidades do Admin](#61-funcionalidades-do-admin)
    - [6.2 Gestao de Configuracoes via Admin](#62-gestao-de-configuracoes-via-admin)
  - [7. Fluxos de Utilizador SaaS](#7-fluxos-de-utilizador-saas)
    - [7.1 Registo e Onboarding](#71-registo-e-onboarding)
    - [7.2 Upload e Processamento](#72-upload-e-processamento)
    - [7.3 Validacao de Licenca por Infoprex](#73-validacao-de-licenca-por-infoprex)
    - [7.4 Fluxo de Excecao: Farmacia Nao Licenciada](#74-fluxo-de-excecao-farmacia-nao-licenciada)
  - [8. Deploy e Infraestrutura](#8-deploy-e-infraestrutura)
    - [8.1 Stack de Deploy](#81-stack-de-deploy)
    - [8.2 Configuracao Railway](#82-configuracao-railway)
    - [8.3 Variaveis de Ambiente](#83-variaveis-de-ambiente)
    - [8.4 Gestao de Ficheiros Temporarios](#84-gestao-de-ficheiros-temporarios)
  - [9. Plano de Migracao por Fases](#9-plano-de-migracao-por-fases)
    - [9.1 Fase 0 — Preparacao](#91-fase-0--preparacao)
    - [9.2 Fase 1 — Fundacao Django](#92-fase-1--fundacao-django)
    - [9.3 Fase 2 — Dominio + Sessoes](#93-fase-2--dominio--sessoes)
    - [9.4 Fase 3 — UI + Tabelas Condicionais](#94-fase-3--ui--tabelas-condicionais)
    - [9.5 Fase 4 — Auth + Multi-Tenancy + Backoffice](#95-fase-4--auth--multi-tenancy--backoffice)
    - [9.6 Fase 5 — Extra BD Rupturas + Subscricoes](#96-fase-5--extra-bd-rupturas--subscricoes)
    - [9.7 Fase 6 — Producao](#97-fase-6--producao)
  - [10. Requisitos Nao-Funcionais da Migracao](#10-requisitos-nao-funcionais-da-migracao)
  - [11. Riscos e Mitigacoes](#11-riscos-e-mitigacoes)
  - [12. ADRs da Migracao](#12-adrs-da-migracao)
    - [ADR-M01: Django como Framework SaaS](#adr-m01-django-como-framework-saas)
    - [ADR-M02: Sessao de Processamento em Cache Redis](#adr-m02-sessao-de-processamento-em-cache-redis)
    - [ADR-M03: Processamento Assincrono com Celery (Fase 6)](#adr-m03-processamento-assincrono-com-celery-fase-6)
    - [ADR-M04: Validacao de Licenca por LOCALIZACAO do Infoprex](#adr-m04-validacao-de-licenca-por-localizacao-do-infoprex)
    - [ADR-M05: Reaproveitamento do Dominio sem Modificacao](#adr-m05-reaproveitamento-do-dominio-sem-modificacao)
    - [ADR-M06: HTML + CSS Classes em Vez de Pandas Styler](#adr-m06-html--css-classes-em-vez-de-pandas-styler)
    - [ADR-M07: Configuracoes em Base de Dados em Vez de Ficheiros JSON](#adr-m07-configuracoes-em-base-de-dados-em-vez-de-ficheiros-json)

---

## 1. Visao e Objectivos da Migracao

### 1.1 Proposta de Valor

Transformar o **Orders Master Infoprex** (actualmente uma aplicacao Streamlit single-tenant, sem auth, sem multi-tenancy) num **produto SaaS multi-tenant** que pode ser vendido por subscricao mensal a multiplos grupos de farmacias.

### 1.2 Objectivos Mensuraveis

| ID | Objectivo | Indicador |
|---|---|---|
| MIG-1 | Migracao completa para Django | Toda a funcionalidade do PRD v2 funciona em Django, zero Streamlit. |
| MIG-2 | Reaproveitamento do dominio | >= 90% do codigo `orders_master/` (parsers, aggregation, business_logic, formatting/rules.py) reaproveitado sem alteracao. |
| MIG-3 | Multi-tenancy | Cada Cliente tem N Farmacias. Upload de Infoprex so e aceite para Farmacias licenciadas ao Cliente. |
| MIG-4 | Autenticacao e licenciamento | Login/logout via Django auth. Validacao de LOCALIZACAO do Infoprex contra Farmacias licenciadas. |
| MIG-5 | Backoffice SaaS | Admin Django para gerir Clientes, Farmacias, Subscricoes, Configs. |
| MIG-6 | Extra BD Rupturas como feature toggled | BD Rupturas (Infarmed) so e visivel para Farmacias com esta feature activa na sua Subscricao. |
| MIG-7 | Paridade visual das tabelas | As 5 regras condicionais (Grupo, Nao Comprar, Rutura, Validade Curta, Preco Anomalo) funcionam em Django com CSS puro. |
| MIG-8 | Deploy em Railway | Aplicacao deployavel em Railway com PostgreSQL, gunicorn, e collectstatic. |
| MIG-9 | Performance mantida ou melhorada | Tempo de recalc < 500ms. Tempo de processamento inicial <= 15s para 4 ficheiros x 30MB. |
| MIG-10 | Testes mantidos | >= 80% de cobertura nos modulos de dominio. Todos os testes unitarios existentes continuam a passar. |

### 1.3 Fora de Ambito (exclusoes)

1. **Migracao de dados historicos** — o sistema actual nao persiste dados, nao ha nada a migrar.
2. **Integracao com gateway de pagamento** — subscricoes sao geridas manualmente pelo admin no backoffice. Stripe/MB Way serao adicionados numa fase futura.
3. **Mobile responsiveness** — mantido do PRD v2: desktop-first (>= 1280px).
4. **Internacionalizacao** — UI continua em Portugues Europeu.
5. **API REST publica** — nao e necessario na fase inicial. A aplicacao e full-server-rendered (Django templates + HTMX).

---

## 2. Justificacao da Escolha: Django vs Flask vs Streamlit

| Criterio | Django | Flask | Streamlit |
|---|---|---|---|
| **Auth built-in** | Sim (User, Group, Permission, Session) | Nao (extensoes necessarias) | Nao (hack frágil) |
| **Admin interface** | Sim (gerir Clientes, Farmacias, Subscricoes, Configs) | Nao (construir from zero) | Nao |
| **Multi-tenancy** | Suportado via middleware + query filtering | Suportado mas manual | Nao suportado |
| **ORM/DB** | Sim (PostgreSQL nativo) | Sim (SQLAlchemy manual) | Nao |
| **Reaproveitamento dominio** | 90%+ (orders_master/ e Python puro) | 90%+ (idem) | 100% (mas preso ao Streamlit) |
| **Tabelas condicionais** | HTML + CSS (flexivel, profissional) | HTML + CSS (idem) | Pandas Styler (limitado, re-executa tudo) |
| **SaaS-ready** | Sim (maduro para SaaS) | Possivel mas 2-3x mais trabalho | Nao (nao e para produtos SaaS) |
| **Deploy Railway** | Sim (Procfile + gunicorn) | Sim | Sim (mas limitado) |
| **Escalabilidade** | Sim (WSGI, multi-worker) | Sim | Nao (single-thread per session) |
| **Curva de aprendizado** | Media-alta | Baixa-media | Baixa |

**Decisao: Django** — oferece auth, admin, ORM e multi-tenancy de serie, reduzindo o trabalho em 2-3x vs Flask. O Streamlit nao e viavel para SaaS.

---

## 3. Arquitectura do Sistema SaaS

### 3.1 Diagrama de Arquitectura

```
┌─────────────────────────────────────────────────────────────────────┐
│                        DJANGO APPLICATION                           │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────────┐│
│  │   Accounts    │  │   Backoffice │  │    Orders App              ││
│  │   (auth)      │  │   (admin)    │  │    (core business)        ││
│  │               │  │              │  │                              ││
│  │ - Login       │  │ - Clientes   │  │ - Upload Infoprex          ││
│  │ - Logout      │  │ - Farmacias  │  │ - Processamento            ││
│  │ - Registo     │  │ - Subscricoes│  │ - Vista Agrupada/Detalhada ││
│  │ - Permissoes  │  │ - Configs    │  │ - Exportacao Excel          ││
│  │ - Licencas    │  │ - Features   │  │ - Filtros / Toggles         ││
│  └──────┬───────┘  └──────┬───────┘  └──────────┬─────────────────┘│
│         │                  │                      │                  │
│         └──────────────────┼──────────────────────┘                  │
│                            │                                         │
│         ┌──────────────────▼──────────────────────┐                 │
│         │        orders_master/ (DOMAIN)          │                 │
│         │                                           │                 │
│         │  ingestion/    aggregation/               │                 │
│         │  business_logic/  formatting/              │                 │
│         │  integrations/  config/                   │                 │
│         │  constants.py  schemas.py  exceptions.py   │                 │
│         └──────────────────────────────────────────┘                 │
│                                                                     │
│  ┌──────────────────┐  ┌──────────────┐                            │
│  │  PostgreSQL DB   │  │  Redis Cache  │                            │
│  │  (Users, Farm,   │  │  (Integracoes │                            │
│  │   Subs, Configs) │  │   BD Rupturas │                            │
│  └──────────────────┘  │   Nao Comprar)│                            │
│                        └──────────────┘                             │
└─────────────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │   Railway Deploy   │
                    │   (gunicorn +      │
                    │    PostgreSQL +    │
                    │    Redis)          │
                    └────────────────────┘
```

### 3.2 Modelos de Dados (Django ORM)

#### Cliente
```python
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
```

#### Farmacia
```python
class Farmacia(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='farmacias')
    nome = models.CharField(max_length=200)
    localizacao_key = models.CharField(
        max_length=100,
        help_text="Valor exacto do campo LOCALIZACAO no Infoprex (ex: 'FARMACIA GUIA')"
    )
    alias = models.CharField(
        max_length=100,
        help_text="Nome de apresentacao (ex: 'Guia')"
    )
    ativa = models.BooleanField(default=True)
    licenciada_ate = models.DateField(null=True, blank=True)
    
    class Meta:
        unique_together = ['cliente', 'localizacao_key']
        verbose_name_plural = 'farmacias'

    def __str__(self):
        return f"{self.alias} ({self.cliente.nome})"
```

#### Subscricao
```python
class Subscricao(models.Model):
    class Plano(models.TextChoices):
        BASICO = 'BAS', 'Basico'
        PROFISSIONAL = 'PRO', 'Profissional'
        ENTERPRISE = 'ENT', 'Enterprise'

    cliente = models.OneToOneField(Cliente, on_delete=models.CASCADE, related_name='subscricao')
    plano = models.CharField(max_length=3, choices=Plano.choices, default=Plano.BASICO)
    bd_rupturas_ativa = models.BooleanField(
        default=False,
        help_text="Extra pago: acesso a BD Esgotados Infarmed"
    )
    data_inicio = models.DateField()
    data_fim = models.DateField(null=True, blank=True)
    ativa = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.cliente.nome} - {self.get_plano_display()}"
```

#### ConfigLaboratorio (config global, editavel via admin)
```python
class ConfigLaboratorio(models.Model):
    nome = models.CharField(max_length=200, unique=True)
    codigos_cla = models.JSONField(
        help_text="Lista de codigos CLA. Ex: [\"137\", \"2651\"]"
    )
    ativo = models.BooleanField(default=True)
    
    def __str__(self):
        return self.nome
```

#### ConfigLocalizacao (config por cliente + global)
```python
class ConfigLocalizacao(models.Model):
    cliente = models.ForeignKey(
        Cliente, on_delete=models.CASCADE, null=True, blank=True,
        help_text="Se null, e uma config global (aplica-se a todos)"
    )
    search_term = models.CharField(
        max_length=200,
        help_text="Termo de pesquisa no campo LOCALIZACAO do Infoprex"
    )
    alias = models.CharField(
        max_length=100,
        help_text="Nome de apresentacao"
    )
    
    class Meta:
        unique_together = ['cliente', 'search_term']

    def __str__(self):
        escopo = "Global" if not self.cliente else str(self.cliente.nome)
        return f"[{escopo}] {self.search_term} -> {self.alias}"
```

#### ConfigPesoPreset (config global)
```python
class ConfigPesoPreset(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    pesos = models.JSONField(
        help_text="Lista de 4 pesos. Ex: [0.4, 0.3, 0.2, 0.1]"
    )
    
    def __str__(self):
        return self.nome
```

#### SessaoProcessamento (log de sessoes, opcional na Fase 5)
```python
class SessaoProcessamento(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    utilizador = models.ForeignKey(User, on_delete=models.CASCADE)
    criado_em = models.DateTimeField(auto_now_add=True)
    num_ficheiros = models.IntegerField()
    num_produtos = models.IntegerField()
    num_farmacias = models.IntegerField()
    lab_selecionados = models.JSONField(default=list)
    modo_detalhado = models.BooleanField(default=False)
    meses_previsao = models.FloatField(default=1.0)
```

#### User (extendido via relacao)
```python
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='utilizadores')
    role = models.CharField(max_length=20, choices=[
        ('admin', 'Administrador'),
        ('compras', 'Responsavel de Compras'),
        ('farmacia', 'Farmacia'),
    ], default='compras')
```

### 3.3 Multi-Tenancy

O acesso multi-tenant e implementado via **middleware + query filtering**:

1. **Middleware `TenantMiddleware`**: apos autenticacao, carrega o `Cliente` do `UserProfile` e armazena em `request.tenant`.
2. **Todas as queries** que envolvam dados do cliente (farmacias, configs, sessoes) filtram automaticamente por `request.tenant`.
3. **Upload de Infoprex**: so sao aceites ficheiros cuja `LOCALIZACAO` corresponde a uma `Farmacia` do `request.tenant.cliente`.

```python
# Middleware conceptual
class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            request.tenant = request.user.profile.cliente
        response = self.get_response(request)
        return response
```

### 3.4 Autenticacao e Licenciamento

**Fluxo de autenticacao:**

1. Utilizador acede a `accounts/login/`.
2. Insere credenciais (email + password).
3. Django auth valida e cria sessao.
4. `UserProfile.cliente` identifica de que grupo de farmacias o utilizador pertence.
5. `request.tenant` e populado pelo middleware em cada request subsequente.

**Fluxo de licenciamento (validacao por Infoprex):**

```
1. Utilizador faz upload de N ficheiros Infoprex.
2. O parser extrai o campo LOCALIZACAO de cada ficheiro.
3. Para cada LOCALIZACAO detectada:
   a. O sistema procura Farmacia(localizacao_key=localizacao_detectada, cliente=request.tenant)
   b. Se match e Farmacia.ativa=True e Subscricao.ativa=True: ACEITE
   c. Se nao houver match: FICHEIRO REJEITADO com erro claro
4. A lista de LOCALIZACAO aceites e passada ao pipeline de processamento.
```

**Implicacao critica:** o `localizacoes.json` actual (mapeamento search_term -> alias) e substituido pelo modelo `ConfigLocalizacao` + `Farmacia`. O match de localizacao continua a ser por substring (como no PRD v2, ADR-012), mas agora validado contra farmacias licenciadas do cliente.

### 3.5 Validacao por Infoprex

Quando um utilizador de um Cliente faz upload dos ficheiros Infoprex:

1. O campo `LOCALIZACAO` de cada ficheiro e extraido (mesma logica do parser actual: `DUV` max -> `LOCALIZACAO` alvo).
2. O mapeamento `search_term -> alias` agora vem da DB (modelo `ConfigLocalizacao`), com fallback para configs globais (`cliente=None`).
3. O sistema verifica se a LOCALIZACAO mapeada corresponde a uma `Farmacia` activa do `request.tenant`.
4. Se o ficheiro pertence a uma farmacia **nao licenciada** para esse Cliente, o ficheiro e rejeitado com a mensagem: `"A farmacia '{alias}' nao esta licenciada para a sua conta. Contacte o administrador."`
5. A mesma verificacao e feita para o campo `LOCALIZACAO` de cada linha individual (dentro do parser), garantindo que so linhas de farmacias licenciadas sao processadas.

---

## 4. Migracao da Camada de Dominio

### 4.1 O Que Se Reaproveita Integramente

Os seguintes modulos de `orders_master/` sao **Python puro sem dependencia de Streamlit** e migram sem alteracao:

| Modulo | Ficheiros | Razao |
|---|---|---|
| `ingestion/` | `infoprex_parser.py`, `codes_txt_parser.py`, `brands_parser.py`, `encoding_fallback.py` | Sem `import streamlit`. Parseiam ficheiros e devolvem DataFrames. |
| `aggregation/` | `aggregator.py` | Sem `import streamlit`. Opera sobre DataFrames. |
| `business_logic/` | `averages.py`, `proposals.py`, `cleaners.py`, `price_validation.py` | Sem `import streamlit`. Funcoes puras sobre DataFrames/arrays. |
| `constants.py` | `constants.py` | Apenas enums/constantes. |
| `schemas.py` | `schemas.py` | Apenas pydantic. |
| `exceptions.py` | `exceptions.py` | Apenas classes de excepcao. |
| `logger.py` | `logger.py` | Configuracao de logging. |
| `formatting/rules.py` | `rules.py` | Dataclasses com predicados e CSS/openpyxl configs. |
| `formatting/excel_formatter.py` | `excel_formatter.py` | Opera sobre DataFrames, devolve bytes. |

**Total estimado de reuso:** ~85-90% do codigo Python existente.

### 4.2 O Que Necessita de Adaptacao

| Modulo | Alteracao Necessaria | Razao |
|---|---|---|
| `formatting/web_styler.py` | Substituir Pandas Styler por geracao de HTML com classes CSS | Pandas Styler e especifico do Streamlit. Em Django, geramos HTML directo com classes CSS nas celulas. |
| `app_services/session_state.py` | Remover dependencia de `st.session_state` | Django usa sessao HTTP e cache Redis, nao `st.session_state`. |
| `app_services/session_service.py` | Remover `st.progress`, `st.error`, etc. Substituir por logica de orquestracao pura que recebe callbacks de progresso | A logica de orquestracao e pura; os efeitos colaterais (progresso, erros) sao callbacks. |
| `app_services/recalc_service.py` | Remover `@st.cache_data` (shortages, donotbuy) | Em Django, o caching e feito via Redis/db, nao `st.cache_data`. |
| `integrations/shortages.py` | Remover `@st.cache_data(ttl=3600)`, substituir por `django.core.cache` | Caching passa a ser via Django cache framework com Redis backend. |
| `integrations/donotbuy.py` | Idem. | Idem. |
| `config/labs_loader.py` | Remover `@st.cache_data`, carregar do DB em vez de JSON | Laboratorios passam a ser modelo Django `ConfigLaboratorio`. |
| `config/locations_loader.py` | Remover `@st.cache_data`, carregar do DB | Localizacoes passam a ser modelo Django `ConfigLocalizacao`. |
| `config/presets_loader.py` | Remover `@st.cache_data`, carregar do DB | Presets passam a ser modelo Django `ConfigPesoPreset`. |
| `secrets_loader.py` | Remover `st.secrets`, usar `settings.py` | Django settings em vez de `.streamlit/secrets.toml`. |

### 4.3 O Que Se Reescreve

| Componente | Novo | Razao |
|---|---|---|
| `app.py` + `ui/` | Views Django + templates HTML | Toda a camada de apresentacao Streamlit e substituida por views Django + templates. |
| SessionState | Sessao Django + sessao de processamento em cache/tmp | Nao existe `st.session_state` em Django. A sessao de processamento (DataFrames em memoria) e gerida via cache ou sessao. |
| Upload de ficheiros | `models.FileField` + `handle_uploaded_file` | O upload deixa de ser `st.file_uploader` e passa a ser um formulario POST com `enctype="multipart/form-data"`. |
| Download de Excel | `HttpResponse` com `content_type` apropriado | Em vez de `st.download_button`. |
| Barra de progresso | HTMX polling ou WebSocket | Streamlit faz re-renders automaticos. Em Django, usamos HTMX para polling de progresso. |
| Tabela principal | Template HTML com classes CSS condicionais | Em vez de `st.dataframe(Styler)`. |
| Toggles/sliders | Formularios Django com HTMX | Em vez de `st.toggle`, `st.number_input`, etc. |
| Scope bar | Template HTML | Em vez de `st.markdown`. |
| File Inventory | Template HTML | Em vez de `st.dataframe(Styler)`. |

---

## 5. UI Django — Tabelas Condicionais

### 5.1 Regras de Formatacao (Paridade com PRD v2)

As 5 regras condicionais do PRD v2 (Secao 6.1.6) sao mantidas exactamente com a mesma logica e cores, mas implementadas em CSS puro em vez de Pandas Styler:

| # | Condicao | Efeito Visual | Classe CSS | Âmbito |
|---|----------|---------------|------------|--------|
| 1 | `LOCALIZACAO == 'Grupo'` | Fundo preto, texto branco, bold | `.row-grupo` | Toda a linha |
| 2 | `DATA_OBS` preenchido | Fundo roxo claro `#E6D5F5`, texto preto | `.row-nao-comprar` | Colunas de `CÓDIGO` ate `T Uni` |
| 3 | `DIR` preenchido (rutura) | Fundo vermelho `#FF0000`, texto branco, bold | `.cell-rutura` | Apenas celula `Proposta` |
| 4 | `DTVAL` com diff <= 4 meses | Fundo laranja `#FFA500`, texto preto, bold | `.cell-validade-curta` | Apenas celula `DTVAL` |
| 5 | `price_anomaly == True` | Icone "⚠️" prefixado + texto vermelho bold | `.cell-preco-anomalo` | Apenas celula `PVP_Médio` |

**Regras de precedencia:** Linhas `Grupo` (regra 1) sobrepoem-se a tudo. As restantes regras sao mutuamente exclusivas em ambito de colunas.

### 5.2 Implementacao CSS das Tabelas

```css
/* Tabela principal — base */
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

/* Regra 1: Linha Grupo — fundo preto, texto branco, bold */
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

/* Regra 2: Nao Comprar — fundo roxo claro */
.table-orders td.row-nao-comprar {
    background-color: #E6D5F5;
    color: #000000;
}

/* Regra 3: Rutura — celula Proposta a vermelho */
.table-orders td.cell-rutura {
    background-color: #FF0000;
    color: #FFFFFF;
    font-weight: bold;
}

/* Regra 4: Validade curta — celula DTVAL a laranja */
.table-orders td.cell-validade-curta {
    background-color: #FFA500;
    color: #000000;
    font-weight: bold;
}

/* Regra 5: Preco anomalo — icon + vermelho */
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
```

### 5.3 HTML das Tabelas

A tabela e renderizada por um template Django que itera sobre o DataFrame e aplica as classes CSS com base nos predicados:

```html
<!-- Template conceptual -->
<table class="table-orders">
  <thead>
    <tr>
      {% for col in columns %}<th>{{ col }}</th>{% endfor %}
    </tr>
  </thead>
  <tbody>
    {% for row in rows %}
    <tr class="{% if row.is_grupo %}row-grupo{% endif %}">
      {% for col in columns %}
      <td class="{{ row.cell_classes|get_item:col }}">
        {{ row.cells|get_item:col }}
      </td>
      {% endfor %}
    </tr>
    {% endfor %}
  </tbody>
</table>
```

A logica de determinar `row.is_grupo` e `row.cell_classes` e executada pela view Django usando os predicados existentes em `formatting/rules.py`.

---

## 6. Backoffice de Administracao

### 6.1 Funcionalidades do Admin

O Django Admin fornecera as seguintes funcionalidades:

| Model | Accoes | Campos Lista | Filtros |
|---|---|---|---|
| **Cliente** | CRUD | nome, email, ativo, n farmacias, plano | ativo, plano |
| **Farmacia** | CRUD | cliente, nome, localizacao_key, alias, ativa, licenciada_ate | cliente, ativa |
| **Subscricao** | CRUD | cliente, plano, bd_rupturas_ativa, data_inicio, data_fim | ativa, plano, bd_rupturas_ativa |
| **UserProfile** | CRUD | user, cliente, role | cliente, role |
| **ConfigLaboratorio** | CRUD | nome, codigos_cla, ativo | ativo |
| **ConfigLocalizacao** | CRUD | cliente (ou Global), search_term, alias | cliente |
| **ConfigPesoPreset** | CRUD | nome, pesos | — |

**Acoes personalizadas no Admin:**

- **Activar/Desactivar Farmacia** em massa (admin action).
- **Exportar lista de farmacias** de um cliente para verificacao.
- **Verificar licenca** de um cliente (verifica se Subscricao.ativa=True e dentro do prazo).

### 6.2 Gestao de Configuracoes via Admin

O ficheiro `config/laboratorios.json` e substituido pelo modelo `ConfigLaboratorio`. Na migracao:

1. Um management command `import_labs_json` le o JSON e popula o modelo.
2. O `labs_loader.py` e adaptado para ler do DB em vez do ficheiro.
3. O Admin permite adicionar/editar/desactivar laboratorios sem tocar em ficheiros.

Idem para `localizacoes.json` (`ConfigLocalizacao`) e `presets.yaml` (`ConfigPesoPreset`).

**Config por cliente vs global:**

- `ConfigLaboratorio` e global — todos os clientes partilham os mesmos laboratorios.
- `ConfigLocalizacao` pode ser global (`cliente=None`) ou especifico de um cliente. O lookup prioriza configs do cliente, com fallback para global.
- A lista de "Nao Comprar" (Google Sheet) continua a ser global (partilhada por todos os clientes), mas pode eventualmente tornar-se por cliente numa versao futura.

---

## 7. Fluxos de Utilizador SaaS

### 7.1 Registo e Onboarding

```
1. Superadmin cria um Cliente no Django Admin.
2. Superadmin cria UserProfiles para os utilizadores desse Cliente.
3. Superadmin regista as Farmacias do Cliente (localizacao_key + alias).
4. Superadmin cria a Subscricao (plano, data_inicio, extras).
5. Utilizador recebe credenciais por email.
6. Utilizador faz login.
7. Sistema redireciona para dashboard (pagina de upload).
```

### 7.2 Upload e Processamento

```
1. Utilizador faz login.
2. Selecciona laboratorios (ou carrega TXT de codigos).
3. Carrega ficheiros Infoprex via formulario upload.
4. Opcionalmente carrega CSVs de marcas.
5. Clica "Processar Dados".
6. Sistema valida LOCALIZACAO de cada ficheiro contra Farmacias licenciadas.
7. Sistema processa apenas ficheiros de farmacias licenciadas.
8. Ficheiros de farmacias nao licenciadas sao rejeitados com erro claro.
9. Sistema renderiza a tabela com formatacao condicional (CSS classes).
10. Utilizador ajusta toggles/sliders (HTMX, sem reload total).
11. Utilizador descarrega Excel.
```

### 7.3 Validacao de Licenca por Infoprex

**Cenario normal:**
- Cliente "Joao" tem 4 farmacias: Guia, Ilha, Colmeias, Souto.
- Joao faz upload de 4 ficheiros Infoprex.
- Cada ficheiro e validado: LOCALIZACAO detectada corresponde a uma Farmacia licenciada.
- Todos aceites. Processamento normal.

**Cenario de rejeicao:**
- Cliente "Joao" tem 4 farmacias: Guia, Ilha, Colmeias, Souto.
- Joao tenta fazer upload de um 5o ficheiro de "Farmacia Nova" que nao esta licenciada.
- Sistema detecta que "Nova" nao esta na lista de Farmacias licenciadas.
- Ficheiro rejeitado: `"A farmacia 'Nova' nao esta licenciada para a sua conta. Contacte o administrador."`
- Os 4 ficheiros validos continuam a ser processados.

### 7.4 Fluxo de Excecao: Farmacia Nao Licenciada

```
1. Utilizador carrega 5 ficheiros.
2. Sistema processa cada ficheiro:
   a. Ficheiro 1 (Guia): LOCALIZACAO="FARMACIA GUIA" -> match com Farmacia(localizacao_key__icontains="guia", cliente=tenant) -> ACEITE
   b. Ficheiro 2 (Ilha): LOCALIZACAO="FARMACIA ILHA" -> match -> ACEITE
   c. Ficheiro 3 (Nova): LOCALIZACAO="FARMACIA NOVA" -> nao ha Farmacia com esta localizacao_key para este cliente -> REJEITADO
   d. Ficheiro 4 (Colmeias): ACEITE
   e. Ficheiro 5 (Souto): ACEITE
3. Sistema exibe File Inventory com:
   - Guia: OK, 847 linhas
   - Ilha: OK, 723 linhas
   - Nova: ERRO - "Farmacia 'Nova' nao licenciada"
   - Colmeias: OK, 801 linhas
   - Souto: OK, 612 linhas
4. Sistema processa os 4 ficheiros aceites normalmente.
```

---

## 8. Deploy e Infraestrutura

### 8.1 Stack de Deploy

| Componente | Tecnologia | Versao |
|---|---|---|
| **Framework** | Django | 5.x |
| **Base de Dados** | PostgreSQL | 16+ |
| **Cache** | Redis | 7+ |
| **Servidor WSGI** | Gunicorn | 21+ |
| **CSS Framework** | TailwindCSS | 4.x |
| **Interactividade** | HTMX | 2.x |
| **Hosting** | Railway | — |
| **Storage de Ficheiros** | Local (tmp) ou Railway Volume | — |
| **CI/CD** | GitHub Actions | — |

### 8.2 Configuracao Railway

```
# Procfile
web: gunicorn orders_master_saas.wsgi:application --bind 0.0.0.0:$PORT --workers 4

# railway.json (ou via Dashboard)
- Servico web (Django + Gunicorn)
- Servico PostgreSQL (addon Railway)
- Servico Redis (addon Railway)
- Variaveis de ambiente: DJANGO_SETTINGS_MODULE, SECRET_KEY, DATABASE_URL, REDIS_URL, SHORTAGES_SHEET_URL, DONOTBUY_SHEET_URL
```

### 8.3 Variaveis de Ambiente

```bash
DJANGO_SETTINGS_MODULE=orders_master_saas.settings.production
SECRET_KEY=<generated>
DATABASE_URL=<railway-postgresql-url>
REDIS_URL=<railway-redis-url>
SHORTAGES_SHEET_URL=https://docs.google.com/.../pub?output=xlsx
DONOTBUY_SHEET_URL=https://docs.google.com/.../pub?output=xlsx
ALLOWED_HOSTS=*.up.railway.app,orders-master.example.com
```

### 8.4 Gestao de Ficheiros Temporarios

Os ficheiros Infoprex carregados (ate 5 x 30MB = 150MB) sao processados em memoria (igual ao comportamento Streamlit actual). Nao e necessario armazenamento persistente para os ficheiros de input — o processamento e feito na request e os DataFrames vivem em cache (Redis) durante a sessao.

---

## 9. Plano de Migracao por Fases

### 9.1 Fase 0 — Preparacao

| Tarefa | Descricao |
|---|---|
| MIG-0.1 | Criar projecto Django (`django-admin startproject orders_master_saas`) |
| MIG-0.2 | Configurar PostgreSQL, Redis, `settings.py` (dev e production) |
| MIG-0.3 | Copiar `orders_master/` (dominio) intacto para o projecto Django |
| MIG-0.4 | Criar app `accounts` com modelos `Cliente`, `Farmacia`, `Subscricao`, `UserProfile` |
| MIG-0.5 | Criar app `backoffice` (Django Admin customizado) |
| MIG-0.6 | Adicionar TailwindCSS + HTMX ao projecto |

### 9.2 Fase 1 — Fundacao Django

| Tarefa | Descricao |
|---|---|
| MIG-1.1 | Implementar `TenantMiddleware` |
| MIG-1.2 | Criar sistema de login/logout/templates base |
| MIG-1.3 | Criar modelos DB: `ConfigLaboratorio`, `ConfigLocalizacao`, `ConfigPesoPreset` |
| MIG-1.4 | Management command `import_labs_json` para migrar config JSON -> DB |
| MIG-1.5 | Adaptar `labs_loader.py`, `locations_loader.py`, `presets_loader.py` para ler do DB |
| MIG-1.6 | Adaptar `shortages.py` e `donotbuy.py`: substituir `@st.cache_data` por `django.core.cache` |
| MIG-1.7 | Adaptar `secrets_loader.py`: usar Django settings em vez de `st.secrets` |

### 9.3 Fase 2 — Dominio + Sessoes

| Tarefa | Descricao |
|---|---|
| MIG-2.1 | Adaptar `session_service.py`: remover `st.progress`, `st.error`, adicionar callbacks |
| MIG-2.2 | Adaptar `recalc_service.py`: remover `@st.cache_data`, usar cache Django |
| MIG-2.3 | Criar servico de sessao Django: `ProcessingSession` que armazena DataFrames em cache Redis |
| MIG-2.4 | Adaptar `session_state.py`: substituir `st.session_state` por sessao Django |
| MIG-2.5 | Validacao de licenca: integrar check de Farmacia no `infoprex_parser.py` |
| MIG-2.6 | Todos os testes unitarios existentes continuam a passar |

### 9.4 Fase 3 — UI + Tabelas Condicionais

| Tarefa | Descricao |
|---|---|
| MIG-3.1 | Criar template base HTML + TailwindCSS (layout geral, sidebar, main area) |
| MIG-3.2 | Criar view e template para upload de ficheiros (formulario com `enctype="multipart/form-data"`) |
| MIG-3.3 | Implementar tabela condicional com classes CSS (5 regras do PRD v2) |
| MIG-3.4 | Implementar Scope Summary Bar como componente HTML |
| MIG-3.5 | Implementar File Inventory como componente HTML |
| MIG-3.6 | Implementar toggles e sliders via HTMX (recalc sem reload total) |
| MIG-3.7 | Implementar barra de progresso durante processamento (HTMX polling) |
| MIG-3.8 | Implementar exportacao Excel (HttpResponse com openpyxl) |
| MIG-3.9 | Reescrever `web_styler.py` para gerar HTML com classes CSS em vez de Pandas Styler |
| MIG-3.10 | Garantir paridade visual com o sistema actual (5 regras condicionais) |

### 9.5 Fase 4 — Auth + Multi-Tenancy + Backoffice

| Tarefa | Descricao |
|---|---|
| MIG-4.1 | Configurar Django Auth (login, logout, permissoes) |
| MIG-4.2 | Implementar registo de utilizadores (admin cria contas) |
| MIG-4.3 | Customizar Django Admin para `Cliente`, `Farmacia`, `Subscricao`, `ConfigLaboratorio`, etc. |
| MIG-4.4 | Implementar validacao de LOCALIZACAO no upload contra Farmacias licenciadas |
| MIG-4.5 | Implementar rejeicao clara de ficheiros de farmacias nao licenciadas |
| MIG-4.6 | Testes de integracao: multi-tenancy, isolamento de dados |
| MIG-4.7 | Gestao de configs via Admin (laboratorios, localizacoes, presets) |

### 9.6 Fase 5 — Extra BD Rupturas + Subscricoes

| Tarefa | Descricao |
|---|---|
| MIG-5.1 | Implementar feature flag `bd_rupturas_ativa` na Subscricao |
| MIG-5.2 | Na view de processamento, verificar se o cliente tem BD Rupturas activa antes de fazer merge |
| MIG-5.3 | Se BD Rupturas inactiva: tabela sem colunas DIR/DPR, sem highlight vermelho |
| MIG-5.4 | Interface no Admin para activar/desactivar extras por cliente |
| MIG-5.5 | Logica de Subscricao expirada: bloquear acesso quando `data_fim < today` |

### 9.7 Fase 6 — Producao

| Tarefa | Descricao |
|---|---|
| MIG-6.1 | Configurar `settings.py` de producao (SECURE, HSTS, CSRF) |
| MIG-6.2 | Deploy em Railway (PostgreSQL, Redis, gunicorn) |
| MIG-6.3 | Migration de dados:popular DB com configs existentes |
| MIG-6.4 | Testes de carga com 5 clientes simultaneos |
| MIG-6.5 | Monitorizacao e logs (Railway) |
| MIG-6.6 | Documentacao de onboarding para novos clientes |

---

## 10. Requisitos Nao-Funcionais da Migracao

| ID | Requisito | Alvo |
|---|---|---|
| NFR-M1 | Tempo de recalc em Django | <= 500ms (paridade com Streamlit) |
| NFR-M2 | Tempo de processamento inicial | <= 15s para 4 ficheiros x 30MB (paridade com Streamlit) |
| NFR-M3 | Cobertura de testes do dominio | >= 80% (mesmos testes unitarios, todos a passar) |
| NFR-M4 | Codigo Streamlit removido | Zero `import streamlit` no projecto final |
| NFR-M5 | Isolamento multi-tenant | Query filtering garante que Cliente A nunca ve dados de Cliente B |
| NFR-M6 | Paridade visual | As 5 regras condicionais produzem o mesmo efeito visual que o PRD v2 |
| NFR-M7 | Paridade funcional | Todas as user stories US-01 a US-16 do PRD v2 funcionam em Django |
| NFR-M8 | Deploy automatizado | Push para main faz deploy em Railway via GitHub Actions |
| NFR-M9 | Lint/type check | Ruff + mypy passam no codigo novo e no codigo migrado |
| NFR-M10 | Zero regressoes | Os testes unitarios do dominio (`orders_master/`) passam sem alteracao |

---

## 11. Riscos e Mitigacoes

| Risco | Probabilidade | Impacto | Mitigacao |
|---|---|---|---|
| Tabelas condicionais perdem fidelidade visual vs Streamlit Styler | Media | Alto | Implementar as 5 regras em CSS puro com !important. Testar com 200+ linhas. |
| Sessao de processamento (DataFrames grandes) consome muita memoria no servidor | Media | Alto | Usar Redis para cache com TTL. DataFrames grandes (>50MB) sao processados e reduzidos antes de cache. |
| Upload de ficheiros grandes bloqueia o worker gunicorn | Alta | Medio | Usar task queue (Celery + Redis) para processamento assincrono com polling via HTMX. |
| Multi-tenancy com fuga de dados entre clientes | Baixa | Critico | Middleware de tenant. Testes de integracao especificos. Query filtering em todas as views. |
| Curva de aprendizado Django se a equipa nao experiencia | Media | Medio | Seguir tutoriais oficiais. Usar Django Admin extensivamente. Foco na camada de dominio que ja e conhecida. |
| Performance de rendering de tabelas HTML grandes (>1000 linhas) | Media | Medio | Usar paginacao server-side ou scroll infinito com HTMX. Manter `display: sticky` nos headers. |

---

## 12. ADRs da Migracao

### ADR-M01: Django como Framework SaaS

**Contexto:** Migracao de aplicacao Streamlit para produto SaaS multi-tenant.

**Decisao:** Usar Django 5.x com PostgreSQL, gunicorn, Redis, HTMX e TailwindCSS.

**Consequencias:**
- (+) Auth, ORM, Admin nativos reduzem esforco em 2-3x vs Flask.
- (+) Ecossistema maduro (middleware, caching, sessions, management commands).
- (+) Deploy simples em Railway (Procfile + gunicorn).
- (-) Curva de aprendizado se equipa nao conhece Django.
- (-) Mais boilerplate vs Flask para coisas simples.

### ADR-M02: Sessao de Processamento em Cache Redis

**Contexto:** Streamlit mantem DataFrames em `st.session_state`. Django nao tem equivalente nativo para objectos grandes.

**Decisao:** Armazenar DataFrames processados em Redis com TTL de 1 hora, indexados por sessao de utilizador. HTMX polling para actualizacao de progresso.

**Consequencias:**
- (+) Funciona com multi-worker gunicorn (sessao partilhada).
- (+) Limite de memoria configuravel (Redis maxmemory + eviction).
- (-) Redis necessario como dependencia extra.
- (-) Serializacao/deserializacao de DataFrames (usar pickle ou parquet).

### ADR-M03: Processamento Assincrono com Celery (Fase 6)

**Contexto:** Upload de ficheiros grandes (5x30MB) pode bloquear workers gunicorn durante 15s.

**Decisao:** Na Fase 6 (Producao), implementar processamento assincrono com Celery + Redis como broker. HTMX faz polling de uma URL de progresso.

**Alternativa considerada:** Processamento sincrono com gunicorn workers (4+ workers). Aceitavel para Fase 3-5 com poucos utilizadores.

**Consequencias:**
- (+) Workers nao bloqueiam durante processamento pesado.
- (+) Escala melhor para multiplos utilizadores simultaneos.
- (-) Adiciona complexidade (Celery workers como servico adicional).
- (-) Nao necessario na Fase 3-5 com poucos utilizadores.

### ADR-M04: Validacao de Licenca por LOCALIZACAO do Infoprex

**Contexto:** Cada Cliente so pode processar ficheiros Infoprex das suas Farmacias licenciadas.

**Decisao:** O campo `LOCALIZACAO` do Infoprex e extraido pelo parser e comparado (substring match) contra `Farmacia.localizacao_key` do Cliente autenticado. Ficheiros sem match sao rejeitados com erro claro.

**Consequencias:**
- (+) Validacao automatica sem accao manual do utilizador.
- (+) Consistente com o mecanismo actual de `localizacoes.json` (substring match).
- (-) Se uma farmacia muda de nome no Sifarma, a `localizacao_key` precisa de ser actualizada no backoffice.
- (-) Match por substring pode dar falsos positivos se nomes forem muito curtos (mitigado por `min_length=3` herdado do PRD v2).

### ADR-M05: Reaproveitamento do Dominio sem Modificacao

**Contexto:** O codigo `orders_master/` e Python puro, sem dependencias Streamlit (excepto caching e session_state).

**Decisao:** O package `orders_master/` e copiado integramente para o projecto Django. As unicas modificacoes sao: (1) remover `@st.cache_data` (substituir por cache Django), (2) remover `import streamlit` (em `averages.py` carregar presets), (3) adaptar `session_state.py` para sessoa Django. Toda a logica de negocio permanece inalterada.

**Consequencias:**
- (+) Zero risco de regressao na logica de negocio.
- (+) Testes unitarios existentes continuam a passar.
- (+) Facil de manter — o dominio e uma "biblioteca" que tanto o Streamlit como o Django consomem.
- (-) Necessario criar adaptadores thin para substituir as dependencias Streamlit.

### ADR-M06: HTML + CSS Classes em Vez de Pandas Styler

**Contexto:** Pandas Styler e especifico do Streamlit. Em Django, precisamos renderizar tabelas em HTML.

**Decisao:** As 5 regras condicionais do `formatting/rules.py` (Grupo, Nao Comprar, Rutura, Validade, Preco Anomalo) sao implementadas como classes CSS aplicadas a elementos `<tr>` e `<td>` no template HTML. Os predicados (logica de quando aplicar cada regra) permanecem em `rules.py` e sao consumidos pela view Django.

**Consequencias:**
- (+) Controlo total sobre o HTML e CSS, sem dependencia de Pandas Styler.
- (+) Mais rapido para tabelas grandes (HTML nativo vs Styler render).
- (+) Facil de customizar (cores, fontes, layout) sem alterar Python.
- (-) Necessario reescrever `web_styler.py` para gerar HTML em vez de Styler.
- (-) Necessario testar paridade visual com o actual.

### ADR-M07: Configuracoes em Base de Dados em Vez de Ficheiros JSON

**Contexto:** O sistema actual usa `laboratorios.json`, `localizacoes.json` e `presets.yaml` como ficheiros editados manualmente.

**Decisao:** Migrar para modelos Django (`ConfigLaboratorio`, `ConfigLocalizacao`, `ConfigPesoPreset`), geridos via Django Admin. Os ficheiros JSON/YAML existentes serao importados via management command. Modificacoes em producao sao feitas via Admin, sem necessidade de reiniciar o servidor.

**Consequencias:**
- (+) Multi-tenancy natural: configs podem ser globais ou por cliente.
- (+) Validacao via Django ORM (null/blank, unique, validators).
- (+) Admin UI para gestao sem tocar em ficheiros.
- (+) Historia de auditoria (quando foi alterado, por quem).
- (-) Perde-se a simplicidade de editar um JSON num editor de texto.
- (-) Necessario endpoint/management command para importar ficheiros existentes.