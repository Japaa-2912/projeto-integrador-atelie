"""Menus e entrada/saída de dados do programa."""

import sys
from datetime import date, datetime

from . import relatorios
from .modelos import ItemPedido, Produto, ResumoPedido
from .servicos import (
    STATUS_ABERTO,
    ErroDeNegocio,
    ServicoLoja,
)
from .utilidades import (
    converter_dinheiro,
    converter_percentual,
    formatar_moeda,
    formatar_percentual,
    truncar,
)

LARGURA = 78


# Entrada de dados
def ler_texto(rotulo: str, padrao: str | None = None) -> str:
    sufixo = f" [{padrao}]" if padrao else ""
    while True:
        valor = input(f"{rotulo}{sufixo}: ").strip()
        if valor:
            return valor
        if padrao is not None:
            return padrao
        print("  ! Este campo é obrigatório.")


def ler_inteiro(
    rotulo: str,
    minimo: int | None = None,
    maximo: int | None = None,
    padrao: int | None = None,
) -> int:
    sufixo = f" [{padrao}]" if padrao is not None else ""
    while True:
        valor = input(f"{rotulo}{sufixo}: ").strip()
        if not valor and padrao is not None:
            return padrao
        try:
            numero = int(valor)
        except ValueError:
            print("  ! Digite apenas números inteiros.")
            continue
        if minimo is not None and numero < minimo:
            print(f"  ! O valor mínimo é {minimo}.")
            continue
        if maximo is not None and numero > maximo:
            print(f"  ! O valor máximo é {maximo}.")
            continue
        return numero


def ler_dinheiro(rotulo: str) -> int:
    while True:
        valor = input(f"{rotulo}: ").strip()
        try:
            return converter_dinheiro(valor)
        except ValueError as erro:
            print(f"  ! {erro}.")


def ler_percentual(rotulo: str, padrao: float = 0) -> float:
    while True:
        valor = input(f"{rotulo} [{formatar_percentual(padrao)}]: ").strip()
        if not valor:
            return padrao
        try:
            return converter_percentual(valor)
        except ValueError as erro:
            print(f"  ! {erro}.")


def ler_data(rotulo: str, padrao: date | None = None) -> date:
    while True:
        sufixo = f" [{padrao.strftime('%d/%m/%Y')}]" if padrao else ""
        valor = input(f"{rotulo}{sufixo}: ").strip()
        if not valor and padrao is not None:
            return padrao
        try:
            return datetime.strptime(valor, "%d/%m/%Y").date()
        except ValueError:
            print("  ! Use o formato dd/mm/aaaa, por exemplo 05/11/2026.")


def ler_opcao(validas: str) -> str:
    while True:
        opcao = input("Opção: ").strip()
        if opcao in validas:
            return opcao
        print(f"  ! Opção inválida. Escolha entre: {', '.join(validas)}.")


def pausar() -> None:
    input("\nPressione Enter para continuar...")


def formatar_data_iso(texto: str) -> str:
    try:
        return datetime.strptime(str(texto), "%Y-%m-%d").strftime("%d/%m/%Y")
    except ValueError:
        return str(texto)


# Saída de dados
def linha(caractere: str = "-") -> str:
    return caractere * LARGURA


def titulo(texto: str) -> None:
    print()
    print(linha("="))
    print(texto.center(LARGURA))
    print(linha("="))


def imprimir_tabela(
    cabecalho: list[tuple[str, str]],
    linhas: list[list[str]],
    vazia: str = "Nenhum registro encontrado.",
) -> None:
    """Cada coluna é (título, alinhamento), com alinhamento <, > ou ^."""
    if not linhas:
        print(f"  {vazia}")
        return

    larguras = [len(titulo_coluna) for titulo_coluna, _ in cabecalho]
    for valores in linhas:
        for indice, valor in enumerate(valores):
            larguras[indice] = max(larguras[indice], len(str(valor)))

    def montar(valores: list[str], alinhamentos: list[str]) -> str:
        celulas = [
            f"{str(valor):{alinhamentos[i]}{larguras[i]}}"
            for i, valor in enumerate(valores)
        ]
        return "  " + " | ".join(celulas)

    alinhamentos = [alinhamento for _, alinhamento in cabecalho]
    print(montar([titulo_coluna for titulo_coluna, _ in cabecalho], alinhamentos))
    print("  " + "-+-".join("-" * largura for largura in larguras))
    for valores in linhas:
        print(montar([str(valor) for valor in valores], alinhamentos))


