"""Pydantic schemas for request/response validation."""
from __future__ import annotations

import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models import FormaPagamento, StatusVenda, TipoMovimentacao

# --------------------------------------------------------------------------
# Produto
# --------------------------------------------------------------------------


class ProdutoBase(BaseModel):
    nome: str = Field(min_length=1, max_length=200)
    categoria: str = Field(min_length=1, max_length=100)
    codigo_barras: str | None = Field(default=None, max_length=64)
    fornecedor: str | None = Field(default=None, max_length=150)
    preco_custo: float = Field(default=0.0, ge=0)
    preco_venda: float = Field(gt=0)
    estoque_atual: float = Field(default=0.0, ge=0)
    estoque_minimo: float = Field(default=0.0, ge=0)
    unidade_medida: str = Field(default="unidade", max_length=20)
    controla_lote: bool = False


class ProdutoCreate(ProdutoBase):
    pass


class ProdutoUpdate(ProdutoBase):
    pass


class ProdutoOut(ProdutoBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    criado_em: datetime.datetime


class ProdutoBusca(BaseModel):
    """Slim shape used by the PDV autocomplete."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    codigo_barras: str | None
    preco_venda: float
    estoque_atual: float
    unidade_medida: str
    dias_para_vencer: int | None = None


# --------------------------------------------------------------------------
# Movimentação de estoque
# --------------------------------------------------------------------------


class MovimentacaoEstoqueCreate(BaseModel):
    tipo: TipoMovimentacao
    quantidade: float = Field(gt=0)
    motivo: str | None = Field(default=None, max_length=200)
    observacao: str | None = None


class MovimentacaoEstoqueOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    produto_id: int
    tipo: TipoMovimentacao
    quantidade: float
    motivo: str | None
    observacao: str | None
    data: datetime.datetime


# --------------------------------------------------------------------------
# Lote
# --------------------------------------------------------------------------


class LoteBase(BaseModel):
    numero_lote: str = Field(min_length=1, max_length=100)
    quantidade: float = Field(ge=0)
    data_validade: datetime.date


class LoteCreate(LoteBase):
    pass


class LoteUpdate(LoteBase):
    pass


class LoteOut(LoteBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    produto_id: int


class LoteComProdutoOut(LoteOut):
    produto_nome: str
    dias_restantes: int


# --------------------------------------------------------------------------
# Cliente
# --------------------------------------------------------------------------


class ClienteBase(BaseModel):
    nome: str = Field(min_length=1, max_length=150)
    telefone: str | None = Field(default=None, max_length=30)
    endereco: str | None = Field(default=None, max_length=250)


class ClienteCreate(ClienteBase):
    pass


class ClienteUpdate(ClienteBase):
    pass


class ClienteOut(ClienteBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    saldo_devedor: float
    criado_em: datetime.datetime


class PagamentoFiadoCreate(BaseModel):
    valor: float = Field(gt=0)


class PagamentoFiadoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    cliente_id: int
    valor: float
    data: datetime.datetime


# --------------------------------------------------------------------------
# Venda
# --------------------------------------------------------------------------


class ItemVendaCreate(BaseModel):
    produto_id: int
    quantidade: float = Field(gt=0)


class ItemVendaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    produto_id: int
    produto_nome: str
    quantidade: float
    preco_unitario: float
    subtotal: float


class VendaCreate(BaseModel):
    itens: list[ItemVendaCreate] = Field(min_length=1)
    desconto: float = Field(default=0.0, ge=0)
    forma_pagamento: FormaPagamento
    cliente_id: int | None = None
    valor_recebido: float | None = None


class VendaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    numero: int
    data: datetime.datetime
    subtotal: float
    desconto: float
    total: float
    forma_pagamento: FormaPagamento
    cliente_id: int | None
    valor_recebido: float | None
    troco: float | None
    status: StatusVenda
    itens: list[ItemVendaOut]


# --------------------------------------------------------------------------
# Pix (Mercado Pago)
# --------------------------------------------------------------------------


class PixCobrancaCreate(BaseModel):
    itens: list[ItemVendaCreate] = Field(min_length=1)
    desconto: float = Field(default=0.0, ge=0)
    cliente_id: int | None = None


class PixCobrancaOut(BaseModel):
    venda_id: int
    qr_code_base64: str | None
    qr_code_copia_cola: str | None
    mp_payment_id: str | None
    expira_em: datetime.datetime | None


class PixStatusOut(BaseModel):
    status: str  # "pendente" | "pago" | "expirado" | "cancelado"


# --------------------------------------------------------------------------
# Configurações
# --------------------------------------------------------------------------


class ConfiguracoesOut(BaseModel):
    pix_gateway_ativo: bool


class ConfiguracoesUpdate(BaseModel):
    pix_gateway_ativo: bool | None = None


# --------------------------------------------------------------------------
# Relatórios
# --------------------------------------------------------------------------


class IndicadoresRelatorio(BaseModel):
    faturamento: float
    lucro_estimado: float
    ticket_medio: float
    numero_vendas: int
    periodo_inicio: datetime.date
    periodo_fim: datetime.date


class ProdutoRankingOut(BaseModel):
    produto_id: int
    produto_nome: str
    quantidade_vendida: float
    faturamento_gerado: float


class FaturamentoPorDia(BaseModel):
    dia: datetime.date
    faturamento: float
