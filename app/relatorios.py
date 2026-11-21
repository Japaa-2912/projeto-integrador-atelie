"""Relatórios gerenciais e exportação de dados.

As consultas deste módulo são somente leitura: elas não alteram o banco e por
isso podem ser executadas a qualquer momento pelo usuário.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

from .algoritmos import ordenacao_por_selecao
from .modelos import Produto
from .servicos import ServicoLoja
from .utilidades import formatar_moeda


@dataclass(frozen=True)
class ProdutoVendido:
    produto_id: int
    nome: str
    quantidade: int
    receita_centavos: int


@dataclass(frozen=True)
class FaturamentoCategoria:
    categoria: str
    itens: int
    receita_centavos: int


@dataclass(frozen=True)
class ResumoGeral:
    produtos_ativos: int
    clientes: int
    pedidos_abertos: int
    pedidos_finalizados: int
    pedidos_cancelados: int
    faturamento_centavos: int
    ticket_medio_centavos: int


def produtos_com_estoque_baixo(servico: ServicoLoja) -> list[Produto]:
    """Produtos cujo estoque atual atingiu ou ficou abaixo do mínimo."""
    return servico.produtos.com_estoque_baixo()


def produtos_mais_vendidos(servico: ServicoLoja, limite: int = 5) -> list[ProdutoVendido]:
    """Ranking de produtos por quantidade vendida em pedidos finalizados."""
    linhas = servico.conexao.execute(
        """
        SELECT p.id AS produto_id, p.nome AS nome,
               SUM(i.quantidade) AS quantidade,
               SUM(i.quantidade * i.preco_unitario_centavos) AS receita
          FROM pedido_itens i
          JOIN pedidos pe ON pe.id = i.pedido_id
          JOIN produtos p  ON p.id = i.produto_id
         WHERE pe.status = 'FINALIZADO'
         GROUP BY p.id, p.nome
        """
    ).fetchall()

    ranking = [
        ProdutoVendido(
            produto_id=linha["produto_id"],
            nome=linha["nome"],
            quantidade=int(linha["quantidade"]),
            receita_centavos=int(linha["receita"]),
        )
        for linha in linhas
    ]

    # Ordenação decrescente por quantidade usando o algoritmo implementado.
    ranking = ordenacao_por_selecao(ranking, chave=lambda item: -item.quantidade)
    return ranking[:limite]


def faturamento_por_categoria(servico: ServicoLoja) -> list[FaturamentoCategoria]:
    """Receita líquida e volume de itens vendidos, agrupados por categoria.

    A receita já considera o desconto concedido em cada pedido, para que o
    total do relatório coincida com o faturamento geral.
    """
    linhas = servico.conexao.execute(
        """
        SELECT c.nome AS categoria,
               SUM(i.quantidade) AS itens,
               SUM(i.quantidade * i.preco_unitario_centavos
                   * (1 - pe.desconto_percentual / 100.0)) AS receita
          FROM pedido_itens i
          JOIN pedidos pe   ON pe.id = i.pedido_id
          JOIN produtos p   ON p.id = i.produto_id
          JOIN categorias c ON c.id = p.categoria_id
         WHERE pe.status = 'FINALIZADO'
         GROUP BY c.id, c.nome
         ORDER BY receita DESC
        """
    ).fetchall()

    return [
        FaturamentoCategoria(
            categoria=linha["categoria"],
            itens=int(linha["itens"]),
            receita_centavos=int(round(float(linha["receita"]))),
        )
        for linha in linhas
    ]


def vendas_por_periodo(
    servico: ServicoLoja, inicio: date, fim: date
) -> list[dict[str, object]]:
    """Pedidos finalizados entre duas datas, com total calculado em centavos."""
    linhas = servico.conexao.execute(
        """
        SELECT pe.id,
               cl.nome AS cliente,
               date(pe.finalizado_em) AS data,
               pe.desconto_percentual,
               COALESCE(SUM(i.quantidade * i.preco_unitario_centavos), 0) AS subtotal
          FROM pedidos pe
          JOIN clientes cl ON cl.id = pe.cliente_id
          LEFT JOIN pedido_itens i ON i.pedido_id = pe.id
         WHERE pe.status = 'FINALIZADO'
           AND date(pe.finalizado_em) BETWEEN ? AND ?
         GROUP BY pe.id, cl.nome, data, pe.desconto_percentual
         ORDER BY data, pe.id
        """,
        (inicio.isoformat(), fim.isoformat()),
    ).fetchall()

    resultado: list[dict[str, object]] = []
    for linha in linhas:
        subtotal = int(linha["subtotal"])
        desconto = int(round(subtotal * float(linha["desconto_percentual"]) / 100))
        resultado.append(
            {
                "id": int(linha["id"]),
                "cliente": linha["cliente"],
                "data": linha["data"],
                "total_centavos": subtotal - desconto,
            }
        )
    return resultado


def resumo_geral(servico: ServicoLoja) -> ResumoGeral:
    """Indicadores gerais do ateliê, usados na tela inicial dos relatórios."""
    conexao = servico.conexao

    produtos_ativos = conexao.execute(
        "SELECT COUNT(*) FROM produtos WHERE ativo = 1"
    ).fetchone()[0]
    clientes = conexao.execute("SELECT COUNT(*) FROM clientes").fetchone()[0]

    contagem = {
        linha[0]: linha[1]
        for linha in conexao.execute(
            "SELECT status, COUNT(*) FROM pedidos GROUP BY status"
        ).fetchall()
    }

    faturamento = conexao.execute(
        """
        SELECT COALESCE(SUM(i.quantidade * i.preco_unitario_centavos), 0)
          FROM pedido_itens i
          JOIN pedidos pe ON pe.id = i.pedido_id
         WHERE pe.status = 'FINALIZADO'
        """
    ).fetchone()[0]

    descontos = conexao.execute(
        """
        SELECT COALESCE(SUM(i.quantidade * i.preco_unitario_centavos), 0) AS bruto,
               COALESCE(SUM(
                   (i.quantidade * i.preco_unitario_centavos) * pe.desconto_percentual / 100.0
               ), 0) AS desconto
          FROM pedido_itens i
          JOIN pedidos pe ON pe.id = i.pedido_id
         WHERE pe.status = 'FINALIZADO'
        """
    ).fetchone()

    liquido = int(round(float(descontos["bruto"]) - float(descontos["desconto"])))
    finalizados = contagem.get("FINALIZADO", 0)

    return ResumoGeral(
        produtos_ativos=int(produtos_ativos),
        clientes=int(clientes),
        pedidos_abertos=int(contagem.get("ABERTO", 0)),
        pedidos_finalizados=int(finalizados),
        pedidos_cancelados=int(contagem.get("CANCELADO", 0)),
        faturamento_centavos=liquido,
        ticket_medio_centavos=liquido // finalizados if finalizados else 0,
    )


def periodo_padrao(dias: int = 30) -> tuple[date, date]:
    """Devolve o intervalo dos últimos ``dias`` dias até hoje."""
    hoje = date.today()
    return hoje - timedelta(days=dias - 1), hoje


def exportar_csv(
    caminho: str | Path,
    cabecalho: list[str],
    linhas: list[list[object]],
) -> Path:
    """Grava uma lista de linhas em arquivo CSV compatível com o Excel."""
    destino = Path(caminho)
    destino.parent.mkdir(parents=True, exist_ok=True)

    with destino.open("w", encoding="utf-8-sig", newline="") as arquivo:
        escritor = csv.writer(arquivo, delimiter=";")
        escritor.writerow(cabecalho)
        escritor.writerows(linhas)

    return destino


def nome_arquivo_relatorio(prefixo: str) -> str:
    """Gera um nome de arquivo com data e hora, evitando sobrescrita."""
    agora = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"{prefixo}-{agora}.csv"


def formatar_receita(centavos: int) -> str:
    return formatar_moeda(centavos)
