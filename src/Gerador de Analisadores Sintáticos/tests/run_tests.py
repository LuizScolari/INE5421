"""Testes automatizados do Gerador de Analisador Sintático SLR.

Cobrem a fidelidade ao livro do Aho (gramática de expressões da Seção 4.6:
12 estados, FIRST/FOLLOW do Exemplo 4.30 e a sequência de reduções da Figura
4.38), o tratamento de produções com épsilon e a integração com a tabela de
símbolos e as palavras reservadas (formato de tokens do Trabalho 1).
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from grammar import load_grammar
from slr_table import build_slr_table
from lr_parser import parse
from syntactic_analyzer import SyntacticAnalyzer
from symbol_table import parse_token_list, tokens_to_terminals

RESULTS = []


def check(description, condition):
    """Registra o resultado de uma verificação booleana."""
    RESULTS.append((description, bool(condition)))


def grammar_path(name):
    return os.path.join(HERE, "gramaticas", name)


def read(*parts):
    with open(os.path.join(HERE, *parts), "r", encoding="utf-8") as handle:
        return handle.read()


def test_expression_grammar():
    """Gramática de expressões: confere estados, FIRST/FOLLOW e reduções (livro)."""
    grammar = load_grammar(grammar_path("expressao.txt"))
    table = build_slr_table(grammar)
    check("Expressao: 12 estados (Fig 4.31)", len(table.states) == 12)
    check("Expressao: sem conflitos (SLR(1))", table.is_slr())
    check("Expressao: FIRST(E) = {(, id}", table.first["E"] == {"(", "id"})
    check("Expressao: FOLLOW(E) = {$, ), +}", table.follow["E"] == {"$", ")", "+"})
    check("Expressao: FOLLOW(T) = {$, ), *, +}", table.follow["T"] == {"$", ")", "*", "+"})

    result = parse(table, ["id", "*", "id", "+", "id"])
    expected = ["F -> id", "T -> F", "F -> id", "T -> T * F", "E -> T", "F -> id", "T -> F", "E -> E + T"]
    check("Expressao: id * id + id aceito", result.accepted)
    check("Expressao: reducoes iguais a Fig 4.38", [p.text() for p in result.reductions] == expected)

    bad = parse(table, ["id", "+", "+", "id"])
    check("Expressao: id + + id rejeitado", not bad.accepted)
    check("Expressao: erro reportado na posicao 2", bad.error_position == 2)


def test_epsilon_grammar():
    """Gramática com épsilon: confere FIRST/FOLLOW e aceitação."""
    grammar = load_grammar(grammar_path("epsilon.txt"))
    table = build_slr_table(grammar)
    check("Epsilon: FIRST(A) = {a, &}", table.first["A"] == {"a", "&"})
    check("Epsilon: FIRST(S) = {a, c}", table.first["S"] == {"a", "c"})
    check("Epsilon: FOLLOW(A) = {c}", table.follow["A"] == {"c"})
    check("Epsilon: a a c aceito", parse(table, ["a", "a", "c"]).accepted)
    check("Epsilon: c aceito (A deriva vazio)", parse(table, ["c"]).accepted)
    check("Epsilon: a a rejeitado", not parse(table, ["a", "a"]).accepted)


def test_reserved_words():
    """Gramática com palavras reservadas: integra tabela de símbolos e tokens."""
    analyzer = SyntacticAnalyzer(read("gramaticas", "comandos.txt"), ["begin", "end"])
    analyzer.build()
    check("Comandos: sem conflitos (SLR(1))", analyzer.table.is_slr())

    tokens = parse_token_list(read("tokens", "comandos_ok.txt"))
    terminals, resolved = tokens_to_terminals(tokens, analyzer.symbol_table, set(analyzer.grammar.terminals))
    expected_terminals = ["begin", "id", "=", "num", ";", "id", "=", "id", "end"]
    check("Comandos: terminais resolvidos corretamente", terminals == expected_terminals)
    check("Comandos: 'begin' resolvido como <begin, PR>", resolved[0] == ("begin", "PR"))
    check("Comandos: 'x' inserido como id na tabela", ("x", "id") in analyzer.symbol_table.entries)
    check("Comandos: programa aceito", parse(analyzer.table, terminals).accepted)


def main():
    """Roda todos os testes e informa o total de verificações aprovadas."""
    test_expression_grammar()
    test_epsilon_grammar()
    test_reserved_words()
    passed = 0
    for description, ok in RESULTS:
        passed += int(ok)
        print(f"[{'OK' if ok else 'FALHOU'}] {description}")
    print(f"\n{passed}/{len(RESULTS)} verificacoes aprovadas.")
    return 0 if passed == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
