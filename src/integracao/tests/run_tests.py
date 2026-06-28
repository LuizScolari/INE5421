"""Testes de integração entre o Trabalho 1 (léxico) e o Trabalho 2 (sintático).

Roda o pipeline completo — programa fonte -> tokens do analisador léxico ->
terminais via tabela de símbolos -> análise SLR — e confere o resultado. Cobre um
caso embutido (while/do) e todos os exemplos da pasta `exemplos/` de ponta a
ponta: os exemplos com "erro" no nome devem ser rejeitados; os demais, aceitos.

Basta rodar este único arquivo para executar tudo:

    python3 src/integracao/tests/run_tests.py
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
INTEGRACAO = os.path.dirname(HERE)
SRC = os.path.dirname(INTEGRACAO)
# Cada gerador tem os algoritmos do enunciado em `algoritmos/` e os módulos de
# apoio/interface na própria pasta; ambos entram no path.
for nome_pasta in ("Gerador de Analisadores Léxicos", "Gerador de Analisadores Sintáticos"):
    pasta = os.path.join(SRC, nome_pasta)
    sys.path.insert(0, os.path.join(pasta, "algoritmos"))
    sys.path.insert(0, pasta)

EXEMPLOS_DIR = os.path.join(INTEGRACAO, "exemplos")

from regular_definitions import parse_definitions
from lexical_analyzer import LexicalAnalyzer
from tokenizer import tokenize, format_tokens
from syntactic_analyzer import SyntacticAnalyzer
from symbol_table import parse_token_list, tokens_to_terminals
from lr_parser import parse

RESULTS = []


def check(description, condition):
    """Registra o resultado de uma verificação booleana."""
    RESULTS.append((description, bool(condition)))


def run_pipeline(definicoes_texto, gramatica, reservadas, fonte):
    """Executa léxico -> integração -> sintático e devolve (terminais, resultado)."""
    lexico = LexicalAnalyzer(parse_definitions(definicoes_texto))
    lexico.build()
    saida_lexico = format_tokens(tokenize(lexico.table, fonte))

    sintatico = SyntacticAnalyzer(gramatica, reservadas)
    sintatico.build()
    tokens = parse_token_list(saida_lexico)
    terminais, _ = tokens_to_terminals(
        tokens, sintatico.symbol_table, set(sintatico.grammar.terminals))
    return terminais, parse(sintatico.table, terminais)


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


def test_caso_embutido():
    """Caso embutido while/do: confere terminais, aceitação e árvore de derivação."""
    terminais, resultado = run_pipeline(
        DEFINICOES, GRAMATICA, ["while", "do"], "while a < b do c = 1")
    esperado = ["while", "id", "<", "id", "do", "id", "=", "num"]
    check("Embutido: terminais resolvidos corretamente", terminais == esperado)
    check("Embutido: entrada aceita pela gramatica", resultado.accepted)
    check("Embutido: arvore de derivacao construida", resultado.tree is not None)


def _ler(pasta, arquivo, opcional=False):
    """Lê um arquivo do exemplo; devolve string vazia se opcional e ausente."""
    caminho = os.path.join(pasta, arquivo)
    if opcional and not os.path.exists(caminho):
        return ""
    with open(caminho, "r", encoding="utf-8") as handle:
        return handle.read()


def test_exemplos():
    """Roda cada exemplo de `exemplos/` de ponta a ponta (aceito x erro pelo nome)."""
    if not os.path.isdir(EXEMPLOS_DIR):
        check("Exemplos: pasta exemplos/ encontrada", False)
        return

    nomes = sorted(
        nome for nome in os.listdir(EXEMPLOS_DIR)
        if os.path.isdir(os.path.join(EXEMPLOS_DIR, nome))
    )
    check("Exemplos: ha exemplos para testar", bool(nomes))

    for nome in nomes:
        pasta = os.path.join(EXEMPLOS_DIR, nome)
        definicoes = _ler(pasta, "definicoes.txt")
        gramatica = _ler(pasta, "gramatica.txt")
        fonte = _ler(pasta, "fonte.txt")
        reservadas = [linha.strip()
                      for linha in _ler(pasta, "reservadas.txt", opcional=True).splitlines()
                      if linha.strip()]

        _, resultado = run_pipeline(definicoes, gramatica, reservadas, fonte)

        if "erro" in nome.lower():
            check(f"Exemplo '{nome}': rejeitado (erro sintatico esperado)", not resultado.accepted)
        else:
            check(f"Exemplo '{nome}': aceito pela gramatica", resultado.accepted)
            check(f"Exemplo '{nome}': arvore de derivacao construida", resultado.tree is not None)


def main():
    """Roda todos os testes e informa o total de verificações aprovadas."""
    test_caso_embutido()
    test_exemplos()
    passed = 0
    for description, ok in RESULTS:
        passed += int(ok)
        print(f"[{'OK' if ok else 'FALHOU'}] {description}")
    print(f"\n{passed}/{len(RESULTS)} verificacoes aprovadas.")
    return 0 if passed == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
