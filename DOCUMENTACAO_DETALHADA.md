# Documentação detalhada — INE5421 (Trabalho 1 e 2)

Este documento explica **o nosso código**, bloco a bloco, e usa os trechos do
livro do **Aho (Compilers — Principles, Techniques, and Tools, 2ª ed.)** para
**justificar a corretude** de cada decisão. Para cada algoritmo há quatro partes:

1. **O que faz** (entrada → saída da função);
2. **O código** (completo, sem cortes);
3. **Explicação linha a linha** do *nosso* código;
4. **Justificativa (Aho)** — o trecho do livro, com seção e página, que prova que
   aquele bloco está certo.

> **Numeração / páginas.** As referências são da 2ª edição. Os números de página
> (ex.: *p. 179*) são as **páginas impressas** do livro. Localização por seção:
> §3.3.4 p.123 · §3.3.5 p.124 · §3.5.3 p.144 · §3.7.1 (Alg. 3.20) p.152–153 ·
> §3.8 (Fig. 3.50) p.166–169 · §3.8.3 p.170 · §3.9.3 (Fig. 3.58) p.176–177 ·
> §3.9.4 p.177 · §3.9.5 (Alg. 3.36, Fig. 3.62) p.179–180 · §3.9.6 (Alg. 3.39,
> Fig. 3.64) p.180–182 · §3.9.7 p.184 · §4.4.2 p.220–222 · §4.6.2 (Fig. 4.32
> p.245, Fig. 4.33 p.246) p.242–246 · §4.6.3 (Alg. 4.44, Fig. 4.36) p.248–251 ·
> §4.6.4 (Alg. 4.46) p.252–253. O enunciado do T2 chama a tabela SLR de "Alg.
> 4.38"; é a mesma construção, muda só o número entre edições.

## Convenções

- **ε (épsilon)** = `&` (o enunciado exige usar `&` para ε).
- **`$`** = marcador de fim de entrada no sintático (Aho §4.4.2, p. 222: *"$ is a
  special endmarker symbol assumed not to be a symbol of any grammar"*).
- **`#`** = marcador de fim na ER aumentada `(r)#` do método direto (Aho §3.9.1).
- **AFD** e **AFND** usam a mesma classe `Automaton`; a diferença é só ter ou não
  ε-transições / ramificação.

## Mapa enunciado → arquivos

| Enunciado | Algoritmo | Página (2e) | Arquivo |
|---|---|---|---|
| T1 (a) ER → AFD | método direto 3.36 | **179** (Fig. 3.62 → 180) | `Léxico/algoritmos/regex_to_dfa.py` |
| T1 (b) Minimização | 3.39 | **180–181** (Fig. 3.64 → 182) | `Léxico/algoritmos/minimization.py` |
| T1 (c) União via ε | §3.8 / Fig. 3.50 | **166–169** | `Léxico/algoritmos/union.py` |
| T1 (d) Determinização | 3.20 | **153** | `Léxico/algoritmos/determinization.py` |
| T2 (a) FIRST/FOLLOW | §4.4.2 | **220–222** | `Sintático/algoritmos/first_follow.py` |
| T2 (b) CLOSURE | Fig. 4.32 | **245** | `Sintático/algoritmos/lr0_items.py` |
| T2 (c) Coleção canônica | Fig. 4.33 | **246** | `Sintático/algoritmos/lr0_items.py` |
| T2 (d) Parsing LR | 4.44 / Fig. 4.36 | **248–251** | `Sintático/algoritmos/lr_parser.py` |
| T2 (e) Tabela SLR | 4.46 | **252–253** | `Sintático/algoritmos/slr_table.py` |

---

# Parte I — Trabalho 1: Gerador de Analisador Léxico

## Pipeline geral e orquestração (`lexical_analyzer.py`)

```python
class LexicalAnalyzer:
    def __init__(self, definitions):
        self.definitions = definitions
        self.priority = {name: index for index, (name, _) in enumerate(definitions)}
        self.dfas = []
        self.minimized = []
        self.combined = None
        self.table = None

    def build(self):
        for name, expression in self.definitions:
            dfa = regex_to_dfa(expression, token=name)
            self.dfas.append((name, dfa))
            self.minimized.append((name, minimize(dfa)))
        automata = [automaton for _, automaton in self.minimized]
        self.combined = union(automata)
        self.table = determinize(self.combined, self.priority)
        return self.table
```

**Explicação linha a linha:**

- `self.priority = {name: index ...}` — constrói um dicionário `token → posição na
  lista`. Como `enumerate` numera na ordem de declaração, o token declarado
  primeiro tem `index` menor. Esse dicionário é passado adiante para a
  determinização decidir empates (menor índice = maior prioridade).
- `self.dfas` / `self.minimized` guardam os autômatos intermediários **só para
  visualização** (o `describe()` os imprime); o que importa para a tabela final é
  a cadeia `regex_to_dfa → minimize → union → determinize`.
- O laço `for name, expression in self.definitions`: para **cada** definição
  regular, gera o AFD (`regex_to_dfa`, rotulando os finais com `token=name`) e o
  **minimiza imediatamente** (`minimize(dfa)`).
- Depois do laço: `union(automata)` junta todos os AFD mínimos num único AFND
  (ligados por ε); `determinize(..., self.priority)` transforma esse AFND no AFD
  final — **a tabela de análise léxica**.

**Justificativa (Aho).** A ordem **gerar AFD de cada ER → minimizar cada → unir por
ε → determinizar** é a do enunciado e é coerente com §3.8 (p. 166–169): o livro
combina os autômatos de cada padrão num só e depois trabalha com o AFD resultante.
A escolha da prioridade pela ordem de declaração é a **regra 2 de §3.5.3** (p. 144):
*"If the longest possible prefix matches two or more patterns, prefer the pattern
listed first."*

---

## I.0 — `automaton.py` (estrutura de dados)

Toda a parte léxica manipula autômatos por esta classe. Não é "um algoritmo do
livro" — é a representação de um autômato finito (Aho §3.6, "Finite Automata") —
mas entender os campos é pré-requisito para ler os algoritmos.

```python
EPSILON = "&"

class Automaton:
    def __init__(self):
        self.states = set()
        self.alphabet = set()
        self.transitions = {}        # estado -> { símbolo -> conjunto de destinos }
        self.initial = None
        self.accepting = set()
        self.token_of = {}           # estado final -> token reconhecido

    def add_state(self, state, accepting=False, token=None):
        self.states.add(state)
        if state not in self.transitions:
            self.transitions[state] = {}
        if accepting:
            self.accepting.add(state)
            if token is not None:
                self.token_of[state] = token

    def add_transition(self, source, symbol, target):
        self.add_state(source)
        self.add_state(target)
        if symbol != EPSILON:
            self.alphabet.add(symbol)
        self.transitions[source].setdefault(symbol, set()).add(target)

    def move(self, state, symbol):
        return self.transitions.get(state, {}).get(symbol, set())

    def step(self, state, symbol):
        targets = self.move(state, symbol)
        if not targets:
            return None
        return next(iter(targets))
```

**Explicação dos pontos que importam para a corretude:**

- `transitions` é um **dicionário de conjuntos**: `transitions[origem][símbolo]` é
  um `set` de destinos. Isso permite representar AFND (vários destinos no mesmo
  símbolo) e AFD (um destino) com a mesma estrutura — por isso os quatro
  algoritmos compartilham a classe.
- `add_transition`: só adiciona o símbolo ao `alphabet` **se não for ε**
  (`if symbol != EPSILON`). Consequência importante: o alfabeto **nunca** contém
  `&`. Isso garante que a determinização e a minimização iteram só sobre símbolos
  reais. **Aho §3.7.1:** ε não é símbolo de entrada do autômato.
- `move(state, symbol)` devolve o **conjunto** de destinos (usado pelo AFND na
  determinização). `step(state, symbol)` devolve **um** destino ou `None` (usado
  pelo AFD na minimização e na tokenização) — `next(iter(targets))` pega o único
  elemento do conjunto.
- `rename(prefix="q")` (abaixo) reescreve os estados como `q0, q1, …` em **ordem
  BFS** a partir do inicial:

```python
    def rename(self, prefix="q"):
        order = []; seen = set()
        queue = [self.initial] if self.initial is not None else []
        while queue:
            current = queue.pop(0)
            if current in seen: continue
            seen.add(current); order.append(current)
            for symbol in sorted(self.transitions.get(current, {}), key=str):
                for target in sorted(self.transitions[current][symbol], key=str):
                    if target not in seen: queue.append(target)
        ...
        mapping = {state: f"{prefix}{index}" for index, state in enumerate(order)}
```

A BFS percorre símbolos e destinos **ordenados** (`sorted(..., key=str)`), o que
torna a numeração **determinística e reproduzível**. Isso é o que permite comparar
a saída com as figuras do livro (ex.: `q0…q3` de `(a|b)*abb`).

---

## I.1 — `regular_definitions.py` (leitura das definições)

```python
def parse_definitions(text):
    definitions = []
    for number, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        if ":" not in line:
            raise ValueError(f"Linha {number} sem ':' separando nome e expressão: {raw!r}")
        name, expression = line.split(":", 1)
        name = name.strip(); expression = expression.strip()
        if not name:
            raise ValueError(f"Linha {number} sem nome de definição: {raw!r}")
        if not expression:
            raise ValueError(f"Linha {number} sem expressão regular: {raw!r}")
        definitions.append((name, expression))
    if not definitions:
        raise ValueError("Nenhuma definição regular encontrada no arquivo.")
    return definitions
```

**Explicação:** percorre o arquivo linha a linha; ignora linhas em branco; exige o
separador `:`; usa `split(":", 1)` (só o **primeiro** `:`) para que a ER possa
conter `:` (ex.: o token `:=`). Devolve uma **lista** de pares `(nome, ER)` na
ordem do arquivo — e essa ordem é o que vira prioridade no `LexicalAnalyzer`.

**Justificativa (Aho §3.3.4, p. 123):** *"a regular definition is a sequence of
definitions of the form d₁ → r₁, d₂ → r₂, …"* — cada linha `nome: ER` é um `dᵢ →
rᵢ`. **Limitação:** o livro permite `rᵢ` referenciar `dⱼ` (j<i); aqui cada ER é
tratada isolada (sem expandir referências entre nomes). Os exemplos do enunciado
(Anexo I) usam só classes inline `[a-z]`, então são atendidos.

---

## I.2 — `regex_to_dfa.py` — **Algoritmo (a): ER → AFD direto** (Alg. 3.36, p. 179)

**O que faz:** recebe a string da ER e o nome do token; devolve um `Automaton`
**determinístico** cujos estados finais estão rotulados com esse token. Não
constrói AFND intermediário — é o **método direto** da §3.9.

O algoritmo tem 6 etapas (parsing → árvore → funções → AFD). Vou explicar cada
função na ordem em que `regex_to_dfa` as chama.

### Etapa 1 — `to_tokens`: ler a ER e expandir classes `[...]`

```python
def to_tokens(regex):
    tokens = []
    index = 0
    length = len(regex)
    while index < length:
        char = regex[index]
        if char == " ":
            index += 1
        elif char == "[":
            end = regex.find("]", index)
            if end == -1:
                raise ValueError("Grupo '[' sem ']' correspondente.")
            members = _expand_group(regex[index + 1:end])
            if not members:
                raise ValueError("Grupo de caracteres '[]' vazio.")
            tokens.append(("op", "("))
            for position, member in enumerate(members):
                if position > 0:
                    tokens.append(("op", "|"))
                tokens.append(("sym", _literal(member)))
            tokens.append(("op", ")"))
            index = end + 1
        elif char in OPERATORS or char in "()":
            tokens.append(("op", char))
            index += 1
        elif char == EPSILON:
            tokens.append(("eps", char))
            index += 1
        elif char == ENDMARKER:
            raise ValueError("Símbolo '#' é reservado (marcador de fim).")
        else:
            tokens.append(("sym", char))
            index += 1
    return tokens
```

**Explicação linha a linha:**

- Varre a ER caractere a caractere. Cada token produzido é um par **tipado**
  `(kind, value)` com `kind ∈ {"op", "sym", "eps"}`. Tipar evita ambiguidade: um
  `+` que é operador (`("op","+")`) fica distinto de um `+` literal vindo de uma
  classe (`("sym","+")`).
- Espaços são ignorados (`if char == " ": index += 1`).
- **Classe `[...]`:** acha o `]` com `regex.find("]", index)`; extrai o miolo e
  chama `_expand_group`; envolve tudo em parênteses e intercala `|` entre os
  membros — ou seja, `[a-c]` vira a sequência de tokens de `(a|b|c)`. Cada membro
  passa por `_literal` (validação). Se faltar `]` ou a classe for vazia, erro.
- `char in OPERATORS or char in "()"` → token de operador. `OPERATORS = {"*", "+",
  "?", "|", "."}`.
- `char == EPSILON` (`&`) → token `("eps", "&")`. `char == ENDMARKER` (`#`) →
  **erro** (é reservado para a ER aumentada).
