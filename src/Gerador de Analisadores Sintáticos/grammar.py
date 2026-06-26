"""Estrutura de dados de Gramática Livre de Contexto e leitura do arquivo.

A gramática é lida no formato `<Não terminal> ::= <Corpo da produção>`, com uma
produção por linha (alternativas separadas por `|` também são aceitas). Os
símbolos do corpo são separados por espaços; um não terminal é todo símbolo que
aparece do lado esquerdo de alguma produção, e os demais símbolos são terminais.
O épsilon é escrito como `&` e representado internamente por um corpo vazio.

Para a construção SLR a gramática é aumentada com uma nova produção `S' ::= S`
(Seção 4.6 do livro do Aho), usada para sinalizar a aceitação da entrada.
"""

EPSILON = "&"
ENDMARK = "$"


class Production:
    """Produção `lhs -> rhs`; rhs é uma tupla de símbolos (vazia para épsilon)."""

    def __init__(self, index, lhs, rhs):
        self.index = index
        self.lhs = lhs
        self.rhs = tuple(rhs)

    def text(self):
        """Devolve a produção em forma legível, usando `&` para o corpo vazio."""
        body = " ".join(self.rhs) if self.rhs else EPSILON
        return f"{self.lhs} -> {body}"


class Grammar:
    """Gramática com não terminais, terminais, produções e símbolo inicial."""

    def __init__(self):
        self.nonterminals = []
        self.terminals = []
        self.productions = []
        self.start = None

    def symbols(self):
        """Devolve todos os símbolos da gramática (não terminais e terminais)."""
        return self.nonterminals + self.terminals

    def productions_for(self, nonterminal):
        """Lista as produções cujo lado esquerdo é o não terminal informado."""
        return [prod for prod in self.productions if prod.lhs == nonterminal]

    def augmented(self):
        """Devolve uma cópia aumentada com a produção `S' -> S` na posição 0."""
        new_start = self.start + "'"
        while new_start in self.nonterminals:
            new_start += "'"
        clone = Grammar()
        clone.nonterminals = [new_start] + list(self.nonterminals)
        clone.terminals = list(self.terminals)
        clone.start = new_start
        clone.original_start = self.start
        clone.productions.append(Production(0, new_start, (self.start,)))
        for prod in self.productions:
            clone.productions.append(Production(len(clone.productions), prod.lhs, prod.rhs))
        return clone


def parse_grammar(text):
    """Lê o texto de uma GLC e devolve a gramática correspondente."""
    raw_productions = []
    nonterminals = []
    for number, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        separator = "::=" if "::=" in stripped else ("->" if "->" in stripped else None)
        if separator is None:
            raise ValueError(f"Linha {number} sem '::=' separando cabeça e corpo: {line!r}")
        head, body = stripped.split(separator, 1)
        head = head.strip()
        if not head:
            raise ValueError(f"Linha {number} sem não terminal à esquerda: {line!r}")
        if head not in nonterminals:
            nonterminals.append(head)
        for alternative in body.split("|"):
            symbols = alternative.split()
            if not symbols or symbols == [EPSILON]:
                raw_productions.append((head, ()))
            else:
                raw_productions.append((head, tuple(symbols)))
    if not raw_productions:
        raise ValueError("Nenhuma produção encontrada na gramática.")

    grammar = Grammar()
    grammar.nonterminals = nonterminals
    grammar.start = nonterminals[0]
    terminals = []
    for head, symbols in raw_productions:
        for symbol in symbols:
            if symbol not in nonterminals and symbol not in terminals:
                terminals.append(symbol)
    grammar.terminals = terminals
    for head, symbols in raw_productions:
        grammar.productions.append(Production(len(grammar.productions), head, symbols))
    return grammar


def load_grammar(path):
    """Carrega a gramática de um arquivo no disco."""
    with open(path, "r", encoding="utf-8") as handle:
        return parse_grammar(handle.read())
