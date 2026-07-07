"""Routes for batches (lotes) linked to products and expiry-date queries."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import LoteComProdutoOut, LoteCreate, LoteOut, LoteUpdate
from app.services import lote_service

router = APIRouter(tags=["Lotes / Validade"])


@router.get("/produtos/{produto_id}/lotes", response_model=list[LoteOut])
def listar_lotes_do_produto(produto_id: int, db: Session = Depends(get_db)) -> list[LoteOut]:
    return lote_service.list_lotes_do_produto(db, produto_id)


@router.post("/produtos/{produto_id}/lotes", response_model=LoteOut, status_code=201)
def criar_lote(produto_id: int, data: LoteCreate, db: Session = Depends(get_db)) -> LoteOut:
    return lote_service.create_lote(db, produto_id, data)


@router.put("/lotes/{lote_id}", response_model=LoteOut)
def atualizar_lote(lote_id: int, data: LoteUpdate, db: Session = Depends(get_db)) -> LoteOut:
    return lote_service.update_lote(db, lote_id, data)


@router.delete("/lotes/{lote_id}", status_code=204, response_model=None)
def remover_lote(lote_id: int, db: Session = Depends(get_db)) -> None:
    lote_service.delete_lote(db, lote_id)


@router.get("/lotes", response_model=list[LoteComProdutoOut])
def consultar_lotes_por_validade(
    dias: int | None = Query(default=None, description="Vence em até N dias (30/60/90)"),
    vencidos: bool = Query(default=False, description="Apenas lotes já vencidos"),
    db: Session = Depends(get_db),
) -> list[LoteComProdutoOut]:
    """Query batches by expiry range: vencidos, or vence em 30/60/90 dias."""
    pares = lote_service.consultar_lotes_por_validade(db, dias=dias, apenas_vencidos=vencidos)
    return [
        LoteComProdutoOut(
            id=lote.id,
            produto_id=lote.produto_id,
            numero_lote=lote.numero_lote,
            quantidade=lote.quantidade,
            data_validade=lote.data_validade,
            produto_nome=lote.produto.nome,
            dias_restantes=dias_restantes,
        )
        for lote, dias_restantes in pares
    ]
