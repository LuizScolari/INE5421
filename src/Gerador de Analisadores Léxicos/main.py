"""Interface de linha de comando do Gerador de Analisador Léxico.

Recebe um arquivo de definições regulares e executa toda a cadeia de algoritmos
pelo `LexicalAnalyzer` (cada ER vira um AFD pelo método direto de Aho, cada AFD é
minimizado, todos são unidos por epsilon-transição e o AFND resultante é
determinizado). Exibe todas as etapas da construção e, se um arquivo fonte for
informado, tokeniza-o usando a tabela de análise léxica gerada.
"""

import argparse
import os
import sys

# Os algoritmos exigidos pelo enunciado ficam em `algoritmos/`; os demais módulos
# (apoio e interfaces) ficam nesta pasta. Ambos entram no path para que os
# imports funcionem rodando de qualquer diretório.
BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE, "algoritmos"))
sys.path.insert(0, BASE)

from regular_definitions import load_definitions
from lexical_analyzer import LexicalAnalyzer
from tokenizer import tokenize, format_tokens


def build_parser():
    """Monta o parser de argumentos da linha de comando."""
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="Gera o analisador léxico a partir de definições regulares, "
                    "exibindo todas as etapas da construção (AFDs, minimizados, "
                    "união e tabela final). Opcionalmente tokeniza um arquivo fonte.",
    )
    parser.add_argument(
        "definicoes",
        help="arquivo de definições regulares, uma por linha no formato 'nome: expressão'",
    )
    parser.add_argument(
        "fonte",
        nargs="?",
        help="arquivo de texto fonte a tokenizar (opcional)",
    )
    parser.add_argument(
        "-o", "--output",
        metavar="ARQUIVO",
        help="grava a lista de tokens neste arquivo em vez de imprimir na tela "
             "(requer um arquivo fonte)",
    )
    return parser


def main(argv=None):
    """Executa a cadeia completa e exibe as etapas; tokeniza o fonte se informado."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.output and not args.fonte:
        parser.error("--output só faz sentido junto com um arquivo fonte a tokenizar.")

    try:
        definitions = load_definitions(args.definicoes)
    except (OSError, ValueError) as error:
        parser.error(str(error))

    analyzer = LexicalAnalyzer(definitions)
    analyzer.build()

    # Mostra todo o processo: AFD de cada ER, minimizados, AFND da união e tabela.
    print(analyzer.describe())

    if not args.fonte:
        return 0

    try:
        with open(args.fonte, "r", encoding="utf-8") as handle:
            source = handle.read()
    except OSError as error:
        parser.error(str(error))

    tokens = format_tokens(tokenize(analyzer.table, source))
    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(tokens + "\n")
        print(f"\nLista de tokens salva em: {args.output}")
    else:
        print("\n=== Tokens reconhecidos ===")
        print(tokens)
    return 0


if __name__ == "__main__":
    sys.exit(main())