def exibir_produtos(produtos: list[Produto]) -> None:
    linhas = [
        [
            str(produto.id),
            truncar(produto.nome, 30),
            truncar(produto.categoria, 18),
            produto.preco_formatado,
            str(produto.estoque),
            str(produto.estoque_minimo),
            "sim" if produto.estoque_baixo else "",
        ]
        for produto in produtos
    ]
    imprimir_tabela(
        [
            ("ID", ">"),
            ("Produto", "<"),
            ("Categoria", "<"),
            ("Preço", ">"),
            ("Estq.", ">"),
            ("Mín.", ">"),
            ("Alerta", "<"),
        ],
        linhas,
        vazia="Nenhum produto encontrado.",
    )


def exibir_itens(itens: list[ItemPedido]) -> None:
    linhas = [
        [
            str(item.id),
            truncar(item.produto, 28),
            str(item.quantidade),
            formatar_moeda(item.preco_unitario_centavos),
            item.subtotal_formatado,
        ]
        for item in itens
    ]
    imprimir_tabela(
        [
            ("Item", ">"),
            ("Produto", "<"),
            ("Qtd", ">"),
            ("Unitário", ">"),
            ("Subtotal", ">"),
        ],
        linhas,
        vazia="O pedido ainda não tem itens.",
    )


def exibir_resumo(resumo: ResumoPedido) -> None:
    print()
    print(f"  Pedido #{resumo.pedido_id}  |  Cliente: {resumo.cliente}"
          f"  |  Status: {resumo.status}")
    print(f"  Desconto: {formatar_percentual(resumo.desconto_percentual)}")
    print()
    exibir_itens(resumo.itens)
    print()
    print(f"  Subtotal: {resumo.subtotal_formatado}")
    print(f"  Desconto: {resumo.desconto_formatado}")
    print(f"  Total....: {resumo.total_formatado}")


# Menu de produtos
def cadastrar_produto(servico: ServicoLoja) -> None:
    titulo("Cadastrar produto")

    categorias = servico.listar_categorias()
    print("  Categorias disponíveis:")
    for categoria in categorias:
        print(f"    {categoria.id} - {categoria.nome}")

    nome = ler_texto("  Nome do produto")
    categoria_id = ler_inteiro("  Número da categoria", minimo=1)
    preco = ler_dinheiro("  Preço (ex.: 12,50)")
    estoque = ler_inteiro("  Estoque inicial", minimo=0, padrao=0)
    minimo = ler_inteiro("  Estoque mínimo para alerta", minimo=0, padrao=0)

    produto_id = servico.cadastrar_produto(
        nome=nome,
        categoria_id=categoria_id,
        preco_centavos=preco,
        estoque=estoque,
        estoque_minimo=minimo,
    )
    print(f"\n  Produto cadastrado com o código {produto_id}.")


def editar_produto(servico: ServicoLoja) -> None:
    titulo("Editar produto")
    exibir_produtos(servico.listar_produtos(apenas_ativos=False))
    produto_id = ler_inteiro("  Código do produto", minimo=1)
    produto = servico.obter_produto(produto_id)

    print("  Deixe em branco para manter o valor atual.")
    nome = input(f"  Nome [{produto.nome}]: ").strip() or None
    categoria = input(f"  Categoria atual: {produto.categoria}. Nova categoria: ").strip()
    preco_texto = input(f"  Preço [{produto.preco_formatado}]: ").strip()
    minimo_texto = input(f"  Estoque mínimo [{produto.estoque_minimo}]: ").strip()

    servico.atualizar_produto(
        produto_id=produto_id,
        nome=nome,
        categoria_id=int(categoria) if categoria else None,
        preco_centavos=converter_dinheiro(preco_texto) if preco_texto else None,
        estoque_minimo=int(minimo_texto) if minimo_texto else None,
    )
    print("\n  Produto atualizado.")


