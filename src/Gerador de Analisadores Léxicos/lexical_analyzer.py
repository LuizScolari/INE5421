from regex_to_dfa import regex_to_dfa
from minimization import minimize
from union import union
from determinization import determinize


class LexicalAnalyzer:
    """constrói e guarda os autômatos intermediários e a tabela de análise léxica"""

    def __init__(self, definitions):
        self.definitions = definitions
        self.priority = {name: index for index, (name, _) in enumerate(definitions)}
        self.dfas = []
        self.minimized = []
        self.combined = None
        self.table = None

    def build(self):
        """executa toda a cadeia de algoritmos e produz a tabela de análise léxica"""
        for name, expression in self.definitions:
            dfa = regex_to_dfa(expression, token=name)
            self.dfas.append((name, dfa))
            self.minimized.append((name, minimize(dfa)))

        automata = [automaton for _, automaton in self.minimized]
        self.combined = union(automata)
        self.table = determinize(self.combined, self.priority)
        return self.table

    def describe(self):
        """devolve uma visualização textual de todas as etapas da construção"""
        blocks = []
        for name, dfa in self.dfas:
            blocks.append(dfa.to_table(f"AFD da ER '{name}' (algoritmo de Aho):"))
        for name, dfa in self.minimized:
            blocks.append(dfa.to_table(f"AFD minimizado da ER '{name}':"))
        if self.combined is not None:
            blocks.append(self.combined.to_table("AFND da uniao (com epsilon-transicoes):"))
        if self.table is not None:
            blocks.append(self.table.to_table("Tabela de analise lexica (AFD final):"))
        return "\n\n".join(blocks)
