# INE5421
Trabalho da disciplina de Linguagens Formais e Compiladores

## Trabalho 1 - Gerador de Analisadores Léxicos

Implementação em Python puro em
[src/Gerador de Analisadores Léxicos/](src/Gerador%20de%20Analisadores%20L%C3%A9xicos/).
Instruções de uso em
[HOWTO.md](src/Gerador%20de%20Analisadores%20L%C3%A9xicos/HOWTO.md).

## Trabalho 2 - Gerador de Analisadores Sintáticos (SLR)

Implementação em Python puro em
[src/Gerador de Analisadores Sintáticos/](src/Gerador%20de%20Analisadores%20Sint%C3%A1ticos/).
Instruções de uso em
[HOWTO.md](src/Gerador%20de%20Analisadores%20Sint%C3%A1ticos/HOWTO.md).

## Integração (Trabalho 1 + Trabalho 2)

Interface gráfica em PyQt6 que executa o pipeline completo (léxico → integração →
sintático) sobre os exemplos em
[src/integracao/exemplos/](src/integracao/exemplos/), exibindo todas as etapas:
lista de tokens, tabela SLR (ACTION/GOTO), resultado da análise e a árvore de
derivação.

```bash
pip install -r src/integracao/requirements.txt
python3 src/integracao/controller.py
```

Sem interface gráfica, a suíte de testes de integração roda em modo texto (um
único arquivo executa o caso embutido e todos os exemplos de ponta a ponta):

```bash
python3 src/integracao/tests/run_tests.py
```