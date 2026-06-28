"""Interface gráfica de integração: Analisador Léxico (T1) -> Sintático (T2).

Aplicação PyQt6 (mesma biblioteca usada no projeto de referência GALS) que roda o
pipeline completo e mostra todas as etapas em abas:

  - Entrada: definições regulares, gramática, palavras reservadas e programa fonte
    (preenchidos a partir dos exemplos da pasta `exemplos/` ou editados à mão).
  - Léxico (T1): etapas da construção (AFDs, minimização, união, tabela final) e a
    lista de tokens `<lexema, padrão>`.
  - Integração: resolução de cada token em um terminal via tabela de símbolos.
  - Sintático (T2): itens LR(0), FIRST/FOLLOW, tabela SLR (ACTION/GOTO) e o
    resultado da análise com a árvore de derivação.
  - Tabela de símbolos final.

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
from regular_definitions import parse_definitions
from lexical_analyzer import LexicalAnalyzer
from tokenizer import tokenize, format_tokens

# Trabalho 2 (sintático) e integração
from syntactic_analyzer import SyntacticAnalyzer
from symbol_table import parse_token_list, tokens_to_terminals
from lr_parser import parse
from grammar import ENDMARK

try:
    from PyQt6 import QtWidgets, QtGui
    from PyQt6.QtCore import Qt
except ModuleNotFoundError:
    sys.stderr.write(
        "Esta interface de integracao usa PyQt6, que nao esta instalado.\n"
        "Instale com:  pip install PyQt6\n"
        "(ou: pip install -r src/integracao/requirements.txt)\n"
    )
    sys.exit(1)

EXEMPLOS_DIR = os.path.join(BASE, "exemplos")


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


def descricao_de(nome):
    """Devolve a descrição (primeira linha de descricao.txt) ou o próprio nome."""
    caminho = os.path.join(EXEMPLOS_DIR, nome, "descricao.txt")
    if os.path.exists(caminho):
        with open(caminho, "r", encoding="utf-8") as handle:
            texto = handle.read().strip()
        if texto:
            return texto.splitlines()[0]
    return nome


def carregar_exemplo_textos(nome):
    """Lê os textos crus de um exemplo (reservadas.txt é opcional)."""
    pasta = os.path.join(EXEMPLOS_DIR, nome)

    def ler(arquivo, opcional=False):
        caminho = os.path.join(pasta, arquivo)
        if opcional and not os.path.exists(caminho):
            return ""
        with open(caminho, "r", encoding="utf-8") as handle:
            return handle.read()

    return (ler("definicoes.txt"), ler("gramatica.txt"),
            ler("reservadas.txt", opcional=True), ler("fonte.txt"))


# --------------------------------------------------------------------------- #
# Pipeline completo (lógica; devolve os blocos de resultado para a interface)
# --------------------------------------------------------------------------- #
def executar_pipeline(definicoes, gramatica, reservadas, fonte):
    """Roda léxico -> integração -> sintático e devolve os dados para exibição."""
    lexico = LexicalAnalyzer(definicoes)
    lexico.build()
    saida_lexico = format_tokens(tokenize(lexico.table, fonte))

    sintatico = SyntacticAnalyzer(gramatica, reservadas)
    sintatico.build()

    tokens = parse_token_list(saida_lexico)
    terminais, resolvidos = tokens_to_terminals(
        tokens, sintatico.symbol_table, set(sintatico.grammar.terminals))
    resultado = parse(sintatico.table, terminais)

    integracao = [
        (f"<{lexema}, {padrao}>", f"<{disp_lexema}, {disp_cat}>", terminal)
        for (lexema, padrao), (disp_lexema, disp_cat), terminal
        in zip(tokens, resolvidos, terminais)
    ]

    linhas = ["Cadeia de terminais: " + " ".join(terminais), ""]
    if resultado.accepted:
        linhas.append("Resultado: ENTRADA ACEITA pela gramatica.")
        linhas += ["", "Reducoes aplicadas (na ordem):"]
        linhas += [f"  {producao.text()}" for producao in resultado.reductions]
        linhas += ["", "Arvore de derivacao:", resultado.tree.render()]
    else:
        linhas.append(f"Resultado: ERRO sintatico na posicao {resultado.error_position} "
                      f"(simbolo '{resultado.error_symbol}').")

    return {
        "lexico_etapas": lexico.describe(),
        "tokens": saida_lexico,
        "integracao": integracao,
        "itens": sintatico.describe_items(),
        "first_follow": sintatico.describe_first_follow(),
        "tabela": sintatico.table,
        "resultado": "\n".join(linhas),
        "simbolos": sintatico.symbol_table.to_table(),
    }


# --------------------------------------------------------------------------- #
# Helpers de interface
# --------------------------------------------------------------------------- #
STYLE = """
QMainWindow, QWidget { background: #f4f6f8; color: #1f2933; }
QLabel#titulo { font-size: 16px; font-weight: bold; color: #1f2933; }
QGroupBox { font-weight: 600; border: 1px solid #cbd2d9; border-radius: 8px;
            margin-top: 14px; background: #ffffff; }
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; color: #334e68; }
QPushButton { background: #ffffff; border: 1px solid #9aa5b1; border-radius: 6px;
              padding: 6px 14px; }
QPushButton:hover { background: #e6f0fb; }
QPushButton#primario { background: #2563eb; color: white; border: none; font-weight: 600; }
QPushButton#primario:hover { background: #1d4ed8; }
QTabWidget::pane { border: 1px solid #cbd2d9; border-radius: 6px; background: white; }
QTabBar::tab { background: #e4e7eb; padding: 8px 16px; margin-right: 2px;
               border-top-left-radius: 6px; border-top-right-radius: 6px; }
QTabBar::tab:selected { background: #2563eb; color: white; }
QPlainTextEdit, QListWidget, QTableView { border: 1px solid #cbd2d9; border-radius: 6px;
               background: white; alternate-background-color: #eef2f7; color: #1f2933; }
QHeaderView::section { background: #334e68; color: white; padding: 4px; border: none; }
QComboBox { background: white; border: 1px solid #9aa5b1; border-radius: 6px; padding: 4px 8px; }
"""


def _mono_font():
    """Fonte monoespaçada para as áreas de código/tabela (preserva alinhamento)."""
    font = QtGui.QFont("Menlo")
    font.setStyleHint(QtGui.QFont.StyleHint.Monospace)
    font.setPointSize(11)
    return font


def _code_view(wrap=False):
    """Área de texto somente leitura, monoespaçada."""
    view = QtWidgets.QPlainTextEdit()
    view.setReadOnly(True)
    view.setFont(_mono_font())
    if not wrap:
        view.setLineWrapMode(QtWidgets.QPlainTextEdit.LineWrapMode.NoWrap)
    return view


def _editor(placeholder=""):
    """Editor de texto monoespaçado para os campos de entrada."""
    editor = QtWidgets.QPlainTextEdit()
    editor.setFont(_mono_font())
    editor.setPlaceholderText(placeholder)
    return editor


def _grupo(titulo, widget):
    """Envolve um widget numa caixa com título."""
    box = QtWidgets.QGroupBox(titulo)
    layout = QtWidgets.QVBoxLayout(box)
    layout.addWidget(widget)
    return box


def _tabela():
    """QTableView somente leitura, no estilo das tabelas do projeto de referência."""
    view = QtWidgets.QTableView()
    view.setFont(_mono_font())
    view.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
    view.setAlternatingRowColors(True)
    return view


def _model(headers, rows):
    """Monta um QStandardItemModel a partir de cabeçalhos e linhas (não editável)."""
    model = QtGui.QStandardItemModel()
    model.setHorizontalHeaderLabels(headers)
    for row in rows:
        items = [QtGui.QStandardItem(str(cell)) for cell in row]
        for item in items:
            item.setEditable(False)
        model.appendRow(items)
    return model


def _fmt_action(move):
    """Formata uma ação da tabela SLR: shift->sj, reduce->rj, accept->acc."""
    if move is None:
        return ""
    if move[0] == "shift":
        return f"s{move[1]}"
    if move[0] == "reduce":
        return f"r{move[1]}"
    return "acc"


def _slr_rows(table):
    """Gera (cabeçalhos, linhas) da tabela SLR (ACTION | GOTO) para o QTableView."""
    grammar = table.grammar
    terminals = list(grammar.terminals) + [ENDMARK]
    nonterminals = [nt for nt in grammar.nonterminals if nt != grammar.start]
    headers = ["Estado"] + terminals + nonterminals
    rows = []
    for state in range(len(table.states)):
        row = [str(state)]
        row += [_fmt_action(table.action.get((state, t))) for t in terminals]
        row += [str(table.goto.get((state, nt), "")) for nt in nonterminals]
        rows.append(row)
    return headers, rows


# --------------------------------------------------------------------------- #
# Janela principal
# --------------------------------------------------------------------------- #
class IntegracaoWindow(QtWidgets.QMainWindow):
    """Janela com a barra de exemplos e as abas do pipeline."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("INE5421 - Integracao: Analisador Lexico (T1) -> Sintatico (T2)")
        self.resize(1180, 800)
        self._build_ui()
        self._popular_exemplos()
        self.setStyleSheet(STYLE)

    # ----- construção da interface ------------------------------------------ #
    def _build_ui(self):
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        outer = QtWidgets.QVBoxLayout(central)

        barra = QtWidgets.QHBoxLayout()
        titulo = QtWidgets.QLabel("Pipeline Lexico -> Sintatico")
        titulo.setObjectName("titulo")
        barra.addWidget(titulo)
        barra.addStretch(1)
        barra.addWidget(QtWidgets.QLabel("Exemplo:"))
        self.combo = QtWidgets.QComboBox()
        self.combo.setMinimumWidth(340)
        barra.addWidget(self.combo)
        self.btn_carregar = QtWidgets.QPushButton("Carregar")
        self.btn_executar = QtWidgets.QPushButton("Executar pipeline")
        self.btn_executar.setObjectName("primario")
        barra.addWidget(self.btn_carregar)
        barra.addWidget(self.btn_executar)
        outer.addLayout(barra)

        self.tabs = QtWidgets.QTabWidget()
        outer.addWidget(self.tabs, 1)
        self._tab_entrada()
        self._tab_lexico()
        self._tab_integracao()
        self._tab_sintatico()
        self._tab_simbolos()

        self.statusBar().showMessage(
            "Pronto. Selecione um exemplo e clique em Carregar, depois em Executar pipeline.")

        self.btn_carregar.clicked.connect(self._on_carregar)
        self.btn_executar.clicked.connect(self._on_executar)

    def _tab_entrada(self):
        widget = QtWidgets.QWidget()
        grid = QtWidgets.QGridLayout(widget)
        self.ed_def = _editor("id: [a-zA-Z]([a-zA-Z] | [0-9])*\nnum: [0-9]+")
        self.ed_gram = _editor("S ::= ...")
        self.ed_res = _editor("while\ndo")
        self.ed_fonte = _editor("while a < b do c = 1")
        grid.addWidget(_grupo("Definicoes regulares (lexico)", self.ed_def), 0, 0)
        grid.addWidget(_grupo("Gramatica (sintatico)", self.ed_gram), 0, 1)
        grid.addWidget(_grupo("Palavras reservadas (uma por linha)", self.ed_res), 1, 0)
        grid.addWidget(_grupo("Programa fonte", self.ed_fonte), 1, 1)
        self.tabs.addTab(widget, "1. Entrada")

    def _tab_lexico(self):
        split = QtWidgets.QSplitter(Qt.Orientation.Vertical)
        self.txt_lex_etapas = _code_view()
        self.lst_tokens = QtWidgets.QListWidget()
        self.lst_tokens.setFont(_mono_font())
        split.addWidget(_grupo("Etapas da construcao (AFDs, minimizacao, uniao, tabela final)",
                               self.txt_lex_etapas))
        split.addWidget(_grupo("Lista de tokens <lexema, padrao> (saida do T1)", self.lst_tokens))
        split.setSizes([520, 240])
        self.tabs.addTab(split, "2. Lexico (T1)")

    def _tab_integracao(self):
        self.tbl_integracao = _tabela()
        self.tabs.addTab(
            _grupo("Resolucao pela tabela de simbolos: token -> terminal", self.tbl_integracao),
            "3. Integracao")

    def _tab_sintatico(self):
        sub = QtWidgets.QTabWidget()
        self.txt_itens = _code_view()
        self.txt_ff = _code_view()
        self.tbl_slr = _tabela()
        self.txt_resultado = _code_view()
        sub.addTab(self.txt_itens, "Itens LR(0)")
        sub.addTab(self.txt_ff, "FIRST / FOLLOW")
        sub.addTab(self.tbl_slr, "Tabela SLR (ACTION/GOTO)")
        sub.addTab(self.txt_resultado, "Resultado & Arvore de derivacao")
        self.tabs.addTab(sub, "4. Sintatico (T2)")

    def _tab_simbolos(self):
        self.txt_simbolos = _code_view()
        self.tabs.addTab(_grupo("Tabela de simbolos final", self.txt_simbolos),
                         "5. Tabela de simbolos")

    # ----- ações ------------------------------------------------------------ #
    def _popular_exemplos(self):
        self.combo.clear()
        exemplos = listar_exemplos()
        for nome in exemplos:
            self.combo.addItem(f"{nome}  -  {descricao_de(nome)}", nome)
        if not exemplos:
            self.combo.addItem("(nenhum exemplo encontrado em exemplos/)", None)
            self.btn_carregar.setEnabled(False)

    def _on_carregar(self):
        nome = self.combo.currentData()
        if not nome:
            return
        try:
            definicoes, gramatica, reservadas, fonte = carregar_exemplo_textos(nome)
        except OSError as erro:
            self._erro(f"Erro ao carregar o exemplo '{nome}':\n{erro}")
            return
        self.ed_def.setPlainText(definicoes)
        self.ed_gram.setPlainText(gramatica)
        self.ed_res.setPlainText(reservadas)
        self.ed_fonte.setPlainText(fonte)
        self.statusBar().showMessage(f"Exemplo '{nome}' carregado. Clique em Executar pipeline.")

    def _on_executar(self):
        try:
            definicoes = parse_definitions(self.ed_def.toPlainText())
            gramatica = self.ed_gram.toPlainText()
            reservadas = [linha.strip() for linha in self.ed_res.toPlainText().splitlines()
                          if linha.strip()]
            fonte = self.ed_fonte.toPlainText()
            dados = executar_pipeline(definicoes, gramatica, reservadas, fonte)
        except Exception as erro:  # entrada inválida do usuário: reporta sem derrubar a GUI
            self._erro(f"Falha ao executar o pipeline:\n{erro}")
            return
        self._mostrar(dados)
        self.statusBar().showMessage("Pipeline executado com sucesso.")

    def _mostrar(self, dados):
        self.txt_lex_etapas.setPlainText(dados["lexico_etapas"])
        self.lst_tokens.clear()
        self.lst_tokens.addItems(dados["tokens"].splitlines() if dados["tokens"] else [])

        self.tbl_integracao.setModel(_model(
            ["Token <lexema, padrao>", "Resolucao <lexema, categoria>", "Terminal"],
            dados["integracao"]))
        self.tbl_integracao.resizeColumnsToContents()
        self.tbl_integracao.horizontalHeader().setStretchLastSection(True)

        self.txt_itens.setPlainText(dados["itens"])
        self.txt_ff.setPlainText(dados["first_follow"])
        self.tbl_slr.setModel(_model(*_slr_rows(dados["tabela"])))
        self.tbl_slr.resizeColumnsToContents()
        self.txt_resultado.setPlainText(dados["resultado"])
        self.txt_simbolos.setPlainText(dados["simbolos"])

        self.tabs.setCurrentIndex(1)

    def _erro(self, mensagem):
        QtWidgets.QMessageBox.warning(self, "Erro", mensagem)


def main():
    """Inicia a aplicação gráfica."""
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("INE5421 Integracao")
    window = IntegracaoWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
