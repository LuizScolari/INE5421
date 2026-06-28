"""Algoritmo (d): programa de análise LR (Algoritmo 4.44 / Figura 4.36 do Aho).

Dirige a análise usando a pilha de estados e as funções ACTION e GOTO da tabela
SLR. A cada passo lê o símbolo de entrada atual e o estado no topo da pilha,
consulta ACTION e executa empilhamento (shift), redução (reduce), aceitação
(accept) ou reporta erro. O resultado informa se a entrada pertence à linguagem
e a sequência de produções aplicadas nas reduções.
"""

from grammar import ENDMARK


class ParseResult:
    """Resultado da análise: aceitação, reduções aplicadas e dados do erro."""

    def __init__(self, accepted, reductions, error_position=None, error_symbol=None, error_state=None):
        self.accepted = accepted
        self.reductions = reductions
        self.error_position = error_position
        self.error_symbol = error_symbol
        self.error_state = error_state


def parse(table, terminals):
    """Executa o Algoritmo 4.44 sobre a lista de terminais e devolve o resultado."""
    stack = [0]
    stream = list(terminals) + [ENDMARK]
    position = 0
    reductions = []

    while True:
        state = stack[-1]
        symbol = stream[position]
        move = table.action.get((state, symbol))

        if move is None:
            return ParseResult(False, reductions, position, symbol, state)
        if move[0] == "shift":
            stack.append(move[1])
            position += 1
        elif move[0] == "reduce":
            production = table.grammar.productions[move[1]]
            for _ in range(len(production.rhs)):
                stack.pop()
            exposed = stack[-1]
            stack.append(table.goto[(exposed, production.lhs)])
            reductions.append(production)
        elif move[0] == "accept":
            return ParseResult(True, reductions)
