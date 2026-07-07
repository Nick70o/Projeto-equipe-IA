"""Custom domain exceptions, translated to HTTP errors at the router layer."""
from __future__ import annotations


class DomainError(Exception):
    """Base class for business-rule violations."""


class NotFoundError(DomainError):
    pass


class EstoqueInsuficienteError(DomainError):
    def __init__(self, produto_nome: str, restante: float) -> None:
        self.produto_nome = produto_nome
        self.restante = restante
        super().__init__(
            f"Estoque insuficiente para '{produto_nome}' — restam {restante} unidades"
        )


class ValidationDomainError(DomainError):
    """Raised for business-rule input problems that aren't plain 404s."""


class MercadoPagoError(DomainError):
    """Raised when the Mercado Pago API call fails or returns an unexpected shape."""
