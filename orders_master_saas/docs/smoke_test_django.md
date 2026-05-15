# Django SaaS Smoke Test Checklist

## Fluxo 1: Upload + Processamento
- [ ] Login com credenciais validas
- [ ] Seleccionar laboratorio
- [ ] Carregar 2+ ficheiros Infoprex
- [ ] Clicar "Processar Dados"
- [ ] Verificar tabela com formatacao condicional
- [ ] Verificar Scope Bar com metricas correctas
- [ ] Verificar File Inventory com estado dos ficheiros

## Fluxo 2: Recalculo HTMX
- [ ] Toggle "Ver Detalhe" -> tabela muda sem reload total
- [ ] Toggle "Mes Anterior" -> valores recalculam
- [ ] Alterar "Meses a Prever" -> proposta recalcula
- [ ] Alterar preset -> pesos actualizam
- [ ] Download Excel -> ficheiro descarregado

## Fluxo 3: Validacao de Licenca
- [ ] Upload de ficheiro de farmacia nao licenciada -> rejeitado com erro claro
- [ ] Upload de ficheiro de farmacia licenciada -> aceite

## Fluxo 4: Multi-Tenancy
- [ ] Utilizador A nao ve dados do Utilizador B
- [ ] Admin ve gestao de clientes e farmacias

## Fluxo 5: Subscricao
- [ ] BD Rupturas visivel quando activa
- [ ] BD Rupturas oculta quando inactiva
- [ ] Subscricao expirada -> bloqueio de acesso