def menu_produtos(servico: ServicoLoja) -> None:
    while True:
        titulo("Produtos")
        print("  1 - Listar catálogo")
        print("  2 - Buscar produto por nome")
        print("  3 - Cadastrar produto")
        print("  4 - Editar produto")
        print("  5 - Repor estoque")
        print("  6 - Desativar produto")
        print("  0 - Voltar")
        opcao = ler_opcao("1234560")

        if opcao == "0":
            return
        try:
            if opcao == "1":
                exibir_produtos(servico.listar_produtos())
                pausar()
            elif opcao == "2":
                termo = ler_texto("  Trecho do nome")
                encontrados = servico.buscar_produtos(termo)
                print(f"\n  {len(encontrados)} produto(s) encontrado(s).")
                exibir_produtos(encontrados)
                pausar()
            elif opcao == "3":
                cadastrar_produto(servico)
                pausar()
            elif opcao == "4":
                editar_produto(servico)
                pausar()
            elif opcao == "5":
                exibir_produtos(servico.listar_produtos())
                produto_id = ler_inteiro("  Código do produto", minimo=1)
                quantidade = ler_inteiro("  Quantidade a repor", minimo=1)
                servico.repor_estoque(produto_id, quantidade)
                atualizado = servico.obter_produto(produto_id)
                print(
                    f"\n  Estoque de '{atualizado.nome}' atualizado para "
                    f"{atualizado.estoque} unidades."
                )
                pausar()
            elif opcao == "6":
                exibir_produtos(servico.listar_produtos())
                produto_id = ler_inteiro("  Código do produto", minimo=1)
                servico.desativar_produto(produto_id)
                print("\n  Produto desativado. Ele permanece no histórico dos pedidos.")
                pausar()
        except ErroDeNegocio as erro:
            print(f"\n  ! {erro}")
            pausar()


# Menu de clientes
def menu_clientes(servico: ServicoLoja) -> None:
    while True:
        titulo("Clientes")
        print("  1 - Listar clientes")
        print("  2 - Buscar por nome")
        print("  3 - Cadastrar cliente")
        print("  0 - Voltar")
        opcao = ler_opcao("1230")

        if opcao == "0":
            return
        try:
            if opcao in {"1", "2"}:
                termo = "" if opcao == "1" else ler_texto("  Trecho do nome")
                clientes = (
                    servico.buscar_clientes(termo)
                    if termo
                    else servico.listar_clientes()
                )
                imprimir_tabela(
                    [
                        ("ID", ">"),
                        ("Nome", "<"),
                        ("Telefone", "<"),
                        ("Cidade", "<"),
                    ],
                    [
                        [
                            str(cliente.id),
                            truncar(cliente.nome, 28),
                            cliente.telefone,
                            cliente.cidade or "-",
                        ]
                        for cliente in clientes
                    ],
                    vazia="Nenhum cliente encontrado.",
                )
                pausar()
            elif opcao == "3":
                nome = ler_texto("  Nome do cliente")
                telefone = ler_texto("  Telefone")
                cidade = ler_texto("  Cidade", padrao="")
                cliente_id = servico.cadastrar_cliente(nome, telefone, cidade)
                print(f"\n  Cliente cadastrado com o código {cliente_id}.")
                pausar()
        except ErroDeNegocio as erro:
            print(f"\n  ! {erro}")
            pausar()


# Menu de pedidos
def adicionar_item(servico: ServicoLoja, pedido_id: int) -> None:
    exibir_produtos(servico.listar_produtos())
    produto_id = ler_inteiro("\n  Código do produto (0 para cancelar)", minimo=0)
    if produto_id == 0:
        return
    quantidade = ler_inteiro("  Quantidade", minimo=1)
    servico.adicionar_item(pedido_id, produto_id, quantidade)
    print("\n  Item incluído no pedido.")


def remover_item(servico: ServicoLoja, pedido_id: int) -> None:
    resumo = servico.resumo_pedido(pedido_id)
    if not resumo.itens:
        print("\n  O pedido não tem itens para remover.")
        return
    exibir_itens(resumo.itens)
    item_id = ler_inteiro("\n  Número do item (0 para cancelar)", minimo=0)
    if item_id == 0:
        return
    servico.remover_item(pedido_id, item_id)
    print("\n  Item removido.")


def gerenciar_pedido(servico: ServicoLoja, pedido_id: int) -> None:
    while True:
        resumo = servico.resumo_pedido(pedido_id)
        titulo(f"Pedido #{pedido_id}")
        exibir_resumo(resumo)

        if resumo.status != STATUS_ABERTO:
            print("\n  Este pedido não está mais aberto e não pode ser alterado.")
            pausar()
            return

        print("\n  1 - Adicionar item")
        print("  2 - Remover item")
        print("  3 - Alterar desconto")
        print("  4 - Finalizar pedido")
        print("  5 - Cancelar pedido")
        print("  0 - Voltar")
        opcao = ler_opcao("123450")

        if opcao == "0":
            return
        try:
            if opcao == "1":
                adicionar_item(servico, pedido_id)
            elif opcao == "2":
                remover_item(servico, pedido_id)
            elif opcao == "3":
                novo = ler_percentual("  Novo desconto (%)", resumo.desconto_percentual)
                servico.alterar_desconto(pedido_id, novo)
                print("\n  Desconto atualizado.")
            elif opcao == "4":
                finalizado = servico.finalizar_pedido(pedido_id)
                print(
                    f"\n  Pedido finalizado. Total: {finalizado.total_formatado}. "
                    "O estoque foi atualizado."
                )
                pausar()
                return
            elif opcao == "5":
                confirmar = ler_texto("  Confirmar cancelamento? (s/n)", padrao="n")
                if confirmar.lower().startswith("s"):
                    servico.cancelar_pedido(pedido_id)
                    print("\n  Pedido cancelado.")
                    pausar()
                    return
        except ErroDeNegocio as erro:
            print(f"\n  ! {erro}")
            pausar()


