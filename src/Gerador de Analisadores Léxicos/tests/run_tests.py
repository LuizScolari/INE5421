"""Testes automatizados do Gerador de Analisador Léxico.

Constrói a tabela de análise léxica para cada conjunto de definições e compara a
lista de tokens gerada com o resultado esperado. Os casos cobrem os exemplos do
enunciado e situações adicionais (palavras-chave com prioridade, maior prefixo e
relato de erro).
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from regular_definitions import load_definitions
from lexical_analyzer import LexicalAnalyzer
from tokenizer import tokenize, format_tokens


def analyze(definitions_file, source):
    """Gera a tabela a partir do arquivo de definições e tokeniza o texto fonte."""
    path = os.path.join(HERE, "definicoes", definitions_file)
    analyzer = LexicalAnalyzer(load_definitions(path))
    analyzer.build()
    return format_tokens(tokenize(analyzer.table, source))


CASES = [
    (
        "Exemplo 1 do enunciado (id e num)",
        "exemplo1_id_num.txt",
        "a1\n0\nteste2\n21\nalpha123\n3444\na43teste",
        "<a1, id>\n<0, num>\n<teste2, id>\n<21, num>\n<alpha123, id>\n<3444, num>\n<a43teste, id>",
    ),
    (
        "Exemplo 2 do enunciado, versao literal (er1 e er2 sao equivalentes)",
        "exemplo2_er1_er2.txt",
        "aa\nbbbba\nababab\nbbbbb",
        "<aa, er1>\n<bbbba, er1>\n<ababab, er1>\n<bbbbb, er1>",
    ),
    (
        "Exemplo 2 corrigido, reproduz a intencao do enunciado",
        "exemplo2_corrigido.txt",
        "aa\nbbbba\nababab\nbbbbb",
        "<aa, er1>\n<bbbba, er2>\n<ababab, er1>\n<bbbbb, er2>",
    ),
    (
        "Palavras-chave com prioridade e maior prefixo",
        "exemplo3_palavras_chave.txt",
        "se entao x1 senao y2 casa 42",
        "<se, se>\n<entao, entao>\n<x1, id>\n<senao, senao>\n<y2, id>\n<casa, id>\n<42, num>",
    ),
    (
        "Numeros binario, hexadecimal e decimal (maior prefixo e prioridade)",
        "exemplo4_numeros.txt",
        "0x1f 1010 27 0 11001",
        "<0x1f, hex>\n<1010, bin>\n<27, dec>\n<0, bin>\n<11001, bin>",
    ),
    (
        "Relato de erro para simbolo fora do alfabeto",
        "exemplo1_id_num.txt",
        "abc 123 a1b2 $%",
        "<abc, id>\n<123, num>\n<a1b2, id>\n<$%, erro!>",
    ),
    (
        "Livro Secao 3.8 (Exemplo 3.28): padrao listado primeiro tem prioridade",
        "livro_secao3_8.txt",
        "abb",
        "<abb, pabb>",
    ),
    (
        "Livro Secao 3.8 (Exemplo 3.29): entrada abba reconhece abb e depois a",
        "livro_secao3_8.txt",
        "abba",
        "<abb, pabb>\n<a, pa>",
    ),
]


def main():
    """Roda todos os casos de teste e informa o total de aprovados."""
    passed = 0
    for description, definitions_file, source, expected in CASES:
        produced = analyze(definitions_file, source)
        ok = produced == expected
        passed += int(ok)
        print(f"[{'OK' if ok else 'FALHOU'}] {description}")
        if not ok:
            print("  esperado:")
            print("    " + expected.replace("\n", "\n    "))
            print("  obtido:")
            print("    " + produced.replace("\n", "\n    "))
    print(f"\n{passed}/{len(CASES)} casos aprovados.")
    return 0 if passed == len(CASES) else 1


if __name__ == "__main__":
    sys.exit(main())
