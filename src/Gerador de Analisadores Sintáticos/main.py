"""Interface de linha de comando do Gerador de Analisador Sintático SLR.

Sem argumentos, abre um menu interativo que permite projetar o analisador
(carregar a gramática e as palavras reservadas, visualizar itens, FIRST/FOLLOW e
a tabela SLR) e executá-lo sobre uma lista de tokens. Com argumentos, roda
diretamente em lote.
"""

import sys

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


def run_batch(grammar_path, tokens_path, reserved_path=None):
    """Executa o fluxo completo: monta a tabela e analisa a lista de tokens."""
    analyzer = build_analyzer(grammar_path, reserved_path)
    with open(tokens_path, "r", encoding="utf-8") as handle:
        token_text = handle.read()
    print(analyze_tokens(analyzer, token_text))


def _ask(prompt):
    """Lê uma linha do usuário, devolvendo string vazia ao encontrar fim de entrada."""
    try:
        return input(prompt)
    except EOFError:
        return ""


def interactive():
    """Executa o menu interativo de projeto e execução do analisador sintático."""
    analyzer = None
    while True:
        print("\n=== Gerador de Analisador Sintatico SLR ===")
        print("1. Carregar gramatica (e palavras reservadas) de arquivo")
        print("2. Visualizar colecao canonica de itens LR(0)")
        print("3. Visualizar FIRST e FOLLOW")
        print("4. Visualizar a tabela de analise SLR")
        print("5. Visualizar a tabela de simbolos")
        print("6. Analisar uma lista de tokens de arquivo")
        print("0. Sair")
        option = _ask("Opcao: ").strip()

        if option == "0":
            break
        elif option == "1":
            grammar_path = _ask("Caminho da gramatica: ").strip()
            reserved_path = _ask("Caminho das palavras reservadas (vazio se nao houver): ").strip()
            try:
                analyzer = build_analyzer(grammar_path, reserved_path or None)
                status = "SLR(1)" if analyzer.table.is_slr() else "NAO e SLR(1) (ha conflitos)"
                print(f"Tabela construida com {len(analyzer.table.states)} estados. Gramatica {status}.")
            except (OSError, ValueError) as error:
                print(f"Erro: {error}")
        elif option in {"2", "3", "4", "5", "6"} and analyzer is None:
            print("Carregue a gramatica primeiro (opcao 1).")
        elif option == "2":
            print(analyzer.describe_items())
        elif option == "3":
            print(analyzer.describe_first_follow())
        elif option == "4":
            print(analyzer.describe_table())
        elif option == "5":
            print(analyzer.symbol_table.to_table())
        elif option == "6":
            path = _ask("Caminho da lista de tokens: ").strip()
            try:
                with open(path, "r", encoding="utf-8") as handle:
                    print(analyze_tokens(analyzer, handle.read()))
            except (OSError, ValueError) as error:
                print(f"Erro: {error}")
        else:
            print("Opcao invalida.")


def main(argv):
    """Decide entre o modo em lote e o menu interativo conforme os argumentos."""
    if len(argv) == 1:
        interactive()
    elif len(argv) in (3, 4):
        run_batch(argv[1], argv[2], argv[3] if len(argv) == 4 else None)
    else:
        print("Uso:")
        print("  python3 main.py                                    (menu interativo)")
        print("  python3 main.py <gramatica> <tokens> [reservadas]  (modo em lote)")


if __name__ == "__main__":
    main(sys.argv)
