from app import db
from app.interface import configurar_saida, executar
from app.servicos import ServicoLoja


def principal() -> int:
    configurar_saida()

    conexao = db.conectar()
    try:
        if db.banco_vazio(conexao):
            db.semear_dados_exemplo(conexao)
            print("Banco criado em dados/atelie.db com dados de exemplo.")

        executar(ServicoLoja(conexao))
    except KeyboardInterrupt:
        print("\nPrograma interrompido.")
        return 1
    finally:
        conexao.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(principal())
