"""Interface de linha de comando do Gerador de Analisador Léxico.

Oferece duas formas de uso. Sem argumentos, abre um menu interativo que permite
projetar o analisador (carregar definições, visualizar os autômatos e a tabela)
e executá-lo sobre um texto fonte. Com argumentos, roda diretamente em lote.
"""

import sys

from regular_definitions import load_definitions, parse_definitions
from lexical_analyzer import LexicalAnalyzer
from tokenizer import tokenize, format_tokens


def build_analyzer(definitions):
    """Cria o analisador léxico e constrói a tabela de análise a partir das definições."""
    analyzer = LexicalAnalyzer(definitions)
    analyzer.build()
    return analyzer


def run_batch(definitions_path, source_path, output_path=None):
    """Executa o fluxo completo: gera a tabela e analisa o arquivo fonte."""
    definitions = load_definitions(definitions_path)
    analyzer = build_analyzer(definitions)
    with open(source_path, "r", encoding="utf-8") as handle:
        source = handle.read()
    result = format_tokens(tokenize(analyzer.table, source))
    if output_path:
        with open(output_path, "w", encoding="utf-8") as handle:
            handle.write(result + "\n")
        print(f"Lista de tokens salva em: {output_path}")
    else:
        print(result)


def _ask(prompt):
    """Lê uma linha do usuário, devolvendo string vazia ao encontrar fim de entrada."""
    try:
        return input(prompt)
    except EOFError:
        return ""


def _print_each(items, title_builder):
    """Imprime a tabela de cada autômato de uma lista de pares (nome, autômato)."""
    for name, automaton in items:
        print(automaton.to_table(title_builder(name)))
        print()


def interactive():
    """Executa o menu interativo de projeto e execução do analisador léxico."""
    analyzer = None
    while True:
        print("\n=== Gerador de Analisador Lexico ===")
        print("1. Carregar definicoes regulares de um arquivo")
        print("2. Visualizar AFDs de cada ER (algoritmo de Aho)")
        print("3. Visualizar AFDs minimizados")
        print("4. Visualizar AFND da uniao (epsilon-transicoes)")
        print("5. Visualizar a tabela de analise lexica")
        print("6. Salvar a tabela de analise lexica em arquivo")
        print("7. Analisar um arquivo de texto fonte")
        print("8. Analisar um texto fonte digitado")
        print("0. Sair")
        option = _ask("Opcao: ").strip()

        if option == "0":
            break
        elif option == "1":
            path = _ask("Caminho do arquivo de definicoes: ").strip()
            try:
                definitions = load_definitions(path)
                analyzer = build_analyzer(definitions)
                print(f"Analisador gerado com {len(definitions)} definicao(oes).")
            except (OSError, ValueError) as error:
                print(f"Erro: {error}")
        elif option in {"2", "3", "4", "5", "6", "7", "8"} and analyzer is None:
            print("Carregue as definicoes regulares primeiro (opcao 1).")
        elif option == "2":
            _print_each(analyzer.dfas, lambda name: f"AFD da ER '{name}' (Aho):")
        elif option == "3":
            _print_each(analyzer.minimized, lambda name: f"AFD minimizado da ER '{name}':")
        elif option == "4":
            print(analyzer.combined.to_table("AFND da uniao (com epsilon-transicoes):"))
            print()
        elif option == "5":
            print(analyzer.table.to_table("Tabela de analise lexica (AFD final):"))
            print()
        elif option == "6":
            path = _ask("Caminho do arquivo de saida: ").strip()
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(analyzer.table.to_table("Tabela de analise lexica (AFD final):") + "\n")
            print(f"Tabela salva em: {path}")
        elif option == "7":
            path = _ask("Caminho do arquivo fonte: ").strip()
            out = _ask("Caminho do arquivo de saida (vazio para tela): ").strip()
            try:
                with open(path, "r", encoding="utf-8") as handle:
                    source = handle.read()
                result = format_tokens(tokenize(analyzer.table, source))
                if out:
                    with open(out, "w", encoding="utf-8") as handle:
                        handle.write(result + "\n")
                    print(f"Lista de tokens salva em: {out}")
                else:
                    print(result)
            except OSError as error:
                print(f"Erro: {error}")
        elif option == "8":
            print("Digite o texto fonte e finalize com uma linha vazia:")
            lines = []
            while True:
                line = _ask("")
                if line == "":
                    break
                lines.append(line)
            print(format_tokens(tokenize(analyzer.table, "\n".join(lines))))
        else:
            print("Opcao invalida.")


def main(argv):
    """Decide entre o modo em lote e o menu interativo conforme os argumentos."""
    if len(argv) == 1:
        interactive()
    elif len(argv) in (3, 4):
        run_batch(*argv[1:])
    else:
        print("Uso:")
        print("  python3 main.py                              (menu interativo)")
        print("  python3 main.py <definicoes> <fonte> [saida] (modo em lote)")


if __name__ == "__main__":
    main(sys.argv)
