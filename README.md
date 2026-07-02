# Automação de Planilhas

Sistema desktop em Python para executar automações de planilhas Excel.

## Estrutura do projeto

```text
.
├── main.py                  # Entrada do sistema
├── automacao/               # Código Python da aplicação
│   ├── app.py               # Janela principal e abas
│   ├── caminhos.py          # Caminhos do projeto e da pasta dados
│   ├── excel.py             # Funções compartilhadas de Excel
│   ├── santander_postos.py  # Automação Santander Postos
│   └── premmia.py           # Automação Premmia
├── dados/                   # Planilhas modelo, brutas e dados de runtime
├── scripts/                 # Scripts de empacotamento
├── GerarExe.bat             # Gera automacao.exe no Windows
├── GerarSFXUbuntu.sh        # Gera dist/instalador.exe no Ubuntu
└── instalador.bat           # Script executado pelo instalador no Windows
```

## Rodar em desenvolvimento

```bash
python3 main.py
```

No Windows:

```bat
python main.py
```

## Gerar instalador Windows pelo Ubuntu

```bash
./GerarSFXUbuntu.sh
```

O instalador final fica em:

```text
dist/instalador.exe
```

## Como adicionar uma nova automação

1. Crie um arquivo novo em `automacao/`, por exemplo `minha_automacao.py`.
2. Coloque nele as regras de planilha e a classe da tela.
3. A classe da tela deve ter um atributo `NOME`.
4. Importe a classe em `automacao/app.py`.
5. Adicione a classe na lista `MODULOS`.
6. Rode `python3 -m compileall main.py automacao`.
7. Teste manualmente pelo sistema.
