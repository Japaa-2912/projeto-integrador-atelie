"""Regras de negócio do sistema.

A camada de serviços é a única que decide o que pode ou não ser gravado.
Ela valida as entradas, garante a consistência do estoque e controla as
transações do banco de dados.
"""

from __future__ import annotations

import sqlite3

from .modelos import Categoria, Cliente, ItemPedido, Produto, ResumoPedido
from .repositorios import (
    CategoriaRepositorio,
    ClienteRepositorio,
    PedidoRepositorio,
    ProdutoRepositorio,
)
from .utilidades import formatar_moeda, normalizar_busca

STATUS_ABERTO = "ABERTO"
STATUS_FINALIZADO = "FINALIZADO"
STATUS_CANCELADO = "CANCELADO"


class ErroDeNegocio(Exception):
    """Erro esperado, com mensagem pronta para ser mostrada ao usuário."""


def _texto_obrigatorio(valor: str, campo: str, minimo: int = 3) -> str:
    texto = (valor or "").strip()
    if len(texto) < minimo:
        raise ErroDeNegocio(f"O campo {campo} deve ter pelo menos {minimo} caracteres.")
    return texto


def _inteiro_nao_negativo(valor: int, campo: str) -> int:
    if not isinstance(valor, int):
        raise ErroDeNegocio(f"O campo {campo} deve ser um número inteiro.")
    if valor < 0:
        raise ErroDeNegocio(f"O campo {campo} não pode ser negativo.")
    return valor


