"""Routes for financial reports and dashboards."""
from __future__ import annotations

import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import FaturamentoPorDia, IndicadoresRelatorio, ProdutoRankingOut
from app.services import relatorio_service

router = APIRouter(prefix="/relatorios", tags=["Relatórios"])


def _resolver_periodo(
    periodo: str, inicio: datetime.date | None, fim: datetime.date | None
) -> tuple[datetime.date, datetime.date]:
    hoje = datetime.date.today()
    if periodo == "hoje":
        return hoje, hoje
    if periodo == "semana":
        return hoje - datetime.timedelta(days=6), hoje
    if periodo == "mes":
        return hoje.replace(day=1), hoje
    if periodo == "personalizado":
        if inicio is None or fim is None:
            raise HTTPException(
                status_code=422,
                detail="Informe 'inicio' e 'fim' para o período personalizado",
            )
        return inicio, fim
    raise HTTPException(
        status_code=422,
        detail="Período inválido. Use: hoje, semana, mes ou personalizado",
    )


@router.get("/indicadores", response_model=IndicadoresRelatorio)
def obter_indicadores(
    periodo: str = Query(default="hoje", description="hoje | semana | mes | personalizado"),
    inicio: datetime.date | None = Query(default=None),
    fim: datetime.date | None = Query(default=None),
    db: Session = Depends(get_db),
) -> IndicadoresRelatorio:
    periodo_inicio, periodo_fim = _resolver_periodo(periodo, inicio, fim)
    return relatorio_service.calcular_indicadores(db, periodo_inicio, periodo_fim)


@router.get("/produtos-mais-vendidos", response_model=list[ProdutoRankingOut])
def obter_ranking_produtos(
    periodo: str = Query(default="mes", description="hoje | semana | mes | personalizado"),
    inicio: datetime.date | None = Query(default=None),
    fim: datetime.date | None = Query(default=None),
    limite: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
) -> list[ProdutoRankingOut]:
    periodo_inicio, periodo_fim = _resolver_periodo(periodo, inicio, fim)
    return relatorio_service.ranking_produtos_mais_vendidos(
        db, periodo_inicio, periodo_fim, limite=limite
    )


@router.get("/faturamento-por-dia", response_model=list[FaturamentoPorDia])
def obter_faturamento_por_dia(
    periodo: str = Query(default="mes", description="hoje | semana | mes | personalizado"),
    inicio: datetime.date | None = Query(default=None),
    fim: datetime.date | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[FaturamentoPorDia]:
    periodo_inicio, periodo_fim = _resolver_periodo(periodo, inicio, fim)
    return relatorio_service.faturamento_por_dia(db, periodo_inicio, periodo_fim)
