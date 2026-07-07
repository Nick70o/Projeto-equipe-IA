"""Routes for reading/updating application settings (feature toggles)."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import ConfiguracoesOut, ConfiguracoesUpdate
from app.services import configuracao_service

router = APIRouter(prefix="/configuracoes", tags=["Configurações"])


@router.get("", response_model=ConfiguracoesOut)
def obter_configuracoes(db: Session = Depends(get_db)) -> ConfiguracoesOut:
    return ConfiguracoesOut(**configuracao_service.get_configuracoes(db))


@router.put("", response_model=ConfiguracoesOut)
def atualizar_configuracoes(
    data: ConfiguracoesUpdate, db: Session = Depends(get_db)
) -> ConfiguracoesOut:
    """Updates feature toggles. Secrets like the Mercado Pago access token are
    never exposed or editable here — they only come from environment variables.
    """
    configuracoes = configuracao_service.update_configuracoes(
        db, pix_gateway_ativo=data.pix_gateway_ativo
    )
    return ConfiguracoesOut(**configuracoes)
