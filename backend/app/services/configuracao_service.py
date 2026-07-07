"""Simple key/value application settings, persisted in the `configuracoes` table.

Kept intentionally minimal: booleans are stored as the strings "true"/"false".
Add new keys here as new toggles are needed — no schema migration required
since the table is a generic key/value store.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import Configuracao

PIX_GATEWAY_ATIVO = "pix_gateway_ativo"

_DEFAULTS: dict[str, str] = {
    PIX_GATEWAY_ATIVO: "false",
}


def _get_raw(db: Session, chave: str) -> str:
    config = db.get(Configuracao, chave)
    if config is not None:
        return config.valor
    return _DEFAULTS.get(chave, "")


def _set_raw(db: Session, chave: str, valor: str) -> None:
    config = db.get(Configuracao, chave)
    if config is None:
        config = Configuracao(chave=chave, valor=valor)
        db.add(config)
    else:
        config.valor = valor


def get_bool(db: Session, chave: str, default: bool = False) -> bool:
    raw = _get_raw(db, chave)
    if not raw:
        return default
    return raw.strip().lower() in ("true", "1", "yes")


def set_bool(db: Session, chave: str, valor: bool) -> None:
    _set_raw(db, chave, "true" if valor else "false")


def get_configuracoes(db: Session) -> dict[str, bool]:
    return {PIX_GATEWAY_ATIVO: get_bool(db, PIX_GATEWAY_ATIVO, default=False)}


def update_configuracoes(db: Session, pix_gateway_ativo: bool | None) -> dict[str, bool]:
    if pix_gateway_ativo is not None:
        set_bool(db, PIX_GATEWAY_ATIVO, pix_gateway_ativo)
    db.commit()
    return get_configuracoes(db)