def novo_pedido(servico: ServicoLoja) -> None:
    titulo("Novo pedido")
    clientes = servico.listar_clientes()
    if not clientes:
        print("  Nenhum cliente cadastrado. Cadastre um cliente antes de abrir um pedido.")
        return

    imprimir_tabela(
        [("ID", ">"), ("Nome", "<"), ("Telefone", "<")],
        [
            [str(cliente.id), truncar(cliente.nome, 30), cliente.telefone]
            for cliente in clientes
        ],
    )

    cliente_id = ler_inteiro("\n  Código do cliente", minimo=1)
    desconto = ler_percentual("  Desconto do pedido (%)", 0)
    pedido_id = servico.abrir_pedido(cliente_id, desconto)
    print(f"\n  Pedido #{pedido_id} criado.")
    pausar()
    gerenciar_pedido(servico, pedido_id)


def menu_pedidos(servico: ServicoLoja) -> None:
    while True:
        titulo("Pedidos")
        print("  1 - Novo pedido")
        print("  2 - Listar pedidos")
        print("  3 - Abrir pedido existente")
        print("  0 - Voltar")
        opcao = ler_opcao("1230")

        if opcao == "0":
            return
        try:
            if opcao == "1":
                novo_pedido(servico)
            elif opcao == "2":
                pedidos = servico.listar_pedidos()
                imprimir_tabela(
                    [
                        ("Pedido", ">"),
                        ("Cliente", "<"),
                        ("Status", "<"),
                        ("Criado em", "<"),
                        ("Total", ">"),
                    ],
                    [
                        [
                            str(pedido["id"]),
                            truncar(pedido["cliente"], 26),
                            pedido["status"],
                            pedido["criado_em"],
                            servico.total_pedido_formatado(int(pedido["id"])),
                        ]
                        for pedido in pedidos
                    ],
                    vazia="Nenhum pedido registrado.",
                )
                pausar()
            elif opcao == "3":
                pedido_id = ler_inteiro("  Número do pedido", minimo=1)
                gerenciar_pedido(servico, pedido_id)
        except ErroDeNegocio as erro:
            print(f"\n  ! {erro}")
            pausar()


# Menu de relatórios
def relatorio_estoque_baixo(servico: ServicoLoja) -> None:
    titulo("Produtos com estoque baixo")
    produtos = relatorios.produtos_com_estoque_baixo(servico)
    linhas = [
        [
            str(produto.id),
            truncar(produto.nome, 30),
            str(produto.estoque),
            str(produto.estoque_minimo),
            str(produto.estoque_minimo - produto.estoque),
        ]
        for produto in produtos
    ]
    imprimir_tabela(
        [
            ("ID", ">"),
            ("Produto", "<"),
            ("Estoque", ">"),
            ("Mínimo", ">"),
            ("Faltam", ">"),
        ],
        linhas,
        vazia="Nenhum produto precisa de reposição.",
    )


def relatorio_mais_vendidos(servico: ServicoLoja) -> None:
    titulo("Produtos mais vendidos")
    ranking = relatorios.produtos_mais_vendidos(servico, limite=10)
    linhas = [
        [
            str(posicao),
            truncar(item.nome, 30),
            str(item.quantidade),
            formatar_moeda(item.receita_centavos),
        ]
        for posicao, item in enumerate(ranking, start=1)
    ]
    imprimir_tabela(
        [("#", ">"), ("Produto", "<"), ("Unidades", ">"), ("Receita", ">")],
        linhas,
        vazia="Ainda não há vendas finalizadas.",
    )


def relatorio_categorias(servico: ServicoLoja) -> None:
    titulo("Faturamento por categoria")
    dados = relatorios.faturamento_por_categoria(servico)
    total = sum(item.receita_centavos for item in dados)
    linhas = [
        [
            item.categoria,
            str(item.itens),
            formatar_moeda(item.receita_centavos),
            f"{(item.receita_centavos / total * 100):.1f}%".replace(".", ",")
            if total
            else "0,0%",
        ]
        for item in dados
    ]
    imprimir_tabela(
        [("Categoria", "<"), ("Itens", ">"), ("Receita", ">"), ("Part.", ">")],
        linhas,
        vazia="Ainda não há vendas finalizadas.",
    )
    print(f"\n  Receita total: {formatar_moeda(total)}")


