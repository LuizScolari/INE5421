# INE5421 — Linguagens Formais e Compiladores

Implementação dos trabalhos T1 e T2 em Python puro. Nenhuma biblioteca externa
faz parte dos algoritmos — só `sys` e `os` da stdlib, para leitura de arquivos
e argumentos de linha de comando.

A referência seguida foi o Aho (*Compilers: Principles, Techniques, and Tools*,
2ª ed.).

---

## T1 — Gerador de Analisadores Léxicos

Recebe um arquivo de definições regulares e constrói a tabela léxica passando
pelos quatro algoritmos pedidos no enunciado, nessa ordem:

- `algoritmos/regex_to_dfa.py` — ER → AFD pelo método direto (Alg. 3.36)
- `algoritmos/minimization.py` — minimização do AFD (Alg. 3.39)
- `algoritmos/union.py` — união dos AFDs por ε-transições
- `algoritmos/determinization.py` — determinização via subconjuntos (Alg. 3.20)

### Formato das definições

Uma definição por linha, `nome: expressão`. A ordem define prioridade em caso
de empate.

```
id: [a-zA-Z]([a-zA-Z] | [0-9])*
num: [1-9]([0-9])* | 0
```

Operadores disponíveis: `*`, `+`, `?`, `|`, classes `[a-z]`. Concatenação é
implícita, espaços são ignorados, epsilon é `&`. Para usar um metacaractere
como literal, coloque dentro de colchetes: `[+]`, `[*]`, `[(]`.

### Executando

```bash
cd "src/Gerador de Analisadores Léxicos"

# mostra todas as etapas da construção
python3 main.py tests/definicoes/exemplo1_id_num.txt

# com arquivo fonte — tokeniza o texto
python3 main.py tests/definicoes/exemplo1_id_num.txt tests/fontes/fonte_exemplo1.txt
python3 main.py tests/definicoes/exemplo3_palavras_chave.txt tests/fontes/fonte_exemplo3.txt
python3 main.py tests/definicoes/exemplo5_minilinguagem.txt tests/fontes/fonte_exemplo5.txt

# salvar tokens em arquivo
python3 main.py tests/definicoes/exemplo1_id_num.txt tests/fontes/fonte_exemplo1.txt -o tokens.txt
```

### Testes

```bash
cd "src/Gerador de Analisadores Léxicos"
python3 tests/run_tests.py
# 11/11
```

---

## T2 — Gerador de Analisadores Sintáticos (SLR)

Recebe uma GLC e gera a tabela SLR(1), depois usa essa tabela para analisar a
lista de tokens produzida pelo T1.

- `algoritmos/first_follow.py` — FIRST e FOLLOW (§4.4.2)
- `algoritmos/lr0_items.py` — CLOSURE, GOTO e coleção canônica LR(0) (Fig. 4.32/4.33)
- `algoritmos/slr_table.py` — tabela ACTION/GOTO (Alg. 4.46); detecta e reporta conflitos
- `algoritmos/lr_parser.py` — parser LR com construção da árvore de derivação (Alg. 4.44)

### Formato da gramática

Uma produção por linha com `::=`; alternativas com `|`. O primeiro não terminal
vira o símbolo inicial; epsilon é `&`.

```
E ::= E + T | T
T ::= T * F | F
F ::= ( E ) | id
```

### Executando

```bash
cd "src/Gerador de Analisadores Sintáticos"

# só a gramática — itens LR(0), FIRST/FOLLOW, tabela SLR
python3 main.py tests/gramaticas/expressao.txt

# com lista de tokens — análise + árvore + tabela de símbolos
python3 main.py tests/gramaticas/expressao.txt tests/tokens/expr_ok.txt
python3 main.py tests/gramaticas/aritmetica_estendida.txt tests/tokens/aritmetica_ok.txt

# com palavras reservadas
python3 main.py tests/gramaticas/comandos.txt tests/tokens/comandos_ok.txt \
        -r tests/reservadas/comandos_reservadas.txt
python3 main.py tests/gramaticas/blocos.txt tests/tokens/blocos_ok.txt \
        -r tests/reservadas/blocos_reservadas.txt

# gramática com conflito (dangling-else)
python3 main.py tests/gramaticas/dangling_else.txt

# salvar relatório
python3 main.py tests/gramaticas/comandos.txt tests/tokens/comandos_ok.txt \
        -r tests/reservadas/comandos_reservadas.txt -o relatorio.txt
```

### Testes

```bash
cd "src/Gerador de Analisadores Sintáticos"
python3 tests/run_tests.py
# 53/53
```

---

## Integração

Interface gráfica em PyQt6 que roda o pipeline completo e exibe cada etapa em
abas separadas (AFDs, tabela léxica, tokens, tabela SLR, árvore de derivação).
Gramáticas não SLR(1) mostram um aviso com os conflitos detectados.

```bash
pip install -r src/integracao/requirements.txt
python3 src/integracao/controller.py
```

Sem interface, a suíte de integração roda em modo texto:

```bash
python3 src/integracao/tests/run_tests.py
# 11/11
```

---

## Rodando tudo

```bash
cd "src/Gerador de Analisadores Léxicos"   && python3 tests/run_tests.py   ; cd ../..
cd "src/Gerador de Analisadores Sintáticos" && python3 tests/run_tests.py   ; cd ../..
python3 src/integracao/tests/run_tests.py
```
