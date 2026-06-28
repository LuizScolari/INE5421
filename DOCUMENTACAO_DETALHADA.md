# Documentacao -- INE5421 (T1 e T2)

Referencia: Aho, Lam, Sethi, Ullman -- *Compilers: Principles, Techniques, and
Tools*, 2a ed. Paginas referem-se a impressao.

---

## Trabalho 1 -- Gerador de Analisador Lexico

### (a) ER -> AFD -- `algoritmos/regex_to_dfa.py`

Implementa o **metodo direto** do Algoritmo 3.36 (Secao 3.9.5, p. 179). A expressao e
aumentada com `#`, transformada em arvore sintatica e anotada com as funcoes
`nullable`, `firstpos`, `lastpos` e `followpos` definidas na Figura 3.58 (p. 177).
O AFD e construido diretamente a partir de `firstpos(raiz)` usando `followpos`,
conforme a Figura 3.62 (p. 180). Os estados finais sao os que contem a posicao de `#`.

Os operadores `+`, `?` e as classes `[a-z]` sao abreviacoes da Secao 3.3.5 (p. 124) e
sao expandidos antes de montar a arvore: `r+ = r.r*`, `r? = r|&`,
`[a-c] = (a|b|c)`. Depois da expansao, a arvore usa so os cinco tipos de no
cobertos pela Figura 3.58.

A conversao infix->posfixa usa o algoritmo shunting-yard com a tabela de precedencia
`| < . < {*, +, ?}` (Secao 3.9.1 menciona que a arvore e construida como em expressoes
aritmeticas, Secao 2.5.1).

### (b) Minimizacao -- `algoritmos/minimization.py`

Implementa o Algoritmo 3.39 (Secao 3.9.6, p. 180-181). O AFD e completado com um estado
morto para tornar a funcao de transicao total, a particao inicial separa
`{finais, nao-finais}` e o refinamento segue a Figura 3.64 (p. 182). Ao final o
estado morto e eliminado conforme recomendado na mesma secao.

Para o analisador lexico, a particao inicial separa estados finais **por token**
(Secao 3.9.7, p. 184): *"group together all states that recognize a particular token"*.
Isso impede que estados de padroes diferentes sejam fundidos.

### (c) Uniao via epsilon -- `algoritmos/union.py`

Cria um novo estado inicial com epsilon-transicoes para o estado inicial de cada
automato, conforme Secao 3.8 e Figura 3.50 (p. 166-169). Os estados sao prefixados para
evitar colisoes. Cada automato mantem seus proprios estados finais com o rotulo do
token -- diferente da construcao de Thompson para `r1|r2` (Alg. 3.23), que une os
finais num unico estado, porque aqui e necessario distinguir qual padrao casou.

### (d) Determinizacao -- `algoritmos/determinization.py`

Implementa o Algoritmo 3.20 (Secao 3.7.1, p. 153): cada estado do AFD e um conjunto de
estados do AFND fechado por epsilon-closure; as transicoes sao calculadas com
`epsilon-closure(move(T, a))`. Quando um subconjunto contem finais de padroes diferentes,
vence o token declarado primeiro no arquivo de definicoes -- regra da Secao 3.5.3 (p. 144)
e Secao 3.8.3 (p. 170): *"prefer the pattern listed first"*.

### Tokenizacao -- `tokenizer.py`

Aplica a tabela gerada ao texto fonte pela **regra do maior prefixo** (Secao 3.5.3,
p. 144, regra 1). A cada posicao, o AFD e simulado e o ultimo estado de aceitacao
visitado e memorizado; quando a simulacao trava, o lexema vai ate esse ponto -- nao
ate onde o automato parou. Tecnica descrita na Secao 3.8.3 (p. 170).

---

## Trabalho 2 -- Gerador de Analisador Sintatico SLR

### Gramatica aumentada -- `grammar.py`

A gramatica e aumentada com `S' -> S` como producao de indice 0, conforme Secao 4.6.2
(p. 242). Terminais sao todos os simbolos que nao aparecem a esquerda de nenhuma
producao.

### (a) FIRST e FOLLOW -- `algoritmos/first_follow.py`

Calcula FIRST e FOLLOW por ponto fixo seguindo as regras da Secao 4.4.2 (p. 220-222).
FIRST(X) e inicializado com `{X}` para terminais e vazio para nao-terminais; o laco
aplica as regras 1-3 ate estabilizar. FOLLOW e inicializado com `{$}` em FOLLOW(S')
e propagado pelas regras 1-3 ate o ponto fixo.

### (b/c) CLOSURE, GOTO e colecao canonica -- `algoritmos/lr0_items.py`

Um item LR(0) e o par `(indice_producao, posicao_do_ponto)`. CLOSURE e calculado
pela Figura 4.32 (p. 245): para cada item com o ponto antes de um nao-terminal B,
adiciona os itens iniciais de todas as producoes de B. GOTO segue a Figura 4.33
(p. 246): avanca o ponto sobre o simbolo e fecha o resultado. A colecao canonica
parte de `CLOSURE({[S'->·S]})` e expande por GOTO ate nao haver estados novos.

### (d) Parsing LR -- `algoritmos/lr_parser.py`

Implementa o Algoritmo 4.44 / Figura 4.36 (p. 248-251). A pilha guarda so estados
(nao pares simbolo/estado). Em cada passo: shift empilha o estado destino e avanca
a entrada; reduce desempilha `|beta|` estados, expoe o novo topo e empilha
`GOTO[topo, A]`; accept encerra. Producoes vazias nao desempilham nada e geram uma
folha `&` na arvore de derivacao.

### (e) Tabela SLR -- `algoritmos/slr_table.py`

Implementa o Algoritmo 4.46 (Secao 4.6.4, p. 252-253):

- **shift:** `[A->alfa·a·beta]` em Ii e `GOTO(Ii,a)=Ij` com `a` terminal -> `ACTION[i,a] = shift j`
- **reduce:** `[A->alfa·]` em Ii e `A != S'` -> `ACTION[i,a] = reduce A->alfa` para todo `a` em `FOLLOW(A)`
- **accept:** `[S'->S·]` em Ii -> `ACTION[i,$] = accept`
- **goto:** `GOTO(Ii,A) = Ij` para nao-terminais A -> `GOTO[i,A] = j`

Conflitos (celula com duas acoes distintas) sao registrados em vez de
silenciosamente sobrescritos. `SLRTable.is_slr()` retorna `True` se nao ha
conflitos. O enunciado do T2 chama essa tabela de "Algoritmo 4.38"; e a mesma
construcao, o numero muda entre edicoes.
