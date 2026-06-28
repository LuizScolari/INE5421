"""Interface de linha de comando do Gerador de Analisador Sintático SLR.

Recebe uma gramática livre de contexto e constrói a tabela de análise SLR pelo
`SyntacticAnalyzer`, exibindo todas as etapas: a coleção canônica de itens
LR(0), os conjuntos FIRST/FOLLOW e a tabela ACTION/GOTO. Se uma lista de tokens
for informada, analisa-a e mostra o resultado e a tabela de símbolos.
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

from syntactic_analyzer import SyntacticAnalyzer
from lr_parser import parse
from symbol_table import parse_token_list, tokens_to_terminals


def load_reserved(path):
    """Lê as palavras reservadas de um arquivo (uma por linha); arquivo opcional."""
    if not path:
        return []
    with open(path, "r", encoding="utf-8") as handle:
        return [line.strip() for line in handle if line.strip()]


def build_analyzer(grammar_path, reserved_path=None):
    """Cria o analisador e constrói a tabela SLR a partir dos arquivos informados."""
    with open(grammar_path, "r", encoding="utf-8") as handle:
        grammar_text = handle.read()
    analyzer = SyntacticAnalyzer(grammar_text, load_reserved(reserved_path))
    analyzer.build()
    return analyzer


def analyze_tokens(analyzer, token_text):
    """Analisa uma lista de tokens e devolve o relatório textual do resultado."""
    tokens = parse_token_list(token_text)
    terminals, resolved = tokens_to_terminals(tokens, analyzer.symbol_table, set(analyzer.grammar.terminals))
    result = parse(analyzer.table, terminals)

    lines = ["Tokens reconhecidos: " + " ".join(terminals)]
    if result.accepted:
        lines.append("Resultado: ENTRADA ACEITA")
        lines.append("Reducoes aplicadas:")
        for production in result.reductions:
            lines.append(f"  {production.text()}")
    else:
        symbol = result.error_symbol
        lines.append(f"Resultado: ERRO sintatico na posicao {result.error_position} (simbolo '{symbol}')")
    return "\n".join(lines)


def describe_all(analyzer):
    """Monta a visualização completa da construção do analisador SLR."""
    blocks = [
        "Colecao canonica de itens LR(0):\n\n" + analyzer.describe_items(),
        analyzer.describe_first_follow(),
        analyzer.describe_table(),
    ]
    return "\n\n".join(blocks)


def build_parser():
    """Monta o parser de argumentos da linha de comando."""
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="Constrói o analisador sintático SLR a partir de uma gramática, "
                    "exibindo todas as etapas (itens LR(0), FIRST/FOLLOW e tabela "
                    "ACTION/GOTO). Opcionalmente analisa uma lista de tokens.",
    )
    parser.add_argument(
        "gramatica",
        help="arquivo com a gramática livre de contexto",
    )
    parser.add_argument(
        "tokens",
        nargs="?",
        help="arquivo com a lista de tokens a analisar, no formato <lexema, padrão> (opcional)",
    )
    parser.add_argument(
        "-r", "--reservadas",
        metavar="ARQUIVO",
        help="arquivo com palavras reservadas, uma por linha (opcional)",
    )
    parser.add_argument(
        "-o", "--output",
        metavar="ARQUIVO",
        help="grava o relatório da análise neste arquivo em vez de imprimir na tela "
             "(requer uma lista de tokens)",
    )
    return parser


def main(argv=None):
    """Constrói a tabela SLR, exibe as etapas e analisa os tokens se informados."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.output and not args.tokens:
        parser.error("--output só faz sentido junto com uma lista de tokens a analisar.")

    try:
        analyzer = build_analyzer(args.gramatica, args.reservadas)
    except (OSError, ValueError) as error:
        parser.error(str(error))

    # Análise dos tokens (se houver) primeiro: popula a tabela de símbolos com
    # os identificadores encontrados, para que ela apareça completa adiante.
    report = None
    if args.tokens:
        try:
            with open(args.tokens, "r", encoding="utf-8") as handle:
                token_text = handle.read()
        except OSError as error:
            parser.error(str(error))
        try:
            report = analyze_tokens(analyzer, token_text)
        except ValueError as error:
            parser.error(str(error))

    # Construção do analisador (itens LR(0), FIRST/FOLLOW e tabela SLR) sempre na tela.
    print(describe_all(analyzer))
    status = "SLR(1)" if analyzer.table.is_slr() else "NAO e SLR(1) (ha conflitos)"
    print(f"\nGramatica {status} - {len(analyzer.table.states)} estados.")

    if report is None:
        if analyzer.symbol_table.entries:
            print("\nTabela de simbolos:\n" + analyzer.symbol_table.to_table())
        return 0

    result_block = report
    if analyzer.symbol_table.entries:
        result_block += "\n\nTabela de simbolos:\n" + analyzer.symbol_table.to_table()

    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(result_block + "\n")
        print(f"\nRelatorio da analise salvo em: {args.output}")
    else:
        print("\n=== Analise da lista de tokens ===")
        print(result_block)
    return 0


if __name__ == "__main__":
    sys.exit(main())
