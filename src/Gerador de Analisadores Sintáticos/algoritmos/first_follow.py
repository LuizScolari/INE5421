from grammar import EPSILON, ENDMARK


def first_of_sequence(first, symbols):
    """calcula o FIRST de uma sequência de símbolos a partir dos FIRST já conhecidos"""
    result = set()
    all_nullable = True
    for symbol in symbols:
        symbol_first = first.get(symbol, {symbol})
        result |= symbol_first - {EPSILON}
        if EPSILON not in symbol_first:
            all_nullable = False
            break
    if all_nullable:
        result.add(EPSILON)
    return result


def compute_first(grammar):
    """calcula FIRST para todos os símbolos da gramática (regras 1 a 3 da Seção 4.4.2)"""
    first = {terminal: {terminal} for terminal in grammar.terminals}
    for nonterminal in grammar.nonterminals:
        first[nonterminal] = set()

    changed = True
    while changed:
        changed = False
        for production in grammar.productions:
            if not production.rhs:
                contribution = {EPSILON}
            else:
                contribution = first_of_sequence(first, production.rhs)
            before = len(first[production.lhs])
            first[production.lhs] |= contribution
            if len(first[production.lhs]) != before:
                changed = True
    return first


def compute_follow(grammar, first):
    """calcula FOLLOW para todos os não terminais (regras 1 a 3 da Seção 4.4.2)"""
    follow = {nonterminal: set() for nonterminal in grammar.nonterminals}
    follow[grammar.start].add(ENDMARK)

    changed = True
    while changed:
        changed = False
        for production in grammar.productions:
            for position, symbol in enumerate(production.rhs):
                if symbol not in follow:
                    continue
                beta = production.rhs[position + 1:]
                first_beta = first_of_sequence(first, beta)
                before = len(follow[symbol])
                follow[symbol] |= first_beta - {EPSILON}
                if EPSILON in first_beta:
                    follow[symbol] |= follow[production.lhs]
                if len(follow[symbol]) != before:
                    changed = True
    return follow
