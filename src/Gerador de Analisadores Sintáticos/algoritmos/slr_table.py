from grammar import ENDMARK
from first_follow import compute_first, compute_follow
from lr0_items import canonical_collection


class SLRTable:
    """tabela SLR com ACTION, GOTO, as produções e os conflitos encontrados"""

    def __init__(self, grammar, states, action, goto, first, follow, conflicts, transitions=None):
        self.grammar = grammar
        self.states = states
        self.action = action
        self.goto = goto
        self.first = first
        self.follow = follow
        self.conflicts = conflicts
        self.transitions = transitions if transitions is not None else {}

    def is_slr(self):
        """indica se a tabela foi construída sem conflitos (gramática SLR(1))"""
        return not self.conflicts


def build_slr_table(grammar):
    """constrói a tabela SLR para uma gramática, aumentando-a antes (Algoritmo 4.46)"""
    augmented = grammar.augmented()
    first = compute_first(augmented)
    follow = compute_follow(augmented, first)
    states, transitions = canonical_collection(augmented)

    action = {}
    goto = {}
    conflicts = []

    def set_action(state, terminal, value):
        existing = action.get((state, terminal))
        if existing is not None and existing != value:
            conflicts.append((state, terminal, existing, value))
            return
        action[(state, terminal)] = value

    for state_index, items in enumerate(states):
        for production_index, dot in items:
            production = augmented.productions[production_index]
            rhs = production.rhs
            if dot < len(rhs):
                symbol = rhs[dot]
                if symbol in augmented.terminals:
                    target = transitions.get((state_index, symbol))
                    if target is not None:
                        set_action(state_index, symbol, ("shift", target))
            else:
                if production.index == 0:
                    set_action(state_index, ENDMARK, ("accept",))
                else:
                    for terminal in follow[production.lhs]:
                        set_action(state_index, terminal, ("reduce", production.index))
        for nonterminal in augmented.nonterminals:
            target = transitions.get((state_index, nonterminal))
            if target is not None:
                goto[(state_index, nonterminal)] = target

    return SLRTable(augmented, states, action, goto, first, follow, conflicts, transitions)
