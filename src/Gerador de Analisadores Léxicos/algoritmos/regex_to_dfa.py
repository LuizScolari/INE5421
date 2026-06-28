from automaton import Automaton

OPERATORS = {"*", "+", "?", "|", "."}
PRECEDENCE = {"|": 1, ".": 2, "*": 3, "+": 3, "?": 3}
EPSILON = "&"
ENDMARKER = "#"
RESERVED = {EPSILON, ENDMARKER}


class Node:
    """nó da árvore sintática; após a expansão só há 'symbol', 'epsilon', '|', '.' e '*'"""

    def __init__(self, kind, symbol=None, left=None, right=None):
        self.kind = kind
        self.symbol = symbol
        self.left = left
        self.right = right
        self.position = None
        self.nullable = False
        self.firstpos = set()
        self.lastpos = set()


def _expand_group(content):
    """expande o conteúdo de um grupo em uma lista de símbolos individuais"""
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


def _literal(char):
    """valida um caractere usado como símbolo literal dentro de uma classe"""
    if char in RESERVED:
        raise ValueError(f"Símbolo '{char}' é reservado e não pode ser literal.")
    return char


def to_tokens(regex):
    """lê a ER como tokens tipados (kind, value), onde kind é 'op', 'sym' ou 'eps'; dentro de [...] tudo é literal"""
    tokens = []
    index = 0
    length = len(regex)
    while index < length:
        char = regex[index]
        if char == " ":
            index += 1
        elif char == "[":
            end = regex.find("]", index)
            if end == -1:
                raise ValueError("Grupo '[' sem ']' correspondente.")
            members = _expand_group(regex[index + 1:end])
            if not members:
                raise ValueError("Grupo de caracteres '[]' vazio.")
            tokens.append(("op", "("))
            for position, member in enumerate(members):
                if position > 0:
                    tokens.append(("op", "|"))
                tokens.append(("sym", _literal(member)))
            tokens.append(("op", ")"))
            index = end + 1
        elif char in OPERATORS or char in "()":
            tokens.append(("op", char))
            index += 1
        elif char == EPSILON:
            tokens.append(("eps", char))
            index += 1
        elif char == ENDMARKER:
            raise ValueError("Símbolo '#' é reservado (marcador de fim).")
        else:
            tokens.append(("sym", char))
            index += 1
    return tokens


def add_concatenation(tokens):
    """insere o operador de concatenação '.' explicitamente entre os tokens"""
    closing = {("op", ")"), ("op", "*"), ("op", "+"), ("op", "?")}
    result = []
    for index, token in enumerate(tokens):
        result.append(token)
        if index + 1 >= len(tokens):
            break
        nxt = tokens[index + 1]
        left_closes = token[0] in ("sym", "eps") or token in closing
        right_opens = nxt[0] in ("sym", "eps") or nxt == ("op", "(")
        if left_closes and right_opens:
            result.append(("op", "."))
    return result


def to_postfix(tokens):
    """converte a sequência de tokens tipados para notação posfixa (shunting-yard)"""
    output = []
    operators = []
    for kind, value in tokens:
        if kind in ("sym", "eps"):
            output.append((kind, value))
        elif value in ("*", "+", "?"):
            output.append(("op", value))
        elif value in ("|", "."):
            while operators and operators[-1] != "(" and PRECEDENCE[operators[-1]] >= PRECEDENCE[value]:
                output.append(("op", operators.pop()))
            operators.append(value)
        elif value == "(":
            operators.append("(")
        elif value == ")":
            while operators and operators[-1] != "(":
                output.append(("op", operators.pop()))
            if not operators:
                raise ValueError("Parêntese ')' sem '(' correspondente.")
            operators.pop()
    while operators:
        top = operators.pop()
        if top == "(":
            raise ValueError("Parêntese '(' sem ')' correspondente.")
        output.append(("op", top))
    return output


