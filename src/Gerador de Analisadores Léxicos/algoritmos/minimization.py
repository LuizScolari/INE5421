from automaton import Automaton

DEAD = object()


def _delta(dfa, state, symbol):
    """transição completa: devolve o estado morto quando não há transição"""
    if state is DEAD:
        return DEAD
    target = dfa.step(state, symbol)
    return target if target is not None else DEAD


def minimize(dfa):
    """minimiza um AFD preservando os rótulos de token dos estados finais"""
    symbols = sorted(dfa.alphabet)
    states = list(dfa.states) + [DEAD]

    group_of = {}
    for state in states:
        if state is not DEAD and state in dfa.accepting:
            group_of[state] = ("final", dfa.token_of.get(state)) # estados finais com tokens diferentes não podem ser juntados
        else:
            group_of[state] = ("comum",)

    while True:
        buckets = {}
        for state in states:
            # cria assinatura para o estado, contém o grupo atual dele e para quais grupos ele vai lendo cada simbolo
            signature = (group_of[state], tuple(group_of[_delta(dfa, state, a)] for a in symbols))
            buckets.setdefault(signature, []).append(state) # estados com a mesma assinatura ficam no mesmo balde
        new_group_of = {}
        # transforma os baldes em numeros de grupos
        # [q0 q1] --> new_group_of[q0] = 0
        for index, members in enumerate(buckets.values()):
            for state in members:
                new_group_of[state] = index
        # se a quantidade de grupos n mudou, acabou
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
