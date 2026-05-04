# Guidelines de Desenvolvimento

A fim de garantir consistência técnica, alta performance e legibilidade, o projecto segue as seguintes directrizes.

## 1. Operações Vectorizadas (Performance)
- **Regra:** Nenhuma função de domínio pode invocar funções `lambda` nas invocações Pandas do tipo `.apply`.
- **Razão:** Processamento `.apply(lambda...)` resulta numa acentuada degradação na eficácia do modelo comparativamente à operação vectorial (cerca de 5x a 10x mais demorado).
- **Abordagem Correcta:** Usar sempre métodos nativos vectoriais do pandas (ex: `.str.replace`, `np.where`, `pd.cut`).

## 2. Tipagem Forçada e Validação 
- Todas as funções públicas devem estar tipadas de forma compreensiva (`mypy --strict`).
- Validações intensas só se dão na **fronteira** (parsing e inputs da UI) recorrendo aos pydantics contidos em `schemas.py`. *Loops* ou ciclos rápidos confiam puramente no contrato pré-estabelecido de modo a evitar custos processuais em runtime.

## 3. Tratamento de Excepções Obrigatório
- Estão completamente **interditados** bare exceptions do estilo `except: pass`. 
- Qualquer falha passível de ser recuperada regista o seu lapso por `logger.debug` ou `logger.warning`.
- Na ingestão de ficheiros (Parsing Defensivo), a excepção é tratada tipicamente, a falha gravada num pacote global (`file_errors`) e as restantes fases continuam normalmente com os dados recuperáveis.

## 4. Regras de Logging
- Funções em produção não utilizam `print()`. 
- Registo é padronizado por intermédio da lib core em `logger.py` e gerido estritamente pelo respectivo ambiente. Níveis são respeitados (`DEBUG` para parsing; `INFO` transições de etapa; `WARNING`/`ERROR` nas anomalias).

## 5. Independência Estrita da UI
- Os componentes alojados no núcleo `orders_master/` são agnósticos ao `streamlit`. Todo e qualquer `import streamlit` está inteiramente restrito ao ficheiro root `app.py` e aos ficheiros alocados à pasta `ui/`.
