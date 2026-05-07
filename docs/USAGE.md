# Orders Master Infoprex — Guia de Utilização

Este documento é o guia exaustivo de utilização do Orders Master Infoprex. Destina-se a três perfis de utilizador: o Responsável de Compras (utilizador principal), o Farmacêutico de Loja (utilizador ocasional), e o Administrador de Dados (mantenedor de configurações).

---

## 1. Visão Geral da Interface

A aplicação é dividida em duas áreas principais:

- **Barra Lateral (Sidebar, esquerda):** Onde configura os filtros e carrega os ficheiros.
- **Área Principal (centro/direita):** Onde visualiza os resultados, ajusta parâmetros e exporta.

### Layout da Sidebar

A sidebar contém 4 blocos sequenciais e um botão de processamento:

1. **Laboratórios** — Multiselect para filtrar produtos por laboratório.
2. **Códigos** — Upload de ficheiro TXT com lista de CNPs (tem prioridade sobre Laboratórios).
3. **Dados Base Infoprex** — Upload dos ficheiros de exportação de vendas.
4. **Base de Marcas** — Upload de CSVs com associação código → marca (opcional).
5. **Botão "🚀 Processar Dados"** — Inicia o processamento.

### Layout da Área Principal (de cima para baixo)

1. **Banner BD Rupturas** — Mostra a data da última consulta à BD de ruturas.
2. **Expander "Documentação e Workflow"** — Checklist de utilização.
3. **Expander "Códigos CLA"** — Mostra os códigos CLA activos dos laboratórios seleccionados.
4. **Inventário de Ficheiros** — Resumo dos ficheiros carregados (após processamento).
5. **Aviso de filtros obsoletos** — Aparece quando altera filtros sem reprocessar.
6. **Erros de ingestão** — Lista de erros por ficheiro (se houver).
7. **Toggle "Ver Detalhe"** — Alterna entre vista agrupada e detalhada por farmácia.
8. **Toggle "Mês Anterior"** — Alterna a base da média ponderada.
9. **Slider "Meses a Prever"** — Define o horizonte de cobertura da proposta.
10. **Selectbox "Preset de Pesos"** — Escolhe os pesos da média ponderada.
11. **Feedback visual** — Indica o horizonte activo.
12. **Multiselect "Filtrar por Marca"** — Filtra produtos por marca comercial.
13. **Tabela formatada** — Vista principal com formatação condicional.
14. **Botão "Download Excel"** — Exporta o resultado.

---

## 2. Tutorial Completo — Passo a Passo

### Fluxo Principal: Preparar encomenda para um laboratório

#### Passo 1: Abrir a aplicação

Abra o browser e navegue para `http://localhost:8501` (ou o endereço onde a aplicação está a correr). A página carrega com a sidebar à esquerda e a área principal vazia, mostrando uma mensagem informativa: "Configure os filtros na barra lateral e clique em **🚀 Processar Dados** para gerar as propostas de encomenda."

#### Passo 2: Seleccionar laboratório( s) na Sidebar

No **Bloco 1 — Laboratórios**, clique no dropdown "Filtrar por Laboratório" e seleccione um ou mais laboratórios. Por exemplo, seleccione **Mylan**.

- Os laboratórios disponíveis vêm do ficheiro `config/laboratorios.json`.
- Pode seleccionar múltiplos laboratórios. Se não seleccionar nenhum, todos os produtos serão incluídos (sem filtro CLA).
- O texto "Ignorado se TXT de códigos for usado" lembra que o Bloco 2 tem prioridade.

#### Passo 3: (Opcional) Carregar lista de CNPs

No **Bloco 2 — Códigos**, pode carregar um ficheiro `.txt` com uma lista de CNPs (Código Nacional do Produto), um por linha. Se carregar este ficheiro, **ele tem prioridade absoluta sobre a selecção de Laboratórios** — o filtro por CLA é ignorado e apenas os CNPs listados são processados.

Isto é útil para encomendas pontuais de produtos-chave específicos.

#### Passo 4: Carregar ficheiros Infoprex

No **Bloco 3 — Dados Base (Infoprex)**, carregue todos os ficheiros de exportação das suas farmácias. São ficheiros `.txt` exportados pelo módulo Infoprex do Sifarma, tipicamente em formato UTF-16 com separador Tab.

