import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GEN = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(GEN, "algoritmos"))
sys.path.insert(0, GEN)

from grammar import load_grammar
from slr_table import build_slr_table
from lr_parser import parse
from syntactic_analyzer import SyntacticAnalyzer
from symbol_table import parse_token_list, tokens_to_terminals

RESULTS = []


def check(description, condition):
    """registra o resultado de uma verificação booleana"""
    RESULTS.append((description, bool(condition)))


def grammar_path(name):
    return os.path.join(HERE, "gramaticas", name)


def read(*parts):
    with open(os.path.join(HERE, *parts), "r", encoding="utf-8") as handle:
        return handle.read()


def test_expression_grammar():
    """gramática de expressões: confere estados, FIRST/FOLLOW e reduções (livro)"""
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
    """gramática com épsilon: confere FIRST/FOLLOW e aceitação"""
    grammar = load_grammar(grammar_path("epsilon.txt"))
    table = build_slr_table(grammar)
    check("Epsilon: FIRST(A) = {a, &}", table.first["A"] == {"a", "&"})
    check("Epsilon: FIRST(S) = {a, c}", table.first["S"] == {"a", "c"})
    check("Epsilon: FOLLOW(A) = {c}", table.follow["A"] == {"c"})
    check("Epsilon: a a c aceito", parse(table, ["a", "a", "c"]).accepted)
    check("Epsilon: c aceito (A deriva vazio)", parse(table, ["c"]).accepted)
    check("Epsilon: a a rejeitado", not parse(table, ["a", "a"]).accepted)


def test_reserved_words():
    """gramática com palavras reservadas: integra tabela de símbolos e tokens"""
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


def test_extended_arithmetic():
    """aritmética com + - * / e parênteses: confere estados e análise (token-file)"""
    grammar = load_grammar(grammar_path("aritmetica_estendida.txt"))
    table = build_slr_table(grammar)
    check("Aritmetica: 17 estados", len(table.states) == 17)
    check("Aritmetica: sem conflitos (SLR(1))", table.is_slr())
    check("Aritmetica: id + num * ( id - num ) aceito",
          parse(table, "id + num * ( id - num )".split()).accepted)
    check("Aritmetica: id / ( id ) - num aceito",
          parse(table, "id / ( id ) - num".split()).accepted)
    rejected = parse(table, "id + + id".split())
    check("Aritmetica: id + + id rejeitado na posicao 2",
          (not rejected.accepted) and rejected.error_position == 2)

    analyzer = SyntacticAnalyzer(read("gramaticas", "aritmetica_estendida.txt"))
    analyzer.build()
    tokens = parse_token_list(read("tokens", "aritmetica_ok.txt"))
    terminals, _ = tokens_to_terminals(tokens, analyzer.symbol_table, set(analyzer.grammar.terminals))
    check("Aritmetica: terminais do token-file corretos",
          terminals == ["id", "+", "num", "*", "(", "id", "-", "num", ")"])
    check("Aritmetica: token-file aceito", parse(analyzer.table, terminals).accepted)


def test_calls_epsilon():
    """chamadas com lista de argumentos e produção épsilon (ARGS -> &)"""
    grammar = load_grammar(grammar_path("chamadas.txt"))
    table = build_slr_table(grammar)
    check("Chamadas: sem conflitos (SLR(1))", table.is_slr())
    check("Chamadas: FIRST(ARGS) contem & e id e num",
          {"&", "id", "num"} <= table.first["ARGS"])
    check("Chamadas: lista vazia id ( ) aceita", parse(table, "id ( )".split()).accepted)
    check("Chamadas: id ( id , num , id ) aceito",
          parse(table, "id ( id , num , id )".split()).accepted)
    check("Chamadas: id ( , id ) rejeitado", not parse(table, "id ( , id )".split()).accepted)
    check("Chamadas: id ( id id ) rejeitado", not parse(table, "id ( id id )".split()).accepted)


