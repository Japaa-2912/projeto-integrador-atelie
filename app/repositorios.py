"""RepositÃ³rios: concentram todo o acesso ao banco de dados.

Nenhuma outra camada escreve SQL diretamente. Isso mantÃ©m as consultas em um
Ãºnico lugar e facilita a manutenÃ§Ã£o do sistema.
"""

from __future__ import annotations

import sqlite3

from .modelos import Categoria, Cliente, ItemPedido, Produto

COLUNAS_PRODUTO = """
    p.id, p.nome, p.categoria_id, c.nome AS categoria,
    p.preco_centavos, p.estoque, p.estoque_minimo, p.ativo
"""

ORDENACOES_PRODUTO = {
    "nome": "p.nome COLLATE NOCASE ASC",
    "preco": "p.preco_centavos ASC",
    "preco_desc": "p.preco_centavos DESC",
    "estoque": "p.estoque ASC",
    "categoria": "c.nome COLLATE NOCASE ASC, p.nome COLLATE NOCASE ASC",
}


class ProdutoRepositorio:
    """OperaÃ§Ãµes de banco relacionadas Ã  tabela ``produtos``."""

    def __init__(self, conexao: sqlite3.Connection) -> None:
        self.conexao = conexao

    def criar(
        self,
        nome: str,
        nome_busca: str,
        categoria_id: int,
        preco_centavos: int,
        estoque: int,
        estoque_minimo: int,
    ) -> int:
        cursor = self.conexao.execute(
            """
            INSERT INTO produtos
                (nome, nome_busca, categoria_id, preco_centavos, estoque, estoque_minimo)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (nome, nome_busca, categoria_id, preco_centavos, estoque, estoque_minimo),
        )
        return int(cursor.lastrowid)

    def atualizar(self, produto_id: int, campos: dict[str, object]) -> None:
        if not campos:
            return
        atribuicoes = ", ".join(f"{coluna} = ?" for coluna in campos)
        valores = list(campos.values()) + [produto_id]
        self.conexao.execute(
            f"UPDATE produtos SET {atribuicoes} WHERE id = ?", valores
        )

    def obter(self, produto_id: int) -> Produto | None:
        linha = self.conexao.execute(
            f"""
            SELECT {COLUNAS_PRODUTO}
              FROM produtos p
              JOIN categorias c ON c.id = p.categoria_id
             WHERE p.id = ?
            """,
            (produto_id,),
        ).fetchone()
        return Produto.de_linha(linha) if linha else None

    def listar(
        self,
        apenas_ativos: bool = True,
        ordenar_por: str = "nome",
    ) -> list[Produto]:
        ordenacao = ORDENACOES_PRODUTO.get(ordenar_por, ORDENACOES_PRODUTO["nome"])
        filtro = "WHERE p.ativo = 1" if apenas_ativos else ""
        linhas = self.conexao.execute(
            f"""
            SELECT {COLUNAS_PRODUTO}
              FROM produtos p
              JOIN categorias c ON c.id = p.categoria_id
              {filtro}
             ORDER BY {ordenacao}
            """
        ).fetchall()
        return [Produto.de_linha(linha) for linha in linhas]

    def buscar(self, termo_normalizado: str, apenas_ativos: bool = True) -> list[Produto]:
        filtro = "AND p.ativo = 1" if apenas_ativos else ""
        linhas = self.conexao.execute(
            f"""
            SELECT {COLUNAS_PRODUTO}
              FROM produtos p
              JOIN categorias c ON c.id = p.categoria_id
             WHERE p.nome_busca LIKE ?
               {filtro}
             ORDER BY p.nome COLLATE NOCASE ASC
            """,
            (f"%{termo_normalizado}%",),
        ).fetchall()
        return [Produto.de_linha(linha) for linha in linhas]

    def desativar(self, produto_id: int) -> None:
        self.conexao.execute("UPDATE produtos SET ativo = 0 WHERE id = ?", (produto_id,))

    def baixar_estoque(self, produto_id: int, quantidade: int) -> None:
        """Reduz o estoque. O CHECK do banco impede valor negativo."""
        self.conexao.execute(
            "UPDATE produtos SET estoque = estoque - ? WHERE id = ?",
            (quantidade, produto_id),
        )

    def repor_estoque(self, produto_id: int, quantidade: int) -> None:
        self.conexao.execute(
            "UPDATE produtos SET estoque = estoque + ? WHERE id = ?",
            (quantidade, produto_id),
        )

    def com_estoque_baixo(self) -> list[Produto]:
        linhas = self.conexao.execute(
            f"""
            SELECT {COLUNAS_PRODUTO}
              FROM produtos p
              JOIN categorias c ON c.id = p.categoria_id
             WHERE p.ativo = 1
               AND p.estoque <= p.estoque_minimo
             ORDER BY (p.estoque - p.estoque_minimo) ASC
            """
        ).fetchall()
        return [Produto.de_linha(linha) for linha in linhas]


class CategoriaRepositorio:
    def __init__(self, conexao: sqlite3.Connection) -> None:
        self.conexao = conexao

    def criar(self, nome: str) -> int:
        cursor = self.conexao.execute(
            "INSERT INTO categorias (nome) VALUES (?)", (nome,)
        )
        return int(cursor.lastrowid)

    def obter(self, categoria_id: int) -> Categoria | None:
        linha = self.conexao.execute(
            "SELECT id, nome FROM categorias WHERE id = ?", (categoria_id,)
        ).fetchone()
        return Categoria(id=linha["id"], nome=linha["nome"]) if linha else None

    def por_nome(self, nome: str) -> Categoria | None:
        linha = self.conexao.execute(
            "SELECT id, nome FROM categorias WHERE nome = ? COLLATE NOCASE", (nome,)
        ).fetchone()
        return Categoria(id=linha["id"], nome=linha["nome"]) if linha else None

    def listar(self) -> list[Categoria]:
        linhas = self.conexao.execute(
            "SELECT id, nome FROM categorias ORDER BY nome COLLATE NOCASE"
        ).fetchall()
        return [Categoria(id=linha["id"], nome=linha["nome"]) for linha in linhas]


class ClienteRepositorio:
    def __init__(self, conexao: sqlite3.Connection) -> None:
        self.conexao = conexao

    def criar(self, nome: str, telefone: str, cidade: str | None) -> int:
        cursor = self.conexao.execute(
            "INSERT INTO clientes (nome, telefone, cidade) VALUES (?, ?, ?)",
            (nome, telefone, cidade),
        )
        return int(cursor.lastrowid)

    def obter(self, cliente_id: int) -> Cliente | None:
        linha = self.conexao.execute(
            "SELECT id, nome, telefone, cidade FROM clientes WHERE id = ?",
            (cliente_id,),
        ).fetchone()
        return Cliente.de_linha(linha) if linha else None

    def listar(self) -> list[Cliente]:
        linhas = self.conexao.execute(
            "SELECT id, nome, telefone, cidade FROM clientes ORDER BY nome COLLATE NOCASE"
        ).fetchall()
        return [Cliente.de_linha(linha) for linha in linhas]

    def buscar(self, termo_normalizado: str) -> list[Cliente]:
        # A tabela de clientes é pequena: a comparação é feita em memória para
        # funcionar também com nomes acentuados.
        linhas = self.conexao.execute(
            "SELECT id, nome, telefone, cidade FROM clientes ORDER BY nome COLLATE NOCASE"
        ).fetchall()
        from .utilidades import normalizar_busca

        return [
            Cliente.de_linha(linha)
            for linha in linhas
            if termo_normalizado in normalizar_busca(linha["nome"])
        ]


class PedidoRepositorio:
    def __init__(self, conexao: sqlite3.Connection) -> None:
        self.conexao = conexao

    def criar(self, cliente_id: int, desconto_percentual: float) -> int:
        cursor = self.conexao.execute(
            "INSERT INTO pedidos (cliente_id, desconto_percentual) VALUES (?, ?)",
            (cliente_id, desconto_percentual),
        )
        return int(cursor.lastrowid)

    def obter(self, pedido_id: int) -> sqlite3.Row | None:
        return self.conexao.execute(
            """
            SELECT pe.id, pe.status, pe.desconto_percentual, pe.criado_em,
                   pe.finalizado_em, pe.cliente_id, cl.nome AS cliente
              FROM pedidos pe
              JOIN clientes cl ON cl.id = pe.cliente_id
             WHERE pe.id = ?
            """,
            (pedido_id,),
        ).fetchone()

    def listar(self, status: str | None = None) -> list[sqlite3.Row]:
        if status:
            return self.conexao.execute(
                """
                SELECT pe.id, pe.status, pe.desconto_percentual, pe.criado_em,
                       cl.nome AS cliente
                  FROM pedidos pe
                  JOIN clientes cl ON cl.id = pe.cliente_id
                 WHERE pe.status = ?
                 ORDER BY pe.id DESC
                """,
                (status,),
            ).fetchall()
        return self.conexao.execute(
            """
            SELECT pe.id, pe.status, pe.desconto_percentual, pe.criado_em,
                   cl.nome AS cliente
              FROM pedidos pe
              JOIN clientes cl ON cl.id = pe.cliente_id
             ORDER BY pe.id DESC
            """
        ).fetchall()

    def listar_itens(self, pedido_id: int) -> list[ItemPedido]:
        linhas = self.conexao.execute(
            """
            SELECT i.id, i.produto_id, p.nome AS produto, i.quantidade,
                   i.preco_unitario_centavos
              FROM pedido_itens i
              JOIN produtos p ON p.id = i.produto_id
             WHERE i.pedido_id = ?
             ORDER BY i.id
            """,
            (pedido_id,),
        ).fetchall()
        return [ItemPedido.de_linha(linha) for linha in linhas]

    def item_do_produto(self, pedido_id: int, produto_id: int) -> ItemPedido | None:
        for item in self.listar_itens(pedido_id):
            if item.produto_id == produto_id:
                return item
        return None

    def adicionar_item(
        self,
        pedido_id: int,
        produto_id: int,
        quantidade: int,
        preco_unitario_centavos: int,
    ) -> None:
        self.conexao.execute(
            """
            INSERT INTO pedido_itens
                (pedido_id, produto_id, quantidade, preco_unitario_centavos)
            VALUES (?, ?, ?, ?)
            """,
            (pedido_id, produto_id, quantidade, preco_unitario_centavos),
        )

    def alterar_quantidade(self, item_id: int, quantidade: int) -> None:
        self.conexao.execute(
            "UPDATE pedido_itens SET quantidade = ? WHERE id = ?",
            (quantidade, item_id),
        )

    def remover_item(self, item_id: int) -> None:
        self.conexao.execute("DELETE FROM pedido_itens WHERE id = ?", (item_id,))

    def definir_status(self, pedido_id: int, status: str, finalizar: bool = False) -> None:
        if finalizar:
            self.conexao.execute(
                """
                UPDATE pedidos
                   SET status = ?, finalizado_em = datetime('now', 'localtime')
                 WHERE id = ?
                """,
                (status, pedido_id),
            )
        else:
            self.conexao.execute(
                "UPDATE pedidos SET status = ? WHERE id = ?", (status, pedido_id)
            )