- Qualquer outro caractere é um **símbolo do alfabeto** (`("sym", char)`).

`_expand_group` e `_literal`:

```python
def _expand_group(content):
    members = []
    index = 0
    while index < len(content):
        if index + 2 < len(content) and content[index + 1] == "-":
            start, end = content[index], content[index + 2]
            for code in range(ord(start), ord(end) + 1):
                members.append(chr(code))
            index += 3
        else:
            if content[index] != " ":
                members.append(content[index])
            index += 1
    return members

def _literal(char):
    if char in RESERVED:               # RESERVED = {"&", "#"}
        raise ValueError(f"Símbolo '{char}' é reservado e não pode ser literal.")
    return char
```

`_expand_group` detecta faixas `x-y` (quando o caractere seguinte é `-`) e gera
todos os caracteres de `ord(start)` a `ord(end)`; senão, adiciona o caractere
literal. `_literal` impede que `&` ou `#` entrem como símbolos do alfabeto.

**Justificativa (Aho §3.3.5, item 3, p. 124):** *"A regular expression a₁|a₂|…|aₙ
… can be replaced by the shorthand [a₁a₂…aₙ] … or a₁-aₙ."* Ou seja, classe é
**abreviação de união** — exatamente o que `to_tokens` produz ao transformar
`[a-c]` em `(a|b|c)`.

### Etapa 2 — `add_concatenation`: tornar a concatenação explícita

```python
def add_concatenation(tokens):
    closing = {("op", ")"), ("op", "*"), ("op", "+"), ("op", "?")}
    result = []
    for index, token in enumerate(tokens):
        result.append(token)
        if index + 1 >= len(tokens):
            break
        nxt = tokens[index + 1]
        left_closes = token[0] in ("sym", "eps") or token in closing
        right_opens = nxt[0] in ("sym", "eps") or nxt == ("op", "(")
        if left_closes and right_opens:
            result.append(("op", "."))
    return result
```

**Explicação:** na ER a concatenação é **implícita** (`abb` = `a·b·b`). Esta função
insere o operador `.` entre dois tokens adjacentes quando o da esquerda "fecha uma
subexpressão" e o da direita "abre uma". `left_closes` é verdadeiro quando o token
à esquerda é símbolo/ε ou um fechamento (`) * + ?`); `right_opens` quando o da
direita é símbolo/ε ou `(`. Quando ambos, insere `("op", ".")`. Assim
`a b` vira `a . b`, `) (` vira `) . (`, `* a` vira `* . a`, etc.

**Justificativa (Aho §3.9.1):** a árvore da ER é construída *"just as we did for
arithmetic expressions in Section 2.5.1"*. Tornar a concatenação um operador
binário explícito é o passo necessário para parsear como expressão aritmética.

### Etapa 3 — `to_postfix`: notação pós-fixa (shunting-yard)

```python
PRECEDENCE = {"|": 1, ".": 2, "*": 3, "+": 3, "?": 3}

def to_postfix(tokens):
    output = []
    operators = []
    for kind, value in tokens:
        if kind in ("sym", "eps"):
            output.append((kind, value))
        elif value in ("*", "+", "?"):
            output.append(("op", value))
        elif value in ("|", "."):
            while operators and operators[-1] != "(" and PRECEDENCE[operators[-1]] >= PRECEDENCE[value]:
                output.append(("op", operators.pop()))
            operators.append(value)
        elif value == "(":
            operators.append("(")
        elif value == ")":
            while operators and operators[-1] != "(":
                output.append(("op", operators.pop()))
            if not operators:
                raise ValueError("Parêntese ')' sem '(' correspondente.")
            operators.pop()
    while operators:
        top = operators.pop()
        if top == "(":
            raise ValueError("Parêntese '(' sem ')' correspondente.")
        output.append(top)
    return output
```

**Explicação (algoritmo shunting-yard de Dijkstra):**

- Símbolos e ε vão **direto** para a saída `output`.
- Operadores unários pós-fixos (`* + ?`) também vão direto para a saída — porque,
  estando logo após seu operando, já estão na posição pós-fixa correta.
- Operadores binários (`|` e `.`): antes de empilhar, **desempilham** da pilha
  `operators` todos os operadores de precedência **maior ou igual** (associando à
  esquerda) — é a comparação `PRECEDENCE[operators[-1]] >= PRECEDENCE[value]`.
  `PRECEDENCE` codifica `| < . < {*,+,?}`.
- `(` é empilhado; `)` desempilha até achar o `(`. Parênteses desbalanceados geram
  erro.
- No fim, esvazia a pilha. O resultado `output` é a ER em **pós-fixa tipada**.

