"""Interface de projeto do Gerador de Analisador Sintático SLR.

Reúne os algoritmos do livro para, a partir de uma Gramática Livre de Contexto e
da lista de palavras reservadas, construir a tabela de análise SLR. Oferece ainda
visualizações da coleção canônica de itens, dos conjuntos FIRST/FOLLOW e da
tabela ACTION/GOTO.
"""

from grammar import parse_grammar, ENDMARK
from slr_table import build_slr_table
from symbol_table import SymbolTable


def format_item(grammar, item):
    """Formata um item LR(0) `(producao, ponto)` como `A -> alfa . beta`."""
    production_index, dot = item
    production = grammar.productions[production_index]
    body = list(production.rhs)
    body.insert(dot, ".")
    return f"{production.lhs} -> {' '.join(body) if body != ['.'] else '.'}"


class SyntacticAnalyzer:
    """Constrói e guarda a tabela SLR e a tabela de símbolos do analisador."""

    def __init__(self, grammar_text, reserved_words=()):
        self.grammar = parse_grammar(grammar_text)
        self.symbol_table = SymbolTable(reserved_words)
        self.table = None

    def build(self):
        """Constrói a tabela de análise SLR para a gramática fornecida."""
        self.table = build_slr_table(self.grammar)
        return self.table

    def describe_items(self):
        """Visualiza a coleção canônica de conjuntos de itens LR(0)."""
        grammar = self.table.grammar
        blocks = []
        for index, items in enumerate(self.table.states):
            ordered = sorted(items, key=lambda item: (item[0], item[1]))
            lines = [f"I{index}:"] + [f"  {format_item(grammar, item)}" for item in ordered]
            blocks.append("\n".join(lines))
        return "\n\n".join(blocks)

    def describe_first_follow(self):
        """Visualiza os conjuntos FIRST e FOLLOW dos não terminais da gramática."""
        lines = ["FIRST e FOLLOW:"]
        for nonterminal in self.grammar.nonterminals:
            first = "{" + ", ".join(sorted(self.table.first[nonterminal])) + "}"
            follow = "{" + ", ".join(sorted(self.table.follow[nonterminal])) + "}"
            lines.append(f"  {nonterminal}: FIRST = {first}  FOLLOW = {follow}")
        return "\n".join(lines)

    def describe_table(self):
        """Visualiza a tabela de análise SLR (ACTION e GOTO), no estilo da Fig. 4.37."""
        grammar = self.table.grammar
        terminals = list(grammar.terminals) + [ENDMARK]
        nonterminals = [nt for nt in grammar.nonterminals if nt != grammar.start]

        header = ["estado"] + terminals + nonterminals
        rows = [header]
        for state in range(len(self.table.states)):
            row = [str(state)]
            for terminal in terminals:
                move = self.table.action.get((state, terminal))
                row.append(_format_action(move))
            for nonterminal in nonterminals:
                target = self.table.goto.get((state, nonterminal))
                row.append(str(target) if target is not None else "")
            rows.append(row)

        widths = [max(len(row[i]) for row in rows) for i in range(len(header))]
        lines = ["Tabela de analise SLR (ACTION | GOTO):"]
        for position, row in enumerate(rows):
            lines.append(" | ".join(row[i].center(widths[i]) for i in range(len(row))))
            if position == 0:
                lines.append("-+-".join("-" * widths[i] for i in range(len(row))))
        report = "\n".join(lines)
        if not self.table.is_slr():
            report += "\n\nConflitos (gramatica nao e SLR(1)):"
            for state, terminal, old, new in self.table.conflicts:
                report += f"\n  estado {state}, simbolo '{terminal}': {old} x {new}"
        return report


def _format_action(move):
    """Converte uma ação da tabela em texto: shift->sj, reduce->rp, accept->acc."""
    if move is None:
        return ""
    if move[0] == "shift":
        return f"s{move[1]}"
    if move[0] == "reduce":
        return f"r{move[1]}"
    return "acc"
