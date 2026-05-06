# Orders Master Infoprex

O **Orders Master Infoprex** é um dashboard desenvolvido em Streamlit focado no *Sell Out* e na consolidação de propostas de encomendas. Agrega e processa múltiplos ficheiros exportados do Infoprex e outras origens, aplicando regras complexas para suportar decisões automatizadas.

## Instalação e Setup

Pode inicializar este projeto no seu ambiente local de forma simples em ≤ 5 passos:

1. **Clonar o Repositório:**
   ```bash
   git clone <repo-url>
   cd Orders_Master_SDD
   ```

2. **Criar e Activar um Ambiente Virtual:**
   ```bash
   python -m venv venv
   # No Linux/Mac:
   source venv/bin/activate
   # No Windows (PowerShell):
   .\venv\Scripts\activate
   ```

3. **Instalar Dependências:**
   ```bash
   pip install -r requirements.txt -r requirements-dev.txt
   ```

4. **Configurar Variáveis e Ficheiros Iniciais:**
   - Crie o ficheiro `secrets.toml` em `.streamlit/secrets.toml` com as suas chaves e URLs confidenciais (veja a secção Configuração).
   - Verifique os ficheiros de suporte em `config/`.

5. **Executar a Aplicação:**
   ```bash
   streamlit run app.py
   ```

## Configuração

O sistema depende de ficheiros estáticos e de configurações seguras:
- `config/laboratorios.json`: Lista de laboratórios reconhecidos, com validações baseadas na dimensão do texto.
- `config/localizacoes.json`: Dicionário de aliases para locais (Farmácias ou Lojas).
- `.streamlit/secrets.toml`: Ficheiro com informações sensíveis (ex: Google Sheets URLs) que **nunca** deve ser submetido para o repositório. O repositório contém um `pre-commit` hook que impede o seu *commit*.

## Testes e Qualidade de Código

A validação da lógica de domínio e da aplicação (excluindo interface web) está a cargo do `pytest`. A suite cobre lógicas de *parsing*, regras financeiras e a formatação *Single Source of Truth*.

Para executar os testes:
```bash
pytest
```

> **Dica:** O projeto usa hooks `pre-commit` com `ruff`, `black`, e `mypy` (`--strict` em `orders_master/`) para assegurar a máxima qualidade do código.

## Estrutura do Projecto

A arquitectura separa estritamente a Interface Web (Presentation) das regras analíticas (Domain). Ver [architecture.md](docs/architecture.md) para detalhes exaustivos.

- `app.py` - Ponto de entrada do dashboard Streamlit.
- `orders_master/` - Camada de Domínio (totalmente livre de referências ao Streamlit). Agrupa regras financeiras, ingestão de dados e lógicas externas.
- `ui/` - Layouts, filtros, diálogos e componentes da interface gráfica em Streamlit.
- `config/` - Ficheiros e configurações passíveis de edição pelo utilizador.
- `tests/` - Módulo isolado contendo *fixtures* preparadas e testes unitários/integração.