def build_tree(postfix):
    """constrói a árvore sintática a partir da expressão tipada em notação posfixa"""
    stack = []
    for kind, value in postfix:
        if kind == "eps":
            stack.append(Node("epsilon"))
        elif kind == "sym":
            stack.append(Node("symbol", symbol=value))
        elif value in ("*", "+", "?"):
            if not stack:
                raise ValueError("Expressão regular mal formada.")
            stack.append(Node(value, left=stack.pop()))
        else:
            if len(stack) < 2:
                raise ValueError("Expressão regular mal formada.")
            right = stack.pop()
            left = stack.pop()
            stack.append(Node(value, left=left, right=right))
    if len(stack) != 1:
        raise ValueError("Expressão regular mal formada.")
    return stack.pop()


def copy_subtree(node):
    """duplica uma subárvore, usado na expansão de `r+` em `rr*`"""
    clone = Node(node.kind, symbol=node.symbol)
    if node.left is not None:
        clone.left = copy_subtree(node.left)
    if node.right is not None:
        clone.right = copy_subtree(node.right)
    return clone


def desugar(node):
    """reescreve os operadores `+` e `?` usando apenas união, concatenação e fecho"""
    if node.kind in ("symbol", "epsilon"):
        return node
    if node.kind in ("|", "."):
        node.left = desugar(node.left)
        node.right = desugar(node.right)
        return node
    if node.kind == "*":
        node.left = desugar(node.left)
        return node
    if node.kind == "?":
        child = desugar(node.left)
        return Node("|", left=child, right=Node("epsilon"))
    if node.kind == "+":
        child = desugar(node.left)
        return Node(".", left=child, right=Node("*", left=copy_subtree(child)))
    raise ValueError(f"Operador desconhecido na árvore: {node.kind}")


def assign_positions(node, counter, symbol_at):
    """numera as folhas de símbolo (incluindo `#`) da esquerda para a direita"""
    if node is None or node.kind == "epsilon":
        return
    if node.kind == "symbol":
        counter[0] += 1
        node.position = counter[0]
        symbol_at[counter[0]] = node.symbol
        return
    assign_positions(node.left, counter, symbol_at)
    assign_positions(node.right, counter, symbol_at)


def annotate(node, followpos):
    """calcula nullable, firstpos, lastpos e followpos pelas regras da Figura 3.58"""
    if node.kind == "epsilon":
        node.nullable = True
        node.firstpos = set()
        node.lastpos = set()
    elif node.kind == "symbol":
        node.nullable = False
        node.firstpos = {node.position}
        node.lastpos = {node.position}
    elif node.kind == "|":
        annotate(node.left, followpos)
        annotate(node.right, followpos)
        node.nullable = node.left.nullable or node.right.nullable
        node.firstpos = node.left.firstpos | node.right.firstpos
        node.lastpos = node.left.lastpos | node.right.lastpos
    elif node.kind == ".":
        annotate(node.left, followpos)
        annotate(node.right, followpos)
        node.nullable = node.left.nullable and node.right.nullable
        if node.left.nullable:
            node.firstpos = node.left.firstpos | node.right.firstpos
        else:
            node.firstpos = set(node.left.firstpos)
        if node.right.nullable:
            node.lastpos = node.right.lastpos | node.left.lastpos
        else:
            node.lastpos = set(node.right.lastpos)
        for position in node.left.lastpos:
            followpos[position] |= node.right.firstpos
    elif node.kind == "*":
        annotate(node.left, followpos)
        node.nullable = True
        node.firstpos = set(node.left.firstpos)
        node.lastpos = set(node.left.lastpos)
        for position in node.left.lastpos:
            followpos[position] |= node.left.firstpos


def regex_to_dfa(regex, token=None):
    """converte uma expressão regular em um AFD rotulado pelo token informado"""
    postfix = to_postfix(add_concatenation(to_tokens(regex)))
    tree = desugar(build_tree(postfix))

    end_leaf = Node("symbol", symbol=ENDMARKER)
    root = Node(".", left=tree, right=end_leaf)

    symbol_at = {}
    counter = [0]
    assign_positions(root, counter, symbol_at)
    end_position = end_leaf.position

    followpos = {position: set() for position in symbol_at}
    annotate(root, followpos)

    alphabet = {symbol_at[position] for position in symbol_at if position != end_position}
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
