"""Algoritmo (b): minimização de AFD (Algoritmo 3.39 do livro do Aho).

Completa o autômato com um estado morto que recebe as transições ausentes,
parte da partição inicial {finais, não-finais} e a refina pelo procedimento da
Figura 3.64: dois estados permanecem no mesmo grupo enquanto, para todo símbolo,
levarem a estados de um mesmo grupo. Ao final, constrói o AFD mínimo escolhendo
um representante por grupo (passo 4) e elimina o estado morto, conforme a seção
"Eliminating the Dead State".

Para o caso do analisador léxico (Seção 3.9.7), os estados finais são separados
na partição inicial por token, de modo que cada grupo reconhece um único padrão.
"""

from automaton import Automaton

DEAD = object()


def _delta(dfa, state, symbol):
    """Função de transição completa: devolve o estado morto quando não há transição."""
    if state is DEAD:
        return DEAD
    target = dfa.step(state, symbol)
    return target if target is not None else DEAD


def minimize(dfa):
    """Minimiza um AFD preservando os rótulos de token dos estados finais."""
    symbols = sorted(dfa.alphabet)
    states = list(dfa.states) + [DEAD]

    group_of = {}
    for state in states:
        if state is not DEAD and state in dfa.accepting:
            group_of[state] = ("final", dfa.token_of.get(state))
        else:
            group_of[state] = ("comum",)

    while True:
        buckets = {}
        for state in states:
            signature = (group_of[state], tuple(group_of[_delta(dfa, state, a)] for a in symbols))
            buckets.setdefault(signature, []).append(state)
        new_group_of = {}
        for index, members in enumerate(buckets.values()):
            for state in members:
                new_group_of[state] = index
        if len(set(new_group_of.values())) == len(set(group_of.values())):
            group_of = new_group_of
            break
        group_of = new_group_of

    representative = {}
    for state in states:
        representative.setdefault(group_of[state], state)

    dead_group = group_of[DEAD]
    start_group = group_of[dfa.initial]

    minimized = Automaton()
    minimized.set_initial(start_group)
    for group, rep in representative.items():
        if group == dead_group and group != start_group:
            continue
        if rep is not DEAD and rep in dfa.accepting:
            minimized.add_state(group, accepting=True, token=dfa.token_of.get(rep))
        else:
            minimized.add_state(group)
    for group, rep in representative.items():
        if group == dead_group and group != start_group:
            continue
        for symbol in symbols:
            target_group = group_of[_delta(dfa, rep, symbol)]
            if target_group == dead_group and target_group != start_group:
                continue
            minimized.add_transition(group, symbol, target_group)
    return minimized.rename("q")