**Justificativa (Aho §3.9.1, §2.5.1):** é o método-padrão de montar a árvore
sintática de uma expressão respeitando precedência — pré-requisito do Algoritmo
3.36, que parte da árvore de `(r)#`.

### Etapa 4 — `build_tree` e `desugar`: árvore e remoção de açúcar

```python
def build_tree(postfix):
    stack = []
    for kind, value in postfix:
        if kind == "eps":
            stack.append(Node("epsilon"))
        elif kind == "sym":
            stack.append(Node("symbol", symbol=value))
        elif value in ("*", "+", "?"):
            if not stack:
                raise ValueError("Expressão regular mal formada.")
            stack.append(Node(value, left=stack.pop()))
        else:                              # '|' ou '.'
            if len(stack) < 2:
                raise ValueError("Expressão regular mal formada.")
            right = stack.pop(); left = stack.pop()
            stack.append(Node(value, left=left, right=right))
    if len(stack) != 1:
        raise ValueError("Expressão regular mal formada.")
    return stack.pop()
```

**Explicação:** avaliação clássica de pós-fixa com pilha. Folhas (`symbol`/
`epsilon`) são empilhadas; um operador unário desempilha **um** nó e cria um nó
pai; um binário desempilha **dois** (cuidando da ordem: `right` é o topo, `left` é
o de baixo). Ao final tem que sobrar exatamente um nó — a raiz. As checagens de
pilha vazia/insuficiente capturam ERs malformadas.

```python
def desugar(node):
    if node.kind in ("symbol", "epsilon"):
        return node
    if node.kind in ("|", "."):
        node.left = desugar(node.left); node.right = desugar(node.right); return node
    if node.kind == "*":
        node.left = desugar(node.left); return node
    if node.kind == "?":                          # r?  ->  r | ε
        child = desugar(node.left)
        return Node("|", left=child, right=Node("epsilon"))
    if node.kind == "+":                          # r+  ->  r . r*
        child = desugar(node.left)
        return Node(".", left=child, right=Node("*", left=copy_subtree(child)))
    raise ValueError(f"Operador desconhecido na árvore: {node.kind}")
```

**Explicação:** `desugar` percorre a árvore e **elimina `?` e `+`**, reescrevendo
em termos de `| . *`:
- `r?` vira o nó `|` com filhos `r` e `ε` (pois `r? = r|ε`).
- `r+` vira o nó `.` com filhos `r` e `r*`; o segundo `r` é uma **cópia
  independente** (`copy_subtree`, abaixo) para que a numeração de posições trate as
  duas ocorrências como posições distintas.
- Símbolo/ε/`|`/`.`/`*` são mantidos (recursão nos filhos).

```python
def copy_subtree(node):
    clone = Node(node.kind, symbol=node.symbol)
    if node.left is not None:  clone.left = copy_subtree(node.left)
    if node.right is not None: clone.right = copy_subtree(node.right)
    return clone
```

`copy_subtree` faz uma cópia **profunda** (recursiva) — necessária em `r+` para que
`r` e a cópia em `r*` não compartilhem nós (senão receberiam a mesma posição).

**Justificativa (Aho §3.3.5, itens 1 e 2, p. 124):** *"r* = r⁺|ε e r⁺ = rr*"* e
*"r? is equivalent to r|ε"*. As reescritas usam **exatamente** essas identidades
algébricas. Como `?` e `+` são abreviações, depois do `desugar` a árvore só tem os
5 tipos de nó (`symbol, epsilon, |, ., *`) cobertos pela Fig. 3.58 — por isso as
quatro funções da próxima etapa funcionam sem caso especial.

### Etapa 5 — `regex_to_dfa` (montagem) + `assign_positions`

```python
def regex_to_dfa(regex, token=None):
    postfix = to_postfix(add_concatenation(to_tokens(regex)))
    tree = desugar(build_tree(postfix))

    end_leaf = Node("symbol", symbol=ENDMARKER)   # a folha '#'
    root = Node(".", left=tree, right=end_leaf)    # (r)#

    symbol_at = {}
    counter = [0]
    assign_positions(root, counter, symbol_at)
    end_position = end_leaf.position

    followpos = {position: set() for position in symbol_at}
    annotate(root, followpos)
    ...
```

**Explicação (primeira metade):**

- Encadeia as etapas 1–4: `to_tokens → add_concatenation → to_postfix →
  build_tree → desugar`, produzindo a árvore de `r`.
- Cria a folha `#` e a **raiz `.`** com filhos `r` e `#` — isto é a **expressão
  aumentada `(r)#`** exigida pelo Algoritmo 3.36.
- `assign_positions` numera as folhas e preenche `symbol_at` (posição → símbolo).
  `counter = [0]` é uma lista (truque para passar um inteiro **por referência** e
  ser incrementado dentro da recursão). `end_position` guarda a posição de `#`.
- `followpos` é inicializado como um dicionário `posição → conjunto vazio`, e
  `annotate(root, followpos)` o preenche (etapa 5).

```python
def assign_positions(node, counter, symbol_at):
    if node is None or node.kind == "epsilon":
        return
    if node.kind == "symbol":
        counter[0] += 1
        node.position = counter[0]
        symbol_at[counter[0]] = node.symbol
        return
    assign_positions(node.left, counter, symbol_at)
    assign_positions(node.right, counter, symbol_at)
```

**Explicação:** percorre a árvore **em ordem (esquerda → direita)**; cada folha-
**símbolo** recebe o próximo inteiro (`counter[0] += 1`) e registra `symbol_at[pos]
= símbolo`. Folhas ε **não** recebem posição (não correspondem a um símbolo de
entrada). Como a recursão visita `left` antes de `right`, a numeração segue a ordem
textual da ER.

**Justificativa (Aho §3.9.1/§3.9.2, p. 173–175):** *"To each leaf not labeled ε we
attach a unique integer … the position of the leaf"*, sobre a árvore da expressão
**aumentada `(r)#`**. O `#` recebe a última posição e será o marcador de aceitação.

### Etapa 5 (cont.) — `annotate`: nullable, firstpos, lastpos, followpos

```python
def annotate(node, followpos):
    if node.kind == "epsilon":
        node.nullable = True
        node.firstpos = set()
        node.lastpos = set()
    elif node.kind == "symbol":
        node.nullable = False
        node.firstpos = {node.position}
        node.lastpos = {node.position}
    elif node.kind == "|":
        annotate(node.left, followpos); annotate(node.right, followpos)
        node.nullable = node.left.nullable or node.right.nullable
        node.firstpos = node.left.firstpos | node.right.firstpos
        node.lastpos = node.left.lastpos | node.right.lastpos
    elif node.kind == ".":
        annotate(node.left, followpos); annotate(node.right, followpos)
        node.nullable = node.left.nullable and node.right.nullable
        if node.left.nullable:
            node.firstpos = node.left.firstpos | node.right.firstpos
        else:
            node.firstpos = set(node.left.firstpos)
        if node.right.nullable:
            node.lastpos = node.right.lastpos | node.left.lastpos
        else:
            node.lastpos = set(node.right.lastpos)
        for position in node.left.lastpos:
            followpos[position] |= node.right.firstpos      # regra 1
    elif node.kind == "*":
        annotate(node.left, followpos)
        node.nullable = True
        node.firstpos = set(node.left.firstpos)
        node.lastpos = set(node.left.lastpos)
        for position in node.left.lastpos:
            followpos[position] |= node.left.firstpos       # regra 2
```

**Explicação (é uma recursão pós-ordem — filhos antes do pai):**

- **folha ε:** `nullable=True` (deriva a cadeia vazia), `firstpos`/`lastpos`
  vazios (não há posição).
- **folha símbolo:** `nullable=False`, `firstpos = lastpos = {posição}` (a própria
  posição é a primeira e a última).
- **`|` (or):** primeiro anota os dois filhos; `nullable` é **ou** dos filhos;
  `firstpos`/`lastpos` são a **união** dos filhos (qualquer lado pode começar/
  terminar a cadeia).
- **`.` (concatenação):** `nullable` é **e** dos filhos. Para `firstpos`: se o filho
  esquerdo é anulável, junta os dois firstpos (porque a cadeia pode "pular" o
  esquerdo e começar pelo direito); senão só o esquerdo. `lastpos` é simétrico,
  testando o filho **direito**. Por fim, a **regra 1 de followpos**: para cada
  posição `i` em `lastpos(esquerdo)`, acrescenta `firstpos(direito)` a
  `followpos[i]` — porque, na concatenação, o que termina o lado esquerdo é seguido
  pelo que começa o direito.
- **`*` (fecho):** `nullable=True` sempre; `firstpos`/`lastpos` = os do filho. A
  **regra 2 de followpos**: para cada `i` em `lastpos(filho)`, acrescenta
  `firstpos(filho)` a `followpos[i]` — porque o fecho permite repetir, então o fim
  de uma repetição é seguido pelo início da próxima.

