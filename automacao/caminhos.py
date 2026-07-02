"""Caminhos base do projeto. Ajusta-se automaticamente quando empacotado com PyInstaller."""

import os
import sys
from pathlib import Path

if getattr(sys, "frozen", False):
    PROJECT_ROOT = Path(sys.executable).resolve().parent
    _local_appdata = os.environ.get("LOCALAPPDATA")
    _runtime_root = Path(_local_appdata) / "AutomacaoPlanilhas" if _local_appdata else PROJECT_ROOT
    DADOS = _runtime_root / "dados"
    if not DADOS.exists():
        DADOS = PROJECT_ROOT / "dados"
else:
    PROJECT_ROOT = Path(__file__).resolve().parents[1]
    DADOS = PROJECT_ROOT / "dados"
