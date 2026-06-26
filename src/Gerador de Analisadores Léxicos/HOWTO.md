# Gerador de Analisadores Léxicos

Trabalho 1 da disciplina de Linguagens Formais e Compiladores.

O programa recebe um conjunto de definições regulares, constrói a tabela de
análise léxica correspondente e usa essa tabela para reconhecer os tokens de um
texto fonte. Tudo foi implementado em Python puro, sem nenhuma biblioteca
externa (apenas `sys` e `os` da biblioteca padrão, para entrada/saída).

## Algoritmos implementados

Cada algoritmo fica em um arquivo separado:

| Arquivo | Algoritmo |
| --- | --- |
| [regex_to_dfa.py](regex_to_dfa.py) | (a) Conversão de Expressão Regular para AFD (método direto do Aho: árvore sintática, `nullable`, `firstpos`, `lastpos`, `followpos`) |
| [minimization.py](minimization.py) | (b) Minimização de AFD (remoção de inalcançáveis/mortos e refinamento de partições) |
| [union.py](union.py) | (c) União de autômatos via epsilon-transição |
| [determinization.py](determinization.py) | (d) Determinização (construção de subconjuntos com fecho-epsilon) |

Arquivos de apoio:

| Arquivo | Função |
| --- | --- |
| [automaton.py](automaton.py) | Estrutura de dados de autômato e visualização em tabela |
| [regular_definitions.py](regular_definitions.py) | Leitura do arquivo de definições regulares |
| [lexical_analyzer.py](lexical_analyzer.py) | Interface de projeto: encadeia os quatro algoritmos e gera a tabela |
| [tokenizer.py](tokenizer.py) | Interface de execução: aplica a tabela ao texto fonte (regra do maior prefixo) |
| [main.py](main.py) | Interface de linha de comando (menu interativo e modo em lote) |

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

## Formato de saída

Para cada lexema reconhecido o programa emite `<lexema, padrão>`; quando um
trecho não é reconhecido, emite `<lexema, erro!>`.

## Como executar

Entre na pasta do projeto antes de rodar (os módulos se importam entre si):

```
cd "src/Gerador de Analisadores Léxicos"
```

### Menu interativo

```
python3 main.py
```

O menu permite carregar as definições, visualizar os AFD de cada ER, os AFD
minimizados, o AFND da união, a tabela de análise léxica, salvar a tabela em
arquivo e analisar um texto fonte (de arquivo ou digitado).

### Modo em lote

```
python3 main.py <definicoes> <fonte> [saida]
```

Exemplo:

```
python3 main.py tests/definicoes/exemplo1_id_num.txt tests/fontes/fonte_exemplo1.txt
```

Se o terceiro argumento for informado, a lista de tokens é gravada nele; caso
contrário, é impressa na tela.

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