- Carregue **todos os ficheiros ao mesmo tempo** — pode seleccionar múltiplos ficheiros no diálogo de upload.
- O nome do ficheiro deve identificar a farmácia (ex: `Guia.txt`, `Ilha.txt`, `Colmeias.txt`, `Souto.txt`). O sistema usa o nome do ficheiro e o campo `LOCALIZACAO` interno para identificar a farmácia.
- O sistema detecta automaticamente o encoding do ficheiro (tenta UTF-16 primeiro, depois UTF-8, depois Latin-1).
- Se um ficheiro estiver corrompido, o sistema processa os outros normalmente e apresenta um erro identificando o ficheiro problemático.

#### Passo 5: (Opcional) Carregar CSVs de marcas

No **Bloco 4 — Base de Marcas**, pode carregar ficheiros CSV com a associação `CÓDIGO → MARCA`. São os ficheiros `Infoprex_SIMPLES.csv`, com separador ponto-e-vírgula (`;`) e colunas `COD` e `MARCA`.

Se carregar estes CSVs, aparecerá posteriormente um multiselect na área principal que permite filtrar por marca comercial.

#### Passo 6: Processar os dados

Clique no botão **🚀 Processar Dados** na sidebar. 

Isto despoleta o pipeline pesado:

1. Uma **barra de progresso** aparece no topo da área principal, mostrando `"Concluído 'Guia.txt' (1/4)"`, etc., conforme cada ficheiro é processado.
2. Após o processamento, a barra desaparece e os resultados aparecem.

A duração depende do tamanho e número de ficheiros. Ficheiros de 30MB podem demorar alguns segundos cada.

#### Passo 7: Verificar o inventário de ficheiros

Após processar, aparece um expander **"📋 Inventário de Ficheiros Processados"** no topo da área principal. Expanda-o para ver uma tabela com:

| Coluna | Significado |
|---|---|
| S | ✅ (sucesso) ou ❌ (erro) |
| Ficheiro | Nome do ficheiro carregado |
| Farmácia | Alias da farmácia detectado (via `localizacoes.json`) |
| Linhas | Número de produtos processados do ficheiro |
| Última Venda | Data da venda mais recente detectada no ficheiro |
| Avisos | Mensagens de aviso (ex: anomalias de preço, códigos inválidos) |

Linhas com erro (❌) aparecem com fundo avermelhado. Verifique se a farmácia e a data de última venda correspondem ao que espera — se carregou o ficheiro errado, isto é visível aqui.

#### Passo 8: Interpretar a Scope Summary Bar

A barra de resumo métrico (fundo gradiente cinza-azulado, na área principal) mostra o contexto actual do processamento:

- `📊 127 produtos` — Número de produtos distintos na vista actual.
- `🏪 4 farmácias` — Número de farmácias detectadas.
- `🎯 Laboratórios: Mylan` ou `🎯 Lista TXT (42 códigos)` — Filtro activo.
- `📅 Janela: JAN–ABR` — Meses usados no cálculo da média.
- `⚖️ Pesos: Padrão` — Preset de pesos activo.
- `🔮 Previsão: 1.0 m` — Horizonte de meses de previsão.
- `👁️ Modo: Agrupada` — Vista actual (Agrupada/Detalhada).
- `⏱️ Base: Mês Anterior` — Base da média (Mês Anterior/Mês Corrente).

#### Passo 9: Ajustar os controlos de recálculo

Todos os controlos abaixo recalculam a tabela **instantaneamente** sem reprocessar ficheiros:

**Toggle "Ver Detalhe de Sell Out (por farmácia)?":**

- **Desactivado (padrão):** Vista Agrupada — 1 linha por produto, valores somados entre todas as farmácias.
- **Activado:** Vista Detalhada — N linhas por produto (uma por farmácia) + 1 linha **"Grupo"** com o total. As linhas "Grupo" têm fundo preto com texto branco.

**Toggle "Média com base no Mês Anterior?":**

- **Activado (padrão):** A média ponderada ignora o mês corrente (possivelmente incompleto) e usa os 4 meses completos anteriores. Isto é recomendado no final/início de cada mês.
- **Desactivado:** A média usa os 4 meses mais recentes incluindo o mês corrente.

**Slider "📅 Meses a Prever":**

- Variável de 1.0 a 6.0, passo 0.1.
- Define quantos meses de stock a proposta deve cobrir. Ex: 2.5 = propõe encomenda para cobrir 2.5 meses de vendas.
- A proposta recalcula instantaneamente ao mover o slider.