Observe que `followpos` é o **mesmo dicionário** passado por toda a recursão, e os
`|=` vão acumulando os pares (i → j). Como a recursão cobre toda a árvore, **todos**
os pares exigidos pelas duas regras são gerados.

**Justificativa (Aho — Figura 3.58, p. 177, e §3.9.4, p. 177).** A Fig. 3.58 dá as
regras de `nullable`/`firstpos`:

| Nó | nullable | firstpos |
|---|---|---|
| folha ε | true | ∅ |
| folha i | false | {i} |
| `c₁\|c₂` | n(c₁) or n(c₂) | first(c₁)∪first(c₂) |
| `c₁·c₂` | n(c₁) and n(c₂) | n(c₁)? first(c₁)∪first(c₂) : first(c₁) |
| `c₁*` | true | first(c₁) |

O código reproduz a tabela linha a linha. Para `lastpos`, o livro diz: *"the rules
for lastpos are the same as for firstpos, with the children interchanged in the
rule for a cat-node"* — e por isso o nosso cat-node testa `node.right.nullable` no
`lastpos`. A §3.9.4 dá **as duas (e únicas) regras de followpos**, que são
exatamente os dois laços `for position in … : followpos[...] |= …`. **Não existe
terceira regra** no livro, e o código não inventa nenhuma.

### Etapa 6 — `regex_to_dfa` (construção do AFD, Fig. 3.62, p. 180)

```python
    alphabet = {symbol_at[position] for position in symbol_at if position != end_position}
    start = frozenset(root.firstpos)
    states = {start}
    pending = [start]
    transitions = {}
    while pending:
        current = pending.pop()
        for symbol in alphabet:
            destination = set()
            for position in current:
                if symbol_at.get(position) == symbol:
                    destination |= followpos.get(position, set())
            if destination:
                destination = frozenset(destination)
                transitions[(current, symbol)] = destination
                if destination not in states:
                    states.add(destination)
                    pending.append(destination)

    automaton = Automaton()
    automaton.set_initial(start)
    for state in states:
        is_final = end_position in state
        automaton.add_state(state, accepting=is_final, token=token if is_final else None)
    for (source, symbol), target in transitions.items():
        automaton.add_transition(source, symbol, target)
    return automaton.rename("q")
```

**Explicação linha a linha:**

- `alphabet` = todos os símbolos das posições, **exceto** o `#` (ele não é símbolo
  de entrada). Por isso o filtro `if position != end_position`.
- `start = frozenset(root.firstpos)` — o estado inicial do AFD é o `firstpos` da
  raiz. Cada estado do AFD é um **conjunto (frozenset) de posições**.
- `states`/`pending` implementam a fila de estados "não-marcados": `states` é o
  conjunto já descoberto, `pending` os que faltam processar.
- Laço principal: tira `current` de `pending`; para cada `symbol` do alfabeto,
  calcula `destination` = união de `followpos[p]` para **toda posição `p` em
  `current` cujo símbolo é `symbol`** (`if symbol_at.get(position) == symbol`).
  Esse `destination` é o estado-destino por aquele símbolo.
- Se `destination` é não-vazio, registra a transição; se for um estado novo, entra
  em `states` e `pending`.
- Construção final: cria o `Automaton`, marca como **final** todo estado que
  contém `end_position` (a posição de `#`) e o rotula com `token`; copia as
  transições; `rename("q")` dá nomes `q0, q1, …`.

**Justificativa (Aho — Figura 3.62, p. 180).** O procedimento do livro: o estado
inicial é `firstpos(n₀)`; enquanto houver estado não-marcado `S`, para cada símbolo
`a`, `U = ∪ followpos(p)` para todo `p∈S` que corresponde a `a`; se `U` é novo,
adiciona-o como não-marcado e define `Dtran[S,a]=U`. *"The accepting states are
those containing the position for the endmarker symbol #."* — é o nosso `is_final =
end_position in state`. O código é uma tradução 1-para-1.

### Conferência empírica (vale para julgar)

`regex_to_dfa("(a|b)*abb")` produz o **mesmo AFD da Fig. 3.63** (p. 180):

| estado | posições | a | b |
|---|---|---|---|
| q0 (ini) | {1,2,3} | q1 | q0 |
| q1 | {1,2,3,4} | q1 | q2 |
| q2 | {1,2,3,5} | q1 | q3 |
| q3 (fim) | {1,2,3,6} | q1 | q0 |

E `firstpos(raiz)={1,2,3}`, `followpos(1)=followpos(2)={1,2,3}`,
`followpos(3)={4}`, `followpos(4)={5}`, `followpos(5)={6}` — idênticos às
Figs. 3.59/3.60.

---

## I.3 — `minimization.py` — **Algoritmo (b): Minimização** (Alg. 3.39, p. 180–181)

**O que faz:** recebe um AFD (parcial, rotulado por token) e devolve o AFD
**mínimo** equivalente, preservando os tokens dos finais.

```python
DEAD = object()

def _delta(dfa, state, symbol):
    if state is DEAD:
        return DEAD
    target = dfa.step(state, symbol)
    return target if target is not None else DEAD
```

**Explicação:** `DEAD` é um objeto sentinela que representa o **estado morto**. O
AFD vindo da etapa anterior é **parcial** (nem todo par estado×símbolo tem
transição). `_delta` torna a função de transição **total**: se não há transição,
o destino é `DEAD`; do `DEAD`, qualquer símbolo leva ao próprio `DEAD`. Sem isso,
o refinamento por assinatura compararia "ausência de transição" de forma
inconsistente.

```python
def minimize(dfa):
    symbols = sorted(dfa.alphabet)
    states = list(dfa.states) + [DEAD]

    group_of = {}
    for state in states:
        if state is not DEAD and state in dfa.accepting:
            group_of[state] = ("final", dfa.token_of.get(state))
        else:
            group_of[state] = ("comum",)
```

**Explicação (partição inicial):** `symbols` é o alfabeto ordenado (determinismo).
`states` inclui o `DEAD`. `group_of` é a partição: cada estado recebe uma
**etiqueta de grupo**. Estados finais recebem `("final", token)` — repare que o
**token entra na etiqueta**, então finais de tokens **diferentes** começam em
grupos diferentes. Não-finais (e o `DEAD`) recebem `("comum",)`. Isso é a partição
inicial `{finais por token, não-finais}`.

```python
    while True:
        buckets = {}
        for state in states:
            signature = (group_of[state], tuple(group_of[_delta(dfa, state, a)] for a in symbols))
            buckets.setdefault(signature, []).append(state)
        new_group_of = {}
        for index, members in enumerate(buckets.values()):
            for state in members:
                new_group_of[state] = index
        if len(set(new_group_of.values())) == len(set(group_of.values())):
            group_of = new_group_of
            break
        group_of = new_group_of
```

**Explicação (refinamento até ponto fixo):**

- Para cada estado calcula uma **assinatura** = `(grupo_atual, tupla dos grupos de
  destino para cada símbolo)`. Dois estados só têm a mesma assinatura se estão no
  mesmo grupo **e** vão, para todo símbolo, a estados de grupos iguais.
- `buckets` agrupa estados por assinatura; `new_group_of` reatribui um índice
  inteiro a cada bucket (a nova partição).
- **Critério de parada:** se o número de grupos não aumentou
  (`len(set(new))==len(set(old))`), atingiu-se o ponto fixo e para. Isso é correto
  porque a partição só pode **refinar** (nunca juntar grupos), então "não cresceu"
  ⇒ "não mudou".

```python
    representative = {}
    for state in states:
        representative.setdefault(group_of[state], state)

    dead_group = group_of[DEAD]
    start_group = group_of[dfa.initial]

    minimized = Automaton()
    minimized.set_initial(start_group)
    for group, rep in representative.items():
        if group == dead_group and group != start_group:
            continue
        if rep is not DEAD and rep in dfa.accepting:
            minimized.add_state(group, accepting=True, token=dfa.token_of.get(rep))
        else:
            minimized.add_state(group)
    for group, rep in representative.items():
        if group == dead_group and group != start_group:
            continue
        for symbol in symbols:
            target_group = group_of[_delta(dfa, rep, symbol)]
            if target_group == dead_group and target_group != start_group:
                continue
            minimized.add_transition(group, symbol, target_group)
    return minimized.rename("q")
