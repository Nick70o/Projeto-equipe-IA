"""Best-effort Mercado Pago webhook receiver.

This app runs locally without a public IP or guaranteed internet, so Mercado
Pago's servers generally cannot reach this endpoint — active polling via
GET /vendas/pix/status/{venda_id} is the primary confirmation mechanism (see
app.services.venda_service.consultar_ou_confirmar_pix). This webhook exists
only as a bonus for if/when the system is hosted with a reachable URL.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Venda
from app.services import venda_service

router = APIRouter(prefix="/webhook", tags=["Webhook"])
logger = logging.getLogger("farmacia.webhook")


@router.post("/mercadopago", status_code=200)
def receber_webhook_mercadopago(payload: dict, db: Session = Depends(get_db)) -> dict[str, str]:
    """Accepts Mercado Pago's notification payload and, best-effort, triggers
    the same confirmation logic used by the polling endpoint.

    Mercado Pago sends different payload shapes depending on notification
    type; we only care about payment notifications, and we look the sale up
    by `mp_payment_id` (set when the charge was created).
    """
    payment_id = str(payload.get("data", {}).get("id") or payload.get("id") or "")
    if not payment_id:
        logger.info("Webhook Mercado Pago recebido sem payment id, ignorando: %s", payload)
        return {"status": "ignorado"}

    venda = db.scalar(select(Venda).where(Venda.mp_payment_id == payment_id))
    if venda is None:
        logger.info("Webhook Mercado Pago: nenhuma venda encontrada para payment_id=%s", payment_id)
        return {"status": "ignorado"}

    try:
        status = venda_service.consultar_ou_confirmar_pix(db, venda.id)
    except Exception:
        logger.exception("Falha ao processar webhook do Mercado Pago para venda %s", venda.id)
        return {"status": "erro"}

    return {"status": status}
