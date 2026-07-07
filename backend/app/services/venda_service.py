"""Business logic for sales: stock validation, automatic stock write-off,
fiado (store credit) posting, change calculation, and Pix-via-Mercado-Pago
charge creation / confirmation.
"""
from __future__ import annotations

import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.exceptions import EstoqueInsuficienteError, NotFoundError, ValidationDomainError
from app.models import Cliente, FormaPagamento, ItemVenda, Produto, StatusVenda, Venda
from app.schemas import ItemVendaCreate, PixCobrancaCreate, VendaCreate
from app.services import configuracao_service, mercadopago_service


def _proximo_numero_venda(db: Session) -> int:
    maior = db.scalar(select(func.max(Venda.numero)))
    return (maior or 0) + 1


def _validar_e_carregar_produtos(
    db: Session, itens: list[ItemVendaCreate]
) -> dict[int, Produto]:
    produtos_por_id: dict[int, Produto] = {}
    for item in itens:
        produto = db.get(Produto, item.produto_id)
        if produto is None:
            raise NotFoundError(f"Produto {item.produto_id} não encontrado")
        if produto.estoque_atual < item.quantidade:
            raise EstoqueInsuficienteError(produto.nome, produto.estoque_atual)
        produtos_por_id[item.produto_id] = produto
    return produtos_por_id


def _calcular_subtotal_total(
    itens: list[ItemVendaCreate], produtos_por_id: dict[int, Produto], desconto: float
) -> tuple[float, float]:
    subtotal = sum(produtos_por_id[item.produto_id].preco_venda * item.quantidade for item in itens)
    total = max(subtotal - desconto, 0.0)
    return subtotal, total


def criar_venda(db: Session, data: VendaCreate) -> Venda:
    """Creates a sale: validates stock, writes off stock per item, applies
    fiado to the customer's balance if applicable, and computes change.

    Pix sales go through this same instant path only when the Mercado Pago
    gateway integration is disabled (`pix_gateway_ativo=false`). When it's
    enabled, Pix sales must be created via `criar_cobranca_pix` instead, since
    they need to wait for payment confirmation before stock is written off.
    """
    if data.forma_pagamento == FormaPagamento.FIADO and data.cliente_id is None:
        raise ValidationDomainError("Venda fiado exige um cliente vinculado")

    if data.forma_pagamento == FormaPagamento.PIX and configuracao_service.get_bool(
        db, configuracao_service.PIX_GATEWAY_ATIVO, default=False
    ):
        raise ValidationDomainError(
            "Integração Pix com Mercado Pago está ativa — use "
            "POST /vendas/pix/cobranca para vendas em Pix"
        )

    cliente: Cliente | None = None
    if data.cliente_id is not None:
        cliente = db.get(Cliente, data.cliente_id)
        if cliente is None:
            raise NotFoundError(f"Cliente {data.cliente_id} não encontrado")

    produtos_por_id = _validar_e_carregar_produtos(db, data.itens)
    subtotal, total = _calcular_subtotal_total(data.itens, produtos_por_id, data.desconto)

    if data.forma_pagamento == FormaPagamento.DINHEIRO:
        if data.valor_recebido is None or data.valor_recebido < total:
            raise ValidationDomainError(
                "Valor recebido insuficiente para concluir a venda em dinheiro"
            )
        troco = round(data.valor_recebido - total, 2)
    else:
        troco = None

    venda = Venda(
        numero=_proximo_numero_venda(db),
        desconto=data.desconto,
        subtotal=subtotal,
        total=total,
        forma_pagamento=data.forma_pagamento,
        cliente_id=data.cliente_id,
        valor_recebido=data.valor_recebido,
        troco=troco,
        status=StatusVenda.CONCLUIDA,
    )
    db.add(venda)

    for item in data.itens:
        produto = produtos_por_id[item.produto_id]
        produto.estoque_atual -= item.quantidade
        db.add(
            ItemVenda(
                venda=venda,
                produto_id=produto.id,
                quantidade=item.quantidade,
                preco_unitario=produto.preco_venda,
                subtotal=produto.preco_venda * item.quantidade,
            )
        )

    if data.forma_pagamento == FormaPagamento.FIADO and cliente is not None:
        cliente.saldo_devedor += total

    db.commit()
    db.refresh(venda)
    return venda


def get_venda(db: Session, venda_id: int) -> Venda:
    venda = db.get(Venda, venda_id)
    if venda is None:
        raise NotFoundError(f"Venda {venda_id} não encontrada")
    return venda


def list_vendas(db: Session, cliente_id: int | None = None) -> list[Venda]:
    stmt = select(Venda).order_by(Venda.data.desc())
    if cliente_id is not None:
        stmt = stmt.where(Venda.cliente_id == cliente_id)
    return list(db.scalars(stmt).all())


# --------------------------------------------------------------------------
# Pix via Mercado Pago
# --------------------------------------------------------------------------


