# Curso Dev Junior: Operando o Sistema e Criando Novas Funcionalidades

## Objetivo

Ao final do curso, o dev junior deve conseguir operar o sistema, entender a
estrutura do projeto, corrigir falhas simples e criar uma nova automação de
planilhas seguindo o padrão atual.

## Módulo 1: Operação do sistema

- Abrir o sistema com `python main.py` ou pelo `automacao.exe`.
- Entender a tela principal e a organização por abas.
- Executar a aba `Santander Postos`.
- Executar a aba `Premmia`.
- Ler mensagens da área de log.
- Identificar erros comuns: arquivo aberto, aba inexistente, cabeçalho errado e modelo ausente.

## Módulo 2: Estrutura do projeto

- `main.py`: ponto de entrada.
- `automacao/app.py`: registra as abas do sistema.
- `automacao/caminhos.py`: resolve onde fica a pasta `dados`.
- `automacao/excel.py`: funções compartilhadas para Excel.
- `automacao/santander_postos.py`: automação existente que altera uma planilha final.
- `automacao/premmia.py`: automação existente que gera um arquivo por input.
- `dados/`: arquivos de entrada, modelos e planilhas finais.
- `scripts/`: empacotamento para Windows.

## Módulo 3: Fluxo de desenvolvimento

1. Entender a regra manual feita pelo usuário.
2. Separar entrada, processamento e saída.
3. Criar uma função pequena que leia a planilha.
4. Criar uma função que transforme os dados.
5. Criar uma função que grave a saída.
6. Criar a tela para selecionar arquivos e executar.
7. Registrar a nova tela em `automacao/app.py`.
8. Testar com uma planilha real de exemplo.

## Módulo 4: Criando uma nova automação

Use este esqueleto mental:

```python
class MinhaAutomacaoPanel(Frame):
    NOME = "Minha Automação"
```

A tela precisa ter:

- seleção dos arquivos necessários;
- botão `Executar`;
- área de log;
- validações antes de iniciar;
- execução em thread para não travar a janela.

A regra precisa ter:

- validação dos arquivos obrigatórios;
- validação de abas e cabeçalhos;
- mensagens de erro claras;
- geração de saída previsível;
- nenhum caminho absoluto fixo.

## Módulo 5: Testes mínimos

Antes de entregar uma mudança, rode:

```bash
python3 -m compileall main.py automacao
python3 -c "from automacao.app import MODULOS; print([m.NOME for m in MODULOS])"
```

Também teste pelo menos um arquivo real de exemplo e confira o resultado no
Excel ou LibreOffice.

## Módulo 6: Gerando instalador

No Ubuntu:

```bash
./GerarSFXUbuntu.sh
```

No Windows, rode o `dist/instalador.exe`. Ele deve gerar o `automacao.exe` na
mesma pasta e remover o instalador ao final.

## Projeto final do curso

Criar uma terceira aba de automação a partir de uma planilha bruta nova:

- documentar a regra manual;
- criar o arquivo em `automacao/`;
- registrar a tela em `automacao/app.py`;
- validar entrada e saída;
- gerar novo `dist/instalador.exe`;
- apresentar para outro dev explicando o fluxo.
