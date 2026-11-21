import unittest

from app.algoritmos import busca_binaria, ordenacao_por_insercao, ordenacao_por_selecao


class TestBuscaBinaria(unittest.TestCase):
    def test_encontra_elemento_do_meio(self) -> None:
        self.assertEqual(busca_binaria([1, 3, 5, 7, 9], 5), 2)

    def test_encontra_primeiro_e_ultimo(self) -> None:
        lista = [2, 4, 6, 8, 10]
        self.assertEqual(busca_binaria(lista, 2), 0)
        self.assertEqual(busca_binaria(lista, 10), 4)

    def test_devolve_menos_um_quando_nao_encontra(self) -> None:
        self.assertEqual(busca_binaria([1, 3, 5], 4), -1)

    def test_lista_vazia(self) -> None:
        self.assertEqual(busca_binaria([], 1), -1)


class TestOrdenacao(unittest.TestCase):
    def test_selecao_ordena_crescente(self) -> None:
        self.assertEqual(ordenacao_por_selecao([5, 2, 9, 1, 7]), [1, 2, 5, 7, 9])

    def test_insercao_ordena_crescente(self) -> None:
        self.assertEqual(ordenacao_por_insercao([5, 2, 9, 1, 7]), [1, 2, 5, 7, 9])

    def test_ordena_por_chave(self) -> None:
        registros = [("b", 2), ("a", 3), ("c", 1)]
        ordenado = ordenacao_por_selecao(registros, chave=lambda item: item[1])
        self.assertEqual([item[0] for item in ordenado], ["c", "b", "a"])

    def test_lista_ja_ordenada(self) -> None:
        self.assertEqual(ordenacao_por_insercao([1, 2, 3]), [1, 2, 3])

    def test_lista_vazia_e_com_um_elemento(self) -> None:
        self.assertEqual(ordenacao_por_selecao([]), [])
        self.assertEqual(ordenacao_por_insercao([42]), [42])


if __name__ == "__main__":
    unittest.main()