**Selectbox "⚖️ Preset de Pesos":**

- **Conservador** `[0.5, 0.3, 0.15, 0.05]` — Dá mais peso ao mês mais recente. Ideal quando as vendas recentes são representativas.
- **Padrão** `[0.4, 0.3, 0.2, 0.1]` — Equilíbrio progressivo. O mais usado no dia-a-dia.
- **Agressivo** `[0.25, 0.25, 0.25, 0.25]` — Pesos iguais (média simples de 4 meses). Suaviza flutuações.
- **Custom** — Permite definir 4 pesos manualmente. A soma deve ser exactamente 1.00. Se não for, o sistema mostra erro e reverte para o preset "Padrão".

**Multiselect "🏷️ Filtrar por Marca"** (aparece apenas se CSVs de marcas foram carregados):

- Mostra todas as marcas presentes no portefólio filtrado.
- Por defeito, todas as marcas estão seleccionadas.
- Desmarque marcas para as excluir da vista. A linha "Grupo" é sempre preservada.
- A key do multiselect muda quando troca de laboratório, evitando "state ghost" (marcas de um laboratório anterior a aparecerem no novo).

#### Passo 10: Interpretar a tabela

A tabela principal contém as seguintes colunas (nem todas visíveis em todas as vistas):

| Coluna | Vista Agrupada | Vista Detalhada | Significado |
|---|---|---|---|
| CÓDIGO | ✔ | ✔ | Código Nacional do Produto |
| DESIGNAÇÃO | ✔ | ✔ | Nome do produto (limpo, sem acentos, Title Case) |
| LOCALIZACAO | — | ✔ | Nome da farmácia ou "Grupo" |
| PVP_Médio / PVP | ✔ | ✔ | Preço de Venda ao Público (média agrupada / individual) |
| P.CUSTO_Médio / P.CUSTO | ✔ | ✔ | Preço de Custo |
| DUC | — | ✔ | Data da Última Compra |
| DTVAL | — | ✔ | Data de Validade (MM/AAAA) |
| STOCK | ✔ | ✔ | Stock actual |
| JAN...DEZ (meses) | ✔ | ✔ | Vendas mensais (colunas dinâmicas) |
| T Uni | ✔ | ✔ | Total de unidades vendidas no período |
| Proposta | ✔ | ✔ | Proposta de encomenda calculada |
| DIR | ✔ | ✔ | Data de Início de Rutura (preenchida apenas se produto em rutura) |
| DPR | ✔ | ✔ | Data Prevista de Reposição (preenchida apenas se produto em rutura) |
| DATA_OBS | ✔ | ✔ | Data de marcação "Não Comprar" (preenchida apenas se produto marcado) |

**Formatação condicional:**

| Formato Visual | Significado |
|---|---|
| Fundo preto, texto branco, bold | Linha "Grupo" (total do produto em todas as farmácias) |
| Fundo roxo claro `#E6D5F5` (da coluna CÓDIGO até T Uni) | Produto marcado como "Não Comprar" |
| Célula "Proposta" a vermelho com texto branco, bold | Produto em rutura oficial (BD Infarmed) |
| Célula "DTVAL" a laranja, bold | Validade curta (≤ 4 meses a partir de hoje) |
| Texto vermelho com prefixo ⚠️ na coluna PVP | Preço anómalo (PVP ≤ 0, P.CUSTO ≤ 0, ou PVP < P.CUSTO) |

#### Passo 11: Exportar para Excel

Clique no botão **📥 Download Excel Encomendas** no fundo da tabela. O sistema gera um ficheiro `.xlsx` com:

- Nome dinâmico: `Sell_Out_<scope_tag>_<YYYYMMDD_HHMM>.xlsx`
  - Se filtrou por 1 laboratório: `Sell_Out_Mylan_20260508_1430.xlsx`
  - Se filtrou por múltiplos: `Sell_Out_Labs-3_20260508_1430.xlsx`
  - Se usou lista TXT: `Sell_Out_TXT-42_20260508_1430.xlsx`
  - Sem filtros: `Sell_Out_GRUPO_20260508_1430.xlsx`
- **Formatação idêntica à web** — todas as cores, bold e formatação condicional são reproduzidos no Excel via openpyxl, consumindo as mesmas regras `RULES` do `formatting/rules.py`.
- Colunas técnicas (TimeDelta, price_anomaly, _sort_key, CLA, MARCA, Media) são excluídas do Excel. Colunas DIR, DPR e DATA_OBS **são incluídas**.

