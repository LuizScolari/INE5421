"""Controller de integração: Analisador Léxico (Trabalho 1) -> Sintático (Trabalho 2).

Interface interativa simples. O usuário escolhe um conjunto de exemplo já pronto
no repositório (pasta `exemplos/`) e o controller executa o pipeline completo,
mostrando TODAS as etapas:

  - Trabalho 1 (léxico): definições regulares -> AFDs -> minimização -> união ->
    tabela de análise léxica -> lista de tokens do programa fonte.
  - Integração: os tokens `<lexema, padrão>` viram terminais via tabela de símbolos.
  - Trabalho 2 (sintático): itens LR(0) -> FIRST/FOLLOW -> tabela SLR -> análise
    da entrada (aceita/erro e reduções) -> tabela de símbolos final.

Cada conjunto de exemplo é uma pasta em `exemplos/` com quatro arquivos de entrada
mutuamente consistentes: `definicoes.txt`, `gramatica.txt`, `reservadas.txt`
(opcional) e `fonte.txt` (e um `descricao.txt` opcional, mostrado no menu). Manter
os dados no repositório garante que léxico e sintático "conversem" (os tokens
gerados são exatamente os terminais que a gramática reconhece) e torna a demo
reprodutível.

Execução (de qualquer diretório):  python3 src/integracao/controller.py
"""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
LEXICO = os.path.join(SRC, "Gerador de Analisadores Léxicos")
SINTATICO = os.path.join(SRC, "Gerador de Analisadores Sintáticos")
# Cada gerador tem os algoritmos do enunciado em `algoritmos/` e os módulos de
# apoio/interface na própria pasta; ambos entram no path.
for pasta in (LEXICO, SINTATICO):
    sys.path.insert(0, os.path.join(pasta, "algoritmos"))
    sys.path.insert(0, pasta)

# Trabalho 1 (léxico)
from regular_definitions import load_definitions
from lexical_analyzer import LexicalAnalyzer
from tokenizer import tokenize, format_tokens

# Trabalho 2 (sintático) e integração
from syntactic_analyzer import SyntacticAnalyzer
from symbol_table import parse_token_list, tokens_to_terminals
from lr_parser import parse

EXEMPLOS_DIR = os.path.join(BASE, "exemplos")


# --------------------------------------------------------------------------- #
# Entrada/saída do terminal
# --------------------------------------------------------------------------- #
def perguntar(prompt):
    """Lê uma linha do usuário; devolve None ao encontrar fim de entrada (Ctrl-D)."""
    try:
        return input(prompt)
    except EOFError:
        return None


def pausa():
    """Pausa entre etapas para acompanhar a saída (Enter para continuar)."""
    perguntar("\n[Enter para a proxima etapa] ")


def etapa(titulo, conteudo):
    """Imprime uma etapa com um cabeçalho destacado."""
    print("\n" + "=" * 72)
    print(titulo)
    print("=" * 72)
    print(conteudo)


# --------------------------------------------------------------------------- #
# Leitura dos exemplos do repositório
# --------------------------------------------------------------------------- #
def listar_exemplos():
    """Lista as pastas de exemplo disponíveis em `exemplos/`."""
    if not os.path.isdir(EXEMPLOS_DIR):
        return []
    return sorted(
        nome for nome in os.listdir(EXEMPLOS_DIR)
        if os.path.isdir(os.path.join(EXEMPLOS_DIR, nome))
    )


def _ler(caminho):
    with open(caminho, "r", encoding="utf-8") as handle:
        return handle.read()


def descricao_de(nome):
    """Devolve a descrição (primeira linha de descricao.txt) ou o próprio nome."""
    caminho = os.path.join(EXEMPLOS_DIR, nome, "descricao.txt")
    if os.path.exists(caminho):
        texto = _ler(caminho).strip()
        if texto:
            return texto.splitlines()[0]
    return nome


def carregar_exemplo(nome):
    """Lê os arquivos de um exemplo; `reservadas.txt` é opcional."""
    pasta = os.path.join(EXEMPLOS_DIR, nome)
    definicoes = load_definitions(os.path.join(pasta, "definicoes.txt"))
    gramatica = _ler(os.path.join(pasta, "gramatica.txt"))
    fonte = _ler(os.path.join(pasta, "fonte.txt"))
    reservadas_path = os.path.join(pasta, "reservadas.txt")
    if os.path.exists(reservadas_path):
        reservadas = [linha.strip() for linha in _ler(reservadas_path).splitlines() if linha.strip()]
    else:
        reservadas = []
    return definicoes, gramatica, reservadas, fonte


