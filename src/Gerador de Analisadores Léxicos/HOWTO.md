# Gerador de Analisadores Léxicos

Trabalho 1 da disciplina de Linguagens Formais e Compiladores.

O programa recebe um conjunto de definições regulares, constrói a tabela de
análise léxica correspondente e usa essa tabela para reconhecer os tokens de um
texto fonte. Tudo foi implementado em Python puro, sem nenhuma biblioteca
externa (apenas `sys` e `os` da biblioteca padrão, para entrada/saída).

## Algoritmos implementados

Cada algoritmo fica em um arquivo separado e segue exatamente o livro
*Compilers: Principles, Techniques, and Tools* (Aho, Lam, Sethi, Ullman, 2ª ed.):

| Arquivo | Algoritmo | Referência no livro |
| --- | --- | --- |
| [regex_to_dfa.py](regex_to_dfa.py) | (a) ER → AFD (método direto: árvore sintática, `nullable`/`firstpos`/`lastpos`/`followpos`) | **Algoritmo 3.36** e Fig. 3.62; funções da **Fig. 3.58** e Seção 3.9.4 |
| [minimization.py](minimization.py) | (b) Minimização de AFD (refinamento de partições) | **Algoritmo 3.39** e Fig. 3.64; "Eliminating the Dead State" |
| [union.py](union.py) | (c) União de autômatos via epsilon-transição | Seção 3.8.3 e Fig. 3.50/3.52 |
| [determinization.py](determinization.py) | (d) Determinização (construção de subconjuntos com fecho-epsilon) | **Algoritmo 3.20** e Fig. 3.32/3.33 |

### Aderência ao livro

- **(a)** As regras de `nullable`/`firstpos`/`lastpos` da Fig. 3.58 cobrem apenas
  `&` (epsilon), folhas, `|`, concatenação e `*`. Os operadores `+`, `?` e os
  grupos `[...]` são *abreviações* (Seção 3.3.5) e são expandidos para os
  operadores básicos antes de montar a árvore, pelas identidades `r+ = rr*`,
  `r? = r|&` e `[a-c] = a|b|c`. Assim as quatro funções usam as regras da Fig.
  3.58 sem alteração.
- **(b)** O AFD é completado com um estado morto que recebe as transições
  ausentes, a partição inicial é `{finais, não-finais}` (separando finais por
  token, como na Seção 3.9.7), o refinamento segue a Fig. 3.64 e, ao final, o
  estado morto é eliminado.
- **(d)** A regra de desempate ao rotular um estado do AFD — "vence o padrão
  listado primeiro" — é a da Seção 3.8.3 (Exemplo 3.28).

Os exemplos do próprio livro são usados como teste de regressão (ver
[tests/run_tests.py](tests/run_tests.py)): o AFD direto de `(a|b)*abb` reproduz a
Fig. 3.63 e o analisador para `a`, `abb`, `a*b+` reproduz os Exemplos 3.28 e 3.29.

Arquivos de apoio:

| Arquivo | Função |
| --- | --- |
| [automaton.py](automaton.py) | Estrutura de dados de autômato e visualização em tabela |
| [regular_definitions.py](regular_definitions.py) | Leitura do arquivo de definições regulares |
| [lexical_analyzer.py](lexical_analyzer.py) | Interface de projeto: encadeia os quatro algoritmos e gera a tabela |
| [tokenizer.py](tokenizer.py) | Interface de execução: aplica a tabela ao texto fonte (regra do maior prefixo) |
| [main.py](main.py) | Interface de linha de comando (argparse): roda toda a cadeia e exibe as etapas |

## Fluxo de construção

1. Cada expressão regular é convertida em um AFD pelo método direto do Aho.
2. Cada AFD é minimizado.
3. Todos os AFD minimizados são unidos por epsilon-transições, formando um AFND.
4. O AFND é determinizado, gerando a tabela de análise léxica (representação
   implícita: o próprio AFD final, com cada estado final rotulado pelo token que
   reconhece).

## Formato de entrada das definições

Uma definição por linha, no formato `nome: expressão`:

```
id: [a-zA-Z]([a-zA-Z] | [0-9])*
num: [1-9]([0-9])* | 0
```

Operadores aceitos: `*` (fecho), `+` (fecho positivo), `?` (zero ou um),
`|` (ou) e grupos como `[a-zA-Z]` e `[0-9]`. A concatenação é implícita.
Espaços dentro da expressão são ignorados (servem apenas para legibilidade) e o
epsilon é escrito como `&`. A ordem das definições define a prioridade entre os
tokens: em caso de empate, vence o token declarado primeiro.

