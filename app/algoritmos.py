"""Algoritmos clássicos de busca e ordenação usados nos relatórios.

O objetivo deste módulo é didático: as mesmas tarefas poderiam ser resolvidas
com ``sorted()`` e ``list.index()``, mas aqui os algoritmos são implementados
passo a passo para demonstrar o funcionamento e o custo de cada um.
"""

from __future__ import annotations

from typing import Callable, Iterable, Sequence, TypeVar

T = TypeVar("T")


def busca_binaria(lista_ordenada: Sequence[T], chave: T) -> int:
    """Procura ``chave`` em uma lista ordenada e devolve o índice ou -1.

    Custo O(log n): a cada comparação, metade da lista é descartada.
    """
    inicio, fim = 0, len(lista_ordenada) - 1

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
    """Ordena por seleção, de forma crescente, segundo a função ``chave``.

    Custo O(n²) e número de trocas proporcional a n: bom para listas pequenas
    e para evidenciar o conceito de comparação entre elementos.
    """
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
    """Ordena por inserção, de forma crescente, segundo a função ``chave``.

    Custo O(n²) no pior caso e O(n) quando a lista já está quase ordenada.
    """
    lista = list(itens)

    for i in range(1, len(lista)):
        atual = lista[i]
        j = i - 1
        while j >= 0 and chave(lista[j]) > chave(atual):
            lista[j + 1] = lista[j]
            j -= 1
        lista[j + 1] = atual

    return lista
