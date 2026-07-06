from automaton import Automaton

DEAD = object()


def _delta(dfa, state, symbol):
    """transição completa: devolve o estado morto quando não há transição"""
    # ex: se dfa.step('q0','a') == None (sem transição), _delta devolve DEAD em vez de None
    if state is DEAD:
        return DEAD  # do morto, qualquer símbolo leva ao próprio morto (ex: _delta(dfa, DEAD, 'a') -> DEAD)
    target = dfa.step(state, symbol)
    return target if target is not None else DEAD


def minimize(dfa):
    """minimiza um AFD preservando os rótulos de token dos estados finais"""
    # ex (AFD "termina em a"): dfa.states = {q0,q1,q2}  ->  states = [q0,q1,q2,DEAD]
    symbols = sorted(dfa.alphabet)
    states = list(dfa.states) + [DEAD]

    group_of = {}
    for state in states:
        if state is not DEAD and state in dfa.accepting:
            group_of[state] = ("final", dfa.token_of.get(state)) # estados finais com tokens diferentes não podem ser juntados
            # ex: q1 e q2 (finais do mesmo token "T") -> os dois recebem group_of = ("final","T"), já começam juntos
        else:
            group_of[state] = ("comum",)
            # ex: q0 e DEAD (não são finais) -> group_of = ("comum",)

    while True:
        buckets = {}
        for state in states:
            # cria assinatura para o estado, contém o grupo atual dele e para quais grupos ele vai lendo cada simbolo
            # ex: q1 -> a:q2(grupo "final") b:q0(grupo "comum") => assinatura = (("final","T"), (("final","T"),("comum",)))
            #     q2 -> a:q1(grupo "final") b:q0(grupo "comum") => mesma assinatura de q1 -> ficam no mesmo balde
            signature = (group_of[state], tuple(group_of[_delta(dfa, state, a)] for a in symbols))
            buckets.setdefault(signature, []).append(state) # estados com a mesma assinatura ficam no mesmo balde
        new_group_of = {}
        # transforma os baldes em numeros de grupos
        # [q0 q1] --> new_group_of[q0] = 0
        # ex: buckets = {sigA:[q0], sigB:[q1,q2], sigC:[DEAD]} -> new_group_of = {q0:0, q1:1, q2:1, DEAD:2}
        for index, members in enumerate(buckets.values()):
            for state in members:
                new_group_of[state] = index
        # se a quantidade de grupos n mudou, acabou
        # ex: antes 2 grupos (final/comum), depois 3 (0,1,2) -> mudou, continua. na proxima rodada some 3 -> 3, para
        if len(set(new_group_of.values())) == len(set(group_of.values())):
            group_of = new_group_of
            break
        group_of = new_group_of

    representative = {}
    for state in states:
        representative.setdefault(group_of[state], state)
        # ex: grupo 0 -> representante q0; grupo 1 -> representante q1 (primeiro visto; q2 é ignorado, é o mesmo grupo)

    dead_group = group_of[DEAD]      # ex: 2
    start_group = group_of[dfa.initial]   # ex: group_of['q0'] = 0

    minimized = Automaton()
    minimized.set_initial(start_group)

    for group, rep in representative.items():
        if group == dead_group and group != start_group:
            continue  # ex: pula o grupo 2 (o morto), nunca vira estado do AFD mínimo
        if rep is not DEAD and rep in dfa.accepting:
            minimized.add_state(group, accepting=True, token=dfa.token_of.get(rep))
            # ex: grupo 1, representante q1, é final com token "T" -> cria o estado "1" já final
        else:
            minimized.add_state(group)  # ex: grupo 0, representante q0, não é final -> estado comum
    for group, rep in representative.items():
        if group == dead_group and group != start_group:
            continue
        for symbol in symbols:
            target_group = group_of[_delta(dfa, rep, symbol)]
            # ex: rep=q1, symbol='a' -> _delta(dfa,'q1','a')='q2' -> group_of['q2']=1 -> target_group=1 (auto laço)
            if target_group == dead_group and target_group != start_group:
                continue
            minimized.add_transition(group, symbol, target_group)
    return minimized.rename("q")
    # resultado final: 2 estados (grupo 0 e grupo 1), onde q1/q2 originais viraram um só com auto laço em 'a'