class ServicoLoja:
    """Fachada com as operações disponíveis para a interface do programa."""

    def __init__(self, conexao: sqlite3.Connection) -> None:
        self.conexao = conexao
        self.produtos = ProdutoRepositorio(conexao)
        self.categorias = CategoriaRepositorio(conexao)
        self.clientes = ClienteRepositorio(conexao)
        self.pedidos = PedidoRepositorio(conexao)

    # ------------------------------------------------------------------
    # Categorias
    # ------------------------------------------------------------------
    def cadastrar_categoria(self, nome: str) -> int:
        nome = _texto_obrigatorio(nome, "nome da categoria")
        existente = self.categorias.por_nome(nome)
        if existente:
            return existente.id
        novo_id = self.categorias.criar(nome)
        self.conexao.commit()
        return novo_id

    def listar_categorias(self) -> list[Categoria]:
        return self.categorias.listar()

    # ------------------------------------------------------------------
    # Produtos
    # ------------------------------------------------------------------
    def cadastrar_produto(
        self,
        nome: str,
        categoria_id: int,
        preco_centavos: int,
        estoque: int = 0,
        estoque_minimo: int = 0,
    ) -> int:
        nome = _texto_obrigatorio(nome, "nome do produto")
        if self.categorias.obter(categoria_id) is None:
            raise ErroDeNegocio("Categoria não encontrada.")
        if preco_centavos <= 0:
            raise ErroDeNegocio("O preço deve ser maior que zero.")
        _inteiro_nao_negativo(estoque, "estoque")
        _inteiro_nao_negativo(estoque_minimo, "estoque mínimo")

        novo_id = self.produtos.criar(
            nome=nome,
            nome_busca=normalizar_busca(nome),
            categoria_id=categoria_id,
            preco_centavos=preco_centavos,
            estoque=estoque,
            estoque_minimo=estoque_minimo,
        )
        self.conexao.commit()
        return novo_id

    def atualizar_produto(
        self,
        produto_id: int,
        nome: str | None = None,
        categoria_id: int | None = None,
        preco_centavos: int | None = None,
        estoque_minimo: int | None = None,
    ) -> None:
        produto = self.obter_produto(produto_id)
        campos: dict[str, object] = {}

        if nome is not None:
            nome = _texto_obrigatorio(nome, "nome do produto")
            campos["nome"] = nome
            campos["nome_busca"] = normalizar_busca(nome)
        if categoria_id is not None:
            if self.categorias.obter(categoria_id) is None:
                raise ErroDeNegocio("Categoria não encontrada.")
            campos["categoria_id"] = categoria_id
        if preco_centavos is not None:
            if preco_centavos <= 0:
                raise ErroDeNegocio("O preço deve ser maior que zero.")
            campos["preco_centavos"] = preco_centavos
        if estoque_minimo is not None:
            campos["estoque_minimo"] = _inteiro_nao_negativo(
                estoque_minimo, "estoque mínimo"
            )

        if not campos:
            raise ErroDeNegocio("Nenhum campo foi informado para atualização.")

        self.produtos.atualizar(produto_id, campos)
        self.conexao.commit()
        _ = produto  # garante que o produto exista antes de atualizar

    def obter_produto(self, produto_id: int) -> Produto:
        produto = self.produtos.obter(produto_id)
        if produto is None:
            raise ErroDeNegocio(f"Produto {produto_id} não encontrado.")
        return produto

    def listar_produtos(
        self, apenas_ativos: bool = True, ordenar_por: str = "nome"
    ) -> list[Produto]:
        return self.produtos.listar(apenas_ativos=apenas_ativos, ordenar_por=ordenar_por)

    def buscar_produtos(self, termo: str, apenas_ativos: bool = True) -> list[Produto]:
        termo_normalizado = normalizar_busca(termo)
        if not termo_normalizado:
            return self.listar_produtos(apenas_ativos=apenas_ativos)
        return self.produtos.buscar(termo_normalizado, apenas_ativos=apenas_ativos)

    def desativar_produto(self, produto_id: int) -> None:
        self.obter_produto(produto_id)
        self.produtos.desativar(produto_id)
        self.conexao.commit()

    def repor_estoque(self, produto_id: int, quantidade: int) -> None:
        self.obter_produto(produto_id)
        if quantidade <= 0:
            raise ErroDeNegocio("A quantidade de reposição deve ser maior que zero.")
        self.produtos.repor_estoque(produto_id, quantidade)
        self.conexao.commit()

    # ------------------------------------------------------------------
    # Clientes
    # ------------------------------------------------------------------
    def cadastrar_cliente(self, nome: str, telefone: str, cidade: str | None = None) -> int:
        nome = _texto_obrigatorio(nome, "nome do cliente")
        telefone = _texto_obrigatorio(telefone, "telefone", minimo=8)
        cidade_limpa = (cidade or "").strip() or None
        novo_id = self.clientes.criar(nome, telefone, cidade_limpa)
        self.conexao.commit()
        return novo_id

    def listar_clientes(self) -> list[Cliente]:
        return self.clientes.listar()

    def obter_cliente(self, cliente_id: int) -> Cliente:
        cliente = self.clientes.obter(cliente_id)
        if cliente is None:
            raise ErroDeNegocio(f"Cliente {cliente_id} não encontrado.")
        return cliente

    def buscar_clientes(self, termo: str) -> list[Cliente]:
        return self.clientes.buscar(normalizar_busca(termo))

    # ------------------------------------------------------------------
    # Pedidos
    # ------------------------------------------------------------------
    def abrir_pedido(self, cliente_id: int, desconto_percentual: float = 0) -> int:
        self.obter_cliente(cliente_id)
        if not 0 <= desconto_percentual <= 100:
            raise ErroDeNegocio("O desconto deve estar entre 0 e 100.")
        pedido_id = self.pedidos.criar(cliente_id, float(desconto_percentual))
        self.conexao.commit()
        return pedido_id

    def _pedido_aberto(self, pedido_id: int) -> sqlite3.Row:
        pedido = self.pedidos.obter(pedido_id)
        if pedido is None:
            raise ErroDeNegocio(f"Pedido {pedido_id} não encontrado.")
        if pedido["status"] != STATUS_ABERTO:
            raise ErroDeNegocio(
                f"O pedido {pedido_id} está {pedido['status'].lower()} e não pode ser alterado."
            )
        return pedido

    def adicionar_item(self, pedido_id: int, produto_id: int, quantidade: int) -> None:
        self._pedido_aberto(pedido_id)
        if quantidade <= 0:
            raise ErroDeNegocio("A quantidade deve ser maior que zero.")

        produto = self.obter_produto(produto_id)
        if not produto.ativo:
            raise ErroDeNegocio("Produto inativo não pode ser incluído em pedidos.")

        item_existente = self.pedidos.item_do_produto(pedido_id, produto_id)
        quantidade_total = quantidade + (item_existente.quantidade if item_existente else 0)

        if quantidade_total > produto.estoque:
            raise ErroDeNegocio(
                f"Estoque insuficiente de '{produto.nome}': "
                f"disponível {produto.estoque}, solicitado {quantidade_total}."
            )

        if item_existente:
            self.pedidos.alterar_quantidade(item_existente.id, quantidade_total)
        else:
            self.pedidos.adicionar_item(
                pedido_id, produto_id, quantidade, produto.preco_centavos
            )
        self.conexao.commit()

    def remover_item(self, pedido_id: int, item_id: int) -> None:
        self._pedido_aberto(pedido_id)
        itens = {item.id: item for item in self.pedidos.listar_itens(pedido_id)}
        if item_id not in itens:
            raise ErroDeNegocio("Item não encontrado neste pedido.")
        self.pedidos.remover_item(item_id)
        self.conexao.commit()

    def alterar_desconto(self, pedido_id: int, desconto_percentual: float) -> None:
        self._pedido_aberto(pedido_id)
        if not 0 <= desconto_percentual <= 100:
            raise ErroDeNegocio("O desconto deve estar entre 0 e 100.")
        self.conexao.execute(
            "UPDATE pedidos SET desconto_percentual = ? WHERE id = ?",
            (float(desconto_percentual), pedido_id),
        )
        self.conexao.commit()

    def resumo_pedido(self, pedido_id: int) -> ResumoPedido:
        pedido = self.pedidos.obter(pedido_id)
        if pedido is None:
            raise ErroDeNegocio(f"Pedido {pedido_id} não encontrado.")

        itens = self.pedidos.listar_itens(pedido_id)
        subtotal = sum(item.subtotal_centavos for item in itens)
        desconto = int(round(subtotal * float(pedido["desconto_percentual"]) / 100))

        return ResumoPedido(
            pedido_id=pedido_id,
            cliente=pedido["cliente"],
            status=pedido["status"],
            desconto_percentual=float(pedido["desconto_percentual"]),
            itens=itens,
            subtotal_centavos=subtotal,
            desconto_centavos=desconto,
            total_centavos=subtotal - desconto,
        )

    def finalizar_pedido(self, pedido_id: int) -> ResumoPedido:
        self._pedido_aberto(pedido_id)
        resumo = self.resumo_pedido(pedido_id)

        if not resumo.itens:
            raise ErroDeNegocio("Não é possível finalizar um pedido sem itens.")

        for item in resumo.itens:
            produto = self.obter_produto(item.produto_id)
            if produto.estoque < item.quantidade:
                raise ErroDeNegocio(
                    f"Estoque insuficiente de '{produto.nome}': "
                    f"disponível {produto.estoque}, solicitado {item.quantidade}."
                )

        try:
            with self.conexao:  # transação: tudo é gravado ou nada é gravado
                for item in resumo.itens:
                    self.produtos.baixar_estoque(item.produto_id, item.quantidade)
                self.pedidos.definir_status(pedido_id, STATUS_FINALIZADO, finalizar=True)
        except sqlite3.Error as erro:
            raise ErroDeNegocio(f"Falha ao finalizar o pedido: {erro}") from erro

        return self.resumo_pedido(pedido_id)

    def cancelar_pedido(self, pedido_id: int) -> None:
        pedido = self.pedidos.obter(pedido_id)
        if pedido is None:
            raise ErroDeNegocio(f"Pedido {pedido_id} não encontrado.")
        if pedido["status"] == STATUS_CANCELADO:
            raise ErroDeNegocio("Este pedido já está cancelado.")

        itens = self.pedidos.listar_itens(pedido_id)

        try:
            with self.conexao:
                if pedido["status"] == STATUS_FINALIZADO:
                    # Devolve ao estoque os itens que haviam sido baixados.
                    for item in itens:
                        self.produtos.repor_estoque(item.produto_id, item.quantidade)
                self.pedidos.definir_status(pedido_id, STATUS_CANCELADO)
        except sqlite3.Error as erro:
            raise ErroDeNegocio(f"Falha ao cancelar o pedido: {erro}") from erro

    def listar_pedidos(self, status: str | None = None) -> list[sqlite3.Row]:
        return self.pedidos.listar(status)

    def total_pedido_formatado(self, pedido_id: int) -> str:
        return formatar_moeda(self.resumo_pedido(pedido_id).total_centavos)
