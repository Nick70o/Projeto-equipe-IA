"""Routes for customers and fiado (store-credit) payments."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    ClienteCreate,
    ClienteOut,
    ClienteUpdate,
    PagamentoFiadoCreate,
    PagamentoFiadoOut,
)
from app.services import cliente_service

router = APIRouter(prefix="/clientes", tags=["Clientes / Fiado"])


@router.get("", response_model=list[ClienteOut])
def listar_clientes(
    q: str | None = Query(default=None, description="Busca por nome ou telefone"),
    db: Session = Depends(get_db),
) -> list[ClienteOut]:
    return cliente_service.list_clientes(db, termo=q)


@router.get("/{cliente_id}", response_model=ClienteOut)
def obter_cliente(cliente_id: int, db: Session = Depends(get_db)) -> ClienteOut:
    return cliente_service.get_cliente(db, cliente_id)


@router.post("", response_model=ClienteOut, status_code=201)
def criar_cliente(data: ClienteCreate, db: Session = Depends(get_db)) -> ClienteOut:
    return cliente_service.create_cliente(db, data)


@router.put("/{cliente_id}", response_model=ClienteOut)
def atualizar_cliente(
    cliente_id: int, data: ClienteUpdate, db: Session = Depends(get_db)
) -> ClienteOut:
    return cliente_service.update_cliente(db, cliente_id, data)


@router.delete("/{cliente_id}", status_code=204, response_model=None)
def remover_cliente(cliente_id: int, db: Session = Depends(get_db)) -> None:
    cliente_service.delete_cliente(db, cliente_id)


@router.post("/{cliente_id}/pagamentos", response_model=PagamentoFiadoOut, status_code=201)
def registrar_pagamento(
    cliente_id: int, data: PagamentoFiadoCreate, db: Session = Depends(get_db)
) -> PagamentoFiadoOut:
    _, pagamento = cliente_service.registrar_pagamento_fiado(db, cliente_id, data)
    return pagamento


@router.get("/{cliente_id}/pagamentos", response_model=list[PagamentoFiadoOut])
def listar_pagamentos(cliente_id: int, db: Session = Depends(get_db)) -> list[PagamentoFiadoOut]:
    return cliente_service.list_pagamentos(db, cliente_id)
