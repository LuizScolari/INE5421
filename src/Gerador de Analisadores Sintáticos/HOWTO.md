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
| [main.py](main.py) | Interface de linha de comando (argparse): roda toda a cadeia e exibe as etapas |

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

```
python3 main.py <gramatica> [tokens] [-r reservadas] [-o saida]
```

Basta informar a gramática para construir a tabela e ver **todas as etapas**: a
coleção canônica de itens LR(0), os conjuntos FIRST/FOLLOW e a tabela de análise
SLR (ACTION/GOTO), além do status SLR(1) e dos conflitos, se houver.

```
python3 main.py tests/gramaticas/expressao.txt
```

Se uma lista de tokens for informada, além das etapas o programa a analisa
(aceita/erro, reduções aplicadas) e mostra a tabela de símbolos resultante. Use
`-r`/`--reservadas` para carregar as palavras reservadas:

```
python3 main.py tests/gramaticas/comandos.txt tests/tokens/comandos_ok.txt -r tests/reservadas/comandos_reservadas.txt
```

O relatório da análise é impresso na tela; use `-o <arquivo>` (ou `--output`)
para gravá-lo em arquivo (essa opção exige uma lista de tokens). Use `-h`/`--help`
para ver todas as opções.

### Comandos prontos para testar

Já dentro de `src/Gerador de Analisadores Sintáticos` (veja o `cd` acima):

```bash
# Ajuda
python3 main.py -h

# Só a gramática — mostra todas as etapas (itens LR(0), FIRST/FOLLOW, tabela SLR)
python3 main.py tests/gramaticas/expressao.txt

# Gramática + tokens — etapas + análise + tabela de símbolos
python3 main.py tests/gramaticas/expressao.txt tests/tokens/expr_ok.txt
python3 main.py tests/gramaticas/aritmetica_estendida.txt tests/tokens/aritmetica_ok.txt
python3 main.py tests/gramaticas/epsilon.txt tests/tokens/epsilon_ok.txt

# Entrada com erro sintático (mostra a posição do erro)
python3 main.py tests/gramaticas/expressao.txt tests/tokens/expr_erro.txt

# Com palavras reservadas (-r) — resolve begin/end, if/then como PR
python3 main.py tests/gramaticas/comandos.txt tests/tokens/comandos_ok.txt -r tests/reservadas/comandos_reservadas.txt
python3 main.py tests/gramaticas/blocos.txt tests/tokens/blocos_ok.txt -r tests/reservadas/blocos_reservadas.txt

# Gramática NÃO SLR(1) — reporta o conflito (dangling-else)
python3 main.py tests/gramaticas/dangling_else.txt

# Salvar o relatório da análise em arquivo
python3 main.py tests/gramaticas/comandos.txt tests/tokens/comandos_ok.txt -r tests/reservadas/comandos_reservadas.txt -o relatorio.txt
```

A partir da **raiz do repositório** (sem `cd`), use os caminhos completos entre
aspas (há espaços no nome da pasta):

```bash
python3 "src/Gerador de Analisadores Sintáticos/main.py" \
        "src/Gerador de Analisadores Sintáticos/tests/gramaticas/expressao.txt" \
        "src/Gerador de Analisadores Sintáticos/tests/tokens/expr_ok.txt"
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