```

**Explicação (construção do AFD mínimo):**

- `representative` escolhe **um estado por grupo** (o primeiro visto). Os estados do
  AFD mínimo passam a ser os **índices de grupo**.
- `dead_group`/`start_group` identificam o grupo do morto e do inicial.
- Primeiro laço: cria os estados do mínimo, **pulando o grupo morto** (`continue`)
  — a menos que o morto coincida com o inicial (caso degenerado). Um estado novo é
  final se seu representante era final, e herda o token (`token=dfa.token_of[rep]`).
- Segundo laço: recria as transições entre grupos, **omitindo as que vão ao grupo
  morto** (volta a ser um AFD parcial, sem o morto).
- `rename("q")` renumera.

**Justificativa (Aho).**
- **Partição inicial por token — §3.9.7, p. 184:** *"begin Algorithm 3.39 with the
  partition that groups together all states that recognize a particular token, and
  also places in one group all those states that do not indicate any token."* É o
  bloco `group_of[state] = ("final", token)` vs `("comum",)`.
- **Refinamento — Figura 3.64, p. 182:** *"partition each group G so that two
  states s and t stay together iff, for every input a, they go to states in the
  same group of Π."* É a `signature`.
- **Estado morto — §3.9.6, p. 182–183 ("Eliminating the Dead State"):** o livro
  recomenda minimizar com o autômato completo (com o morto) e depois *"eliminate
  the dead state"* — o que fazemos ao construir com `DEAD` e omiti-lo no fim.

---

## I.4 — `union.py` — **Algoritmo (c): União via ε** (§3.8 / Fig. 3.50, p. 166–169)

**O que faz:** recebe a lista de AFDs mínimos (um por token) e devolve **um único
AFND** que reconhece a união, ligado por ε-transições.

```python
def union(automata):
    result = Automaton()
    start = "S"
    result.set_initial(start)

    for index, automaton in enumerate(automata):
        prefix = f"A{index}_"
        rename = lambda state, prefix=prefix: f"{prefix}{state}"
        for source, by_symbol in automaton.transitions.items():
            result.add_state(rename(source))
            for symbol, targets in by_symbol.items():
                for target in targets:
                    result.add_transition(rename(source), symbol, rename(target))
        for state in automaton.accepting:
            renamed = rename(state)
            result.add_state(renamed, accepting=True, token=automaton.token_of.get(state))
        result.add_transition(start, EPSILON, rename(automaton.initial))

    return result
```

**Explicação linha a linha:**

- Cria um `Automaton` `result` e um **novo estado inicial** `"S"`.
- Para cada autômato de entrada (com índice `index`): define um `prefix` único
  (`A0_`, `A1_`, …) e uma função `rename` que prefixa o nome de cada estado. O
  `prefix=prefix` no lambda "congela" o valor (evita o bug clássico de closure em
  laço).
- Copia **todas as transições** do autômato para `result`, com os estados
  renomeados — assim os estados de autômatos diferentes nunca colidem.
- Copia os **estados finais**, mantendo `accepting=True` e o **token** original
  (`token=automaton.token_of.get(state)`). É isto que preserva "qual padrão casou".
- `result.add_transition(start, EPSILON, rename(automaton.initial))` — liga o novo
  início `S` ao início (renomeado) de cada autômato por **ε** (`EPSILON = "&"`).

**Justificativa (Aho §3.8, p. 166–169, Fig. 3.50):** *"we combine all the NFAs into
one by introducing a new start state with ε-transitions to each of the start states
of the NFAs Nᵢ for pattern pᵢ."* É exatamente o `start = "S"` + a ε-transição para
cada autômato. **Nota de corretude:** mantemos **um estado final por padrão** (cada
um com seu token), e **não** um final único como na união binária de Thompson
(Alg. 3.23) — porque na análise léxica é preciso saber **qual** token foi
reconhecido. A escolha entre finais concorrentes é resolvida depois, na
determinização.

---

## I.5 — `determinization.py` — **Algoritmo (d): Determinização** (Alg. 3.20, p. 153)

**O que faz:** recebe o AFND da união (com ε) e a tabela de prioridades; devolve o
AFD equivalente, com cada final rotulado pelo token de **maior prioridade**.

```python
def epsilon_closure(automaton, states):
    closure = set(states)
    stack = list(states)
    while stack:
        state = stack.pop()
        for target in automaton.move(state, EPSILON):
            if target not in closure:
                closure.add(target)
                stack.append(target)
    return closure
```

**Explicação:** calcula o **fecho-ε** de um conjunto de estados por busca em
profundidade. Começa com os próprios estados; enquanto a pilha tem elementos, pega
um estado e adiciona ao fecho todos os alcançáveis por ε (`automaton.move(state,
EPSILON)`) ainda não vistos. Termina quando nada novo é alcançável.

```python
def determinize(automaton, priority=None):
    priority = priority or {}
    alphabet = sorted(automaton.alphabet)

    start = frozenset(epsilon_closure(automaton, {automaton.initial}))
    states = {start}
    pending = [start]
    transitions = {}
    while pending:
        current = pending.pop()
        for symbol in alphabet:
            moved = set()
            for state in current:
                moved |= automaton.move(state, symbol)
            if not moved:
                continue
            destination = frozenset(epsilon_closure(automaton, moved))
            transitions[(current, symbol)] = destination
            if destination not in states:
                states.add(destination)
                pending.append(destination)
```

**Explicação (construção de subconjuntos):**

- O estado inicial do AFD é `ε-closure({inicial})` — o fecho-ε do estado inicial
  do AFND (lembre que o `S` da união alcança por ε o início de cada padrão).
- Cada estado do AFD é um `frozenset` de estados do AFND.
- Laço: para `current` e cada `symbol`, calcula `moved` = união de
  `move(state, symbol)` para todos os estados de `current` (todos os destinos por
  aquele símbolo, **sem** ε); o estado-destino é `ε-closure(moved)`. Estados novos
  entram em `pending`. `if not moved: continue` evita criar um estado vazio.

```python
def _choose_token(automaton, subset, priority):
    best = None
    for state in subset:
        if state in automaton.accepting:
            token = automaton.token_of.get(state)
            rank = priority.get(token, len(priority))
            if best is None or rank < best[0]:
                best = (rank, token)
    return best[1] if best is not None else None
```

**Explicação (resolução de prioridade):** dado um subconjunto (estado do AFD),
percorre seus estados do AFND; para cada **final**, pega o `token` e seu `rank`
(posição na prioridade; ausentes recebem `len(priority)`, o pior). Mantém o de
**menor rank**. Devolve o token vencedor (ou `None` se não há final no subconjunto).

```python
    dfa = Automaton()
    dfa.set_initial(start)
    for subset in states:
        token = _choose_token(automaton, subset, priority)
        if token is not None or any(state in automaton.accepting for state in subset):
            dfa.add_state(subset, accepting=True, token=token)
        else:
            dfa.add_state(subset)
    for (source, symbol), target in transitions.items():
        dfa.add_transition(source, symbol, target)
    return dfa.rename("q")
```

**Explicação (montagem):** cria o AFD; um subconjunto é **final** se contém algum
estado final do AFND, e recebe o token escolhido por `_choose_token`; copia as
transições; renumera. Esse AFD final, rotulado por token, **é a tabela de análise
léxica**.

**Justificativa (Aho).**
- **Subconjuntos — Algoritmo 3.20, p. 153 (Fig. 3.31):** estado inicial =
  `ε-closure(s₀)`; para cada `T` e `a`, destino = `ε-closure(move(T,a))`. É a
  tradução direta do laço. `ε-closure(T)` e `move(T,a)` são as funções da Fig. 3.31.
- **Prioridade — §3.5.3, p. 144 (regra 2) e §3.8.3, p. 170:** *"prefer the pattern
  listed first."* O `rank` por ordem de declaração implementa exatamente isso;
  §3.8.3 mostra a mesma regra ao combinar estados de aceitação no AFD.

---

## I.6 — `tokenizer.py` (interface de execução: varredura do fonte)

**O que faz:** usa a tabela (AFD final) para varrer o texto-fonte e produzir a
lista de tokens, pela regra do **maior prefixo**.

```python
def tokenize(table, text):
    tokens = []
    position = 0
    length = len(text)
    while position < length:
        if text[position].isspace():
            position += 1
            continue

        state = table.initial
        last_accept = -1
        last_token = None
        cursor = position
        while cursor < length and not text[cursor].isspace():
            destination = table.step(state, text[cursor])
            if destination is None:
                break
            state = destination
            cursor += 1
            if state in table.accepting:
                last_accept = cursor
                last_token = table.token_of.get(state)

        if last_accept != -1:
            tokens.append((text[position:last_accept], last_token))
            position = last_accept
        else:
            end = position
            while end < length and not text[end].isspace():
                end += 1
            tokens.append((text[position:end], None))
            position = end
    return tokens
