"""Routes for products, stock movements and PDV search — thin handlers only."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    MovimentacaoEstoqueCreate,
    MovimentacaoEstoqueOut,
    ProdutoBusca,
    ProdutoCreate,
    ProdutoOut,
    ProdutoUpdate,
)
from app.services import produto_service

router = APIRouter(prefix="/produtos", tags=["Produtos"])


@router.get("", response_model=list[ProdutoOut])
def listar_produtos(
    apenas_estoque_baixo: bool = Query(default=False),
    db: Session = Depends(get_db),
) -> list[ProdutoOut]:
    return produto_service.list_produtos(db, apenas_estoque_baixo=apenas_estoque_baixo)


@router.get("/buscar", response_model=list[ProdutoBusca])
def buscar_produtos(
    q: str = Query(min_length=1, description="Nome ou código de barras"),
    limite: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
) -> list[ProdutoBusca]:
    """Autocomplete used by the PDV: search by name or barcode."""
    produtos = produto_service.buscar_produtos(db, termo=q, limite=limite)
    return [
        ProdutoBusca(
            id=p.id,
            nome=p.nome,
            codigo_barras=p.codigo_barras,
            preco_venda=p.preco_venda,
            estoque_atual=p.estoque_atual,
            unidade_medida=p.unidade_medida,
            dias_para_vencer=produto_service.dias_para_vencer(p),
        )
        for p in produtos
    ]


@router.get("/{produto_id}", response_model=ProdutoOut)
def obter_produto(produto_id: int, db: Session = Depends(get_db)) -> ProdutoOut:
    return produto_service.get_produto(db, produto_id)


@router.post("", response_model=ProdutoOut, status_code=201)
def criar_produto(data: ProdutoCreate, db: Session = Depends(get_db)) -> ProdutoOut:
    return produto_service.create_produto(db, data)


@router.put("/{produto_id}", response_model=ProdutoOut)
def atualizar_produto(
    produto_id: int, data: ProdutoUpdate, db: Session = Depends(get_db)
) -> ProdutoOut:
    return produto_service.update_produto(db, produto_id, data)


@router.delete("/{produto_id}", status_code=204, response_model=None)
def remover_produto(produto_id: int, db: Session = Depends(get_db)) -> None:
    produto_service.delete_produto(db, produto_id)


@router.post("/{produto_id}/movimentacoes", response_model=MovimentacaoEstoqueOut, status_code=201)
def registrar_movimentacao(
    produto_id: int, data: MovimentacaoEstoqueCreate, db: Session = Depends(get_db)
) -> MovimentacaoEstoqueOut:
    """Dedicated quick entry/exit endpoint — does not require full product edit."""
    _, movimentacao = produto_service.registrar_movimentacao(db, produto_id, data)
    return movimentacao


@router.get("/{produto_id}/movimentacoes", response_model=list[MovimentacaoEstoqueOut])
def listar_movimentacoes(
    produto_id: int, db: Session = Depends(get_db)
) -> list[MovimentacaoEstoqueOut]:
    return produto_service.list_movimentacoes(db, produto_id)
