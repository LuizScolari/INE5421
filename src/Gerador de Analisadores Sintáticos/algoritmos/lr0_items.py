def closure(grammar, items):
    """fecho de um conjunto de itens LR(0) (Figura 4.32 do livro)"""
    result = set(items)
    changed = True
    while changed:
        changed = False
        for production_index, dot in list(result):
            rhs = grammar.productions[production_index].rhs
            if dot < len(rhs):
                symbol = rhs[dot]
                if symbol in grammar.nonterminals:
                    for production in grammar.productions_for(symbol):
                        new_item = (production.index, 0)
                        if new_item not in result:
                            result.add(new_item)
                            changed = True
    return frozenset(result)


def goto(grammar, items, symbol):
    """avança o ponto sobre o símbolo X e fecha o conjunto resultante (GOTO)"""
    moved = set()
    for production_index, dot in items:
        rhs = grammar.productions[production_index].rhs
        if dot < len(rhs) and rhs[dot] == symbol:
            moved.add((production_index, dot + 1))
    if not moved:
        return frozenset()
    return closure(grammar, moved)


def canonical_collection(grammar):
    """constrói a coleção canônica de itens LR(0); devolve os estados e o GOTO como dicionário (estado, simbolo) -> estado"""
    start_item = (0, 0)
    initial = closure(grammar, {start_item})
    states = [initial]
    index_of = {initial: 0}
    transitions = {}

    changed = True
    while changed:
        changed = False
        for state in list(states):
            source = index_of[state]
            for symbol in grammar.symbols():
                target = goto(grammar, state, symbol)
                if not target:
                    continue
                if target not in index_of:
                    index_of[target] = len(states)
                    states.append(target)
                    changed = True
                transitions[(source, symbol)] = index_of[target]
    return states, transitions
