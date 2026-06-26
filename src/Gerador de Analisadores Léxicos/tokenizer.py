"""Interface de execução do analisador léxico.

Usa a tabela de análise léxica (AFD final) para varrer um texto fonte e produzir
a lista de tokens. A varredura segue a regra do maior prefixo: a cada posição
reconhece o lexema mais longo aceito pelo autômato. Espaços em branco separam os
lexemas. Quando nenhum prefixo válido é encontrado, o trecho é reportado como
erro no formato <lexema, erro!>.
"""


def tokenize(table, text):
    """Varre o texto fonte e devolve a lista de pares (lexema, token_ou_None)."""
    tokens = []
    position = 0
    length = len(text)
    while position < length:
        if text[position].isspace():
            position += 1
            continue

        state = table.initial
        last_accept = -1
        last_token = None
        cursor = position
        while cursor < length and not text[cursor].isspace():
            destination = table.step(state, text[cursor])
            if destination is None:
                break
            state = destination
            cursor += 1
            if state in table.accepting:
                last_accept = cursor
                last_token = table.token_of.get(state)

        if last_accept != -1:
            tokens.append((text[position:last_accept], last_token))
            position = last_accept
        else:
            end = position
            while end < length and not text[end].isspace():
                end += 1
            tokens.append((text[position:end], None))
            position = end
    return tokens


def format_tokens(tokens):
    """Formata a lista de tokens conforme o enunciado (<lexema, padrão>)."""
    lines = []
    for lexeme, token in tokens:
        if token is None:
            lines.append(f"<{lexeme}, erro!>")
        else:
            lines.append(f"<{lexeme}, {token}>")
    return "\n".join(lines)
