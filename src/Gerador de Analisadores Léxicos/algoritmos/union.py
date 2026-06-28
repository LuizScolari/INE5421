from automaton import Automaton, EPSILON


def union(automata):
    """une vários autômatos em um único AFND ligado por epsilon-transições"""
    result = Automaton()
    start = "S"
    result.set_initial(start)

    for index, automaton in enumerate(automata):
        prefix = f"A{index}_"
        rename = lambda state, prefix=prefix: f"{prefix}{state}"
        for source, by_symbol in automaton.transitions.items():
            result.add_state(rename(source))
            for symbol, targets in by_symbol.items():
                for target in targets:
                    result.add_transition(rename(source), symbol, rename(target))
        for state in automaton.accepting:
            renamed = rename(state)
            result.add_state(renamed, accepting=True, token=automaton.token_of.get(state))
        result.add_transition(start, EPSILON, rename(automaton.initial))

    return result
