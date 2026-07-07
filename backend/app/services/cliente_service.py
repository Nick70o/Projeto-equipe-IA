"""Business logic for customers and fiado (store-credit) payments."""
from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.exceptions import NotFoundError, ValidationDomainError
from app.models import Cliente, PagamentoFiado
from app.schemas import ClienteCreate, ClienteUpdate, PagamentoFiadoCreate


def list_clientes(db: Session, termo: str | None = None) -> list[Cliente]:
    stmt = select(Cliente).order_by(Cliente.nome)
    if termo:
        termo_like = f"%{termo}%"
        stmt = stmt.where(
            or_(Cliente.nome.ilike(termo_like), Cliente.telefone.ilike(termo_like))
        )
    return list(db.scalars(stmt).all())


def get_cliente(db: Session, cliente_id: int) -> Cliente:
    cliente = db.get(Cliente, cliente_id)
    if cliente is None:
        raise NotFoundError(f"Cliente {cliente_id} não encontrado")
    return cliente


def create_cliente(db: Session, data: ClienteCreate) -> Cliente:
    cliente = Cliente(**data.model_dump())
    db.add(cliente)
    db.commit()
    db.refresh(cliente)
    return cliente


def update_cliente(db: Session, cliente_id: int, data: ClienteUpdate) -> Cliente:
    cliente = get_cliente(db, cliente_id)
    for field, value in data.model_dump().items():
        setattr(cliente, field, value)
    db.commit()
    db.refresh(cliente)
    return cliente


def delete_cliente(db: Session, cliente_id: int) -> None:
    cliente = get_cliente(db, cliente_id)
    db.delete(cliente)
    db.commit()


def registrar_pagamento_fiado(
    db: Session, cliente_id: int, data: PagamentoFiadoCreate
) -> tuple[Cliente, PagamentoFiado]:
    cliente = get_cliente(db, cliente_id)
    if data.valor > cliente.saldo_devedor:
        raise ValidationDomainError(
            f"Valor de pagamento (R$ {data.valor:.2f}) maior que o saldo devedor "
            f"(R$ {cliente.saldo_devedor:.2f})"
        )
    cliente.saldo_devedor -= data.valor
    pagamento = PagamentoFiado(cliente_id=cliente_id, valor=data.valor)
    db.add(pagamento)
    db.commit()
    db.refresh(cliente)
    db.refresh(pagamento)
    return cliente, pagamento


def list_pagamentos(db: Session, cliente_id: int) -> list[PagamentoFiado]:
    get_cliente(db, cliente_id)
    stmt = (
        select(PagamentoFiado)
        .where(PagamentoFiado.cliente_id == cliente_id)
        .order_by(PagamentoFiado.data.desc())
    )
    return list(db.scalars(stmt).all())
