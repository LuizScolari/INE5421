"""Algoritmo (b): minimização de Autômatos Finitos Determinísticos.

A minimização remove estados inalcançáveis e estados mortos (de onde nenhum
estado final é atingível) e em seguida aplica refinamento de partições. Dois
estados ficam no mesmo bloco enquanto não houver um símbolo que os leve a
blocos diferentes. Estados finais com tokens distintos começam separados para
preservar a informação de qual padrão cada estado reconhece.
"""

from automaton import Automaton

DEAD = object()


def remove_unreachable(dfa):
    """Devolve o conjunto de estados alcançáveis a partir do estado inicial."""
    reachable = set()
    queue = [dfa.initial]
    while queue:
        state = queue.pop(0)
        if state in reachable:
            continue
        reachable.add(state)
        for targets in dfa.transitions.get(state, {}).values():
            for target in targets:
                if target not in reachable:
                    queue.append(target)
    return reachable


def find_live(dfa, allowed):
    """Devolve os estados que conseguem alcançar algum estado final."""
    predecessors = {state: set() for state in allowed}
    for state in allowed:
        for targets in dfa.transitions.get(state, {}).values():
            for target in targets:
                if target in allowed:
                    predecessors[target].add(state)
    live = set()
    queue = [state for state in allowed if state in dfa.accepting]
    while queue:
        state = queue.pop(0)
        if state in live:
            continue
        live.add(state)
        for predecessor in predecessors[state]:
            if predecessor not in live:
                queue.append(predecessor)
    return live


def minimize(dfa):
    """Minimiza um AFD preservando os rótulos de token dos estados finais."""
    reachable = remove_unreachable(dfa)
    live = find_live(dfa, reachable)
    kept = {state for state in reachable if state in live or state == dfa.initial}

    block_of = {}
    for state in kept:
        if state in dfa.accepting:
            block_of[state] = ("final", dfa.token_of.get(state))
        else:
            block_of[state] = ("comum",)

    symbols = sorted(dfa.alphabet)
    while True:
        signatures = {}
        for state in kept:
            targets = []
            for symbol in symbols:
                destination = dfa.step(state, symbol)
                targets.append(block_of[destination] if destination in block_of else DEAD)
            signatures[state] = (block_of[state], tuple(targets))
        groups = {}
        for state in kept:
            groups.setdefault(signatures[state], set()).add(state)
        new_block_of = {}
        for index, (signature, members) in enumerate(groups.items()):
            for state in members:
                new_block_of[state] = index
        if len(set(new_block_of.values())) == len(set(block_of.values())):
            block_of = new_block_of
            break
        block_of = new_block_of

    minimized = Automaton()
    initial_block = block_of[dfa.initial]
    minimized.set_initial(initial_block)
    for state in kept:
        block = block_of[state]
        if state in dfa.accepting:
            minimized.add_state(block, accepting=True, token=dfa.token_of.get(state))
        else:
            minimized.add_state(block)
    for state in kept:
        for symbol in symbols:
            destination = dfa.step(state, symbol)
            if destination in block_of:
                minimized.add_transition(block_of[state], symbol, block_of[destination])
    return minimized.rename("q")