def relatorio_periodo(servico: ServicoLoja) -> None:
    titulo("Vendas por período")
    inicio_padrao, fim_padrao = relatorios.periodo_padrao(30)
    inicio = ler_data("  Data inicial", inicio_padrao)
    fim = ler_data("  Data final", fim_padrao)
    if inicio > fim:
        raise ErroDeNegocio("A data inicial deve ser anterior à data final.")

    vendas = relatorios.vendas_por_periodo(servico, inicio, fim)
    linhas = [
        [
            str(venda["id"]),
            formatar_data_iso(str(venda["data"])),
            truncar(str(venda["cliente"]), 26),
            formatar_moeda(int(venda["total_centavos"])),
        ]
        for venda in vendas
    ]
    imprimir_tabela(
        [("Pedido", ">"), ("Data", "<"), ("Cliente", "<"), ("Total", ">")],
        linhas,
        vazia="Nenhuma venda finalizada no período.",
    )
    total = sum(int(venda["total_centavos"]) for venda in vendas)
    print(f"\n  {len(vendas)} pedido(s) no período. Total: {formatar_moeda(total)}")


def relatorio_resumo(servico: ServicoLoja) -> None:
    titulo("Resumo geral do ateliê")
    dados = relatorios.resumo_geral(servico)
    print(f"  Produtos ativos........: {dados.produtos_ativos}")
    print(f"  Clientes cadastrados...: {dados.clientes}")
    print(f"  Pedidos abertos........: {dados.pedidos_abertos}")
    print(f"  Pedidos finalizados....: {dados.pedidos_finalizados}")
    print(f"  Pedidos cancelados.....: {dados.pedidos_cancelados}")
    print(f"  Faturamento............: {formatar_moeda(dados.faturamento_centavos)}")
    print(f"  Ticket médio...........: {formatar_moeda(dados.ticket_medio_centavos)}")


def exportar_estoque_csv(servico: ServicoLoja) -> None:
    produtos = relatorios.produtos_com_estoque_baixo(servico)
    nome_arquivo = relatorios.nome_arquivo_relatorio("estoque-baixo")
    destino = relatorios.exportar_csv(
        caminho=f"relatorios/{nome_arquivo}",
        cabecalho=["ID", "Produto", "Categoria", "Estoque", "Estoque mínimo"],
        linhas=[
            [
                produto.id,
                produto.nome,
                produto.categoria,
                produto.estoque,
                produto.estoque_minimo,
            ]
            for produto in produtos
        ],
    )
    print(f"\n  Arquivo gerado: {destino.resolve()}")


def menu_relatorios(servico: ServicoLoja) -> None:
    while True:
        titulo("Relatórios")
        print("  1 - Produtos com estoque baixo")
        print("  2 - Produtos mais vendidos")
        print("  3 - Faturamento por categoria")
        print("  4 - Vendas por período")
        print("  5 - Resumo geral")
        print("  6 - Exportar estoque baixo para CSV")
        print("  0 - Voltar")
        opcao = ler_opcao("1234560")

        if opcao == "0":
            return
        try:
            if opcao == "1":
                relatorio_estoque_baixo(servico)
            elif opcao == "2":
                relatorio_mais_vendidos(servico)
            elif opcao == "3":
                relatorio_categorias(servico)
            elif opcao == "4":
                relatorio_periodo(servico)
            elif opcao == "5":
                relatorio_resumo(servico)
            elif opcao == "6":
                exportar_estoque_csv(servico)
        except ErroDeNegocio as erro:
            print(f"\n  ! {erro}")
        pausar()


# Programa principal
def executar(servico: ServicoLoja) -> None:
    while True:
        titulo("Ateliê Encanto — Controle de Pedidos e Estoque")
        print("  1 - Produtos")
        print("  2 - Clientes")
        print("  3 - Pedidos")
        print("  4 - Relatórios")
        print("  0 - Sair")
        opcao = ler_opcao("12340")

        if opcao == "0":
            print("\n  Até logo!")
            return
        if opcao == "1":
            menu_produtos(servico)
        elif opcao == "2":
            menu_clientes(servico)
        elif opcao == "3":
            menu_pedidos(servico)
        elif opcao == "4":
            menu_relatorios(servico)


def configurar_saida() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass
