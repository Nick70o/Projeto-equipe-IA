"""Business logic for financial reports and product ranking."""
from __future__ import annotations

import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import ItemVenda, Produto, Venda


def calcular_indicadores(
    db: Session, inicio: datetime.date, fim: datetime.date
) -> dict:
    inicio_dt = datetime.datetime.combine(inicio, datetime.time.min)
    fim_dt = datetime.datetime.combine(fim, datetime.time.max)

    vendas_stmt = select(Venda).where(Venda.data >= inicio_dt, Venda.data <= fim_dt)
    vendas = list(db.scalars(vendas_stmt).all())

    faturamento = sum(v.total for v in vendas)
    numero_vendas = len(vendas)
    ticket_medio = faturamento / numero_vendas if numero_vendas else 0.0

    lucro_estimado = 0.0
    for venda in vendas:
        for item in venda.itens:
            custo_unitario = item.produto.preco_custo if item.produto else 0.0
            lucro_estimado += (item.preco_unitario - custo_unitario) * item.quantidade
    # Discount applied to a sale is subtracted proportionally from estimated profit.
    lucro_estimado -= sum(v.desconto for v in vendas)

    return {
        "faturamento": round(faturamento, 2),
        "lucro_estimado": round(lucro_estimado, 2),
        "ticket_medio": round(ticket_medio, 2),
        "numero_vendas": numero_vendas,
        "periodo_inicio": inicio,
        "periodo_fim": fim,
    }


def ranking_produtos_mais_vendidos(
    db: Session, inicio: datetime.date, fim: datetime.date, limite: int = 10
) -> list[dict]:
    inicio_dt = datetime.datetime.combine(inicio, datetime.time.min)
    fim_dt = datetime.datetime.combine(fim, datetime.time.max)

    stmt = (
        select(
            Produto.id,
            Produto.nome,
            func.sum(ItemVenda.quantidade).label("quantidade_vendida"),
            func.sum(ItemVenda.subtotal).label("faturamento_gerado"),
        )
        .join(ItemVenda, ItemVenda.produto_id == Produto.id)
        .join(Venda, Venda.id == ItemVenda.venda_id)
        .where(Venda.data >= inicio_dt, Venda.data <= fim_dt)
        .group_by(Produto.id, Produto.nome)
        .order_by(func.sum(ItemVenda.quantidade).desc())
        .limit(limite)
    )
    rows = db.execute(stmt).all()
    return [
        {
            "produto_id": row.id,
            "produto_nome": row.nome,
            "quantidade_vendida": row.quantidade_vendida,
            "faturamento_gerado": round(row.faturamento_gerado, 2),
        }
        for row in rows
    ]


def faturamento_por_dia(
    db: Session, inicio: datetime.date, fim: datetime.date
) -> list[dict]:
    inicio_dt = datetime.datetime.combine(inicio, datetime.time.min)
    fim_dt = datetime.datetime.combine(fim, datetime.time.max)

    stmt = (
        select(
            func.date(Venda.data).label("dia"),
            func.sum(Venda.total).label("faturamento"),
        )
        .where(Venda.data >= inicio_dt, Venda.data <= fim_dt)
        .group_by(func.date(Venda.data))
        .order_by(func.date(Venda.data))
    )
    rows = db.execute(stmt).all()
    return [
        {"dia": datetime.date.fromisoformat(row.dia), "faturamento": round(row.faturamento, 2)}
        for row in rows
    ]