---

## 3. Formatos de Input Esperados

### 3.1 Ficheiros Infoprex (`.txt`)

Estes são os ficheiros de exportação do módulo Infoprex do Sifarma. O sistema espera:

- **Separador:** Tabulação (`\t`).
- **Encoding:** UTF-16 (o mais comum), UTF-8, ou Latin-1. O sistema tenta automaticamente por esta ordem.
- **Colunas estruturais obrigatórias:** `CPR` (código do produto) e `DUV` (data de última venda). Se estas colunas não existirem, o ficheiro é rejeitado com um erro de schema.
- **Colunas de dados (opcionais mas esperadas):** `NOM`, `LOCALIZACAO`, `SAC`, `PVP`, `PCU`, `DUC`, `DTVAL`, `CLA`.
- **Colunas de vendas:** `V0` a `V14` (15 colunas mensais). `V0` = mês mais recente, `V14` = mais antigo. O sistema inverte esta ordem internamente.
- **Colunas extra** no ficheiro são ignoradas automaticamente.

Exemplo das primeiras linhas de um ficheiro Infoprex (simplificado):

```
CPR	NOM	LOCALIZACAO	SAC	PVP	PCU	DUC	DTVAL	CLA	DUV	V0	V1	V2	V3	V4
1234567	PRODUTO A	Farmácia da Ilha	10	5.50	3.20	01/04/2026	06/2026	137	30/04/2026	5	8	3	6	4
```

**Nota sobre múltiplas localizações no mesmo ficheiro:** Se um ficheiro contém dados de mais do que uma localização (campo `LOCALIZACAO`), o sistema selecciona automaticamente a localização com a data de venda mais recente (campo `DUV` máximo) e descarta as restantes. Isto evita duplicação de dados.

### 3.2 Ficheiro de Códigos CNP (`.txt`)

Um ficheiro de texto simples com um CNP (Código Nacional do Produto) por linha. Apenas linhas compostas exclusivamente por dígitos são aceites — cabeçalhos, linhas em branco e linhas alfanuméricas são descartadas silenciosamente.

Exemplo:

```
Códigos prioritários - Não apagar esta linha
1234567
2345678
3456789

1234560
abc123  ← esta linha será ignorada
4567890
```

Neste exemplo, seriam extraídos 4 códigos: `1234567`, `2345678`, `3456789`, `4567890`. As outras linhas (cabeçalho, linha em branco, alfanumérica) são descartadas.

O ficheiro é lido como UTF-8, com BOM (Byte Order Mark) tolerado e removido automaticamente.

### 3.3 CSVs de Marcas (`Infoprex_SIMPLES.csv`)

Ficheiros CSV com separador ponto-e-vírgula (`;`) e colunas `COD` e `MARCA`.

Exemplo:

```
COD;MARCA
1234567;BENURON
2345678;BENURON
3456789;BRUFEN
```

Regras de processamento:

- `COD` é convertido para inteiro. Valores não-numéricos são descartados.
- `MARCA` vazia, `"nan"` ou `"None"` é descartada.
- Se o mesmo `COD` aparece em múltiplos ficheiros, a primeira MARCA vista é mantida.
- Linhas malformadas são ignoradas (`on_bad_lines='skip'`).

### 3.4 Ficheiros de Configuração

**`config/laboratorios.json`** — Mapeamento de nome de laboratório para lista de códigos CLA:

```json
{
    "Mylan": ["137", "2651", "2953", "6403"],
    "Teva": ["2326", "2618", "4873", "1463"],
    "KRKA": ["75A", "19P", "1546"]
}
```

- Chaves: nomes de laboratório (mínimo 2 caracteres, primeira maiúscula).
- Valores: lista de códigos CLA (alfanuméricos, máximo 10 caracteres). Duplicados são removidos automaticamente com warning.
- Pode editar este ficheiro enquanto a aplicação corre — basta recarregar a página (F5) no browser.

**`config/localizacoes.json`** — Mapeamento de termos de pesquisa para aliases de farmácia:

```json
{
    "ilha": "Ilha",
    "Colmeias": "colmeias",
    "Souto": "Souto"
}
```

