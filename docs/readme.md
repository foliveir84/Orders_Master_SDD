# Orders Master Infoprex — Documentação do Projecto

## O que é o Orders Master Infoprex?

O **Orders Master Infoprex** é uma aplicação web interna (Streamlit) desenhada para um grupo de farmácias comunitárias que transforma ficheiros de exportação de vendas (sell-out) do módulo Infoprex do software Sifarma em **propostas de encomenda consolidadas multi-loja**.

O sistema aplica regras determinísticas de agregação, calcula médias ponderadas sobre o histórico de vendas (4 meses com pesos configuráveis), ajusta automaticamente propostas quando um produto está em rutura oficial (BD Infarmed), e sinaliza produtos que a equipa marcou como "não comprar". O resultado pode ser exportado como um ficheiro Excel com formatação condicional idêntica à vista web.

### Problema que resolve

A consolidação manual de vendas entre várias farmácias para preparar encomendas a fornecedores é um processo moroso, propenso a erros humanos (transcrição, soma, interpretação de histórico) e pouco auditável. Pequenas discrepâncias propagam-se até à compra final, resultando em rupturas por sub-encomenda ou stock excessivo por sobre-encomenda.

O Orders Master Infoprex resolve isto ao:

- **Reduzir o tempo de preparação** de horas para segundos — o pipeline é determinístico, os mesmos inputs produzem sempre os mesmos outputs.
- **Garantir auditabilidade** — cada número exibido é rastreável à sua fórmula e aos dados de origem.
- **Ajustar automaticamente** a proposta quando um produto está em rutura conhecida, cobrindo apenas o intervalo até à reposição prevista em vez de cobertura plena.
- **Prevenir compras indesejadas** — sinaliza visualmente produtos em lista de "não comprar" e validades curtas.

### O que NÃO é

Este sistema **não** faz redistribuição de stocks entre farmácias, não tem autenticação/autorização, não se integra automaticamente com APIs do Sifarma (apenas via upload manual), não submete encomendas ao fornecedor (o output é um Excel), não persiste histórico de propostas (cada sessão é independente), não tem internacionalização (UI exclusivamente em Português Europeu), e não é responsivo para mobile (requer ecrãs de pelo menos 1280px).

---

## Pré-requisitos

| Requisito | Versão Mínima | Notas |
|---|---|---|
| Python | 3.11 ou superior | O código usa `StrEnum` (disponível desde 3.11) e sintaxe moderna |
| pip | 21+ | Para instalar dependências |
| Git | 2.x | Para clonar o repositório |
| Navegador web | Moderno (Chrome/Firefox/Edge) | Streamlit renders numa interface web |

### Dependências Python (instaladas automaticamente)

As dependências de runtime estão definidas em `requirements.txt`:

- `streamlit` >=1.30, <1.40
- `pandas` >=2.0, <3.0
- `openpyxl` >=3.1, <4.0
- `pydantic` >=2.0, <3.0
- `python-dotenv` >=1.0, <2.0
- `pyyaml` >=6.0, <7.0
- `python-dateutil` >=2.8, <3.0
- `pandera` >=0.18, <1.0

As dependências de desenvolvimento estão em `requirements-dev.txt`:

- `pytest` >=7.0, <9.0
- `pytest-cov` >=4.0, <6.0
- `pytest-benchmark` >=4.0, <5.0
- `ruff` >=0.5, <1.0
- `black` >=24.0, <25.0
- `mypy` >=1.0, <2.0
- `pre-commit` >=3.0, <4.0

### Dados externos (opcionais mas recomendados)

A aplicação pode integrar duas Google Sheets públicas. Sem elas, o sistema funciona normalmente mas sem informação de ruturas ou lista de "não comprar":

- **BD Esgotados Infarmed** — URL pública de uma Google Sheet com lista de produtos em rutura.
- **Lista Não Comprar** — URL pública de uma Google Sheet colaborativa de produtos a evitar.

Estas URLs devem ser configuradas no ficheiro `.streamlit/secrets.toml` (ver secção de instalação abaixo).

---

## Instalação e Setup (Passo-a-Passo)

### 1. Clonar o repositório

```bash
git clone <url-do-repositorio>
cd Orders_Master_SDD
```

### 2. Criar e activar um ambiente virtual

```bash
# Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Linux/macOS
python -m venv venv
source venv/bin/activate
```

### 3. Instalar as dependências

Instale ambas as listas de dependências (runtime + desenvolvimento):

