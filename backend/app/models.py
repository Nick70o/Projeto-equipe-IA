"""SQLAlchemy declarative models for the pharmacy management system."""
from __future__ import annotations

import datetime
import enum

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TipoMovimentacao(str, enum.Enum):
    ENTRADA = "entrada"
    SAIDA = "saida"
    AJUSTE = "ajuste"
    PERDA = "perda"
    DEVOLUCAO = "devolucao"


class FormaPagamento(str, enum.Enum):
    DINHEIRO = "dinheiro"
    CARTAO = "cartao"
    PIX = "pix"
    FIADO = "fiado"


class StatusVenda(str, enum.Enum):
    CONCLUIDA = "concluida"
    AGUARDANDO_PAGAMENTO = "aguardando_pagamento"
    CANCELADA = "cancelada"
    EXPIRADA = "expirada"


class Produto(Base):
    __tablename__ = "produtos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    categoria: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    codigo_barras: Mapped[str | None] = mapped_column(
        String(64), unique=True, nullable=True, index=True
    )
    fornecedor: Mapped[str | None] = mapped_column(String(150), nullable=True)
    preco_custo: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    preco_venda: Mapped[float] = mapped_column(Float, nullable=False)
    estoque_atual: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    estoque_minimo: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    unidade_medida: Mapped[str] = mapped_column(String(20), nullable=False, default="unidade")
    controla_lote: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    criado_em: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow
    )

    lotes: Mapped[list["Lote"]] = relationship(
        back_populates="produto", cascade="all, delete-orphan"
    )
    movimentacoes: Mapped[list["MovimentacaoEstoque"]] = relationship(
        back_populates="produto", cascade="all, delete-orphan"
    )


class Lote(Base):
    __tablename__ = "lotes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    produto_id: Mapped[int] = mapped_column(ForeignKey("produtos.id"), nullable=False)
    numero_lote: Mapped[str] = mapped_column(String(100), nullable=False)
    quantidade: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    data_validade: Mapped[datetime.date] = mapped_column(Date, nullable=False)

    produto: Mapped["Produto"] = relationship(back_populates="lotes")


class MovimentacaoEstoque(Base):
    __tablename__ = "movimentacoes_estoque"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    produto_id: Mapped[int] = mapped_column(ForeignKey("produtos.id"), nullable=False)
    tipo: Mapped[TipoMovimentacao] = mapped_column(Enum(TipoMovimentacao), nullable=False)
    quantidade: Mapped[float] = mapped_column(Float, nullable=False)
    motivo: Mapped[str | None] = mapped_column(String(200), nullable=True)
    observacao: Mapped[str | None] = mapped_column(Text, nullable=True)
    data: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow
    )

    produto: Mapped["Produto"] = relationship(back_populates="movimentacoes")


class Cliente(Base):
    __tablename__ = "clientes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    telefone: Mapped[str | None] = mapped_column(String(30), nullable=True, index=True)
    endereco: Mapped[str | None] = mapped_column(String(250), nullable=True)
    saldo_devedor: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    criado_em: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow
    )

    vendas: Mapped[list["Venda"]] = relationship(back_populates="cliente")
    pagamentos: Mapped[list["PagamentoFiado"]] = relationship(
        back_populates="cliente", cascade="all, delete-orphan"
    )


class Venda(Base):
    __tablename__ = "vendas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    numero: Mapped[int] = mapped_column(Integer, unique=True, nullable=False, index=True)
    data: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow
    )
    desconto: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    subtotal: Mapped[float] = mapped_column(Float, nullable=False)
    total: Mapped[float] = mapped_column(Float, nullable=False)
    forma_pagamento: Mapped[FormaPagamento] = mapped_column(
        Enum(FormaPagamento), nullable=False
    )
    cliente_id: Mapped[int | None] = mapped_column(
        ForeignKey("clientes.id"), nullable=True
    )
    valor_recebido: Mapped[float | None] = mapped_column(Float, nullable=True)
    troco: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[StatusVenda] = mapped_column(
        Enum(StatusVenda), nullable=False, default=StatusVenda.CONCLUIDA
    )
    # Mercado Pago Pix integration fields (only populated when pix_gateway_ativo is on).
    mp_payment_id: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    mp_qr_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    mp_qr_code_base64: Mapped[str | None] = mapped_column(Text, nullable=True)
    expira_em: Mapped[datetime.datetime | None] = mapped_column(DateTime, nullable=True)

    cliente: Mapped["Cliente | None"] = relationship(back_populates="vendas")
    itens: Mapped[list["ItemVenda"]] = relationship(
        back_populates="venda", cascade="all, delete-orphan"
    )


class ItemVenda(Base):
    __tablename__ = "itens_venda"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    venda_id: Mapped[int] = mapped_column(ForeignKey("vendas.id"), nullable=False)
    produto_id: Mapped[int] = mapped_column(ForeignKey("produtos.id"), nullable=False)
    quantidade: Mapped[float] = mapped_column(Float, nullable=False)
    preco_unitario: Mapped[float] = mapped_column(Float, nullable=False)
    subtotal: Mapped[float] = mapped_column(Float, nullable=False)

    venda: Mapped["Venda"] = relationship(back_populates="itens")
    produto: Mapped["Produto"] = relationship()


class PagamentoFiado(Base):
    __tablename__ = "pagamentos_fiado"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clientes.id"), nullable=False)
    valor: Mapped[float] = mapped_column(Float, nullable=False)
    data: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow
    )

    cliente: Mapped["Cliente"] = relationship(back_populates="pagamentos")


class Configuracao(Base):
    """Simple key/value settings table (e.g. feature toggles).

    Kept intentionally simple: one row per setting, value stored as text
    and parsed by the caller (see app.services.configuracao_service).
    """

    __tablename__ = "configuracoes"

    chave: Mapped[str] = mapped_column(String(100), primary_key=True)
    valor: Mapped[str] = mapped_column(String(500), nullable=False)
