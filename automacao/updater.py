"""Auto-atualização do app a partir das Releases do GitHub.

Fluxo (apenas no modo .exe / PyInstaller):
  1. O usuário clica em "Atualizar".
  2. Consultamos a Release `latest` do repositório e comparamos o commit embutido
     no .exe atual (automacao/_version.py, gravado na compilação) com o da Release.
  3. Se houver versão nova, baixamos o novo automacao.exe ao lado do atual.
  4. Um .bat aguarda o app fechar, troca o .exe e reabre.

Nenhuma dependência extra: usa só a biblioteca padrão. A verificação TLS é mantida
ligada de propósito (um updater que baixa e executa .exe não pode aceitar MITM).
"""

from __future__ import annotations

import json
import os
import ssl
import subprocess
import sys
import urllib.request
from dataclasses import dataclass
from pathlib import Path


def _env_sem_pyinstaller() -> dict:
    """Ambiente sem as variáveis internas do PyInstaller onefile.

    O bootloader do exe atual define `_MEIPASS2`/`_PYI_*` apontando para a pasta
    temporária de extração dele. Se o processo filho (o .bat que reinicia o app)
    herdar essas variáveis, o exe novo acha que já foi extraído e tenta usar a
    pasta do processo antigo — que já foi apagada — resultando em
    'Failed to load Python DLL'. Por isso removemos essas chaves antes de lançar.
    """
    return {k: v for k, v in os.environ.items()
            if not k.startswith(("_MEIPASS", "_PYI", "_PYINSTALLER"))}


def _ssl_context() -> ssl.SSLContext:
    """Contexto TLS confiável mesmo com inspeção de HTTPS no Windows.

    Dois problemas aparecem no .exe (PyInstaller):
      - Sem CA bundle o Python gera 'unable to get local issuer certificate'.
      - Antivírus/proxy corporativo que inspeciona HTTPS re-assina o tráfego com
        um CA raiz próprio, gerando 'self-signed certificate in certificate
        chain' — esse CA só existe na store do Windows, não no certifi.

    Por isso preferimos o `truststore`, que usa a store nativa do SO (e portanto
    enxerga o CA da inspeção). Se indisponível, caímos no `certifi` e, por fim,
    no contexto padrão.
    """
    try:
        import truststore
        return truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    except Exception:
        pass
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()


_SSL = _ssl_context()

REPO = "alyson21/pythonSheets"
API_RELEASE = f"https://api.github.com/repos/{REPO}/releases/tags/latest"
EXE_ASSET = "automacao.exe"
NOVO_EXE = "automacao.new.exe"
BAT_UPDATE = "_update.bat"
FLAG_BOOT = "update_ok.flag"   # o app cria ao subir; o updater confirma a troca por ela
TIMEOUT = 15
_HEADERS = {"User-Agent": "automacao-updater", "Accept": "application/vnd.github+json"}


@dataclass
class ReleaseInfo:
    versao: str          # commit SHA publicado na Release
    url_exe: str         # link de download do automacao.exe
    nome: str            # nome/título da release (informativo)


def modo_exe() -> bool:
    """True quando rodando como .exe empacotado (PyInstaller)."""
    return getattr(sys, "frozen", False)


def versao_atual() -> str:
    try:
        from automacao._version import VERSION
        return (VERSION or "dev").strip()
    except Exception:
        return "dev"


def versao_curta(v: str) -> str:
    return v[:7] if v and v != "dev" else (v or "dev")


def _get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers=_HEADERS)
    with urllib.request.urlopen(req, timeout=TIMEOUT, context=_SSL) as resp:
        return json.loads(resp.read().decode("utf-8"))


def buscar_release() -> ReleaseInfo | None:
    """Consulta a Release `latest`. Retorna None se não houver .exe publicado."""
    data = _get_json(API_RELEASE)
    versao = (data.get("body") or data.get("tag_name") or "").strip()
    url = None
    for asset in data.get("assets", []):
        if asset.get("name") == EXE_ASSET:
            url = asset.get("browser_download_url")
            break
    if not url:
        return None
    return ReleaseInfo(versao=versao, url_exe=url, nome=(data.get("name") or "").strip())


def ha_atualizacao() -> tuple[bool, ReleaseInfo | None]:
    """(tem_update, info). Pode levantar exceção de rede."""
    rel = buscar_release()
    if rel is None or not rel.versao:
        return False, rel
    return rel.versao != versao_atual(), rel


