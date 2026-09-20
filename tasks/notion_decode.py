"""Decodificador do envelope de fetch do Notion MCP.

O arquivo de resultado vem com escapes no estilo JSON numa única linha. Desescapar
com replaces encadeados corrompe LaTeX: `\\neq` vira barra + quebra de linha + `eq`,
porque o replace de `\\n` roda antes do replace de `\\\\`. Este decodificador varre
uma vez só, da esquerda para a direita, e por isso não tem esse problema.
"""

import re

_SIMPLES = {"n": "\n", "t": "\t", "r": "\r", '"': '"', "\\": "\\", "/": "/"}


def decodificar(texto: str) -> str:
    saida = []
    i = 0
    while i < len(texto):
        if texto[i] == "\\" and i + 1 < len(texto):
            proximo = texto[i + 1]
            if proximo in _SIMPLES:
                saida.append(_SIMPLES[proximo])
                i += 2
                continue
            if proximo == "u" and i + 5 < len(texto):
                try:
                    saida.append(chr(int(texto[i + 2 : i + 6], 16)))
                    i += 6
                    continue
                except ValueError:
                    pass
        saida.append(texto[i])
        i += 1
    return "".join(saida)


def carregar(caminho: str) -> str:
    with open(caminho, encoding="utf-8") as arquivo:
        return decodificar(arquivo.read())


def normalizar_imagens(texto: str) -> str:
    """Troca as URLs assinadas do S3 por um marcador, para comparar duas safras."""
    return re.sub(r"https://prod-files-secure[^)\"\s]*", "S3", texto)
