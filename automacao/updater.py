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
import subprocess
import sys
import urllib.request
from dataclasses import dataclass
from pathlib import Path

REPO = "alyson21/pythonSheets"
API_RELEASE = f"https://api.github.com/repos/{REPO}/releases/tags/latest"
EXE_ASSET = "automacao.exe"
NOVO_EXE = "automacao.new.exe"
BAT_UPDATE = "_update.bat"
TIMEOUT = 20
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
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
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
    """Baixa o .exe para `destino`. `progresso` recebe fração 0..1 (opcional)."""
    req = urllib.request.Request(url, headers={"User-Agent": "automacao-updater"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        total = int(resp.headers.get("Content-Length", 0))
        baixado = 0
        with open(destino, "wb") as fh:
            while True:
                chunk = resp.read(65536)
                if not chunk:
                    break
                fh.write(chunk)
                baixado += len(chunk)
                if progresso and total:
                    progresso(baixado / total)
    if progresso:
        progresso(1.0)


def aplicar_e_reiniciar(novo_exe: Path) -> None:
    """Agenda a troca do .exe (via .bat) e deixa o app fechar em seguida."""
    atual = Path(sys.executable)
    bat = atual.parent / BAT_UPDATE
    script = (
        "@echo off\r\n"
        "setlocal\r\n"
        f'set "ALVO={atual}"\r\n'
        f'set "NOVO={novo_exe}"\r\n'
        ":wait\r\n"
        "timeout /t 1 /nobreak >nul\r\n"
        'move /y "%NOVO%" "%ALVO%" >nul 2>&1\r\n'
        "if errorlevel 1 goto wait\r\n"
        'start "" "%ALVO%"\r\n'
        'del "%~f0"\r\n'
    )
    bat.write_text(script, encoding="ascii")
    CREATE_NO_WINDOW = 0x08000000
    subprocess.Popen(["cmd", "/c", str(bat)], creationflags=CREATE_NO_WINDOW,
                     close_fds=True)


def destino_novo_exe() -> Path:
    return Path(sys.executable).parent / NOVO_EXE
