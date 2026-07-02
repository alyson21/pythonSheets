# Gerar Instalador Windows no Ubuntu

Este projeto gera `dist/instalador.exe` no Ubuntu usando NSIS. No Windows, esse instalador cria o executavel final da aplicacao na mesma pasta onde ele foi aberto.

Fluxo:

1. No Ubuntu, rode `./GerarSFXUbuntu.sh`.
2. O script le o projeto atual e cria `dist/instalador.exe`.
3. No Windows, abra `instalador.exe`.
4. O instalador extrai os arquivos temporariamente e executa `instalador.bat`.
5. Se o Windows nao tiver Python, o `instalador.bat` baixa e instala automaticamente.
6. O `automacao.exe` e salvo na mesma pasta do `instalador.exe`.
7. A pasta `dados` de runtime e sincronizada em `%LOCALAPPDATA%\AutomacaoPlanilhas\dados`.
8. Ao final com sucesso, o `instalador.exe` e removido automaticamente.

## Pre-requisitos no Ubuntu

- `python3`
- internet na primeira execucao caso `makensis` nao esteja instalado

O script usa `makensis`. Se ele nao existir no sistema, o build baixa os pacotes `nsis` e `nsis-common` com `apt-get download` e extrai tudo localmente em:

```text
tools/nsis-local/
```

Isso nao instala nada no sistema e nao precisa de `sudo`.

## Gerar o instalador

Na raiz do projeto, rode:

```bash
./GerarSFXUbuntu.sh
```

Saida final:

```text
dist/instalador.exe
```

## Conteudo incluido no pacote

```text
instalador.bat
app/main.py
app/requirements.txt
app/GerarExe.bat
app/automacao/
app/dados/
```

## Itens excluidos

```text
.git
.env
.env.*
node_modules
venv
.venv
__pycache__
build
dist
dist-package
*.spec
*.log
*.sqlite
*.sqlite3
*.db
*.pyc
*.pyo
```

## Como testar no Windows

1. Copie `dist/instalador.exe` para uma pasta no Windows.
2. De duplo clique no `instalador.exe`.
3. Ao finalizar, deve restar `automacao.exe` nessa mesma pasta.
4. O `instalador.exe` deve ser removido automaticamente.

## Debug

Se algo falhar no Windows, veja:

```text
%TEMP%\AutomacaoInstalador\instalador.log
```

No Windows, o primeiro uso tambem precisa de internet caso seja necessario baixar o instalador do Python.

## Observacao

O instalador nao atualiza sozinho depois de gerado. Quando mudar o projeto, rode `./GerarSFXUbuntu.sh` de novo para criar um novo `dist/instalador.exe`.
