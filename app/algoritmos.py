"""Busca binária e ordenações feitas na mão."""

from typing import Callable, Iterable, Sequence, TypeVar

T = TypeVar("T")


def busca_binaria(lista_ordenada: Sequence[T], chave: T) -> int:
    """Devolve o índice da chave ou -1 se não encontrar."""
    inicio, fim = 0, len(lista_ordenada) - 1

    # A cada volta, metade da lista é descartada: O(log n).
    while inicio <= fim:
        meio = (inicio + fim) // 2
        if lista_ordenada[meio] == chave:
            return meio
        if lista_ordenada[meio] < chave:
            inicio = meio + 1
        else:
            fim = meio - 1

    return -1


def ordenacao_por_selecao(
    itens: Iterable[T], chave: Callable[[T], object] = lambda item: item
) -> list[T]:
    """Ordena por seleção, comparando os itens pela função chave."""
    lista = list(itens)
    total = len(lista)

    for i in range(total - 1):
        menor = i
        for j in range(i + 1, total):
            if chave(lista[j]) < chave(lista[menor]):
                menor = j
        if menor != i:
            lista[i], lista[menor] = lista[menor], lista[i]

    return lista


def ordenacao_por_insercao(
    itens: Iterable[T], chave: Callable[[T], object] = lambda item: item
) -> list[T]:
    """Ordena por inserção, comparando os itens pela função chave."""
    lista = list(itens)

    for i in range(1, len(lista)):
        atual = lista[i]
        j = i - 1
        while j >= 0 and chave(lista[j]) > chave(atual):
            lista[j + 1] = lista[j]
            j -= 1
        lista[j + 1] = atual

    return lista
