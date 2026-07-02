#!/usr/bin/env python3
"""Build a Windows installer from Linux/Ubuntu using NSIS."""

from __future__ import annotations

import argparse
import fnmatch
import os
import shutil
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DIST_PACKAGE = PROJECT_ROOT / "dist-package"
DIST_DIR = PROJECT_ROOT / "dist"
APP_DIR = DIST_PACKAGE / "app"
TOOLS_DIR = PROJECT_ROOT / "tools"
NSIS_LOCAL = TOOLS_DIR / "nsis-local"
NSIS_DEB_DIR = TOOLS_DIR / "nsis-deb"

PACKAGE_NAME = "AutomacaoPlanilhas"
OUTPUT_NAME = "instalador.exe"
OUTPUT_EXE_PATH = DIST_DIR / OUTPUT_NAME
NSI_PATH = DIST_DIR / f"{PACKAGE_NAME}.nsi"
OLD_7Z_ARCHIVE = DIST_DIR / f"{PACKAGE_NAME}.7z"
OLD_7Z_CONFIG = DIST_DIR / f"{PACKAGE_NAME}.sfx.config"

REQUIRED_ITEMS = [
    "main.py",
    "requirements.txt",
    "GerarExe.bat",
    "instalador.bat",
    "automacao",
    "dados",
]

INCLUDED_IN_APP = [
    "main.py",
    "requirements.txt",
    "GerarExe.bat",
    "automacao",
    "dados",
]

EXCLUDED_DIR_NAMES = {
    ".git",
    "node_modules",
    "venv",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "dist-package",
    "formatados",
}

EXCLUDED_FILE_PATTERNS = [
    ".env",
    ".env.*",
    "*.spec",
    "*.log",
    "*.sqlite",
    "*.sqlite3",
    "*.db",
    ".~lock.*#",
    "*.pyc",
    "*.pyo",
]


def fail(message: str) -> None:
    raise RuntimeError(f"ERRO: {message}")


def run(command: list[str], cwd: Path | None = None, env: dict[str, str] | None = None) -> None:
    printable = " ".join(command)
    print(f"> {printable}")
    completed = subprocess.run(command, cwd=cwd, env=env)
    if completed.returncode != 0:
        fail(f"comando falhou com codigo {completed.returncode}: {printable}")


def command_path(name: str) -> str | None:
    return shutil.which(name)


def is_excluded(path: Path) -> bool:
    relative_parts = path.relative_to(PROJECT_ROOT).parts
    if any(part in EXCLUDED_DIR_NAMES for part in relative_parts):
        return True

    return any(fnmatch.fnmatch(path.name, pattern) for pattern in EXCLUDED_FILE_PATTERNS)


def validate_required_items() -> None:
    print("Validando arquivos obrigatorios...")
    for relative_path in REQUIRED_ITEMS:
        path = PROJECT_ROOT / relative_path
        if not path.exists():
            fail(f"item obrigatorio nao encontrado: {relative_path}")


def clean_old_build() -> None:
    print("Limpando builds antigos...")
    if DIST_PACKAGE.exists():
        shutil.rmtree(DIST_PACKAGE)

    for path in [OUTPUT_EXE_PATH, NSI_PATH, OLD_7Z_ARCHIVE, OLD_7Z_CONFIG]:
        if path.exists():
            path.unlink()

    APP_DIR.mkdir(parents=True, exist_ok=True)
    DIST_DIR.mkdir(parents=True, exist_ok=True)


def copy_project_item(relative_path: str, target_root: Path) -> None:
    source = PROJECT_ROOT / relative_path
    target = target_root / relative_path

    if source.is_dir():
        for item in source.rglob("*"):
            if is_excluded(item):
                continue

            destination = target / item.relative_to(source)
            if item.is_dir():
                destination.mkdir(parents=True, exist_ok=True)
            elif item.is_file():
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, destination)
        return

    if is_excluded(source):
        return

    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def write_package_contents() -> None:
    contents = [
        "INCLUIDOS:",
        "instalador.bat",
        "app/main.py",
        "app/requirements.txt",
        "app/GerarExe.bat",
        "app/automacao/",
        "app/dados/",
        "",
        "EXCLUIDOS:",
    ]
    contents.extend(f"- {item}" for item in sorted(EXCLUDED_DIR_NAMES))
    contents.extend(f"- {pattern}" for pattern in EXCLUDED_FILE_PATTERNS)

    (DIST_PACKAGE / "PACKAGE-CONTENTS.txt").write_text(
        "\n".join(contents) + "\n",
        encoding="utf-8",
    )


