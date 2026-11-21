import sqlite3
import unittest

from app.servicos import ErroDeNegocio, ServicoLoja
from app.utilidades import converter_dinheiro, formatar_moeda, normalizar_busca


def criar_servico() -> ServicoLoja:
    conexao = sqlite3.connect(":memory:")
    conexao.row_factory = sqlite3.Row
    conexao.execute("PRAGMA foreign_keys = ON")
    from app.db import criar_esquema

    criar_esquema(conexao)
    return ServicoLoja(conexao)


class TestProdutos(unittest.TestCase):
    def setUp(self) -> None:
        self.servico = criar_servico()
        self.categoria = self.servico.cadastrar_categoria("Caixinhas")

    def test_cadastra_produto_e_recupera_dados(self) -> None:
        produto_id = self.servico.cadastrar_produto(
            "Caixinha milk", self.categoria, 450, 10, 3
        )
        produto = self.servico.obter_produto(produto_id)

        self.assertEqual(produto.nome, "Caixinha milk")
        self.assertEqual(produto.preco_centavos, 450)
        self.assertEqual(produto.estoque, 10)
        self.assertFalse(produto.estoque_baixo)

    def test_recusa_preco_invalido(self) -> None:
        with self.assertRaises(ErroDeNegocio):
            self.servico.cadastrar_produto("Caixa", self.categoria, 0)

    def test_recusa_nome_muito_curto(self) -> None:
        with self.assertRaises(ErroDeNegocio):
            self.servico.cadastrar_produto("ab", self.categoria, 100)

    def test_busca_ignora_acentos_e_maiusculas(self) -> None:
        self.servico.cadastrar_produto("Caixa Coração", self.categoria, 500, 5, 1)
        self.servico.cadastrar_produto("Sacola kraft", self.categoria, 300, 5, 1)

        encontrados = self.servico.buscar_produtos("CORACAO")

        self.assertEqual(len(encontrados), 1)
        self.assertEqual(encontrados[0].nome, "Caixa Coração")

    def test_produto_desativado_sai_do_catalogo(self) -> None:
        produto_id = self.servico.cadastrar_produto("Tag", self.categoria, 200, 5, 1)
        self.servico.desativar_produto(produto_id)

        self.assertEqual(self.servico.listar_produtos(), [])
        self.assertEqual(len(self.servico.listar_produtos(apenas_ativos=False)), 1)

    def test_estoque_baixo_quando_atinge_minimo(self) -> None:
        self.servico.cadastrar_produto("Caixa", self.categoria, 500, 2, 2)

        from app.relatorios import produtos_com_estoque_baixo

        self.assertEqual(len(produtos_com_estoque_baixo(self.servico)), 1)


class TestPedidos(unittest.TestCase):
    def setUp(self) -> None:
        self.servico = criar_servico()
        categoria = self.servico.cadastrar_categoria("Caixinhas")
        self.produto_a = self.servico.cadastrar_produto(
            "Caixa milk", categoria, 450, 100, 10
        )
        self.produto_b = self.servico.cadastrar_produto(
            "Tag de agradecimento", categoria, 180, 100, 10
        )
        self.cliente = self.servico.cadastrar_cliente(
            "Ana Ribeiro", "(11) 98888-1010", "São Paulo"
        )

    def test_total_com_desconto(self) -> None:
        pedido = self.servico.abrir_pedido(self.cliente, desconto_percentual=10)
        self.servico.adicionar_item(pedido, self.produto_a, 10)
        self.servico.adicionar_item(pedido, self.produto_b, 5)

        resumo = self.servico.resumo_pedido(pedido)

        self.assertEqual(resumo.subtotal_centavos, 5400)
        self.assertEqual(resumo.desconto_centavos, 540)
        self.assertEqual(resumo.total_centavos, 4860)

    def test_item_repetido_soma_quantidade(self) -> None:
        pedido = self.servico.abrir_pedido(self.cliente)
        self.servico.adicionar_item(pedido, self.produto_a, 3)
        self.servico.adicionar_item(pedido, self.produto_a, 2)

        resumo = self.servico.resumo_pedido(pedido)

        self.assertEqual(len(resumo.itens), 1)
        self.assertEqual(resumo.itens[0].quantidade, 5)

    def test_recusa_quantidade_acima_do_estoque(self) -> None:
        pedido = self.servico.abrir_pedido(self.cliente)

        with self.assertRaises(ErroDeNegocio):
            self.servico.adicionar_item(pedido, self.produto_a, 101)

    def test_finalizar_baixa_estoque(self) -> None:
        pedido = self.servico.abrir_pedido(self.cliente)
        self.servico.adicionar_item(pedido, self.produto_a, 30)
        self.servico.finalizar_pedido(pedido)

        self.assertEqual(self.servico.obter_produto(self.produto_a).estoque, 70)
        self.assertEqual(self.servico.resumo_pedido(pedido).status, "FINALIZADO")

    def test_nao_finaliza_pedido_vazio(self) -> None:
        pedido = self.servico.abrir_pedido(self.cliente)

        with self.assertRaises(ErroDeNegocio):
            self.servico.finalizar_pedido(pedido)

    def test_nao_finaliza_duas_vezes(self) -> None:
        pedido = self.servico.abrir_pedido(self.cliente)
        self.servico.adicionar_item(pedido, self.produto_a, 1)
        self.servico.finalizar_pedido(pedido)

        with self.assertRaises(ErroDeNegocio):
            self.servico.finalizar_pedido(pedido)

        self.assertEqual(self.servico.obter_produto(self.produto_a).estoque, 99)

    def test_cancelar_pedido_finalizado_devolve_estoque(self) -> None:
        pedido = self.servico.abrir_pedido(self.cliente)
        self.servico.adicionar_item(pedido, self.produto_a, 20)
        self.servico.finalizar_pedido(pedido)
        self.servico.cancelar_pedido(pedido)

        self.assertEqual(self.servico.obter_produto(self.produto_a).estoque, 100)
        self.assertEqual(self.servico.resumo_pedido(pedido).status, "CANCELADO")

    def test_remover_item(self) -> None:
        pedido = self.servico.abrir_pedido(self.cliente)
        self.servico.adicionar_item(pedido, self.produto_a, 4)
        item = self.servico.resumo_pedido(pedido).itens[0]
        self.servico.remover_item(pedido, item.id)

        self.assertEqual(self.servico.resumo_pedido(pedido).itens, [])

    def test_pedido_preserva_preco_do_momento_da_venda(self) -> None:
        pedido = self.servico.abrir_pedido(self.cliente)
        self.servico.adicionar_item(pedido, self.produto_a, 2)

        self.servico.atualizar_produto(self.produto_a, preco_centavos=900)
        resumo = self.servico.resumo_pedido(pedido)

        self.assertEqual(resumo.itens[0].preco_unitario_centavos, 450)
        self.assertEqual(resumo.subtotal_centavos, 900)


