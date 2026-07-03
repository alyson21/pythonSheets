# Automação de Planilhas

Sistema desktop em Python para executar automações de planilhas Excel.

## Estrutura do projeto

```text
.
├── main.py                  # Entrada do sistema
├── automacao/               # Código Python da aplicação
│   ├── app.py               # Janela principal, abas e botão Atualizar
│   ├── caminhos.py          # Caminhos do projeto e da pasta dados
│   ├── excel.py             # Funções compartilhadas de Excel
│   ├── updater.py           # Auto-atualização a partir das Releases do GitHub
│   ├── santander_postos.py  # Automação Santander Postos
│   ├── apuracao.py          # Automação Apuração (notas SIEG por cliente)
│   └── premmia.py           # Automação Premmia
├── dados/                   # Planilhas modelo, brutas e dados de runtime
├── GerarExe.bat             # Gera automacao.exe no Windows
└── .github/workflows/       # CI: compila o .exe e publica na Release "latest"
```

## Rodar em desenvolvimento

```bash
python3 main.py
```

No Windows:

```bat
python main.py
```

## Distribuição

O `.exe` é compilado automaticamente pelo GitHub Actions a cada push no `main`
e publicado na Release `latest`. O link estável para a última versão é:

```text
https://github.com/alyson21/pythonSheets/releases/latest/download/automacao.exe
```

É um executável portátil (roda direto, sem instalar Python). A partir da segunda
versão, o próprio app se atualiza pelo botão **Atualizar** no canto superior.

Para compilar manualmente no Windows: `GerarExe.bat`.

## Identidade visual

A paleta e a marca ficam em `automacao/tema.py` (símbolo desenhado por vetores,
sem depender de arquivo de imagem). Na abertura aparece um **loading** com a
marca Factus, e o `.exe` mostra ainda o splash nativo do PyInstaller durante a
extração (imagem `automacao/assets/factus_splash.png`, passada em `--splash`).

Para regenerar o PNG do splash após mexer nas cores/marca (requer Pillow, só em
dev): `python tools/gerar_assets.py`.

## Como adicionar uma nova automação

1. Crie um arquivo novo em `automacao/`, por exemplo `minha_automacao.py`.
2. Coloque nele as regras de planilha e a classe da tela.
3. A classe da tela deve ter um atributo `NOME`.
4. Em `automacao/app.py`, importe a classe dentro de `_construir` e adicione-a
   à tupla de painéis passada para `_montar_ui`.
5. Rode `python3 -m compileall main.py automacao` e `python3 -m pytest -q`.
6. Teste manualmente pelo sistema.