### Símbolos literais que também são metacaracteres

Para reconhecer como símbolo do alfabeto um caractere que também é metacaractere
de ER (`( ) * + ? | .`), coloque-o numa **classe de caracteres**: o conteúdo de
`[...]` é sempre tratado como literal (Seção 3.3.5 do Aho).

```
mais: [+]
vezes: [*]
apar: [(]
fpar: [)]
```

O epsilon `&` e o marcador de fim `#` continuam reservados e não podem ser
símbolos do alfabeto (tentar usá-los como literal gera erro).

## Formato de saída

Para cada lexema reconhecido o programa emite `<lexema, padrão>`; quando um
trecho não é reconhecido, emite `<lexema, erro!>`.

## Como executar

Entre na pasta do projeto antes de rodar (os módulos se importam entre si):

```
cd "src/Gerador de Analisadores Léxicos"
```

```
python3 main.py <definicoes> [fonte] [-o saida]
```

Basta informar o arquivo de definições para executar **toda a cadeia** e ver
**todas as etapas** da construção: o AFD de cada ER (método direto de Aho), os
AFD minimizados, o AFND da união (com epsilon-transições) e a tabela de análise
léxica final.

```
python3 main.py tests/definicoes/exemplo1_id_num.txt
```

Se um arquivo fonte for informado, além das etapas o programa tokeniza esse
texto usando a tabela gerada:

```
python3 main.py tests/definicoes/exemplo1_id_num.txt tests/fontes/fonte_exemplo1.txt
```

A lista de tokens é impressa na tela; use `-o <arquivo>` (ou `--output`) para
gravá-la em arquivo (essa opção exige um arquivo fonte). Use `-h`/`--help` para
ver todas as opções.

### Comandos prontos para testar

Já dentro de `src/Gerador de Analisadores Léxicos` (veja o `cd` acima):

```bash
# Ajuda
python3 main.py -h

# Só as definições — mostra todas as etapas da construção
python3 main.py tests/definicoes/exemplo1_id_num.txt

# Definições + fonte — etapas + tokenização
python3 main.py tests/definicoes/exemplo1_id_num.txt tests/fontes/fonte_exemplo1.txt
python3 main.py tests/definicoes/exemplo3_palavras_chave.txt tests/fontes/fonte_exemplo3.txt
python3 main.py tests/definicoes/exemplo4_numeros.txt tests/fontes/fonte_exemplo4.txt
python3 main.py tests/definicoes/exemplo5_minilinguagem.txt tests/fontes/fonte_exemplo5.txt

# Fonte com símbolo fora do alfabeto (gera <..., erro!>)
python3 main.py tests/definicoes/exemplo1_id_num.txt tests/fontes/fonte_com_erro.txt

# Salvar a lista de tokens em arquivo
python3 main.py tests/definicoes/exemplo1_id_num.txt tests/fontes/fonte_exemplo1.txt -o tokens.txt
```

A partir da **raiz do repositório** (sem `cd`), use os caminhos completos entre
aspas (há espaços no nome da pasta):

```bash
python3 "src/Gerador de Analisadores Léxicos/main.py" \
        "src/Gerador de Analisadores Léxicos/tests/definicoes/exemplo1_id_num.txt" \
        "src/Gerador de Analisadores Léxicos/tests/fontes/fonte_exemplo1.txt"
```

## Testes

Os casos de teste ficam em [tests/](tests/): as definições em
`tests/definicoes/` e os textos fonte em `tests/fontes/`. Para rodar a suíte
automatizada, que compara as saídas com o resultado esperado:

```
python3 tests/run_tests.py
```

## Observação sobre o Exemplo 2 do enunciado

O Exemplo 2 do enunciado define `er1: a?(a | b)+` e `er2: b?(a | b)+`. Como o
primeiro caractere é opcional (`?`), as duas expressões reconhecem exatamente a
mesma linguagem (`{a, b}+`) e, portanto, são indistinguíveis: qualquer palavra
de `a` e `b` casa com as duas, e a prioridade faz `er1` vencer sempre. A saída
mostrada no enunciado (classificação pela primeira letra) corresponde, na
verdade, às expressões `a(a | b)*` e `b(a | b)*`. Por isso há dois arquivos:
[tests/definicoes/exemplo2_er1_er2.txt](tests/definicoes/exemplo2_er1_er2.txt)
(versão literal do enunciado) e
[tests/definicoes/exemplo2_corrigido.txt](tests/definicoes/exemplo2_corrigido.txt)
(reproduz a saída pretendida).