```bash
pip install -r requirements.txt -r requirements-dev.txt
```

> **Verificação:** Corra `pip list` e confirme que `streamlit`, `pandas`, `openpyxl`, e `pydantic` estão instalados.

### 4. Configurar os Secrets (Google Sheets)

Crie o ficheiro `.streamlit/secrets.toml` com as URLs das Google Sheets. Se não tiver acesso às sheets, a aplicação funciona sem elas — apenas não terá dados de ruturas nem lista de "não comprar".

Crie o ficheiro `.streamlit/secrets.toml` (este ficheiro está no `.gitignore` e **nunca** deve ser commitado):

```toml
# .streamlit/secrets.toml
SHORTAGES_URL = "https://docs.google.com/spreadsheets/d/e/.../pub?output=xlsx"
DONOTBUY_URL = "https://docs.google.com/spreadsheets/d/e/.../pub?output=xlsx"
```

Se não tiver URLs, pode simplesmente omitir este ficheiro. A aplicação continuará funcional — as integrações falham silenciosamente e devolvem DataFrames vazios.

### 5. Configurar os ficheiros de configuração

Os ficheiros de configuração já vêm com dados de exemplo no directório `config/`:

- **`config/laboratorios.json`** — Mapeamento de nome de laboratório para lista de códigos CLA. Já contém laboratórios reais (Mylan, Teva, KRKA, etc.). Pode ser editado em produção sem reiniciar o servidor — o sistema detecta alterações via `mtime` do ficheiro.
- **`config/localizacoes.json`** — Mapeamento de termos de pesquisa para aliases de farmácia. O sistema usa matching com word-boundary. Exemplo: `{"ilha": "Ilha", "Colmeias": "colmeias"}`.
- **`config/presets.yaml`** — Presets de pesos para a média ponderada. Contém três presets pré-definidos:
  - **Conservador:** `[0.5, 0.3, 0.15, 0.05]` — Dá mais peso ao mês mais recente.
  - **Padrão:** `[0.4, 0.3, 0.2, 0.1]` — Equilíbrio progressivo.
  - **Agressivo:** `[0.25, 0.25, 0.25, 0.25]` — Pesos iguais (média simples).

### 6. Verificar que os testes passam

Antes de executar a aplicação, garanta que a suite de testes unitários passa:

```bash
pytest -v --tb=short
```

O CI (GitHub Actions) requer cobertura >= 80% na lógica de domínio. Para verificar localmente:

```bash
pytest --cov=orders_master --cov-fail-under=80 -m "not slow"
```

### 7. Validar os ficheiros de configuração (opcional)

O projecto inclui um validador CLI para os JSONs de configuração:

```bash
python -m orders_master.config.validate config/laboratorios.json
python -m orders_master.config.validate config/localizacoes.json
```

Se o ficheiro for válido, o comando imprime `✓ Ficheiro <path> é válido.` e sai com código 0. Se inválido, imprime o erro e sai com código 1.

---

## Como Arrancar o Projecto

Com o ambiente virtual activado e as dependências instaladas:

```bash
streamlit run app.py
```

A aplicação abre automaticamente no browser em `http://localhost:8501`. Se não abrir, navegue manualmente para esse endereço.

### Argumentos úteis do Streamlit

```bash
# Especificar porta
streamlit run app.py --server.port 8502

# Não abrir o browser automaticamente
streamlit run app.py --server.headless true
```

### Para parar o servidor

Pressione `Ctrl+C` no terminal onde o Streamlit está a correr.

---

## Estrutura da Documentação

| Ficheiro | Destinatário | Conteúdo |
|---|---|---|
| **`docs/README.md`** (este ficheiro) | Todos | Descrição do projecto, pré-requisitos, instalação, setup |
| **`docs/ARCHITECTURE.md`** | Mantenedores e desenvolvedores | Estrutura do sistema, fluxo de dados, decisões técnicas |
| **`docs/USAGE.md`** | Utilizadores finais | Tutorial de uso, formatos de input, resolução de erros |

---

## Quick Reference — Comandos Úteis

| Comando | Descrição |
|---|---|
| `streamlit run app.py` | Arranca a aplicação web |
| `pytest -v` | Corre a suite de testes |
| `pytest --cov=orders_master` | Corre testes com relatório de cobertura |
| `ruff check .` | Linting do código |
| `black --check .` | Verifica formatação |
| `mypy --strict orders_master/` | Type checking estático |
| `python -m orders_master.config.validate <ficheiro>` | Valida um JSON de configuração |