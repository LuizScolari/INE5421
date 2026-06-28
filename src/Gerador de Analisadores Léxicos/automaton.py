EPSILON = "&"


class Automaton:
    """autômato finito com estados, alfabeto, transições e rótulos de token"""

    def __init__(self):
        self.states = set()
        self.alphabet = set()
        self.transitions = {}
        self.initial = None
        self.accepting = set()
        self.token_of = {}

    def add_state(self, state, accepting=False, token=None):
        """inclui um estado, opcionalmente marcando-o como final e seu token"""
        self.states.add(state)
        if state not in self.transitions:
            self.transitions[state] = {}
        if accepting:
            self.accepting.add(state)
            if token is not None:
                self.token_of[state] = token

    def set_initial(self, state):
        """define o estado inicial, garantindo que ele exista"""
        self.add_state(state)
        self.initial = state

    def add_transition(self, source, symbol, target):
        """acrescenta a transição source --symbol--> target ao autômato"""
        self.add_state(source)
        self.add_state(target)
        if symbol != EPSILON:
            self.alphabet.add(symbol)
        self.transitions[source].setdefault(symbol, set()).add(target)

    def move(self, state, symbol):
        """retorna o conjunto de estados alcançados a partir de state por symbol"""
        return self.transitions.get(state, {}).get(symbol, set())

    def step(self, state, symbol):
        """retorna o único destino de um AFD ou None quando não há transição"""
        targets = self.move(state, symbol)
        if not targets:
            return None
        return next(iter(targets))

    def is_deterministic(self):
        """indica se o autômato é determinístico (sem epsilon e sem ramificação)"""
        for source in self.transitions.values():
            for symbol, targets in source.items():
                if symbol == EPSILON or len(targets) > 1:
                    return False
        return True

    def rename(self, prefix="q"):
        """devolve uma cópia com estados renomeados em ordem de alcance (BFS)"""
        order = []
        seen = set()
        queue = [self.initial] if self.initial is not None else []
        while queue:
            current = queue.pop(0)
            if current in seen:
                continue
            seen.add(current)
            order.append(current)
            for symbol in sorted(self.transitions.get(current, {}), key=str):
                for target in sorted(self.transitions[current][symbol], key=str):
                    if target not in seen:
                        queue.append(target)
        for state in sorted(self.states, key=str):
            if state not in seen:
                seen.add(state)
                order.append(state)

        mapping = {state: f"{prefix}{index}" for index, state in enumerate(order)}
        renamed = Automaton()
        renamed.alphabet = set(self.alphabet)
        if self.initial is not None:
            renamed.set_initial(mapping[self.initial])
        for source, by_symbol in self.transitions.items():
            renamed.add_state(mapping[source])
            for symbol, targets in by_symbol.items():
                for target in targets:
                    renamed.add_transition(mapping[source], symbol, mapping[target])
        for state in self.accepting:
            renamed.accepting.add(mapping[state])
            if state in self.token_of:
                renamed.token_of[mapping[state]] = self.token_of[state]
        return renamed

    def to_table(self, title=None):
        """monta uma representação textual do autômato em forma de tabela"""
        symbols = sorted(self.alphabet)
        has_epsilon = any(EPSILON in by_symbol for by_symbol in self.transitions.values())
        columns = symbols + ([EPSILON] if has_epsilon else [])

        state_names = {state: str(state) for state in self.states}
        header_cells = ["", "estado"] + columns
        rows = [header_cells]
        for state in sorted(self.states, key=str):
            marker = ""
            if state == self.initial:
                marker += "->"
            if state in self.accepting:
                marker += "*"
            label = state_names[state]
            if state in self.token_of:
                label += f" ({self.token_of[state]})"
            row = [marker, label]
            for symbol in columns:
                targets = self.move(state, symbol)
                cell = ",".join(sorted(state_names[t] for t in targets)) if targets else "-"
                row.append(cell)
            rows.append(row)

        widths = [max(len(row[i]) for row in rows) for i in range(len(header_cells))]
        lines = []
        if title:
            lines.append(title)
        for index, row in enumerate(rows):
            cells = [row[i].ljust(widths[i]) for i in range(len(row))]
            lines.append(" | ".join(cells))
            if index == 0:
                lines.append("-+-".join("-" * widths[i] for i in range(len(row))))
        return "\n".join(lines)
