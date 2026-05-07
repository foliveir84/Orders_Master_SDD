# Smoke Test Checklist — Orders Master Infoprex

Este documento descreve os testes manuais E2E (smoke tests) que devem ser executados antes de cada release para garantir a funcionalidade crítica da aplicação.

## Fluxo Principal (§2.3.1)
- [ ] **Passo 1:** Abrir a aplicação. Seleccionar o laboratório "Mylan" no multiselect (Bloco 1). Deixar "Filtrar por Códigos" vazio.
- [ ] **Passo 2:** Carregar 4 ficheiros Infoprex válidos de lojas diferentes.
- [ ] **Passo 3:** Clicar em "Processar Dados".
- [ ] **Passo 4:** Verificar se a barra de progresso aparece e mostra o texto com os nomes dos ficheiros em tempo real.
- [ ] **Passo 5:** Verificar a presença do "File Inventory" listando os 4 ficheiros com estado "✓ OK".
- [ ] **Passo 6:** Verificar o "Scope Summary Bar" com os totais de produtos e farmácias ("Laboratórios: [Mylan]").
- [ ] **Passo 7:** Confirmar se a Vista Agrupada é apresentada por defeito. Produtos com PVP/P.Custo anómalo devem ter o ícone "⚠️".
- [ ] **Passo 8:** Ajustar o slider "Meses a Prever" para 2.5 e verificar se a coluna "Proposta" recalcula instantaneamente sem reprocessar.
- [ ] **Passo 9:** Clicar no botão "Download Excel Encomendas".
- [ ] **Passo 10:** Abrir o Excel gerado e verificar se a formatação (cores, bold) coincide exactamente com a tabela web (Paridade Web↔Excel).

## Fluxo Alternativo: TXT de Códigos (§2.3.2)
- [ ] **Passo 1:** Sem reiniciar a app, adicionar um ficheiro de texto ao Bloco 2 ("Filtrar por Códigos") com uma lista de 5 CNPs. Manter a selecção de laboratório.
- [ ] **Passo 2:** Clicar em "Processar Dados".
- [ ] **Passo 3:** O Scope Summary Bar deve indicar "Lista TXT (5 códigos)", demonstrando que a prioridade do ficheiro TXT sobrepõe-se à selecção do laboratório.
- [ ] **Passo 4:** A tabela deve listar apenas os códigos contidos no ficheiro TXT.

## Fluxo Excepção: Ficheiro Corrompido (§2.3.3)
- [ ] **Passo 1:** Carregar 3 ficheiros Infoprex válidos e 1 corrompido (ex: sem colunas CPR/DUV, ou encoding inválido) no Bloco 3.
- [ ] **Passo 2:** Clicar em "Processar Dados".
- [ ] **Passo 3:** A aplicação não deve "crashar" (sem white screen of death).
- [ ] **Passo 4:** O File Inventory deve mostrar o ficheiro corrompido a vermelho com a mensagem de erro (ex: `❌ Erro no ficheiro ...`).
- [ ] **Passo 5:** A tabela final deve exibir a consolidação das 3 lojas válidas.

## Fluxo Manutenção: Actualização de JSON (§2.3.4)
- [ ] **Passo 1:** Com a aplicação a correr, editar localmente o ficheiro `config/laboratorios.json`.
- [ ] **Passo 2:** Adicionar uma entrada nova: `"TesteSmokeLab": ["99999"]`. Gravar o ficheiro.
- [ ] **Passo 3:** Fazer "Refresh" (F5) no browser.
- [ ] **Passo 4:** Verificar se "TesteSmokeLab" aparece imediatamente no multiselect (Bloco 1), comprovando o reload por alteração do `mtime`.

## Fluxo Excepção: Filtros Obsoletos (§2.3.5)
- [ ] **Passo 1:** Após os dados estarem processados e a tabela visível, alterar a selecção de laboratório no Bloco 1. Não clicar em "Processar".
- [ ] **Passo 2:** Um banner amarelo ("⚠️ Filtros Modificados!") deve aparecer imediatamente.
- [ ] **Passo 3:** A tabela existente deve permanecer visível para consulta, sem ser apagada.
- [ ] **Passo 4:** Voltar a colocar a selecção inicial. O banner amarelo deve desaparecer.