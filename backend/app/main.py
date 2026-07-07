"""FastAPI application factory for the pharmacy management backend."""
from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.database import Base, engine
from app.exceptions import (
    EstoqueInsuficienteError,
    MercadoPagoError,
    NotFoundError,
    ValidationDomainError,
)
from app.routers import clientes, configuracoes, lotes, produtos, relatorios, vendas, webhook

logger = logging.getLogger("farmacia")
logging.basicConfig(level=logging.INFO)


def create_app() -> FastAPI:
    settings = get_settings()

    # SQLite dev setup: creates tables on startup if they don't exist yet.
    # For PostgreSQL/production, replace this with a proper migration tool
    # (e.g. Alembic) instead of relying on create_all.
    Base.metadata.create_all(bind=engine)

    app = FastAPI(
        title="Sistema de Gestão para Farmácia — API",
        description="API local (sem dependência de internet) para PDV, estoque, validade, fiado e relatórios.",
        version="1.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(NotFoundError)
    async def not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(EstoqueInsuficienteError)
    async def estoque_insuficiente_handler(
        request: Request, exc: EstoqueInsuficienteError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content={
                "detail": str(exc),
                "produto_nome": exc.produto_nome,
                "estoque_restante": exc.restante,
            },
        )

    @app.exception_handler(ValidationDomainError)
    async def validation_domain_handler(
        request: Request, exc: ValidationDomainError
    ) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @app.exception_handler(MercadoPagoError)
    async def mercadopago_error_handler(
        request: Request, exc: MercadoPagoError
    ) -> JSONResponse:
        logger.error("Falha na integração Mercado Pago: %s", exc)
        return JSONResponse(status_code=502, content={"detail": str(exc)})

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        # Never leak stack traces to the client — log details, return a generic message.
        logger.exception("Erro não tratado em %s %s", request.method, request.url)
        return JSONResponse(
            status_code=500,
            content={"detail": "Erro interno do servidor. Consulte os logs do sistema."},
        )

    app.include_router(produtos.router)
    app.include_router(lotes.router)
    app.include_router(clientes.router)
    app.include_router(vendas.router)
    app.include_router(relatorios.router)
    app.include_router(configuracoes.router)
    app.include_router(webhook.router)

    @app.get("/", tags=["Status"])
    def raiz() -> dict[str, str]:
        return {"status": "ok", "sistema": "Farmácia API"}

    return app


app = create_app()
