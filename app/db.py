"""Conexão com o banco de dados SQLite e criação do esquema.

O banco é o arquivo ``dados/atelie.db``. Ele é criado automaticamente na
primeira execução, de modo que o programa não depende de instalação de
servidor de banco de dados.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

CAMINHO_PADRAO = Path(__file__).resolve().parent.parent / "dados" / "atelie.db"

# Valores monetários são guardados em centavos (números inteiros) para
# evitar erros de arredondamento típicos de números de ponto flutuante.
ESQUEMA = """
CREATE TABLE IF NOT EXISTS categorias (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT    NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS produtos (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    nome           TEXT    NOT NULL,
    nome_busca     TEXT    NOT NULL,
    categoria_id   INTEGER NOT NULL REFERENCES categorias (id),
    preco_centavos INTEGER NOT NULL CHECK (preco_centavos >= 0),
    estoque        INTEGER NOT NULL DEFAULT 0 CHECK (estoque >= 0),
    estoque_minimo INTEGER NOT NULL DEFAULT 0 CHECK (estoque_minimo >= 0),
    ativo          INTEGER NOT NULL DEFAULT 1 CHECK (ativo IN (0, 1)),
    criado_em      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE INDEX IF NOT EXISTS idx_produtos_busca ON produtos (nome_busca);

CREATE TABLE IF NOT EXISTS clientes (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    nome     TEXT NOT NULL,
    telefone TEXT NOT NULL,
    cidade   TEXT,
    criado_em TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS pedidos (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id          INTEGER NOT NULL REFERENCES clientes (id),
    status              TEXT    NOT NULL DEFAULT 'ABERTO'
                        CHECK (status IN ('ABERTO', 'FINALIZADO', 'CANCELADO')),
    desconto_percentual REAL    NOT NULL DEFAULT 0
                        CHECK (desconto_percentual BETWEEN 0 AND 100),
    criado_em           TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    finalizado_em       TEXT
);

CREATE TABLE IF NOT EXISTS pedido_itens (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    pedido_id               INTEGER NOT NULL REFERENCES pedidos (id) ON DELETE CASCADE,
    produto_id              INTEGER NOT NULL REFERENCES produtos (id),
    quantidade              INTEGER NOT NULL CHECK (quantidade > 0),
    preco_unitario_centavos INTEGER NOT NULL CHECK (preco_unitario_centavos >= 0)
);

CREATE INDEX IF NOT EXISTS idx_itens_pedido ON pedido_itens (pedido_id);
"""


def conectar(caminho: str | Path = CAMINHO_PADRAO) -> sqlite3.Connection:
    """Abre (ou cria) o banco e garante que o esquema exista.

    Aceita ``":memory:"`` para execução em memória, recurso usado pelos
    testes automatizados.
    """
    texto_caminho = str(caminho)
    if texto_caminho != ":memory:":
        arquivo = Path(texto_caminho)
        arquivo.parent.mkdir(parents=True, exist_ok=True)

    conexao = sqlite3.connect(texto_caminho)
    conexao.row_factory = sqlite3.Row
    conexao.execute("PRAGMA foreign_keys = ON")
    criar_esquema(conexao)
    return conexao


def criar_esquema(conexao: sqlite3.Connection) -> None:
    """Executa o script de criação das tabelas e índices."""
    conexao.executescript(ESQUEMA)
    conexao.commit()


def banco_vazio(conexao: sqlite3.Connection) -> bool:
    """Informa se ainda não há nenhuma categoria cadastrada."""
    total = conexao.execute("SELECT COUNT(*) FROM categorias").fetchone()[0]
    return total == 0


def semear_dados_exemplo(conexao: sqlite3.Connection) -> None:
    """Carrega um catálogo inicial para demonstração do sistema."""
    if not banco_vazio(conexao):
        return

    from .servicos import ServicoLoja

    servico = ServicoLoja(conexao)

    categorias = {
        "Caixinhas": servico.cadastrar_categoria("Caixinhas"),
        "Sacos e sacolas": servico.cadastrar_categoria("Sacos e sacolas"),
        "Tags e cartões": servico.cadastrar_categoria("Tags e cartões"),
        "Kits de festa": servico.cadastrar_categoria("Kits de festa"),
    }

    catalogo = [
        ("Caixinha milk personalizada", categorias["Caixinhas"], 450, 120, 20),
        ("Caixa hexagonal com laço", categorias["Caixinhas"], 790, 60, 15),
        ("Sacola de papel kraft", categorias["Sacos e sacolas"], 350, 200, 40),
        ("Sacolinha de tecido", categorias["Sacos e sacolas"], 1250, 25, 10),
        ("Tag de agradecimento", categorias["Tags e cartões"], 180, 300, 50),
        ("Cartão impresso com nome", categorias["Tags e cartões"], 260, 150, 30),
        ("Kit festa 10 convidados", categorias["Kits de festa"], 8900, 12, 5),
        ("Kit maternidade", categorias["Kits de festa"], 6400, 8, 5),
    ]

    for nome, categoria_id, preco, estoque, minimo in catalogo:
        servico.cadastrar_produto(
            nome=nome,
            categoria_id=categoria_id,
            preco_centavos=preco,
            estoque=estoque,
            estoque_minimo=minimo,
        )

    ana = servico.cadastrar_cliente("Ana Ribeiro", "(11) 98888-1010", "São Paulo")
    bruno = servico.cadastrar_cliente("Bruno Almeida", "(11) 97777-2020", "Osasco")
    servico.cadastrar_cliente("Carla Souza", "(11) 96666-3030", "Guarulhos")
    servico.cadastrar_cliente("Ateliê Doce Festa", "(11) 95555-4040", "Santo André")

    pedido = servico.abrir_pedido(ana, desconto_percentual=5)
    servico.adicionar_item(pedido, 1, 30)
    servico.adicionar_item(pedido, 5, 30)
    servico.finalizar_pedido(pedido)

    pedido = servico.abrir_pedido(bruno)
    servico.adicionar_item(pedido, 7, 2)
    servico.finalizar_pedido(pedido)