def criar_cobranca_pix(db: Session, data: PixCobrancaCreate) -> Venda:
    """Validates stock (without writing it off yet), creates a sale in
    AGUARDANDO_PAGAMENTO status and requests a Pix charge from Mercado Pago.

    Stock is only written off later, once payment is confirmed — see
    `consultar_ou_confirmar_pix`.
    """
    cliente: Cliente | None = None
    if data.cliente_id is not None:
        cliente = db.get(Cliente, data.cliente_id)
        if cliente is None:
            raise NotFoundError(f"Cliente {data.cliente_id} não encontrado")

    produtos_por_id = _validar_e_carregar_produtos(db, data.itens)
    subtotal, total = _calcular_subtotal_total(data.itens, produtos_por_id, data.desconto)

    venda = Venda(
        numero=_proximo_numero_venda(db),
        desconto=data.desconto,
        subtotal=subtotal,
        total=total,
        forma_pagamento=FormaPagamento.PIX,
        cliente_id=data.cliente_id,
        status=StatusVenda.AGUARDANDO_PAGAMENTO,
    )
    db.add(venda)

    for item in data.itens:
        produto = produtos_por_id[item.produto_id]
        db.add(
            ItemVenda(
                venda=venda,
                produto_id=produto.id,
                quantidade=item.quantidade,
                preco_unitario=produto.preco_venda,
                subtotal=produto.preco_venda * item.quantidade,
            )
        )

    # Flush so `venda.id` is available to use as the external_reference sent
    # to Mercado Pago, without committing yet (charge creation can still fail).
    db.flush()

    resposta_mp = mercadopago_service.criar_pagamento_pix(
        valor=total,
        descricao=f"Venda #{venda.numero} - Farmácia",
        external_reference=str(venda.id),
    )

    transaction_data = (
        resposta_mp.get("point_of_interaction", {}).get("transaction_data", {})
    )
    venda.mp_payment_id = str(resposta_mp.get("id")) if resposta_mp.get("id") else None
    venda.mp_qr_code = transaction_data.get("qr_code")
    venda.mp_qr_code_base64 = transaction_data.get("qr_code_base64")

    date_of_expiration = resposta_mp.get("date_of_expiration")
    if date_of_expiration:
        try:
            parsed = datetime.datetime.fromisoformat(date_of_expiration)
            # Normalize to naive UTC to keep comparisons simple against
            # datetime.utcnow() elsewhere in this module.
            if parsed.tzinfo is not None:
                parsed = parsed.astimezone(datetime.timezone.utc).replace(tzinfo=None)
            venda.expira_em = parsed
        except ValueError:
            venda.expira_em = None

    db.commit()
    db.refresh(venda)
    return venda


def _baixar_estoque_pix(db: Session, venda: Venda) -> None:
    """Writes off stock for a confirmed Pix sale.

    Stock was intentionally left untouched at charge-creation time (see
    `criar_cobranca_pix`), so it's only decremented here, once payment is
    confirmed as approved.
    """
    for item in venda.itens:
        produto = db.get(Produto, item.produto_id)
        if produto is not None:
            produto.estoque_atual = max(produto.estoque_atual - item.quantidade, 0.0)


def consultar_ou_confirmar_pix(db: Session, venda_id: int) -> str:
    """Returns the current Pix payment status for a sale.

    If the sale is already in a terminal state (CONCLUIDA/CANCELADA/EXPIRADA)
    it's returned directly from the database. Otherwise, Mercado Pago's API is
    queried in real time (this is the primary confirmation mechanism, since
    the app has no public IP to receive webhooks) and, if approved, stock is
    written off and the sale is marked CONCLUIDA right here.
    """
    venda = get_venda(db, venda_id)

    if venda.status == StatusVenda.CONCLUIDA:
        return "pago"
    if venda.status == StatusVenda.CANCELADA:
        return "cancelado"
    if venda.status == StatusVenda.EXPIRADA:
        return "expirado"

    if venda.mp_payment_id is None:
        # Should not normally happen — a pending Pix sale always has a charge.
        return "pendente"

    resposta_mp = mercadopago_service.consultar_pagamento(venda.mp_payment_id)
    status_mp = resposta_mp.get("status")

    if status_mp == "approved":
        _baixar_estoque_pix(db, venda)
        venda.status = StatusVenda.CONCLUIDA
        db.commit()
        return "pago"

    if status_mp in ("cancelled", "rejected"):
        venda.status = StatusVenda.CANCELADA
        db.commit()
        return "cancelado"

    if venda.expira_em is not None and datetime.datetime.utcnow() > venda.expira_em:
        venda.status = StatusVenda.EXPIRADA
        db.commit()
        return "expirado"

    return "pendente"


def get_venda(db: Session, venda_id: int) -> Venda:
    venda = db.get(Venda, venda_id)
    if venda is None:
        raise NotFoundError(f"Venda {venda_id} não encontrada")
    return venda


def list_vendas(db: Session, cliente_id: int | None = None) -> list[Venda]:
    stmt = select(Venda).order_by(Venda.data.desc())
    if cliente_id is not None:
        stmt = stmt.where(Venda.cliente_id == cliente_id)
    return list(db.scalars(stmt).all())
