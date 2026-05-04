# Decisões de Arquitectura Registadas (ADRs)

Este ficheiro elenca o resumo dos ADRs definidos no projecto de base:

## ADR-001 — Exclusão Estrita da Redistribuição de Stocks
A componente de redistribuição fica banida deste pipeline para evitar contaminação do escopo e focar integralmente na parte das Encomendas de *Sell Out*.

## ADR-002 — Arquitectura em Camadas
O repositório é forçado a separar as vistas em Domínio, Aplicação e Apresentação, para permitir testes massivos em `pytest` puro sem incorrer em interacções do Streamlit.

## ADR-003 — Single Source of Truth para Formatação
Evitou-se a duplicação de regras visuais entre openpyxl (excel) e o Pandas Styler (web) consolidando-as numa lista mestre em `formatting/rules.py`.

## ADR-004 — Position-Relative Column Addressing (`T Uni`)
Operações mensais usam sempre offset relativo à posição da coluna `T Uni` de modo a salvaguardar o sistema de *bugs sazonais* causados por mudanças na calendarização.

## ADR-005 — Recalculate-in-Memory
Após o processamento inicial, qualquer filtragem adicional ocorre através do recálculo directo no estado persistido `SessionState`, o que assegura uma performance inferior a 500ms por acção na UI.

## ADR-006 a ADR-014 (Sumário de optimizações críticas)
- **ADR-006:** JSONs editáveis (`laboratorios.json` e `localizacoes.json`) quebram a cache perante alterações no tempo de modificação `mtime`.
- **ADR-007:** O processamento recolhe erros (defensive parsing) sem cancelar os ficheiros limpos.
- **ADR-008:** Uso explícito de um `_sort_key` auxiliar na agregação em vez de alfabéticos disfuncionais.
- **ADR-009:** Prevenção de corrupções nas chaves com validação pydantic nas fronteiras do sistema.
- **ADR-010:** Parsing assíncrono multi-ficheiro com `concurrent.futures`.
- **ADR-011:** Total proibição de laços `.apply` de instâncias puras de python com obrigatoriedade da abordagem Vectorizada.
- **ADR-012:** Busca rigorosa de localização com `min_length=3` com limites `\b` para prevenir falsos positivos.
- **ADR-013:** A linha de "Grupo" não possui marca específica e foi isolada logicamente em processos de filtro para evitar desaparecimento indesejado.
- **ADR-014:** Absoluta restrição a `except:` vazios; exige-se sempre tipagem e logging associado de erros.
