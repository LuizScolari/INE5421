"""Algoritmo (a): conversão de Expressão Regular para AFD.

Implementa o método direto descrito no livro do Aho. A expressão regular é
aumentada com um marcador de fim, transformada em uma árvore sintática e, a
partir das funções nullable, firstpos, lastpos e followpos, o AFD é construído
sem passar por um autômato não determinístico intermediário.
"""

from automaton import Automaton

OPERATORS = {"*", "+", "?", "|", "."}
PRECEDENCE = {"|": 1, ".": 2, "*": 3, "+": 3, "?": 3}
EPSILON = "&"
ENDMARKER = "#"


class Node:
    """Nó da árvore sintática da expressão regular."""

    def __init__(self, kind, symbol=None, left=None, right=None):
        self.kind = kind
        self.symbol = symbol
        self.left = left
        self.right = right
        self.position = None
        self.nullable = False
        self.firstpos = set()
        self.lastpos = set()


def expand_classes(regex):
    """Substitui grupos como [a-z] por alternações equivalentes (a|b|...)."""
    output = []
    index = 0
    while index < len(regex):
        char = regex[index]
        if char == "[":
            end = regex.find("]", index)
            if end == -1:
                raise ValueError("Grupo '[' sem ']' correspondente.")
            members = _expand_group(regex[index + 1:end])
            output.append("(")
            output.append("|".join(members))
            output.append(")")
            index = end + 1
        else:
            output.append(char)
            index += 1
    return "".join(output)


def _expand_group(content):
    """Expande o conteúdo de um grupo em uma lista de símbolos individuais."""
    members = []
    index = 0
    while index < len(content):
        if index + 2 < len(content) and content[index + 1] == "-":
            start, end = content[index], content[index + 2]
            for code in range(ord(start), ord(end) + 1):
                members.append(chr(code))
            index += 3
        else:
            if content[index] != " ":
                members.append(content[index])
            index += 1
    return members


def to_tokens(regex):
    """Lê a expressão regular como uma lista de símbolos e operadores."""
    tokens = []
    for char in regex:
        if char == " ":
            continue
        if char in OPERATORS or char in "()":
            tokens.append(("op", char))
        else:
            tokens.append(("sym", char))
    return tokens


def add_concatenation(tokens):
    """Insere o operador de concatenação '.' explicitamente entre os tokens."""
    closing = {("op", ")"), ("op", "*"), ("op", "+"), ("op", "?")}
    result = []
    for index, token in enumerate(tokens):
        result.append(token)
        if index + 1 >= len(tokens):
            break
        nxt = tokens[index + 1]
        left_closes = token[0] == "sym" or token in closing
        right_opens = nxt[0] == "sym" or nxt == ("op", "(")
        if left_closes and right_opens:
            result.append(("op", "."))
    return result


def to_postfix(tokens):
    """Converte a sequência de tokens para notação posfixa (shunting-yard)."""
    output = []
    operators = []
    for kind, value in tokens:
        if kind == "sym":
            output.append(value)
        elif value in ("*", "+", "?"):
            output.append(value)
        elif value in ("|", "."):
            while operators and operators[-1] != "(" and PRECEDENCE[operators[-1]] >= PRECEDENCE[value]:
                output.append(operators.pop())
            operators.append(value)
        elif value == "(":
            operators.append("(")
        elif value == ")":
            while operators and operators[-1] != "(":
                output.append(operators.pop())
            if not operators:
                raise ValueError("Parêntese ')' sem '(' correspondente.")
            operators.pop()
    while operators:
        top = operators.pop()
        if top == "(":
            raise ValueError("Parêntese '(' sem ')' correspondente.")
        output.append(top)
    return output


def build_tree(postfix):
    """Constrói a árvore sintática a partir da expressão em notação posfixa."""
    stack = []
    counter = [0]
    for token in postfix:
        if token == EPSILON:
            stack.append(Node("epsilon"))
        elif token not in OPERATORS:
            counter[0] += 1
            node = Node("symbol", symbol=token)
            node.position = counter[0]
            stack.append(node)
        elif token in ("*", "+", "?"):
            child = stack.pop()
            stack.append(Node(token, left=child))
        else:
            right = stack.pop()
            left = stack.pop()
            stack.append(Node(token, left=left, right=right))
    if len(stack) != 1:
        raise ValueError("Expressão regular mal formada.")
    return stack.pop(), counter[0]


def annotate(node, followpos, symbol_at):
    """Calcula nullable, firstpos, lastpos e followpos em pós-ordem."""
    if node.kind == "epsilon":
        node.nullable = True
        return
    if node.kind == "symbol":
        node.nullable = False
        node.firstpos = {node.position}
        node.lastpos = {node.position}
        symbol_at[node.position] = node.symbol
        followpos.setdefault(node.position, set())
        return

    if node.kind == "|":
        annotate(node.left, followpos, symbol_at)
        annotate(node.right, followpos, symbol_at)
        node.nullable = node.left.nullable or node.right.nullable
        node.firstpos = node.left.firstpos | node.right.firstpos
        node.lastpos = node.left.lastpos | node.right.lastpos
    elif node.kind == ".":
        annotate(node.left, followpos, symbol_at)
        annotate(node.right, followpos, symbol_at)
        node.nullable = node.left.nullable and node.right.nullable
        node.firstpos = node.left.firstpos | (node.right.firstpos if node.left.nullable else set())
        node.lastpos = node.right.lastpos | (node.left.lastpos if node.right.nullable else set())
        for position in node.left.lastpos:
            followpos[position] |= node.right.firstpos
    elif node.kind in ("*", "+"):
        annotate(node.left, followpos, symbol_at)
        node.nullable = True if node.kind == "*" else node.left.nullable
        node.firstpos = set(node.left.firstpos)
        node.lastpos = set(node.left.lastpos)
        for position in node.left.lastpos:
            followpos[position] |= node.left.firstpos
    elif node.kind == "?":
        annotate(node.left, followpos, symbol_at)
        node.nullable = True
        node.firstpos = set(node.left.firstpos)
        node.lastpos = set(node.left.lastpos)


def regex_to_dfa(regex, token=None):
    """Converte uma expressão regular em um AFD rotulado pelo token informado."""
    expanded = expand_classes(regex)
    tokens = add_concatenation(to_tokens(expanded))
    postfix = to_postfix(tokens)
    tree, last_position = build_tree(postfix)

    end_position = last_position + 1
    end_leaf = Node("symbol", symbol=ENDMARKER)
    end_leaf.position = end_position
    root = Node(".", left=tree, right=end_leaf)

    followpos = {}
    symbol_at = {}
    annotate(root, followpos, symbol_at)

    alphabet = {sym for pos, sym in symbol_at.items() if pos != end_position}
    start = frozenset(root.firstpos)
    states = {start}
    pending = [start]
    transitions = {}
    while pending:
        current = pending.pop()
        for symbol in alphabet:
            destination = set()
            for position in current:
                if symbol_at.get(position) == symbol:
                    destination |= followpos.get(position, set())
            if destination:
                destination = frozenset(destination)
                transitions[(current, symbol)] = destination
                if destination not in states:
                    states.add(destination)
                    pending.append(destination)

    automaton = Automaton()
    automaton.set_initial(start)
    for state in states:
        is_final = end_position in state
        automaton.add_state(state, accepting=is_final, token=token if is_final else None)
    for (source, symbol), target in transitions.items():
        automaton.add_transition(source, symbol, target)
    return automaton.rename("q")
