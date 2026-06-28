class SymbolTable:
    """tabela de símbolos com palavras reservadas e identificadores"""

    def __init__(self, reserved_words=()):
        self.entries = []
        self.index_of = {}
        for word in reserved_words:
            self._insert(word, "PR")

    def _insert(self, lexeme, category):
        """insere um lexema e devolve a linha em que foi armazenado"""
        line = len(self.entries)
        self.entries.append((lexeme, category))
        self.index_of[lexeme] = line
        return line

    def is_reserved(self, lexeme):
        """indica se o lexema é uma palavra reservada já registrada"""
        return self.index_of.get(lexeme) is not None and self.entries[self.index_of[lexeme]][1] == "PR"

    def resolve(self, lexeme, pattern, grammar_terminals):
        """devolve o token de saída e o terminal de gramática para o lexema (reservada e terminal usam o lexema; num usa o padrão; o resto vira id)"""
        if self.is_reserved(lexeme):
            return (lexeme, "PR"), lexeme
        if lexeme in grammar_terminals:
            return (lexeme, pattern), lexeme
        if pattern in grammar_terminals and pattern != "id":
            return (lexeme, pattern), pattern
        line = self.index_of.get(lexeme)
        if line is None:
            line = self._insert(lexeme, "id")
        return ("id", line), "id"

    def to_table(self):
        """monta uma visualização textual da tabela de símbolos"""
        lines = ["linha | lexema | categoria", "------+--------+----------"]
        for line, (lexeme, category) in enumerate(self.entries):
            lines.append(f"{line:<5} | {lexeme:<6} | {category}")
        return "\n".join(lines)


def parse_token_list(text):
    """lê a saída do analisador léxico (`<lexema, padrão>`, um por linha)"""
    tokens = []
    for number, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        if not (stripped.startswith("<") and stripped.endswith(">")):
            raise ValueError(f"Linha {number} fora do formato <lexema, padrao>: {line!r}")
        inner = stripped[1:-1]
        lexeme, pattern = inner.rsplit(",", 1)
        tokens.append((lexeme.strip(), pattern.strip()))
    return tokens


def tokens_to_terminals(tokens, symbol_table, grammar_terminals):
    """converte os tokens em terminais da gramática, atualizando a tabela de símbolos"""
    terminals = []
    resolved = []
    for lexeme, pattern in tokens:
        display, terminal = symbol_table.resolve(lexeme, pattern, grammar_terminals)
        terminals.append(terminal)
        resolved.append(display)
    return terminals, resolved
