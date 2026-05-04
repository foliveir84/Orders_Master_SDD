# Arquitectura e Padrões de Design

O projecto segue uma arquitectura em camadas com separação estrita entre domínio e apresentação. Todas as dependências apontam para o domínio; nenhum módulo de domínio importa código de apresentação.

## Arquitectura em Camadas
- **Presentation (Apresentação):** `app.py` e a pasta `ui/`. Componentes puramente focados no Streamlit.
- **Application (Aplicação):** `orders_master/app_services/`. Coordena processos de ingestão e agregação.
- **Domain (Domínio):** Toda a pasta `orders_master/` (excepto app_services). Concentra as integrações externas, lógicas de limpeza, validações de schema e constantes. 

## Estrutura de Directorias
```text
orders_master_infoprex/
├── app.py                          # Entry-point do Streamlit
├── config/                         # Configurações JSON/YAML editáveis em produção
├── orders_master/                  # Domínio puro (agnóstico de framework web)
│   ├── constants.py                # Centralização de constantes
│   ├── schemas.py                  # Schemas tipados (Pydantic)
│   ├── ingestion/                  # Lógica de parsing (txt, csv)
│   ├── aggregation/                # Lógica de agregação core
│   ├── business_logic/             # Cálculo de médias, limpeza e propostas
│   ├── integrations/               # Integrações externas (Google Sheets)
│   ├── config/                     # Loaders com validação de schemas
│   ├── formatting/                 # Fonte única de verdade de regras visuais
│   └── app_services/               # Lógica de coordenação (Application Layer)
├── ui/                             # Camada de apresentação Streamlit
└── tests/                          # Testes unitários e de integração
```

## Padrões de Design Adoptados
- **Single Source of Truth para formatações:** As regras (Grupo, Não Comprar, Rutura, Validade, Anomalias de preço) residem em `formatting/rules.py` como SSOT e são aplicadas tanto ao render na web como na exportação do Excel.
- **Endereçamento Posicional:** Devido a meses dinâmicos (`JAN`, `FEV`), qualquer cálculo aos dados de meses é efetuado através da âncora relacional `T Uni`.
- **Aggregate-once + recalculate-in-memory:** Acções pesadas sobre ficheiros apenas são corridas no clique inicial. Filtros subsequentes são corridos em memória no *SessionState*.
- **Domain Types:** Os esquemas pydantic são aplicados nas fronteiras para assegurar coerência (e prevenir erros de chaves dinâmicas).
