# Resumo do projeto: Sistema de Gestão para Farmácia (uso local)

**Stack:** Backend FastAPI + SQLite (`backend/`), Frontend HTML/Tailwind/JS vanilla (`frontend/`), especificação de UX em `design-spec.md`, documentação em `README.md`.

## O que foi construído

1. **ui-ux-designer** → `design-spec.md`: navegação, telas (PDV, Estoque, Validade/Lotes, Clientes/Fiado, Relatórios), paleta de cores, tipografia, microcopy em PT-BR.
2. **backend-dev** → API completa: produtos, lotes, movimentações de estoque, clientes/fiado, vendas (com baixa automática de estoque, bloqueio de venda sem estoque, cálculo de troco), relatórios financeiros.
3. **frontend-dev** → as 8 telas do spec, consumindo a API via `js/api.js`.
4. **qa-engineer** → revisão de integração, encontrou 7 divergências de contrato entre frontend e backend (paths errados, nomes de campo diferentes, cadastro de lotes sendo descartado silenciosamente).
5. **frontend-dev** (2ª rodada) → corrigiu os 7 pontos + 2 bugs extras encontrados na verificação cruzada.
6. **Tech Lead (eu)** → instalei Python 3.12 no ambiente, rodei o backend de verdade e testei 21 cenários end-to-end (venda, fiado, estoque insuficiente, relatórios, CORS, delete). Encontrei e corrigi mais um bug: rotas `DELETE` quebravam a inicialização do servidor (`status_code=204` incompatível com `response_model` implícito).
7. **docs-writer** → `README.md` na raiz, com instalação, funcionalidades e limitações conhecidas.
8. **Rodei o sistema completo** (backend :8000 + frontend :5500) e corrigi um bug adicional descoberto no uso real: `API_BASE` do frontend estava vazio, fazendo as chamadas de API caírem no próprio servidor do frontend em vez do backend — corrigido para `http://127.0.0.1:8000`.

## Estado atual

Sistema funcional de ponta a ponta, testado via API e em uso real no navegador.

Para rodar novamente:
- Backend: `cd backend`, ativar venv (`venv/Scripts/python.exe`), `uvicorn app.main:app --host 127.0.0.1 --port 8000`
- Frontend: servir a pasta `frontend/` com um servidor estático (ex. `python -m http.server 5500`), nunca abrir via `file://`
- Backend em `http://127.0.0.1:8000` (docs em `/docs`), frontend em `http://127.0.0.1:5500/pdv.html`

## Próximos passos sugeridos

- **Testar a UI mais a fundo** no navegador (fluxos completos de cada tela, não só o que já foi validado).
- **Autenticação/perfis** (Atendente/Responsável) — mencionado no design-spec mas não implementado.
- **Filtro de categoria** no Estoque hoje é só client-side; decidir se vale implementar no backend.
- **Recibo/impressão** de venda — hoje é só uma tela de confirmação.
- Quando estiver satisfeito com os testes manuais, decidir sobre **deploy/empacotamento** para uso real na farmácia (ex.: rodar como serviço no Windows, atalho para abrir os dois servidores juntos) — isso passa pelo **devops**, sempre com confirmação antes de qualquer coisa em produção.