class TestRelatorios(unittest.TestCase):
    def setUp(self) -> None:
        self.servico = criar_servico()
        categoria = self.servico.cadastrar_categoria("Kits")
        self.caixa = self.servico.cadastrar_produto("Kit caixa", categoria, 1000, 50, 5)
        self.tag = self.servico.cadastrar_produto("Kit tag", categoria, 500, 50, 5)
        cliente = self.servico.cadastrar_cliente("Bruno", "(11) 97777-2020", "Osasco")

        pedido = self.servico.abrir_pedido(cliente)
        self.servico.adicionar_item(pedido, self.caixa, 3)
        self.servico.adicionar_item(pedido, self.tag, 10)
        self.servico.finalizar_pedido(pedido)

    def test_ranking_mais_vendidos(self) -> None:
        from app.relatorios import produtos_mais_vendidos

        ranking = produtos_mais_vendidos(self.servico)

        self.assertEqual(ranking[0].nome, "Kit tag")
        self.assertEqual(ranking[0].quantidade, 10)
        self.assertEqual(ranking[1].quantidade, 3)

    def test_faturamento_por_categoria(self) -> None:
        from app.relatorios import faturamento_por_categoria

        dados = faturamento_por_categoria(self.servico)

        self.assertEqual(len(dados), 1)
        self.assertEqual(dados[0].categoria, "Kits")
        self.assertEqual(dados[0].itens, 13)
        self.assertEqual(dados[0].receita_centavos, 8000)

    def test_resumo_geral(self) -> None:
        from app.relatorios import resumo_geral

        dados = resumo_geral(self.servico)

        self.assertEqual(dados.produtos_ativos, 2)
        self.assertEqual(dados.clientes, 1)
        self.assertEqual(dados.pedidos_finalizados, 1)
        self.assertEqual(dados.faturamento_centavos, 8000)
        self.assertEqual(dados.ticket_medio_centavos, 8000)


class TestUtilidades(unittest.TestCase):
    def test_converte_dinheiro_em_formatos_diferentes(self) -> None:
        self.assertEqual(converter_dinheiro("12,50"), 1250)
        self.assertEqual(converter_dinheiro("12.50"), 1250)
        self.assertEqual(converter_dinheiro("R$ 1.234,56"), 123456)
        self.assertEqual(converter_dinheiro("7"), 700)

    def test_recusa_valor_invalido(self) -> None:
        with self.assertRaises(ValueError):
            converter_dinheiro("abc")

    def test_formata_moeda(self) -> None:
        self.assertEqual(formatar_moeda(1250), "R$ 12,50")
        self.assertEqual(formatar_moeda(123456), "R$ 1.234,56")
        self.assertEqual(formatar_moeda(5), "R$ 0,05")

    def test_normaliza_busca(self) -> None:
        self.assertEqual(normalizar_busca("  Caixa Coração "), "caixa coracao")


if __name__ == "__main__":
    unittest.main()
