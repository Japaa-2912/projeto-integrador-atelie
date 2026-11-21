"""Ponto de entrada do Sistema de Controle de Pedidos e Estoque.

Execute com:

    py main.py
"""

from __future__ import annotations

from app import db
from app.interface import configurar_saida, executar
from app.servicos import ServicoLoja


def principal() -> int:
    configurar_saida()

    conexao = db.conectar()
    try:
        if db.banco_vazio(conexao):
            db.semear_dados_exemplo(conexao)
            print("Banco de dados criado em 'dados/atelie.db' com dados de exemplo.")

        servico = ServicoLoja(conexao)
        executar(servico)
    except KeyboardInterrupt:
        print("\nOperação interrompida pelo usuário.")
        return 1
    finally:
        conexao.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(principal())
