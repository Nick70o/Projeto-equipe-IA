"""Routes for sales (PDV checkout)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    ItemVendaOut,
    PixCobrancaCreate,
    PixCobrancaOut,
    PixStatusOut,
    VendaCreate,
    VendaOut,
)
from app.services import venda_service

router = APIRouter(prefix="/vendas", tags=["Vendas"])


def _to_venda_out(venda) -> VendaOut:
    return VendaOut(
        id=venda.id,
        numero=venda.numero,
        data=venda.data,
        subtotal=venda.subtotal,
        desconto=venda.desconto,
        total=venda.total,
        forma_pagamento=venda.forma_pagamento,
        cliente_id=venda.cliente_id,
        valor_recebido=venda.valor_recebido,
        troco=venda.troco,
        status=venda.status,
        itens=[
            ItemVendaOut(
                id=item.id,
                produto_id=item.produto_id,
                produto_nome=item.produto.nome,
                quantidade=item.quantidade,
                preco_unitario=item.preco_unitario,
                subtotal=item.subtotal,
            )
            for item in venda.itens
        ],
    )


@router.get("", response_model=list[VendaOut])
def listar_vendas(
    cliente_id: int | None = Query(default=None), db: Session = Depends(get_db)
) -> list[VendaOut]:
    vendas = venda_service.list_vendas(db, cliente_id=cliente_id)
    return [_to_venda_out(v) for v in vendas]


@router.post("", response_model=VendaOut, status_code=201)
def criar_venda(data: VendaCreate, db: Session = Depends(get_db)) -> VendaOut:
    """Validates stock, writes off stock, posts fiado balance and computes change.

    For Pix, this instant path is only allowed while pix_gateway_ativo=false;
    when it's true, use POST /vendas/pix/cobranca instead.
    """
    venda = venda_service.criar_venda(db, data)
    return _to_venda_out(venda)


@router.post("/pix/cobranca", response_model=PixCobrancaOut, status_code=201)
def criar_cobranca_pix(data: PixCobrancaCreate, db: Session = Depends(get_db)) -> PixCobrancaOut:
    """Creates a sale awaiting payment and requests a Pix charge from Mercado Pago.

    Stock is validated but NOT written off yet — it only happens once the
    payment is confirmed via GET /vendas/pix/status/{venda_id}.
    """
    venda = venda_service.criar_cobranca_pix(db, data)
    return PixCobrancaOut(
        venda_id=venda.id,
        qr_code_base64=venda.mp_qr_code_base64,
        qr_code_copia_cola=venda.mp_qr_code,
        mp_payment_id=venda.mp_payment_id,
        expira_em=venda.expira_em,
    )


@router.get("/pix/status/{venda_id}", response_model=PixStatusOut)
def obter_status_pix(venda_id: int, db: Session = Depends(get_db)) -> PixStatusOut:
    """Polling endpoint: the frontend calls this repeatedly to know when a Pix
    charge has been paid. This is the primary confirmation mechanism (no
    reliance on Mercado Pago webhooks, since this app has no public IP).
    """
    status = venda_service.consultar_ou_confirmar_pix(db, venda_id)
    return PixStatusOut(status=status)


@router.get("/{venda_id}", response_model=VendaOut)
def obter_venda(venda_id: int, db: Session = Depends(get_db)) -> VendaOut:
    return _to_venda_out(venda_service.get_venda(db, venda_id))
