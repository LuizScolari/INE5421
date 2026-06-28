def parse_definitions(text):
    """lê o texto das definições e devolve a lista de pares (nome, expressão)"""
    definitions = []
    for number, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        if ":" not in line:
            raise ValueError(f"Linha {number} sem ':' separando nome e expressão: {raw!r}")
        name, expression = line.split(":", 1)
        name = name.strip()
        expression = expression.strip()
        if not name:
            raise ValueError(f"Linha {number} sem nome de definição: {raw!r}")
        if not expression:
            raise ValueError(f"Linha {number} sem expressão regular: {raw!r}")
        definitions.append((name, expression))
    if not definitions:
        raise ValueError("Nenhuma definição regular encontrada no arquivo.")
    return definitions


def load_definitions(path):
    """carrega as definições regulares de um arquivo no disco"""
    with open(path, "r", encoding="utf-8") as handle:
        return parse_definitions(handle.read())
