"""Business logic for batches (lotes) and expiry-date queries."""
from __future__ import annotations

import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.exceptions import NotFoundError
from app.models import Lote, Produto
from app.schemas import LoteCreate, LoteUpdate


def get_lote(db: Session, lote_id: int) -> Lote:
    lote = db.get(Lote, lote_id)
    if lote is None:
        raise NotFoundError(f"Lote {lote_id} não encontrado")
    return lote


def list_lotes_do_produto(db: Session, produto_id: int) -> list[Lote]:
    stmt = select(Lote).where(Lote.produto_id == produto_id).order_by(Lote.data_validade)
    return list(db.scalars(stmt).all())


def create_lote(db: Session, produto_id: int, data: LoteCreate) -> Lote:
    produto = db.get(Produto, produto_id)
    if produto is None:
        raise NotFoundError(f"Produto {produto_id} não encontrado")
    lote = Lote(produto_id=produto_id, **data.model_dump())
    db.add(lote)
    db.commit()
    db.refresh(lote)
    return lote


def update_lote(db: Session, lote_id: int, data: LoteUpdate) -> Lote:
    lote = get_lote(db, lote_id)
    for field, value in data.model_dump().items():
        setattr(lote, field, value)
    db.commit()
    db.refresh(lote)
    return lote


def delete_lote(db: Session, lote_id: int) -> None:
    lote = get_lote(db, lote_id)
    db.delete(lote)
    db.commit()


def consultar_lotes_por_validade(
    db: Session, dias: int | None = None, apenas_vencidos: bool = False
) -> list[tuple[Lote, int]]:
    """Returns (lote, dias_restantes) pairs, ordered by closest expiry date.

    - apenas_vencidos=True: only batches whose expiry date already passed.
    - dias=N: batches expiring within the next N days (including overdue ones).
    - No filters: returns all batches.
    """
    hoje = datetime.date.today()
    stmt = (
        select(Lote)
        .options(joinedload(Lote.produto))
        .order_by(Lote.data_validade)
    )
    lotes = list(db.scalars(stmt).all())

    resultado: list[tuple[Lote, int]] = []
    for lote in lotes:
        dias_restantes = (lote.data_validade - hoje).days
        if apenas_vencidos and dias_restantes >= 0:
            continue
        if dias is not None and not apenas_vencidos and dias_restantes > dias:
            continue
        resultado.append((lote, dias_restantes))
    return resultado