def prepare_dist_package() -> None:
    print("Copiando arquivos permitidos para dist-package...")
    shutil.copy2(PROJECT_ROOT / "instalador.bat", DIST_PACKAGE / "instalador.bat")

    for item in INCLUDED_IN_APP:
        copy_project_item(item, APP_DIR)

    write_package_contents()


def ensure_local_nsis() -> tuple[str, Path | None]:
    system_makensis = command_path("makensis")
    if system_makensis:
        return system_makensis, None

    local_makensis = NSIS_LOCAL / "usr" / "bin" / "makensis"
    local_share = NSIS_LOCAL / "usr" / "share" / "nsis"
    if local_makensis.exists() and local_share.exists():
        return str(local_makensis), local_share

    apt_get = command_path("apt-get")
    dpkg_deb = command_path("dpkg-deb")
    if not apt_get or not dpkg_deb:
        fail("makensis nao encontrado. Instale nsis ou disponibilize apt-get e dpkg-deb.")

    print("Baixando NSIS localmente para tools/nsis-local...")
    NSIS_DEB_DIR.mkdir(parents=True, exist_ok=True)
    run([apt_get, "download", "nsis"], cwd=NSIS_DEB_DIR)
    run([apt_get, "download", "nsis-common"], cwd=NSIS_DEB_DIR)

    if NSIS_LOCAL.exists():
        shutil.rmtree(NSIS_LOCAL)

    for deb in sorted(NSIS_DEB_DIR.glob("*.deb")):
        run([dpkg_deb, "-x", str(deb), str(NSIS_LOCAL)])

    if not local_makensis.exists() or not local_share.exists():
        fail("nao foi possivel preparar o NSIS local em tools/nsis-local.")

    return str(local_makensis), local_share


def nsis_escape(path: Path) -> str:
    return str(path).replace("\\", "\\\\").replace('"', '\\"')


def write_nsis_script() -> None:
    print("Gerando script NSIS...")
    source_root = nsis_escape(DIST_PACKAGE)
    output_path = nsis_escape(OUTPUT_EXE_PATH)
    nsi = f"""
Unicode true
SilentInstall silent
RequestExecutionLevel user
SetCompressor /SOLID lzma
Name "{PACKAGE_NAME}"
OutFile "{output_path}"

Section
  InitPluginsDir
  SetOutPath "$PLUGINSDIR"
  File /r "{source_root}/*"
  ExecWait '"$PLUGINSDIR\\instalador.bat" "$EXEDIR\\{OUTPUT_NAME}"' $0
  SetErrorLevel $0
SectionEnd
""".lstrip()
    NSI_PATH.write_text(nsi, encoding="utf-8")


def build_installer(makensis: str, nsis_share: Path | None) -> None:
    print("Compilando instalador Windows com NSIS...")
    env = None
    if nsis_share:
        env = {**os.environ, "NSISDIR": str(nsis_share)}
    run([makensis, str(NSI_PATH)], env=env)

    if not OUTPUT_EXE_PATH.exists():
        fail("executavel final nao foi criado.")

    if OUTPUT_EXE_PATH.read_bytes()[:2] != b"MZ":
        fail("executavel final nao tem assinatura Windows PE.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Gera dist/instalador.exe no Ubuntu para rodar no Windows."
    )
    parser.add_argument(
        "--no-download-nsis",
        action="store_true",
        help="Falha se makensis nao estiver instalado/localmente disponivel.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        if args.no_download_nsis and not command_path("makensis"):
            local_makensis = NSIS_LOCAL / "usr" / "bin" / "makensis"
            if not local_makensis.exists():
                fail("makensis nao encontrado e --no-download-nsis foi usado.")

        validate_required_items()
        makensis, nsis_share = ensure_local_nsis()
        clean_old_build()
        prepare_dist_package()
        write_nsis_script()
        build_installer(makensis, nsis_share)
    except Exception as exc:
        print(exc, file=sys.stderr)
        return 1

    print()
    print("Pacote criado com sucesso:")
    print(OUTPUT_EXE_PATH)
    print()
    print("Estrutura temporaria:")
    print(DIST_PACKAGE)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
