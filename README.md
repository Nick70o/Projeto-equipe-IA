# Sistema de Gestão para Farmácia

Sistema local (sem dependência de internet) para gestão de uma farmácia: ponto de venda (PDV), controle de estoque, controle de validade de lotes, cadastro de clientes com fiado e relatórios financeiros.

Composto por dois projetos independentes:

- **`backend/`** — API em FastAPI + SQLite.
- **`frontend/`** — Interface web em HTML + Tailwind (via CDN) + JavaScript vanilla (ES modules), consumindo a API do backend.

A especificação completa de telas e regras de negócio está em [`design-spec.md`](./design-spec.md).

## Funcionalidades

- **PDV / Vendas** — registro de vendas com baixa automática de estoque.
- **Estoque** — listagem de produtos com alertas de estoque baixo e estoque zerado.
- **Validade** — controle de lotes com alertas de vencimento em 30/60/90 dias.
- **Clientes e fiado** — cadastro de clientes, conta a receber (fiado) e registro de pagamentos.
- **Relatórios** — faturamento, lucro estimado, ticket médio e produtos mais vendidos.

## Requisitos

- Python 3.11+ (backend)
- Node.js (apenas se for usar `npx serve` para servir o frontend — veja abaixo) **ou** VSCode com a extensão Live Server **ou** qualquer outro servidor estático de sua preferência.

## Como instalar e rodar

O backend e o frontend são executados separadamente. Rode o backend primeiro.

### 1. Backend

#### Windows (PowerShell)

```powershell
cd backend
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

#### Linux / macOS

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

O banco SQLite (`farmacia.db`) é criado automaticamente na primeira execução. A documentação interativa da API (Swagger) fica disponível em `http://localhost:8000/docs`.

### 2. Frontend

O frontend usa `<script type="module">` e `fetch`, portanto **não pode ser aberto diretamente com duplo clique (`file://`)** — precisa ser servido por um servidor HTTP estático. Com o backend já rodando em `localhost:8000`, escolha uma das opções:

**Opção A — `npx serve` (Windows e Linux):**

```bash
npx serve frontend
```

**Opção B — VSCode:** abra a pasta `frontend/` no VSCode e use a extensão **Live Server**, clicando com o botão direito em `pdv.html` → "Open with Live Server".

A tela inicial/padrão é `pdv.html`.

## Estrutura de pastas

```
Projeto-equipe-IA/
├── design-spec.md          # Especificação de UX/UI e regras de negócio
├── README.md                # Este arquivo
├── backend/
│   ├── README.md            # Instruções específicas do backend
│   ├── .env.example          # Modelo de variáveis de ambiente
│   ├── requirements.txt
│   └── app/
│       ├── main.py           # Ponto de entrada da API (FastAPI app)
│       ├── config.py         # Configurações (env vars)
│       ├── database.py       # Conexão e sessão do SQLite
│       ├── models.py         # Modelos SQLAlchemy
│       ├── schemas.py        # Schemas Pydantic (validação/serialização)
│       ├── exceptions.py     # Exceções de domínio (ex.: estoque insuficiente)
│       ├── routers/          # Rotas da API: produtos, lotes, clientes, vendas, relatorios
│       └── services/         # Regras de negócio por domínio
└── frontend/
    ├── pdv.html               # Tela padrão/inicial (ponto de venda)
    ├── estoque.html            # Listagem e alertas de estoque
    ├── produto.html            # Cadastro/edição de produto
    ├── validade.html           # Controle de validade/lotes
    ├── clientes.html           # Listagem de clientes
    ├── cliente-detalhe.html    # Detalhe do cliente e fiado
    ├── relatorios.html         # Relatórios financeiros
    ├── configuracoes.html
    ├── css/styles.css
    └── js/
        ├── api.js              # Centraliza as chamadas fetch para o backend
        └── ...                 # Um arquivo JS por tela
```

## Rotas da API (resumo)

As rotas não usam prefixo `/api`. Principais grupos: `/produtos`, `/lotes`, `/clientes`, `/vendas`, `/relatorios`. Detalhes completos de parâmetros e respostas em `http://localhost:8000/docs`.

## Limitações conhecidas / próximos passos

- **Sem autenticação/controle de perfil de usuário.** Qualquer pessoa com acesso à interface tem acesso total ao sistema. A necessidade de login está mencionada no `design-spec.md` como algo ainda em aberto.
- **Filtro por categoria no Estoque é feito no frontend.** A API não possui suporte a filtro de categoria — a tela busca todos os produtos e filtra localmente no navegador.
- **Não há emissão de recibo/impressão real.** A confirmação de venda no PDV é apenas uma tela de confirmação em tela, sem geração de PDF ou integração com impressora.

## Documentação adicional

- Instruções específicas do backend: [`backend/README.md`](./backend/README.md)
- Especificação de UX/UI e regras de negócio: [`design-spec.md`](./design-spec.md)
