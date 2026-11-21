"""Funções de apoio para formatar e converter valores."""

import unicodedata


def remover_acentos(texto: str) -> str:
    decomposto = unicodedata.normalize("NFD", texto)
    return "".join(c for c in decomposto if unicodedata.category(c) != "Mn")


def normalizar_busca(texto: str) -> str:
    return remover_acentos(texto).strip().lower()


def formatar_moeda(centavos: int) -> str:
    reais, resto = divmod(int(centavos), 100)
    inteiro = f"{reais:,}".replace(",", ".")
    return f"R$ {inteiro},{resto:02d}"


def converter_dinheiro(texto: str) -> int:
    """Aceita valores como 12,50, 12.50 e R$ 12,50."""
    limpo = texto.strip().replace("R$", "").replace(" ", "")
    if not limpo:
        raise ValueError("informe um valor")

    # 1.234,56 vira 1234.56
    if "," in limpo and "." in limpo:
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
    limpo = texto.strip().replace("%", "").replace(",", ".")
    try:
        valor = float(limpo)
    except ValueError as erro:
        raise ValueError("use apenas números, por exemplo 5 ou 5,5") from erro

    if not 0 <= valor <= 100:
        raise ValueError("o desconto deve estar entre 0 e 100")

    return valor


def formatar_percentual(valor: float) -> str:
    texto = f"{valor:.2f}".rstrip("0").rstrip(".")
    return texto.replace(".", ",") + "%"


def truncar(texto: str, limite: int) -> str:
    if len(texto) <= limite:
        return texto
    return texto[: limite - 1] + "…"
