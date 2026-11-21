"""Modelos de domínio do sistema, representados por classes de dados."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from .utilidades import formatar_moeda


@dataclass(frozen=True)
class Categoria:
    id: int
    nome: str


@dataclass(frozen=True)
class Produto:
    id: int
    nome: str
    categoria_id: int
    categoria: str
    preco_centavos: int
    estoque: int
    estoque_minimo: int
    ativo: bool = True

    @classmethod
    def de_linha(cls, linha: sqlite3.Row) -> "Produto":
        return cls(
            id=linha["id"],
            nome=linha["nome"],
            categoria_id=linha["categoria_id"],
            categoria=linha["categoria"],
            preco_centavos=linha["preco_centavos"],
            estoque=linha["estoque"],
            estoque_minimo=linha["estoque_minimo"],
            ativo=bool(linha["ativo"]),
        )

    @property
    def preco_formatado(self) -> str:
        return formatar_moeda(self.preco_centavos)

    @property
    def estoque_baixo(self) -> bool:
        return self.estoque <= self.estoque_minimo


@dataclass(frozen=True)
class Cliente:
    id: int
    nome: str
    telefone: str
    cidade: str | None

    @classmethod
    def de_linha(cls, linha: sqlite3.Row) -> "Cliente":
        return cls(
            id=linha["id"],
            nome=linha["nome"],
            telefone=linha["telefone"],
            cidade=linha["cidade"],
        )


@dataclass(frozen=True)
class ItemPedido:
    id: int
    produto_id: int
    produto: str
    quantidade: int
    preco_unitario_centavos: int

    @classmethod
    def de_linha(cls, linha: sqlite3.Row) -> "ItemPedido":
        return cls(
            id=linha["id"],
            produto_id=linha["produto_id"],
            produto=linha["produto"],
            quantidade=linha["quantidade"],
            preco_unitario_centavos=linha["preco_unitario_centavos"],
        )

    @property
    def subtotal_centavos(self) -> int:
        return self.preco_unitario_centavos * self.quantidade

    @property
    def subtotal_formatado(self) -> str:
        return formatar_moeda(self.subtotal_centavos)


@dataclass(frozen=True)
class ResumoPedido:
    """Resultado do cálculo de um pedido, com os valores já conferidos."""

    pedido_id: int
    cliente: str
    status: str
    desconto_percentual: float
    itens: list[ItemPedido]
    subtotal_centavos: int
    desconto_centavos: int
    total_centavos: int

    @property
    def subtotal_formatado(self) -> str:
        return formatar_moeda(self.subtotal_centavos)

    @property
    def desconto_formatado(self) -> str:
        return formatar_moeda(self.desconto_centavos)

    @property
    def total_formatado(self) -> str:
        return formatar_moeda(self.total_centavos)
