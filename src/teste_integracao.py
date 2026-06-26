"""Teste de integração entre o Trabalho 1 (léxico) e o Trabalho 2 (sintático).

Demonstra o fluxo completo da apresentação: um programa fonte é analisado pelo
gerador de analisador léxico, produzindo a lista de tokens `<lexema, padrão>`;
essa lista alimenta o gerador de analisador sintático SLR, que atualiza a tabela
de símbolos (palavras reservadas e identificadores) e decide se a entrada
pertence à linguagem da gramática.

Execute a partir da pasta `src`:  python3 teste_integracao.py
"""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE, "Gerador de Analisadores Léxicos"))
sys.path.insert(0, os.path.join(BASE, "Gerador de Analisadores Sintáticos"))

from regular_definitions import parse_definitions
from lexical_analyzer import LexicalAnalyzer
from tokenizer import tokenize, format_tokens

from syntactic_analyzer import SyntacticAnalyzer
from symbol_table import parse_token_list, tokens_to_terminals
from lr_parser import parse


DEFINICOES = """
kw: while | do
id: [a-zA-Z]([a-zA-Z] | [0-9])*
num: [0-9]+
op: = | <
"""

GRAMATICA = """
S ::= while C do S | A
C ::= id < id
A ::= id = E
E ::= id | num
"""

RESERVADAS = ["while", "do"]
FONTE = "while a < b do c = 1"


def main():
    """Roda o pipeline léxico -> sintático e confere o resultado esperado."""
    lexico = LexicalAnalyzer(parse_definitions(DEFINICOES))
    lexico.build()
    saida_lexico = format_tokens(tokenize(lexico.table, FONTE))
    print("Programa fonte:", FONTE)
    print("\nSaida do analisador lexico (Trabalho 1):")
    print(saida_lexico)

    analisador = SyntacticAnalyzer(GRAMATICA, RESERVADAS)
    analisador.build()
    tokens = parse_token_list(saida_lexico)
    terminais, _ = tokens_to_terminals(tokens, analisador.symbol_table, set(analisador.grammar.terminals))
    resultado = parse(analisador.table, terminais)

    print("\nAnalisador sintatico (Trabalho 2):")
    print("  Terminais:", " ".join(terminais))
    print("  Aceito?", resultado.accepted)
    print("  Reducoes:", [producao.text() for producao in resultado.reductions])
    print("\nTabela de simbolos:")
    print(analisador.symbol_table.to_table())

    esperado = ["while", "id", "<", "id", "do", "id", "=", "num"]
    ok = resultado.accepted and terminais == esperado
    print("\n[" + ("OK" if ok else "FALHOU") + "] integracao lexico -> sintatico")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
