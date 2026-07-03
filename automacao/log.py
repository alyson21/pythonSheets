"""Logging em arquivo + captura de exceções não tratadas.

No .exe `--windowed` não há console: sem isto, uma exceção não tratada some sem
deixar rastro e o suporte vira adivinhação. `instalar()` liga o log em arquivo
(com rotação) e os hooks globais de exceção (thread + interpretador); depois de
criar a janela, `instalar_tk(root)` captura também erros de callbacks do Tk e
mostra uma mensagem amigável apontando o arquivo de log.

O log fica em `<runtime>/logs/app.log` — ao lado de `dados/`, portanto no
LOCALAPPDATA quando empacotado e na raiz do projeto (ignorada) em dev.
"""

from __future__ import annotations

import logging
import logging.handlers
import sys
import threading
from pathlib import Path

from automacao.caminhos import DADOS

LOGGER = "automacao"
_configurado = False


def diretorio_log() -> Path:
    d = DADOS.parent / "logs"
    d.mkdir(parents=True, exist_ok=True)
    return d


def caminho_log() -> Path:
    return diretorio_log() / "app.log"


def instalar() -> logging.Logger:
    """Configura o logger em arquivo e os hooks globais. Idempotente."""
    global _configurado
    logger = logging.getLogger(LOGGER)
    if _configurado:
        return logger

    logger.setLevel(logging.INFO)
    arquivo = logging.handlers.RotatingFileHandler(
        caminho_log(), maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    arquivo.setFormatter(logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s: %(message)s"))
    logger.addHandler(arquivo)
    if sys.stderr is not None:  # também no console em modo dev
        logger.addHandler(logging.StreamHandler())

    def _hook(exc_type, exc, tb):
        logger.critical("Exceção não tratada", exc_info=(exc_type, exc, tb))

    def _thread_hook(args):
        logger.critical("Exceção não tratada em thread",
                        exc_info=(args.exc_type, args.exc_value, args.exc_traceback))

    sys.excepthook = _hook
    threading.excepthook = _thread_hook

    _configurado = True
    logger.info("Logging iniciado (%s)", caminho_log())
    return logger


def instalar_tk(root) -> None:
    """Loga e mostra erros de callbacks do Tk em vez de deixá-los sumir."""
    from tkinter import messagebox
    logger = logging.getLogger(LOGGER)

    def _hook(exc, val, tb):
        logger.critical("Exceção em callback Tk", exc_info=(exc, val, tb))
        try:
            messagebox.showerror(
                "Erro inesperado",
                f"Ocorreu um erro inesperado:\n{val}\n\n"
                f"Detalhes registrados em:\n{caminho_log()}")
        except Exception:
            pass

    root.report_callback_exception = _hook