def baixar_exe(url: str, destino: Path, progresso=None) -> None:
    """Baixa o .exe para `destino`, validando a integridade.

    Baixa para um arquivo `.part`, confere que veio inteiro (tamanho declarado)
    e que é mesmo um executável (cabeçalho 'MZ'), e só então promove para
    `destino`. Assim um download truncado nunca vira o exe trocado pelo .bat
    (o que dá 'Failed to load Python DLL' ao abrir).
    """
    parcial = destino.with_name(destino.name + ".part")
    req = urllib.request.Request(url, headers={"User-Agent": "automacao-updater"})
    with urllib.request.urlopen(req, timeout=TIMEOUT, context=_SSL) as resp:
        total = int(resp.headers.get("Content-Length", 0))
        baixado = 0
        with open(parcial, "wb") as fh:
            while True:
                chunk = resp.read(65536)
                if not chunk:
                    break
                fh.write(chunk)
                baixado += len(chunk)
                if progresso and total:
                    progresso(baixado / total)

    if total and baixado != total:
        parcial.unlink(missing_ok=True)
        raise IOError(f"download incompleto: {baixado} de {total} bytes")
    with open(parcial, "rb") as fh:
        if fh.read(2) != b"MZ":
            parcial.unlink(missing_ok=True)
            raise IOError("arquivo baixado não é um executável válido")

    os.replace(parcial, destino)
    if progresso:
        progresso(1.0)


def flag_boot() -> Path:
    return Path(sys.executable).parent / FLAG_BOOT


def marcar_boot_ok() -> None:
    """O app chama isto ao subir; o updater usa a flag para confirmar a troca."""
    try:
        flag_boot().write_text("ok", encoding="ascii")
    except Exception:
        pass


def aplicar_e_reiniciar(novo_exe: Path) -> None:
    """Agenda a troca do .exe (via .bat) e deixa o app fechar em seguida.

    Robustez do .bat:
      - `set "_..."` limpa as variáveis do PyInstaller herdadas, senão o exe
        reaberto tenta extrair da pasta temp do processo antigo (ver
        _env_sem_pyinstaller) e falha com 'Failed to load Python DLL'.
      - guarda um backup do exe atual antes de sobrescrever;
      - só sobrescreve quando o app fecha (o overwrite de um exe em uso falha);
      - reabre e espera a flag de boot; se ela não aparecer (o novo não subiu),
        restaura o backup e reabre a versão anterior — rollback automático.
    """
    atual = Path(sys.executable)
    backup = atual.with_name(f"{atual.stem}.bak{atual.suffix}")
    flag = flag_boot()
    bat = atual.parent / BAT_UPDATE
    script = (
        "@echo off\r\n"
        "setlocal\r\n"
        'set "_MEIPASS2="\r\n'
        'set "_PYI_APPLICATION_HOME_DIR="\r\n'
        'set "_PYI_ARCHIVE_FILE="\r\n'
        'set "_PYI_PARENT_PROCESS_LEVEL="\r\n'
        f'set "ALVO={atual}"\r\n'
        f'set "NOVO={novo_exe}"\r\n'
        f'set "BACKUP={backup}"\r\n'
        f'set "FLAG={flag}"\r\n'
        'copy /y "%ALVO%" "%BACKUP%" >nul 2>&1\r\n'
        ":wait\r\n"
        "timeout /t 1 /nobreak >nul\r\n"
        'move /y "%NOVO%" "%ALVO%" >nul 2>&1\r\n'
        "if errorlevel 1 goto wait\r\n"
        'del "%FLAG%" >nul 2>&1\r\n'
        "timeout /t 1 /nobreak >nul\r\n"
        'start "" "%ALVO%"\r\n'
        "set /a t=0\r\n"
        ":check\r\n"
        "timeout /t 2 /nobreak >nul\r\n"
        'if exist "%FLAG%" goto ok\r\n'
        "set /a t+=1\r\n"
        "if %t% lss 10 goto check\r\n"
        'copy /y "%BACKUP%" "%ALVO%" >nul 2>&1\r\n'
        'del "%FLAG%" >nul 2>&1\r\n'
        'start "" "%ALVO%"\r\n'
        "goto fim\r\n"
        ":ok\r\n"
        'del "%BACKUP%" >nul 2>&1\r\n'
        ":fim\r\n"
        'del "%~f0"\r\n'
    )
    bat.write_text(script, encoding="ascii")
    CREATE_NO_WINDOW = 0x08000000
    subprocess.Popen(["cmd", "/c", str(bat)], creationflags=CREATE_NO_WINDOW,
                     close_fds=True, env=_env_sem_pyinstaller())


def destino_novo_exe() -> Path:
    return Path(sys.executable).parent / NOVO_EXE
