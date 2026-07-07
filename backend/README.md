# Backend — Sistema de Gestão para Farmácia

API local (FastAPI + SQLite), sem dependência de internet.

## Como rodar

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
copy .env.example .env          # ajustar se necessário
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Documentação automática: http://localhost:8000/docs (Swagger) e /redoc.

O banco SQLite (`farmacia.db`) é criado automaticamente na primeira execução.