- Termos de pesquisa: mínimo 3 caracteres (para evitar matches frágeis).
- O sistema usa matching por word-boundary. Exemplo: o termo `"ilha"` faz match em `"Farmácia da Ilha"` mas NÃO em `"Vilha"`.
- Pode editar este ficheiro enquanto a aplicação corre — recarregue a página (F5).

**`config/presets.yaml`** — Pesos para a média ponderada:

```yaml
presets:
  Conservador: [0.5, 0.3, 0.15, 0.05]
  Padrão: [0.4, 0.3, 0.2, 0.1]
  Agressivo: [0.25, 0.25, 0.25, 0.25]
```

Cada preset é uma lista de exactamente 4 pesos. A soma deve ser ≈ 1.0.

---

## 4. Fórmulas de Cálculo — O Que Significam os Números

### 4.1 Média Ponderada

A coluna `Media` é calculada como uma média ponderada dos 4 meses de vendas mais recentes:

```
Media = (Vendas_Mês_n × Peso_n) + (Vendas_Mês_n-1 × Peso_n-1) + (Vendas_Mês_n-2 × Peso_n-2) + (Vendas_Mês_n-3 × Peso_n-3)
```

Onde `n` é o mês mais recente incluído na janela. Os pesos dependem do preset seleccionado. A identificação das colunas de mês é feita por **posição** (relativa à coluna `T Uni`), não por nome — o que torna o sistema imune a bugs sazonais.

Exemplo com preset Padrão `[0.4, 0.3, 0.2, 0.1]` e toggle "Mês Anterior" activado:

```
Media = ABR×0.4 + MAR×0.3 + FEV×0.2 + JAN×0.1
```

Exemplo com toggle "Mês Corrente" activado:

```
Media = MAI×0.4 + ABR×0.3 + MAR×0.2 + FEV×0.1
```

### 4.2 Proposta Base

```
Proposta = round(Media × Meses_a_Prever − STOCK)
```

- A proposta pode ser **negativa** — isto indica que o stock actual excede as vendas previstas para o horizonte escolhido. É informação útil (sugere sobre-stock), não um erro.
- A proposta é sempre um número inteiro (arredondado).
- A proposta é calculada individualmente por farmácia na vista detalhada e agrupada na vista agrupada.

### 4.3 Proposta de Rutura

Para produtos que estão na BD de Esgotados do Infarmed (coluna `DIR` preenchida), a fórmula é diferente:

```
Proposta = round((Media / 30) × TimeDelta − STOCK)
```

Onde `TimeDelta` é o número de dias até à data prevista de reposição, **recalculado dinamicamente** contra a data actual do sistema. Isto significa que se a reposição estava prevista para daqui a 60 dias mas passou 1 mês, o TimeDelta será ≈30 dias e a proposta ajusta-se automaticamente.

- Se `TimeDelta` for 0 ou negativo (reposição já passou ou é hoje), a proposta será `-STOCK` ou negativa.
- Se o produto NÃO está em rutura, a proposta base é usada.

---

## 5. Erros Comuns e Como Resolvê-los

### 5.1 Erro: "Colunas estruturais em falta no ficheiro ... Esperado: CPR, DUV"

**Causa:** O ficheiro carregado não contém as colunas `CPR` (código do produto) e/ou `DUV` (data de última venda). Isto pode acontecer se:

- Carregou um ficheiro que não é uma exportação Infoprex.
- O ficheiro está corrompido e os cabeçalhos foram perdidos.
- O ficheiro usa nomes de coluna diferentes dos esperados pelo sistema.

**Resolução:**

1. Verifique se o ficheiro é realmente uma exportação do módulo Infoprex do Sifarma.
2. Abra o ficheiro num editor de texto e confirme que a primeira linha contém os nomes das colunas, incluindo `CPR` e `DUV`.
3. Se exportou de uma versão diferente do Sifarma, os nomes das colunas podem ter mudado. Nesse caso, terá de adaptar o ficheiro ou o parser.

### 5.2 Erro: "Codificação não suportada para o ficheiro"

**Causa:** O sistema tentou ler o ficheiro com UTF-16, UTF-8 e Latin-1, e nenhum funcionou.

**Resolução:**

1. Abra o ficheiro num editor de texto (Notepad++, VS Code).
2. Verifique o encoding do ficheiro (No Notepad++: menu Encoding).
3. Se for um encoding raro (ex: UTF-8 BOM, Windows-1252), converta o ficheiro para UTF-8 antes de o carregar.
4. Se o ficheiro contém dados binários lixo, está corrompido — re-exporte do Sifarma.