```

**Explicação linha a linha:**

- Laço externo: avança `position` pelo texto, pulando espaços.
- Para cada lexema, simula o AFD a partir de `table.initial`. `last_accept` e
  `last_token` guardam **a posição e o token do último estado de aceitação** visto
  — é o coração do "maior prefixo".
- Laço interno: enquanto não acaba o texto e não é espaço, segue a transição
  (`table.step`). Se não há transição (`destination is None`), **para** (o autômato
  travou). A cada passo, se o estado atual é final, **atualiza** `last_accept`/
  `last_token` — assim, ao travar, ainda lembramos do prefixo aceito mais longo.
- Se houve algum aceite (`last_accept != -1`): emite `(lexema, token)` do início
  até `last_accept` e retoma dali (note: pode ser **antes** de onde travou — recua
  para o último aceite). Senão: consome até o próximo espaço e emite
  `(lexema, None)` → será reportado como `<lexema, erro!>`.

**Justificativa (Aho §3.5.3, p. 144, regra 1; implementação em §3.8.3, p. 170):**
*"Always prefer a longer prefix to a shorter prefix."* A técnica de seguir o AFD e
**recuar para o último estado de aceitação** ao travar é exatamente a descrita em
§3.8.3 para casar o lexema mais longo. A saída usa **a tabela gerada na parte de
projeto**, como o enunciado exige (`table.step`, `table.accepting`, `table.token_of`).

---

# Parte II — Trabalho 2: Gerador de Analisador Sintático SLR

## II.0 — `grammar.py` (GLC e gramática aumentada) — §4.6.2, p. 242–243

```python
class Production:
    def __init__(self, index, lhs, rhs):
        self.index = index
        self.lhs = lhs
        self.rhs = tuple(rhs)       # tupla de símbolos; vazia = ε

class Grammar:
    def __init__(self):
        self.nonterminals = []
        self.terminals = []
        self.productions = []
        self.start = None

    def symbols(self):
        return self.nonterminals + self.terminals

    def productions_for(self, nonterminal):
        return [prod for prod in self.productions if prod.lhs == nonterminal]
```

**Explicação:** uma `Production` é `lhs -> rhs`, com `rhs` uma **tupla** (vazia
representa ε) e um `index` que a identifica (usado para nomear reduções). A
`Grammar` guarda `nonterminals`, `terminals`, `productions` e `start` em **listas**
(ordem preservada → resultados determinísticos). `symbols()` devolve
não-terminais + terminais; `productions_for(A)` lista as produções de `A` (usado no
CLOSURE).

```python
    def augmented(self):
        new_start = self.start + "'"
        while new_start in self.nonterminals:
            new_start += "'"
        clone = Grammar()
        clone.nonterminals = [new_start] + list(self.nonterminals)
        clone.terminals = list(self.terminals)
        clone.start = new_start
        clone.original_start = self.start
        clone.productions.append(Production(0, new_start, (self.start,)))
        for prod in self.productions:
            clone.productions.append(Production(len(clone.productions), prod.lhs, prod.rhs))
        return clone
```

**Explicação:** cria `S'` (acrescentando `'` até não colidir) e devolve uma cópia
da gramática com a produção **`S' -> S` no índice 0** e as demais reindexadas a
partir de 1. O índice 0 é o que sinaliza **aceitação** na tabela SLR.

**Justificativa (Aho §4.6.2, p. 242):** *"G', the augmented grammar for G, is G
with a new start symbol S' and production S' → S."* O `parse_grammar` (lido do
arquivo) classifica como **não-terminal** todo símbolo que aparece à esquerda de
`::=`, e como **terminal** os demais — convenção do enunciado.

---

## II.1 — `first_follow.py` — **FIRST e FOLLOW** (§4.4.2, p. 220–222)

```python
def first_of_sequence(first, symbols):
    result = set()
    all_nullable = True
    for symbol in symbols:
        symbol_first = first.get(symbol, {symbol})
        result |= symbol_first - {EPSILON}
        if EPSILON not in symbol_first:
            all_nullable = False
            break
    if all_nullable:
        result.add(EPSILON)
    return result
```

**Explicação:** calcula FIRST de uma **sequência** `X₁X₂…` a partir dos FIRST já
conhecidos. Acumula `FIRST(Xᵢ) \ {ε}`; se algum `Xᵢ` **não** é anulável (ε∉FIRST),
para — porque os símbolos seguintes não influenciam mais o início. Se **todos**
forem anuláveis (`all_nullable` chegou ao fim verdadeiro), acrescenta ε. O
`first.get(symbol, {symbol})` faz terminais (ausentes do dicionário) valerem por si
mesmos.

```python
def compute_first(grammar):
    first = {terminal: {terminal} for terminal in grammar.terminals}
    for nonterminal in grammar.nonterminals:
        first[nonterminal] = set()

    changed = True
    while changed:
        changed = False
        for production in grammar.productions:
            if not production.rhs:
                contribution = {EPSILON}
            else:
                contribution = first_of_sequence(first, production.rhs)
            before = len(first[production.lhs])
            first[production.lhs] |= contribution
            if len(first[production.lhs]) != before:
                changed = True
    return first
```

**Explicação:** inicializa `FIRST(terminal) = {terminal}` e `FIRST(nãoterminal) =
∅`. Itera até o **ponto fixo** (`while changed`): para cada produção, a
contribuição é `{ε}` se o corpo é vazio (`A → ε`), senão `first_of_sequence` do
corpo; junta a `FIRST(lhs)`. O `before`/comparação detecta se algo mudou (controle
do ponto fixo).

```python
def compute_follow(grammar, first):
    follow = {nonterminal: set() for nonterminal in grammar.nonterminals}
    follow[grammar.start].add(ENDMARK)

    changed = True
    while changed:
        changed = False
        for production in grammar.productions:
            for position, symbol in enumerate(production.rhs):
                if symbol not in follow:
                    continue
                beta = production.rhs[position + 1:]
                first_beta = first_of_sequence(first, beta)
                before = len(follow[symbol])
                follow[symbol] |= first_beta - {EPSILON}
                if EPSILON in first_beta:
                    follow[symbol] |= follow[production.lhs]
                if len(follow[symbol]) != before:
                    changed = True
    return follow
```

**Explicação:** começa com `$` em FOLLOW(símbolo inicial). Itera até o ponto fixo:
para cada produção `A → … B β` (percorrendo cada `symbol = B` no corpo), seja `β` o
que vem **depois** de `B`. Acrescenta `FIRST(β) \ {ε}` a `FOLLOW(B)`; e se `β` é
anulável (`ε ∈ FIRST(β)`, incluindo `β` vazio, pois `first_of_sequence([])` devolve
`{ε}`), acrescenta `FOLLOW(A)` a `FOLLOW(B)`. O `if symbol not in follow` ignora
terminais (que não têm FOLLOW).

**Justificativa (Aho §4.4.2, p. 220–222).**
- **FIRST (regras 1–3):** *(1) X terminal ⇒ FIRST(X)={X}*; *(2) X→Y₁…Yₖ propaga
  FIRST enquanto houver ε*; *(3) X→ε ⇒ ε∈FIRST(X)*. São, respectivamente,
  `{t:{t}}`, `first_of_sequence`, e `contribution={EPSILON}` quando o corpo é vazio.
- **FOLLOW (regras 1–3):** *(1) $∈FOLLOW(S)*; *(2) A→αBβ ⇒ FIRST(β)\{ε}⊆FOLLOW(B)*;
  *(3) A→αB ou A→αBβ com ε∈FIRST(β) ⇒ FOLLOW(A)⊆FOLLOW(B)*. Tradução direta. Ambos
  "aplicam as regras até nada mais ser adicionado" — o nosso `while changed`.

---

## II.2 — `lr0_items.py` — **CLOSURE, GOTO, coleção canônica** (§4.6.2; Figs. 4.32 p. 245 / 4.33 p. 246)

Um **item LR(0)** é o par `(índice_da_produção, posição_do_ponto)`. Ex.: a produção
3 `A → X Y` com o ponto após `X` é `(3, 1)`.

```python
def closure(grammar, items):
    result = set(items)
    changed = True
    while changed:
        changed = False
        for production_index, dot in list(result):
            rhs = grammar.productions[production_index].rhs
            if dot < len(rhs):
                symbol = rhs[dot]
                if symbol in grammar.nonterminals:
                    for production in grammar.productions_for(symbol):
                        new_item = (production.index, 0)
                        if new_item not in result:
                            result.add(new_item)
                            changed = True
    return frozenset(result)
```

**Explicação:** começa com os itens dados. Itera até o ponto fixo: para cada item
`(prod, dot)`, se há símbolo após o ponto (`dot < len(rhs)`) e ele é um
**não-terminal** `B` (`symbol in grammar.nonterminals`), adiciona o item inicial
`(prod_de_B, 0)` para **cada** produção de `B`. Repete até não adicionar nada.
Devolve um `frozenset` (estados precisam ser *hashable* para indexar a coleção).

**Justificativa (Aho — Figura 4.32, p. 245):** *"if [A→α·Bβ] is in CLOSURE(I) and
B→γ is a production, add [B→·γ]; repeat until no more items can be added."*

