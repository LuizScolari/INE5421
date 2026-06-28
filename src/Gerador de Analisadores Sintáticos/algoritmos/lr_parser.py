"""Algoritmo (d): programa de análise LR (Algoritmo 4.44 / Figura 4.36 do Aho).

Dirige a análise usando a pilha de estados e as funções ACTION e GOTO da tabela
SLR. A cada passo lê o símbolo de entrada atual e o estado no topo da pilha,
consulta ACTION e executa empilhamento (shift), redução (reduce), aceitação
(accept) ou reporta erro. O resultado informa se a entrada pertence à linguagem,
a sequência de produções aplicadas nas reduções e a árvore de derivação.

A árvore de derivação é montada junto com a análise: cada `shift` cria uma folha
com o terminal lido; cada redução `A -> X1 ... Xk` cria um nó `A` cujos filhos
são os k nós no topo da pilha de nós (a subárvore de cada símbolo do corpo); e
uma produção vazia `A -> &` vira um nó `A` com uma única folha `&`. Assim todos
os casos ficam cobertos, inclusive as produções épsilon. Na aceitação, o nó que
resta é a raiz (o símbolo inicial da gramática).
"""

from grammar import ENDMARK, EPSILON


class DerivationNode:
    """Nó da árvore de derivação: um símbolo e seus filhos (folha não tem filhos)."""

    def __init__(self, symbol, children=None):
        self.symbol = symbol
        self.children = children if children is not None else []

    def is_leaf(self):
        """Indica se o nó é uma folha (terminal ou o épsilon de uma produção vazia)."""
        return not self.children

    def render(self):
        """Devolve a árvore de derivação como texto indentado (estilo ASCII)."""
        lines = [self.symbol]
        self._render_children(lines, "")
        return "\n".join(lines)

    def _render_children(self, lines, prefix):
        total = len(self.children)
        for index, child in enumerate(self.children):
            last = index == total - 1
            lines.append(prefix + ("`-- " if last else "|-- ") + child.symbol)
            child._render_children(lines, prefix + ("    " if last else "|   "))


class ParseResult:
    """Resultado da análise: aceitação, reduções, árvore de derivação e dados do erro."""

    def __init__(self, accepted, reductions, tree=None,
                 error_position=None, error_symbol=None, error_state=None):
        self.accepted = accepted
        self.reductions = reductions
        self.tree = tree
        self.error_position = error_position
        self.error_symbol = error_symbol
        self.error_state = error_state


def parse(table, terminals):
    """Executa o Algoritmo 4.44 sobre a lista de terminais e devolve o resultado."""
    stack = [0]
    nodes = []
    stream = list(terminals) + [ENDMARK]
    position = 0
    reductions = []

    while True:
        state = stack[-1]
        symbol = stream[position]
        move = table.action.get((state, symbol))

        if move is None:
            return ParseResult(False, reductions,
                               error_position=position, error_symbol=symbol, error_state=state)
        if move[0] == "shift":
            stack.append(move[1])
            nodes.append(DerivationNode(symbol))
            position += 1
        elif move[0] == "reduce":
            production = table.grammar.productions[move[1]]
            count = len(production.rhs)
            if count:
                children = nodes[-count:]
                del nodes[-count:]
                del stack[-count:]
            else:
                children = [DerivationNode(EPSILON)]
            exposed = stack[-1]
            stack.append(table.goto[(exposed, production.lhs)])
            nodes.append(DerivationNode(production.lhs, children))
            reductions.append(production)
        elif move[0] == "accept":
            return ParseResult(True, reductions, tree=nodes[-1] if nodes else None)