### 5.3 Aviso: "⚠️ Filtros Modificados! Clique em 🚀 Processar Dados para actualizar a base de dados"

**Causa:** Após processar os dados, alterou a selecção de laboratórios na sidebar ou carregou um ficheiro TXT de códigos diferente, sem clicar novamente em "Processar Dados". Os dados visíveis na tabela correspondem ao processamento anterior, não aos novos filtros.

**Resolução:**

1. Se quiser ver os dados com os novos filtros, clique novamente em **🚀 Processar Dados**.
2. Se não quiser reprocessar, pode simplesmente ignorar o aviso — a tabela anterior permanece visível e funcional. A decisão é sua.

### 5.4 Aviso: "Nenhum produto encontrado com os filtros actuais"

**Causa:** Após processar, a tabela aparece vazia. Isto pode acontecer se:

- Seleccionou laboratórios cujos códigos CLA não existem nos ficheiros carregados.
- A lista de CNPs não tem nenhum código presente nos ficheiros.
- Todos os produtos foram descartados como zombies (stock=0 e vendas=0 em todas as farmácias).
- Filtros de marca excluíram todos os produtos.

**Resolução:**

1. Verifique se seleccionou os laboratórios correctos.
2. Verifique se os ficheiros carregados realmente contêm dados dos laboratórios seleccionados (use o Inventário de Ficheiros).
3. Tente sem seleccionar laboratórios (processamento sem filtro).
4. Se usou filtro de marca, verifique se seleccionou marcas válidas.

### 5.5 Erro: "ConfigError" ao arrancar a aplicação

**Causa:** O ficheiro `config/laboratorios.json` ou `config/localizacoes.json` está malformado ou falta.

**Resolução:**

1. Verifique se os ficheiros existem no directório `config/`.
2. Valide os ficheiros com o CLI:
   ```bash
   python -m orders_master.config.validate config/laboratorios.json
   python -m orders_master.config.validate config/localizacoes.json
   ```
3. Para `laboratorios.json`: as chaves devem ter ≥2 caracteres e começar com maiúscula; os valores devem ser listas de strings alfanuméricas com ≤10 caracteres.
4. Para `localizacoes.json`: os termos de pesquisa devem ter ≥3 caracteres.

### 5.6 Banner "Data Consulta BD Rupturas — Não disponível"

**Causa:** A aplicação não consegue aceder à Google Sheet de Esgotados, ou o URL não está configurado.

**Resolução:**

1. Verifique se o ficheiro `.streamlit/secrets.toml` existe e contém a chave `SHORTAGES_URL` com um URL válido.
2. Verifique se a Google Sheet está publicada como "Anyone with the link can view".
3. Se estiver offline ou a sheet estiver inacessível, o sistema funciona normalmente — apenas a informação de ruturas não será disponível.

### 5.7 Produtos com preço anómalo (⚠️)

**Causa:** O sistema detectou que o preço do produto é inválido (PVP ≤ 0, P.CUSTO ≤ 0, ou PVP < P.CUSTO). Isto é sinalizado com prefixo ⚠️ e texto vermelho na coluna PVP.

**Impacto:** O produto continua visível na tabela, mas as suas linhas são **excluídas do cálculo de média de preço** (PVP_Médio e P.CUSTO_Médio). A proposta ainda é calculada com base nos dados disponíveis.

**Resolução:** Corrigir os dados na origem (Sifarma) é a acção correcta. O sistema apenas sinaliza — não corrige automaticamente.

### 5.8 Linha "Grupo" não aparece ou aparece incompleta

**Causa:** A linha "Grupo" aparece apenas na vista detalhada (toggle "Ver Detalhe" activado). Na vista agrupada, não há linha "Grupo" porque cada produto já é um único registo.

**Resolução:** Active o toggle "Ver Detalhe de Sell Out (por farmácia)?" para ver as linhas "Grupo".

### 5.9 Ficheiro reconhecido mas com 0 linhas

**Causa:** O ficheiro foi carregado com sucesso mas após a filtragem (por laboratório ou CNPs), nenhum produto restou.

**Resolução:**