```python
def goto(grammar, items, symbol):
    moved = set()
    for production_index, dot in items:
        rhs = grammar.productions[production_index].rhs
        if dot < len(rhs) and rhs[dot] == symbol:
            moved.add((production_index, dot + 1))
    if not moved:
        return frozenset()
    return closure(grammar, moved)
```

**Explicação:** `GOTO(I, X)` = pega todo item de `I` com o ponto **antes** de `X`
(`rhs[dot] == symbol`), **avança o ponto** (`dot + 1`), e fecha o resultado. Se
nenhum item casa, devolve conjunto vazio.

**Justificativa (Aho §4.6.2, p. 246):** *"GOTO(I,X) is the closure of the set of
all items [A→αX·β] such that [A→α·Xβ] is in I."*

```python
def canonical_collection(grammar):
    start_item = (0, 0)
    initial = closure(grammar, {start_item})
    states = [initial]
    index_of = {initial: 0}
    transitions = {}

    changed = True
    while changed:
        changed = False
        for state in list(states):
            source = index_of[state]
            for symbol in grammar.symbols():
                target = goto(grammar, state, symbol)
                if not target:
                    continue
                if target not in index_of:
                    index_of[target] = len(states)
                    states.append(target)
                    changed = True
                transitions[(source, symbol)] = index_of[target]
    return states, transitions
```

**Explicação:** o estado 0 é `CLOSURE({(0,0)})` = fecho de `S' → · S`. Itera até o
ponto fixo: para cada estado e cada símbolo da gramática, calcula `GOTO`; se
não-vazio e **novo**, registra-o com um índice novo (`len(states)`). `transitions`
guarda a função GOTO como `(índice_origem, símbolo) → índice_destino`. Como
`grammar.symbols()` é uma **lista** (ordem fixa), os estados saem **sempre na mesma
ordem** — numeração reproduzível.

**Justificativa (Aho — Figura 4.33, p. 246):** o procedimento `items(G')`: parte de
`CLOSURE({[S'→·S]})` e fecha a coleção adicionando todo `GOTO(I,X)` não-vazio novo,
até estabilizar.

---

## II.3 — `slr_table.py` — **Tabela SLR** (Algoritmo 4.46, §4.6.4, p. 252–253)

```python
class SLRTable:
    def __init__(self, grammar, states, action, goto, first, follow, conflicts):
        self.grammar = grammar
        self.states = states
        self.action = action
        self.goto = goto
        self.first = first
        self.follow = follow
        self.conflicts = conflicts

    def is_slr(self):
        return not self.conflicts
```

**Explicação:** `SLRTable` é só um contêiner: a gramática aumentada, os estados
(coleção canônica), as funções `action` e `goto` (como dicionários), FIRST/FOLLOW
e a lista de `conflicts`. `is_slr()` é verdadeiro **sse não houve conflito**.

```python
def build_slr_table(grammar):
    augmented = grammar.augmented()
    first = compute_first(augmented)
    follow = compute_follow(augmented, first)
    states, transitions = canonical_collection(augmented)

    action = {}
    goto = {}
    conflicts = []

    def set_action(state, terminal, value):
        existing = action.get((state, terminal))
        if existing is not None and existing != value:
            conflicts.append((state, terminal, existing, value))
            return
        action[(state, terminal)] = value
```

**Explicação (preparação + detecção de conflito):** aumenta a gramática, calcula
FIRST/FOLLOW e a coleção canônica. `set_action` é o **ponto único** onde a tabela
ACTION é escrita: se a célula `(state, terminal)` já tem uma ação **diferente**,
registra um **conflito** (e não sobrescreve); senão grava. É isto que detecta
gramáticas não-SLR(1).

```python
    for state_index, items in enumerate(states):
        for production_index, dot in items:
            production = augmented.productions[production_index]
            rhs = production.rhs
            if dot < len(rhs):
                symbol = rhs[dot]
                if symbol in augmented.terminals:
                    target = transitions.get((state_index, symbol))
                    if target is not None:
                        set_action(state_index, symbol, ("shift", target))
            else:
                if production.index == 0:
                    set_action(state_index, ENDMARK, ("accept",))
                else:
                    for terminal in follow[production.lhs]:
                        set_action(state_index, terminal, ("reduce", production.index))
        for nonterminal in augmented.nonterminals:
            target = transitions.get((state_index, nonterminal))
            if target is not None:
                goto[(state_index, nonterminal)] = target

    return SLRTable(augmented, states, action, goto, first, follow, conflicts)
```

**Explicação (preenchimento):** para cada estado e cada item dele:

- **Ponto no meio, antes de um terminal** `a` (`dot < len(rhs)` e `symbol in
  terminals`): se existe `GOTO(state, a)`, grava `shift` para lá — **regra (a)**.
- **Ponto no fim** (`else`): se é a produção 0 (`S' → S·`), grava `accept` em `$`
  — **regra (c)**. Senão, grava `reduce` por essa produção **para cada terminal de
  FOLLOW(lhs)** — **regra (b)**.
- Depois, para os **não-terminais**, copia `GOTO(state, A)` para a tabela `goto`.

**Justificativa (Aho — Algoritmo 4.46, p. 252–253, citação literal):**
- *(a) If [A→α·aβ] is in Iᵢ and GOTO(Iᵢ,a)=Iⱼ, set ACTION[i,a]="shift j". Here a
  must be a terminal.* ⟶ bloco do `if symbol in augmented.terminals`.
- *(b) If [A→α·] is in Iᵢ, set ACTION[i,a]="reduce A→α" for all a in FOLLOW(A);
  **here A may not be S'**.* ⟶ o laço `for terminal in follow[...]`. A restrição "A
  ≠ S'" é garantida porque `production.index == 0` (a produção de S') cai no ramo
  **accept**, nunca no reduce.
- *(c) If [S'→S·] is in Iᵢ, set ACTION[i,$]="accept".* ⟶ `set_action(.., ENDMARK,
  ("accept",))`.
- *goto: if GOTO(Iᵢ,A)=Iⱼ then GOTO[i,A]=j.* ⟶ laço dos não-terminais.
- *"If any conflicting actions result, the grammar is not SLR(1)."* ⟶ `set_action`
  acumula em `conflicts`; `is_slr()` reporta. (Ex.: dangling-else → `estado 4,
  'else': s5 x r2`.)

---

## II.4 — `lr_parser.py` — **Programa de análise LR** (Alg. 4.44 / Fig. 4.36, p. 248–251)

```python
def parse(table, terminals):
    stack = [0]
    nodes = []
    stream = list(terminals) + [ENDMARK]
    position = 0
    reductions = []

    while True:
        state = stack[-1]
        symbol = stream[position]
        move = table.action.get((state, symbol))

        if move is None:
            return ParseResult(False, reductions,
                               error_position=position, error_symbol=symbol, error_state=state)
        if move[0] == "shift":
            stack.append(move[1])
            nodes.append(DerivationNode(symbol))
            position += 1
        elif move[0] == "reduce":
            production = table.grammar.productions[move[1]]
            count = len(production.rhs)
            if count:
                children = nodes[-count:]
                del nodes[-count:]
                del stack[-count:]
            else:
                children = [DerivationNode(EPSILON)]
            exposed = stack[-1]
            stack.append(table.goto[(exposed, production.lhs)])
            nodes.append(DerivationNode(production.lhs, children))
            reductions.append(production)
        elif move[0] == "accept":
            return ParseResult(True, reductions, tree=nodes[-1] if nodes else None)
```

**Explicação linha a linha:**

- `stack = [0]` — pilha **só de estados** (começa no estado 0). `stream` é a lista
  de terminais com `$` no fim. `position` é o ponteiro de leitura.
- Em cada iteração: `state` é o topo da pilha, `symbol` o terminal atual,
  `move = ACTION[state, symbol]`.
- `move is None` → não há ação → **erro** (devolve a posição/símbolo/estado do erro,
  e `tree` fica `None`).
- **shift** `("shift", t)`: empilha o estado `t`, cria uma **folha** com o terminal
  lido e avança a entrada (`position += 1`).
- **reduce** `("reduce", p)`: pega a produção `p`; `count = |β|`. Se `count > 0`,
  os `count` nós do topo da pilha de nós viram **filhos** do novo nó, e desempilha
  `count` estados **e** `count` nós. Se `count == 0` (produção `A → ε`), cria uma
  folha `&` como único filho e **não desempilha** nada. Depois, com `exposed` = novo
  topo, empilha `GOTO[exposed, lhs]` e cria o nó `A` (com seus filhos). Registra a
  produção em `reductions`.
- **accept**: devolve sucesso; a raiz da árvore é o nó que restou (`nodes[-1]`).

**Justificativa (Aho — Algoritmo 4.44 / Figura 4.36, p. 248–251):**
- *if ACTION[s,a]=shift t: push t; advance* ⟶ ramo shift.
- *if ACTION[s,a]=reduce A→β: pop |β| symbols; push GOTO[t,A]; output A→β* ⟶ ramo
  reduce (`del stack[-count:]` é o "pop |β|"; `goto[exposed, lhs]` é o "push
  GOTO[t,A]").
- *if accept: break* ⟶ ramo accept. *else error* ⟶ `move is None`.

**Nota de corretude.** A pilha guarda **só estados** (não pares símbolo/estado) — é
a simplificação que o próprio livro adota (§4.6: o estado no topo já determina o
GOTO). Produções ε são tratadas certo (`count == 0`: não desempilha; gera folha `&`).

### Árvore de derivação (`DerivationNode`) — extra, não exigido

```python
class DerivationNode:
    def __init__(self, symbol, children=None):
        self.symbol = symbol
        self.children = children if children is not None else []

    def render(self):
        lines = [self.symbol]
        self._render_children(lines, "")
        return "\n".join(lines)

    def _render_children(self, lines, prefix):
        total = len(self.children)
        for index, child in enumerate(self.children):
            last = index == total - 1
            lines.append(prefix + ("`-- " if last else "|-- ") + child.symbol)
            child._render_children(lines, prefix + ("    " if last else "|   "))
