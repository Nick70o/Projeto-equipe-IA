"""Business logic for products, stock movements and barcode/name search."""
from __future__ import annotations

import datetime

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.exceptions import EstoqueInsuficienteError, NotFoundError
from app.models import MovimentacaoEstoque, Produto, TipoMovimentacao
from app.schemas import MovimentacaoEstoqueCreate, ProdutoCreate, ProdutoUpdate


def list_produtos(db: Session, apenas_estoque_baixo: bool = False) -> list[Produto]:
    stmt = select(Produto).order_by(Produto.nome)
    produtos = list(db.scalars(stmt).all())
    if apenas_estoque_baixo:
        produtos = [p for p in produtos if p.estoque_atual <= p.estoque_minimo]
    return produtos


def get_produto(db: Session, produto_id: int) -> Produto:
    produto = db.get(Produto, produto_id)
    if produto is None:
        raise NotFoundError(f"Produto {produto_id} não encontrado")
    return produto


def create_produto(db: Session, data: ProdutoCreate) -> Produto:
    produto = Produto(**data.model_dump())
    db.add(produto)
    db.commit()
    db.refresh(produto)
    return produto


def update_produto(db: Session, produto_id: int, data: ProdutoUpdate) -> Produto:
    produto = get_produto(db, produto_id)
    for field, value in data.model_dump().items():
        setattr(produto, field, value)
    db.commit()
    db.refresh(produto)
    return produto


def delete_produto(db: Session, produto_id: int) -> None:
    produto = get_produto(db, produto_id)
    db.delete(produto)
    db.commit()


def buscar_produtos(db: Session, termo: str, limite: int = 10) -> list[Produto]:
    """Search by name (partial) or barcode (exact/partial) for the PDV autocomplete."""
    termo_like = f"%{termo}%"
    stmt = (
        select(Produto)
        .where(or_(Produto.nome.ilike(termo_like), Produto.codigo_barras.ilike(termo_like)))
        .order_by(Produto.nome)
        .limit(limite)
    )
    return list(db.scalars(stmt).all())


def dias_para_vencer(produto: Produto) -> int | None:
    """Returns the smallest number of days to expiry among the product's batches."""
    if not produto.controla_lote or not produto.lotes:
        return None
    hoje = datetime.date.today()
    dias = [(lote.data_validade - hoje).days for lote in produto.lotes if lote.quantidade > 0]
    if not dias:
        return None
    return min(dias)


def registrar_movimentacao(
    db: Session, produto_id: int, data: MovimentacaoEstoqueCreate
) -> tuple[Produto, MovimentacaoEstoque]:
    """Registers a stock movement and updates the product's current stock.

    Entrada/Devolução increase stock; Saída/Perda decrease it; Ajuste sets a
    manual correction (positive or negative) — here treated as decrease when
    used to remove and increase when used to add, so quantidade should be
    signed by the caller's motivo for 'ajuste'. For simplicity, ajuste always
    decreases like a correction of loss; use entrada/saida for normal flows.
    """
    produto = get_produto(db, produto_id)

    incrementa = data.tipo in (TipoMovimentacao.ENTRADA, TipoMovimentacao.DEVOLUCAO)
    decrementa = data.tipo in (TipoMovimentacao.SAIDA, TipoMovimentacao.PERDA, TipoMovimentacao.AJUSTE)

    if decrementa and produto.estoque_atual < data.quantidade:
        raise EstoqueInsuficienteError(produto.nome, produto.estoque_atual)

    if incrementa:
        produto.estoque_atual += data.quantidade
    elif decrementa:
        produto.estoque_atual -= data.quantidade

    movimentacao = MovimentacaoEstoque(
        produto_id=produto_id,
        tipo=data.tipo,
        quantidade=data.quantidade,
        motivo=data.motivo,
        observacao=data.observacao,
    )
    db.add(movimentacao)
    db.commit()
    db.refresh(produto)
    db.refresh(movimentacao)
    return produto, movimentacao


def list_movimentacoes(db: Session, produto_id: int) -> list[MovimentacaoEstoque]:
    get_produto(db, produto_id)  # ensures 404 if not found
    stmt = (
        select(MovimentacaoEstoque)
        .where(MovimentacaoEstoque.produto_id == produto_id)
        .order_by(MovimentacaoEstoque.data.desc())
    )
    return list(db.scalars(stmt).all())
