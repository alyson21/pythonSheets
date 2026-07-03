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

## Como adicionar uma nova automação

1. Crie um arquivo novo em `automacao/`, por exemplo `minha_automacao.py`.
2. Coloque nele as regras de planilha e a classe da tela.
3. A classe da tela deve ter um atributo `NOME`.
4. Importe a classe em `automacao/app.py`.
5. Adicione a classe na lista `MODULOS`.
6. Rode `python3 -m compileall main.py automacao`.
7. Teste manualmente pelo sistema.