def test_blocks():
    """blocos aninhados com if-then, atribuições e expressões (token-file)"""
    analyzer = SyntacticAnalyzer(read("gramaticas", "blocos.txt"), ["if", "then"])
    analyzer.build()
    check("Blocos: 24 estados", len(analyzer.table.states) == 24)
    check("Blocos: sem conflitos (SLR(1))", analyzer.table.is_slr())
    check("Blocos: { { id = num } ; id = id } aceito",
          parse(analyzer.table, "{ { id = num } ; id = id }".split()).accepted)

    tokens = parse_token_list(read("tokens", "blocos_ok.txt"))
    terminals, resolved = tokens_to_terminals(tokens, analyzer.symbol_table, set(analyzer.grammar.terminals))
    check("Blocos: 'if' resolvido como <if, PR>", resolved[1] == ("if", "PR"))
    check("Blocos: 'then' resolvido como <then, PR>", resolved[3] == ("then", "PR"))
    check("Blocos: 'x' inserido como id na tabela", ("x", "id") in analyzer.symbol_table.entries)
    check("Blocos: programa com if-then aceito", parse(analyzer.table, terminals).accepted)


def test_non_slr():
    """gramática ambígua (dangling-else): deve acusar conflito (não é SLR(1))"""
    grammar = load_grammar(grammar_path("dangling_else.txt"))
    table = build_slr_table(grammar)
    check("Dangling-else: nao e SLR(1)", not table.is_slr())
    check("Dangling-else: conflito reportado", len(table.conflicts) >= 1)


def leaves(node):
    """folhas da árvore de derivação, da esquerda para a direita"""
    if node.is_leaf():
        return [node.symbol]
    collected = []
    for child in node.children:
        collected.extend(leaves(child))
    return collected


def test_derivation_tree():
    """árvore de derivação: caso normal, produção épsilon e caso de erro"""
    # Caso normal: as folhas (esq->dir) reproduzem a entrada e a raiz e o inicial.
    table = build_slr_table(load_grammar(grammar_path("expressao.txt")))
    ok = parse(table, ["id", "*", "id", "+", "id"])
    check("Arvore: entrada aceita tem arvore", ok.tree is not None)
    check("Arvore: raiz e o simbolo inicial E", ok.tree.symbol == "E")
    check("Arvore: folhas reproduzem a entrada na ordem",
          leaves(ok.tree) == ["id", "*", "id", "+", "id"])
    check("Arvore: render produz texto", bool(ok.tree.render().strip()))

    # Caso épsilon: A -> & deve virar um no A com a folha '&' (S -> A C, A -> a A | &).
    eps = build_slr_table(load_grammar(grammar_path("epsilon.txt")))
    vazio = parse(eps, ["c"])
    check("Arvore epsilon: entrada 'c' aceita", vazio.accepted and vazio.tree is not None)
    check("Arvore epsilon: producao vazia gera folha '&'", "&" in leaves(vazio.tree))
    check("Arvore epsilon: folhas sao ['&', 'c']", leaves(vazio.tree) == ["&", "c"])

    nao_vazio = parse(eps, ["a", "a", "c"])
    check("Arvore epsilon: 'a a c' aceita com arvore", nao_vazio.accepted and nao_vazio.tree is not None)
    check("Arvore epsilon: folhas de 'a a c' terminam com a, &, c",
          leaves(nao_vazio.tree) == ["a", "a", "&", "c"])

    # Caso de erro: nao ha arvore e o erro e localizado.
    erro = parse(eps, ["a", "a"])
    check("Arvore erro: entrada rejeitada nao tem arvore", (not erro.accepted) and erro.tree is None)
    check("Arvore erro: posicao do erro reportada", erro.error_position is not None)


def main():
    """roda todos os testes e informa o total de verificações aprovadas"""
    test_expression_grammar()
    test_epsilon_grammar()
    test_reserved_words()
    test_extended_arithmetic()
    test_calls_epsilon()
    test_blocks()
    test_non_slr()
    test_derivation_tree()
    passed = 0
    for description, ok in RESULTS:
        passed += int(ok)
        print(f"[{'OK' if ok else 'FALHOU'}] {description}")
    print(f"\n{passed}/{len(RESULTS)} verificacoes aprovadas.")
    return 0 if passed == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
