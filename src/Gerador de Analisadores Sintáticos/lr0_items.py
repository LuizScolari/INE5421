"""Algoritmos (b) e (c): itens LR(0), CLOSURE, GOTO e coleção canônica.

Um item LR(0) é representado pelo par `(indice_da_producao, posicao_do_ponto)`,
como sugerido no quadro "Representing Item Sets" do livro. CLOSURE segue a
Figura 4.32, GOTO segue a definição da Seção 4.6.2 e a coleção canônica de
conjuntos de itens segue o algoritmo da Figura 4.33, sempre sobre a gramática
aumentada `G'`.
"""


def closure(grammar, items):
    """CLOSURE de um conjunto de itens (Figura 4.32 do livro)."""
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
    """GOTO(I, X): avança o ponto sobre o símbolo X e fecha o resultado."""
    moved = set()
    for production_index, dot in items:
        rhs = grammar.productions[production_index].rhs
        if dot < len(rhs) and rhs[dot] == symbol:
            moved.add((production_index, dot + 1))
    if not moved:
        return frozenset()
    return closure(grammar, moved)


def canonical_collection(grammar):
    """Constrói a coleção canônica de conjuntos de itens LR(0) (Figura 4.33).

    Devolve a lista de estados (conjuntos de itens) e a função GOTO codificada
    como um dicionário `(indice_estado, simbolo) -> indice_estado`.
    """
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