# --------------------------------------------------------------------------- #
# Pipeline completo, etapa por etapa
# --------------------------------------------------------------------------- #
def executar(definicoes, gramatica, reservadas, fonte):
    """Roda o pipeline léxico -> sintático exibindo todas as etapas."""
    # ----- Trabalho 1: análise léxica -----
    lexico = LexicalAnalyzer(definicoes)
    lexico.build()

    etapa("[1] LEXICO - Definicoes regulares (entrada)",
          "\n".join(f"{nome}: {expressao}" for nome, expressao in definicoes))
    pausa()

    etapa("[2] LEXICO - Etapas da construcao (AFDs, minimizados, uniao, tabela final)",
          lexico.describe())
    pausa()

    etapa("[3] LEXICO - Programa fonte (entrada)", fonte.strip())
    saida_lexico = format_tokens(tokenize(lexico.table, fonte))
    etapa("[4] LEXICO - Lista de tokens <lexema, padrao> (saida do Trabalho 1)",
          saida_lexico)
    pausa()

    # ----- Trabalho 2: análise sintática -----
    sintatico = SyntacticAnalyzer(gramatica, reservadas)
    sintatico.build()

    etapa("[5] SINTATICO - Gramatica (entrada)", gramatica.strip())
    pausa()

    etapa("[6] SINTATICO - Colecao canonica de itens LR(0)",
          sintatico.describe_items())
    pausa()

    etapa("[7] SINTATICO - Conjuntos FIRST e FOLLOW",
          sintatico.describe_first_follow())
    pausa()

    etapa("[8] SINTATICO - Tabela de analise SLR (ACTION/GOTO)",
          sintatico.describe_table())
    pausa()

    # ----- Integração: tokens do léxico -> terminais do sintático -----
    tokens = parse_token_list(saida_lexico)
    terminais, resolvidos = tokens_to_terminals(
        tokens, sintatico.symbol_table, set(sintatico.grammar.terminals))
    linhas = []
    for (lexema, padrao), (disp_lexema, disp_cat), terminal in zip(tokens, resolvidos, terminais):
        linhas.append(f"  <{lexema}, {padrao}>".ljust(22)
                      + f"->  <{disp_lexema}, {disp_cat}>".ljust(20)
                      + f"->  terminal '{terminal}'")
    etapa("[9] INTEGRACAO - Resolucao pela tabela de simbolos (token -> terminal)",
          "\n".join(linhas))
    pausa()

    # ----- Resultado da análise sintática -----
    resultado = parse(sintatico.table, terminais)
    linhas = ["Cadeia de terminais: " + " ".join(terminais), ""]
    if resultado.accepted:
        linhas.append("Resultado: ENTRADA ACEITA pela gramatica.")
        linhas.append("\nReducoes aplicadas (na ordem):")
        for producao in resultado.reductions:
            linhas.append(f"  {producao.text()}")
        linhas.append("\nArvore de derivacao:")
        linhas.append("  " + resultado.tree.render().replace("\n", "\n  "))
    else:
        linhas.append(f"Resultado: ERRO sintatico na posicao {resultado.error_position} "
                      f"(simbolo '{resultado.error_symbol}').")
    etapa("[10] SINTATICO - Resultado da analise da entrada", "\n".join(linhas))

    etapa("[11] INTEGRACAO - Tabela de simbolos final",
          sintatico.symbol_table.to_table())


# --------------------------------------------------------------------------- #
# Menu interativo
# --------------------------------------------------------------------------- #
def main():
    """Menu: escolhe um exemplo do repositório e roda o pipeline completo."""
    while True:
        exemplos = listar_exemplos()
        print("\n" + "#" * 72)
        print("  INTEGRACAO: Analisador Lexico (T1) -> Analisador Sintatico (T2)")
        print("#" * 72)

        if not exemplos:
            print(f"Nenhum exemplo encontrado em: {EXEMPLOS_DIR}")
            print("Crie uma pasta em 'exemplos/' com definicoes.txt, gramatica.txt, "
                  "reservadas.txt (opcional) e fonte.txt.")
            return 1

        print("Exemplos disponiveis:")
        for indice, nome in enumerate(exemplos, start=1):
            print(f"  {indice}. {nome}  -  {descricao_de(nome)}")
        print("  0. Sair")

        escolha = perguntar("Escolha um exemplo: ")
        if escolha is None or escolha.strip() == "0":
            break
        escolha = escolha.strip()
        if not escolha.isdigit() or not (1 <= int(escolha) <= len(exemplos)):
            print("Opcao invalida.")
            continue

        nome = exemplos[int(escolha) - 1]
        try:
            dados = carregar_exemplo(nome)
        except (OSError, ValueError) as erro:
            print(f"Erro ao carregar o exemplo '{nome}': {erro}")
            continue
        executar(*dados)

    print("Encerrado.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
