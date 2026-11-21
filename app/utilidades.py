"""Funções auxiliares de formatação, conversão e normalização de texto."""

from __future__ import annotations

import unicodedata


def remover_acentos(texto: str) -> str:
    """Devolve o texto sem acentos, preservando as demais letras."""
    decomposto = unicodedata.normalize("NFD", texto)
    return "".join(c for c in decomposto if unicodedata.category(c) != "Mn")


def normalizar_busca(texto: str) -> str:
    """Padroniza o texto para comparação: sem acento, minúsculo e sem espaços extras."""
    return remover_acentos(texto).strip().lower()


def formatar_moeda(centavos: int) -> str:
    """Converte 12345 em 'R$ 123,45'."""
    reais, resto = divmod(int(centavos), 100)
    inteiro = f"{reais:,}".replace(",", ".")
    return f"R$ {inteiro},{resto:02d}"


def converter_dinheiro(texto: str) -> int:
    """Converte '12,50', '12.50' ou 'R$ 12,50' em 1250 centavos.

    Levanta ``ValueError`` quando o texto não representa um valor válido.
    """
    limpo = texto.strip().replace("R$", "").replace(" ", "")
    if not limpo:
        raise ValueError("informe um valor")

    if "," in limpo and "." in limpo:
        # Formato 1.234,56 (ponto de milhar e vírgula decimal)
        limpo = limpo.replace(".", "").replace(",", ".")
    elif "," in limpo:
        limpo = limpo.replace(",", ".")

    try:
        valor = float(limpo)
    except ValueError as erro:
        raise ValueError("use apenas números, por exemplo 12,50") from erro

    if valor < 0:
        raise ValueError("o valor não pode ser negativo")

    return int(round(valor * 100))


def converter_percentual(texto: str) -> float:
    """Converte '5' ou '5,5' em 5 ou 5.5, validando o intervalo de 0 a 100."""
    limpo = texto.strip().replace("%", "").replace(",", ".")
    try:
        valor = float(limpo)
    except ValueError as erro:
        raise ValueError("use apenas números, por exemplo 5 ou 5,5") from erro

    if not 0 <= valor <= 100:
        raise ValueError("o desconto deve estar entre 0 e 100")

    return valor


def formatar_percentual(valor: float) -> str:
    """Mostra 5.0 como '5%' e 5.5 como '5,5%'."""
    texto = f"{valor:.2f}".rstrip("0").rstrip(".")
    return texto.replace(".", ",") + "%"


def truncar(texto: str, limite: int) -> str:
    """Corta o texto no limite indicado, acrescentando reticências."""
    if len(texto) <= limite:
        return texto
    return texto[: limite - 1] + "…"
