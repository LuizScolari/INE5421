"""Algoritmo (d): determinização de Autômatos (construção de subconjuntos).

Transforma um AFND (possivelmente com epsilon-transições) em um AFD. Cada estado
do AFD corresponde a um conjunto de estados do AFND fechado por epsilon. Quando
um conjunto contém estados finais de tokens diferentes, vence o token de maior
prioridade, definida pela ordem em que as expressões regulares foram declaradas.
"""

from automaton import Automaton, EPSILON


def epsilon_closure(automaton, states):
    """Calcula o fecho-epsilon de um conjunto de estados."""
    closure = set(states)
    stack = list(states)
    while stack:
        state = stack.pop()
        for target in automaton.move(state, EPSILON):
            if target not in closure:
                closure.add(target)
                stack.append(target)
    return closure


def _choose_token(automaton, subset, priority):
    """Seleciona o token de maior prioridade entre os estados finais do subconjunto."""
    best = None
    for state in subset:
        if state in automaton.accepting:
            token = automaton.token_of.get(state)
            rank = priority.get(token, len(priority))
            if best is None or rank < best[0]:
                best = (rank, token)
    return best[1] if best is not None else None


def determinize(automaton, priority=None):
    """Determiniza um AFND gerando o AFD equivalente com rótulos de token."""
    priority = priority or {}
    alphabet = sorted(automaton.alphabet)

    start = frozenset(epsilon_closure(automaton, {automaton.initial}))
    states = {start}
    pending = [start]
    transitions = {}
    while pending:
        current = pending.pop()
        for symbol in alphabet:
            moved = set()
            for state in current:
                moved |= automaton.move(state, symbol)
            if not moved:
                continue
            destination = frozenset(epsilon_closure(automaton, moved))
            transitions[(current, symbol)] = destination
            if destination not in states:
                states.add(destination)
                pending.append(destination)

    dfa = Automaton()
    dfa.set_initial(start)
    for subset in states:
        token = _choose_token(automaton, subset, priority)
        if token is not None or any(state in automaton.accepting for state in subset):
            dfa.add_state(subset, accepting=True, token=token)
        else:
            dfa.add_state(subset)
    for (source, symbol), target in transitions.items():
        dfa.add_transition(source, symbol, target)
    return dfa.rename("q")
