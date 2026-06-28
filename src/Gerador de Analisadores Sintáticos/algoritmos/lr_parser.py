from grammar import ENDMARK, EPSILON


class DerivationNode:
    """nó da árvore de derivação: um símbolo e seus filhos (folha não tem filhos)"""

    def __init__(self, symbol, children=None):
        self.symbol = symbol
        self.children = children if children is not None else []

    def is_leaf(self):
        """indica se o nó é uma folha (terminal ou o épsilon de uma produção vazia)"""
        return not self.children

    def render(self):
        """devolve a árvore de derivação como texto indentado (estilo ASCII)"""
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
    """resultado da análise: aceitação, reduções, árvore de derivação e dados do erro"""

    def __init__(self, accepted, reductions, tree=None,
                 error_position=None, error_symbol=None, error_state=None):
        self.accepted = accepted
        self.reductions = reductions
        self.tree = tree
        self.error_position = error_position
        self.error_symbol = error_symbol
        self.error_state = error_state


def parse(table, terminals):
    """executa a análise LR sobre a lista de terminais e devolve o resultado"""
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