```

**Explicação:** um nó tem um símbolo e uma lista de filhos. `render` produz a árvore
em ASCII indentado (estilo `tree`). É construída **junto** com a análise (cada shift
= folha; cada reduce = nó com os filhos do topo), então na aceitação o nó restante é
a raiz (o símbolo inicial). Mostra a árvore sintática concreta da entrada — útil
para inspeção, mas além do que o enunciado pede.

---

## II.5 — `symbol_table.py` (tabela de símbolos)

```python
class SymbolTable:
    def __init__(self, reserved_words=()):
        self.entries = []
        self.index_of = {}
        for word in reserved_words:
            self._insert(word, "PR")

    def _insert(self, lexeme, category):
        line = len(self.entries)
        self.entries.append((lexeme, category))
        self.index_of[lexeme] = line
        return line

    def is_reserved(self, lexeme):
        return self.index_of.get(lexeme) is not None and self.entries[self.index_of[lexeme]][1] == "PR"
```

**Explicação:** a tabela é pré-carregada com as **palavras reservadas** na categoria
`PR`. `_insert` adiciona uma entrada e devolve a **linha** (índice). `is_reserved`
verifica se o lexema está na tabela como `PR`.

```python
    def resolve(self, lexeme, pattern, grammar_terminals):
        if self.is_reserved(lexeme):
            return (lexeme, "PR"), lexeme                  # <for, PR>
        if lexeme in grammar_terminals:
            return (lexeme, pattern), lexeme
        if pattern in grammar_terminals and pattern != "id":
            return (lexeme, pattern), pattern
        line = self.index_of.get(lexeme)
        if line is None:
            line = self._insert(lexeme, "id")
        return ("id", line), "id"                          # <id, linha>
```

**Explicação:** decide, para cada lexema, **(token de saída, terminal da
gramática)**:
- reservada → `(<lexema, PR>, lexema)` — o terminal é o próprio lexema (ex.: `if`);
- lexema que **já é terminal** da gramática (ex.: `+`, `(`) → usa o próprio lexema;
- lexema cujo **padrão** é um terminal (ex.: `num`) → usa o padrão como terminal;
- senão é **identificador**: insere se novo e devolve `(<id, linha>, "id")`.

**Justificativa (Enunciado T2):** *"Se o lexema já estiver na tabela, retornar o
token lá indicado, p.ex. `<for, PR>`; caso contrário, incluir e retornar `<id,
10>`, onde 10 é a linha onde o id foi armazenado."* O `resolve` implementa
literalmente essa regra; a parte de mapear token → terminal é o que liga o T1 ao T2.

---

## II.6 / II.7 — `syntactic_analyzer.py` e `main.py`

`SyntacticAnalyzer.build()` chama `build_slr_table(self.grammar)` e guarda a tabela.
`describe_items` / `describe_first_follow` / `describe_table` geram as
**visualizações** (coleção de itens LR(0); FIRST/FOLLOW; tabela ACTION/GOTO no
estilo da Fig. 4.37, p. 254). O `main.py` (CLI) constrói a tabela, mostra as etapas,
informa se é SLR(1) e, recebendo a lista de tokens do T1, analisa-a e imprime
resultado + árvore + tabela de símbolos.

---

# Parte III — Integração e Interface Gráfica

## III.1 — `integracao/controller.py` (GUI PyQt6)

A função-núcleo é `executar_pipeline`, que roda **todo** o fluxo T1→T2 e devolve um
dicionário de blocos para a interface:

```python
def executar_pipeline(definicoes, gramatica, reservadas, fonte):
    lexico = LexicalAnalyzer(definicoes)
    lexico.build()
    saida_lexico = format_tokens(tokenize(lexico.table, fonte))     # T1 usa a tabela gerada

    sintatico = SyntacticAnalyzer(gramatica, reservadas)
    sintatico.build()

    tokens = parse_token_list(saida_lexico)
    terminais, resolvidos = tokens_to_terminals(
        tokens, sintatico.symbol_table, set(sintatico.grammar.terminals))
    resultado = parse(sintatico.table, terminais)                    # T2 analisa
    ...
```

**Explicação:** (1) constrói o analisador léxico e tokeniza o fonte **usando a
tabela gerada** (`tokenize(lexico.table, fonte)`); (2) constrói o SLR; (3) converte
os tokens do T1 em **terminais** via `tokens_to_terminals` (que usa a tabela de
símbolos); (4) chama `parse`. A GUI (`IntegracaoWindow`) é só a apresentação em abas
desses blocos; a **mesma** `executar_pipeline`/`run_pipeline` é testada sem Qt em
`integracao/tests/run_tests.py`. A aba "Tabela SLR" mostra o **aviso de conflito**
(`_slr_conflitos_texto`) quando `table.is_slr()` é falso.

---

# Parte IV — Como julgar a corretude

### 1. Rastreabilidade (cada bloco do nosso código ↔ livro)

| Nosso código | Função | Referência Aho | Pág. (2e) |
|---|---|---|---|
| ER→AFD direto | `regex_to_dfa.regex_to_dfa` | Alg. 3.36; Figs. 3.58/3.62; §3.9.4 | 179 (3.58→177, 3.62→180) |
| classes/`+`/`?` | `to_tokens`, `desugar` | §3.3.5 (classes; r⁺=rr*; r?=r\|ε) | 124 |
| nullable/first/last/follow | `annotate` | Fig. 3.58 + §3.9.4 | 177 |
| Minimização | `minimize` | Alg. 3.39; Fig. 3.64; §3.9.6/§3.9.7 | 180–182 / 184 |
| União ε | `union` | §3.8 (Fig. 3.50) | 166–169 |
| Determinização | `determinize` | Alg. 3.20; Fig. 3.31 | 153 |
| Prioridade / maior prefixo | `_choose_token`, `tokenize` | §3.5.3 (regras 2 e 1) / §3.8.3 | 144 / 170 |
| FIRST/FOLLOW | `compute_first/compute_follow` | §4.4.2 (regras 1–3) | 220–222 |
| CLOSURE / GOTO / coleção | `closure/goto/canonical_collection` | Figs. 4.32/4.33; §4.6.2 | 245 / 246 |
| Gramática aumentada | `Grammar.augmented` | §4.6.2 (S'→S) | 242–243 |
| Tabela SLR | `build_slr_table` | Alg. 4.46 (regras a/b/c) | 252–253 |
| Parsing LR | `parse` | Alg. 4.44 / Fig. 4.36 | 248–251 |
| Tabela de símbolos | `SymbolTable.resolve` | Enunciado T2 (PR / <id,linha>) | — |

### 2. Testes (rodar e conferir)

```
python3 "src/Gerador de Analisadores Léxicos/tests/run_tests.py"      # 11/11
python3 "src/Gerador de Analisadores Sintáticos/tests/run_tests.py"   # 53/53
python3 "src/integracao/tests/run_tests.py"                           # 11/11
```

Incluem casos do **próprio livro**: AFD de `(a|b)*abb` (Fig. 3.63), Exemplos
3.28/3.29 da §3.8 (prioridade e maior prefixo) e a gramática dangling-else
(conflito SLR, §4.6).

### 3. Conferências manuais rápidas

- `regex_to_dfa("(a|b)*abb")` deve dar os 4 estados da Fig. 3.63.
- `annotate` só pode ter **duas** regras de followpos (cat e star) — §3.9.4.
- Na minimização, finais de tokens diferentes **nunca** se fundem (partição por
  token, §3.9.7).
- Em `build_slr_table`, a redução usa `FOLLOW(lhs)` e `S'` vira **accept**, nunca
  reduce — regra (b) do Alg. 4.46.
- Em `parse`, a pilha tem só estados e o reduce desempilha `|β|` — Alg. 4.44.
