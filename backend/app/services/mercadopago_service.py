"""Thin client for the Mercado Pago Payments API (Pix charges).

Only two calls are needed for this integration:
  - create a Pix payment (POST /v1/payments)
  - fetch a payment's current status (GET /v1/payments/{id})

No webhook dependency: since this system runs locally without a public IP,
status confirmation is done by active polling from the frontend against our
own `/vendas/pix/status/{venda_id}` endpoint, which in turn calls
`consultar_pagamento` below in real time.
"""
from __future__ import annotations

import uuid

import httpx

from app.config import get_settings
from app.exceptions import MercadoPagoError

_TIMEOUT_SECONDS = 15.0


def _headers() -> dict[str, str]:
    settings = get_settings()
    if not settings.mercadopago_access_token:
        raise MercadoPagoError(
            "MERCADOPAGO_ACCESS_TOKEN não configurado no .env — não é possível "
            "gerar cobranças Pix via Mercado Pago"
        )
    return {
        "Authorization": f"Bearer {settings.mercadopago_access_token}",
        # Prevents the API from creating a duplicate payment on client retries.
        "X-Idempotency-Key": str(uuid.uuid4()),
    }


def criar_pagamento_pix(
    *,
    valor: float,
    descricao: str,
    external_reference: str,
    payer_email: str = "cliente@farmacia.local",
) -> dict:
    """Creates a Pix payment charge on Mercado Pago and returns the raw response."""
    settings = get_settings()
    payload = {
        "transaction_amount": round(valor, 2),
        "description": descricao,
        "payment_method_id": "pix",
        "external_reference": external_reference,
        "payer": {"email": payer_email},
    }
    try:
        response = httpx.post(
            f"{settings.mercadopago_api_base_url}/v1/payments",
            json=payload,
            headers=_headers(),
            timeout=_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise MercadoPagoError(
            f"Mercado Pago recusou a cobrança Pix ({exc.response.status_code}): "
            f"{exc.response.text}"
        ) from exc
    except httpx.HTTPError as exc:
        raise MercadoPagoError(f"Falha de rede ao chamar o Mercado Pago: {exc}") from exc

    return response.json()


def consultar_pagamento(payment_id: str) -> dict:
    """Fetches a payment's current status in real time from Mercado Pago."""
    settings = get_settings()
    try:
        response = httpx.get(
            f"{settings.mercadopago_api_base_url}/v1/payments/{payment_id}",
            headers=_headers(),
            timeout=_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise MercadoPagoError(
            f"Mercado Pago retornou erro ao consultar pagamento {payment_id} "
            f"({exc.response.status_code}): {exc.response.text}"
        ) from exc
    except httpx.HTTPError as exc:
        raise MercadoPagoError(f"Falha de rede ao consultar pagamento: {exc}") from exc

    return response.json()