1. Verifique no Inventário de Ficheiros se o campo "Farmácia" foi detectado correctamente. Se o nome da farmácia no ficheiro Infoprex não tem correspondência no `localizacoes.json`, o sistema usa o nome original em Title Case.
2. Verifique se os códigos CLA do laboratório seleccionado correspondem aos que aparecem no ficheiro. Pode usar o expander "Códigos CLA Ativos" para ver os códigos que foram usados no filtro.

### 5.10 Aviso de soma de pesos inválida (Custom)

**Causa:** Ao seleccionar "Custom" no preset de pesos, a soma dos 4 pesos não é exactamente 1.00.

**Resolução:** Ajuste os valores dos 4 pesos até que a soma seja 1.00 (tolerância ±0.001). O sistema mostra o valor actual da soma. Até corrigir, o preset "Padrão" é usado como fallback.

---

## 6. Tarefas de Manutenção (Administrador de Dados)

### 6.1 Adicionar um novo laboratório

1. Abra `config/laboratorios.json` num editor de texto.
2. Adicione uma nova entrada: `"NovoLab": ["1234", "5678"]`.
3. Guarde o ficheiro.
4. Na aplicação em execução, recarregue a página (F5).
5. O sistema detecta `mtime` alterado → invalida cache → recarrega JSON → `NovoLab` aparece no multiselect.

**Regras de validação:**
- Nome do laboratório: ≥2 caracteres, primeira letra maiúscula, alfanuméricos e underscores.
- Códigos CLA: alfanuméricos, máximo 10 caracteres. Duplicados são removidos automaticamente.

### 6.2 Adicionar uma nova farmácia

1. Abra `config/localizacoes.json` num editor de texto.
2. Adicione uma entrada: `"nova farmacia": "Nova Farmácia"`. O termo de pesquisa (chave) deve ter ≥3 caracteres.
3. Guarde o ficheiro.
4. Recarregue a página (F5).

O termo de pesquisa faz matching por word-boundary no nome `LOCALIZACAO` do ficheiro Infoprex. Se o nome no Infoprex for `"Farmácia Nova da Cidade"`, o termo `"nova"` fará match mas `"cid"` faria match errado — use termos suficientemente distintivos.

### 6.3 Adicionar um novo preset de pesos

1. Abra `config/presets.yaml`.
2. Adicione: `  NovoPreset: [0.35, 0.30, 0.20, 0.15]` (os 4 pesos devem somar ≈1.0).
3. Guarde o ficheiro. O novo preset aparecerá no selectbox após recarregar a página.

### 6.4 Alterar URLs das Google Sheets

1. Edite `.streamlit/secrets.toml`.
2. Actualize `SHORTAGES_URL` e/ou `DONOTBUY_URL`.
3. Reinicie a aplicação (`Ctrl+C` + `streamlit run app.py`). As caches TTL são de 1 hora — para forçar o recarregamento, reiniciar é o caminho mais simples.

### 6.5 Validar ficheiros de configuração via CLI

```bash
python -m orders_master.config.validate config/laboratorios.json
python -m orders_master.config.validate config/localizacoes.json
```

O comando sai com código 0 se válido, 1 se inválido. Útil para automatizar validações em scripts de deployment.

---

## 7. Limitações Conhecidas

- **Sem persistência:** Cada sessão é independente. Ao fechar o browser, os dados processados perdem-se. Deve exportar o Excel antes de fechar.
- **Sem autenticação:** A aplicação não tem login, permissões ou multi-tenancy. Assumida como interna numa rede privada.
- **Desktop only:** A interface é optimizada para ecrãs de ≥1280px de largura. Não é responsiva para mobile.
- **Linguagem:** A UI está exclusivamente em Português Europeu.
- **Encoding dos ficheiros Infoprex:** Suporta UTF-16, UTF-8 e Latin-1. Encodings fora desta lista não são suportados.
- **Google Sheets:** A integração depende de URLs públicos. Se a sheet for despublicada ou o URL mudar, a integração falha silenciosamente (sem ruturas, sem lista de "não comprar").
- **Ficheiros grandes:** Embora o parsing seja paralelo, ficheiros muito grandes (>50MB) podem causar lentidão no processamento inicial. Contudo, o recálculo subsequente é sempre rápido porque opera sobre dados já em memória.
- **Propostas negativas:** A proposta pode ser negativa quando o stock actual excede as vendas previstas. Isto é intencional — indica sobre-stock. O sistema não força o valor a zero porque essa informação é valiosa para o utilizador.