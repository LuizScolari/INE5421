# Gerador de Analisadores Sintáticos (SLR)

Trabalho 2 da disciplina de Linguagens Formais e Compiladores.

O programa recebe uma Gramática Livre de Contexto e a lista de palavras
reservadas, constrói a tabela de análise **SLR** e usa essa tabela para
reconhecer a lista de tokens produzida pelo analisador léxico do Trabalho 1.
Tudo foi implementado em Python puro, sem nenhuma biblioteca externa (apenas
`sys` e `os` da biblioteca padrão, para entrada/saída).

## Algoritmos implementados

Cada algoritmo fica em um arquivo separado e segue exatamente o livro
*Compilers: Principles, Techniques, and Tools* (Aho, Lam, Sethi, Ullman, 2ª ed.),
Seção 4.6 (Introduction to LR Parsing: Simple LR):

| Arquivo | Algoritmo | Referência no livro |
| --- | --- | --- |
| [first_follow.py](first_follow.py) | (a) Funções FIRST e FOLLOW | Seção 4.4.2 |
| [lr0_items.py](lr0_items.py) | (b) CLOSURE | **Figura 4.32** |
| [lr0_items.py](lr0_items.py) | (c) GOTO e coleção canônica de itens LR(0) | **Figura 4.33** e Seção 4.6.2 |
| [lr_parser.py](lr_parser.py) | (d) Programa de análise LR | **Algoritmo 4.44** / **Figura 4.36** |
| [slr_table.py](slr_table.py) | (e) Construção da tabela SLR | **Algoritmo 4.46** (citado como 4.38 no enunciado) |

Arquivos de apoio:

| Arquivo | Função |
| --- | --- |
| [grammar.py](grammar.py) | Estrutura da GLC, leitura do formato `::=` e gramática aumentada `S' -> S` |
| [symbol_table.py](symbol_table.py) | Tabela de símbolos com palavras reservadas e leitura da lista de tokens |
| [syntactic_analyzer.py](syntactic_analyzer.py) | Interface de projeto: encadeia os algoritmos e fornece as visualizações |
| [main.py](main.py) | Interface de linha de comando (menu interativo e modo em lote) |

## Fluxo de construção

1. A gramática é lida e **aumentada** com a produção `S' -> S`.
2. Calculam-se os conjuntos **FIRST** e **FOLLOW** (Seção 4.4.2).
3. Constrói-se a **coleção canônica** de conjuntos de itens LR(0) usando
   **CLOSURE** (Fig. 4.32) e **GOTO** (Fig. 4.33).
4. Monta-se a **tabela SLR** (ACTION e GOTO) pelo **Algoritmo 4.46**. Conflitos
   indicam que a gramática não é SLR(1) e são reportados.
5. Na execução, o **Algoritmo 4.44** dirige a análise da lista de tokens.

## Formato de entrada da gramática

Uma produção por linha, no formato `<Não terminal> ::= <Corpo da produção>`
(alternativas com `|` também são aceitas). Os símbolos do corpo são separados por
espaços; um não terminal é todo símbolo que aparece à esquerda de alguma
produção, e os demais são terminais. O épsilon é escrito como `&` e o primeiro
não terminal é o símbolo inicial.

```
E ::= E + T | T
T ::= T * F | F
F ::= ( E ) | id
```

## Integração com o léxico e a tabela de símbolos

A entrada da execução é a lista de tokens do Trabalho 1, no formato
`<lexema, padrão>` (um por linha). Cada token é resolvido pela tabela de
símbolos, conforme o enunciado:

- se o lexema é uma **palavra reservada**, devolve-se o token indicado, por
  exemplo `<for, PR>` (PR = palavra-reservada), e o terminal é o próprio lexema;
- caso contrário, se for um **identificador**, o lexema é inserido na tabela e
  devolve-se `<id, linha>`, onde `linha` é a posição na tabela; o terminal é `id`.

As palavras reservadas são pré-carregadas na tabela de símbolos a partir de um
arquivo (uma por linha).

## Como executar

Entre na pasta do projeto antes de rodar (os módulos se importam entre si):

```
cd "src/Gerador de Analisadores Sintáticos"
```

### Menu interativo

```
python3 main.py
```

Permite carregar a gramática e as palavras reservadas, visualizar a coleção
canônica de itens, os conjuntos FIRST/FOLLOW, a tabela SLR e a tabela de
símbolos, e analisar uma lista de tokens.

### Modo em lote

```
python3 main.py <gramatica> <tokens> [reservadas]
```

Exemplo:

```
python3 main.py tests/gramaticas/comandos.txt tests/tokens/comandos_ok.txt tests/reservadas/comandos_reservadas.txt
```

## Testes

Os casos de teste ficam em [tests/](tests/): gramáticas em `tests/gramaticas/`,
palavras reservadas em `tests/reservadas/` e listas de tokens em `tests/tokens/`.
Para rodar a suíte automatizada:

```
python3 tests/run_tests.py
```

Os testes confirmam a aderência ao livro: a gramática de expressões da Seção 4.6
produz **12 estados** (Fig. 4.31), os FIRST/FOLLOW do **Exemplo 4.30**, a tabela
da **Fig. 4.37** e a sequência de reduções da **Fig. 4.38** para `id * id + id`.
