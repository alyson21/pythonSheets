"""Identidade visual Factus: paleta, tema ttk, a marca desenhada e o splash.

A marca "F" é desenhada por vetores (retângulos) — nada de arquivo de imagem —
para funcionar sem tropeços no .exe onefile. A mesma especificação (`MARCA`) é
reaproveitada por tools/gerar_assets.py para gerar o PNG do splash nativo.
"""

from __future__ import annotations

import sys
import tkinter as tk
from pathlib import Path
from tkinter import ttk


def _dir_assets() -> Path:
    """Pasta de assets, tanto em dev quanto no .exe onefile (PyInstaller)."""
    if getattr(sys, "frozen", False):
        base = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
        return base / "automacao" / "assets"
    return Path(__file__).resolve().parent / "assets"


def asset(nome: str) -> Path:
    return _dir_assets() / nome


def imagem(nome: str) -> tk.PhotoImage | None:
    """Carrega um PNG dos assets como PhotoImage, ou None se faltar/falhar.

    Guarde a referência retornada (o Tk descarta a imagem se ela for coletada).
    """
    caminho = asset(nome)
    if not caminho.exists():
        return None
    try:
        return tk.PhotoImage(file=str(caminho))
    except tk.TclError:
        return None


_carregar_imagem = imagem  # alias interno


def aplicar_icone(root: tk.Tk) -> None:
    """Define o ícone da janela e da barra de tarefas (Factus, não a pena do Tk)."""
    try:  # Windows: agrupa na taskbar com ícone próprio, não o genérico do Python
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Factus.Automacoes")
    except Exception:
        pass
    ico = asset("factus.ico")
    if ico.exists():
        try:
            root.iconbitmap(default=str(ico))  # titlebar nítida no Windows
        except tk.TclError:
            pass
    img = imagem("factus_icon.png")
    if img is not None:
        try:
            root.iconphoto(True, img)
            root._icone = img  # mantém referência viva
        except tk.TclError:
            pass

# ── paleta (extraída do logo) ────────────────────────────────────────────────
NAVY = "#232946"       # fundo da marca (igual ao PNG oficial, p/ emendar sem costura)
NAVY_D = "#1B2038"     # navy mais escuro (texto sobre claro / sombras)
NAVY_L = "#343B60"     # navy claro (abas, hover)
ACCENT = "#8E9BD0"     # periwinkle do símbolo
ACCENT_L = "#C6CEEA"   # acento claro
LIGHT = "#D7DCEF"      # tom claro do símbolo
SURFACE = "#F4F6FB"    # área de trabalho
CARD = "#FFFFFF"
INK = "#23273B"        # texto sobre claro
MUTED = "#9AA3C0"      # texto secundário
ON_NAVY = "#EEF1F8"    # texto sobre navy

WORDMARK = ("Segoe UI", 30, "bold")   # cai para fonte padrão fora do Windows

# marca "F": retângulos em coordenadas normalizadas (0..1) da caixa + cor
MARCA = [
    (0.14, 0.06, 0.82, 0.28, LIGHT),    # braço superior
    (0.14, 0.06, 0.36, 0.94, LIGHT),    # haste
    (0.62, 0.06, 0.82, 0.28, ACCENT),   # ponta do braço (acento)
    (0.36, 0.42, 0.62, 0.60, ACCENT),   # braço do meio
]


def desenhar_marca(canvas: tk.Canvas, ox: float, oy: float, size: float) -> None:
    """Desenha o símbolo da Factus no canvas, caixa `size`x`size` a partir de (ox, oy)."""
    for x0, y0, x1, y1, cor in MARCA:
        canvas.create_rectangle(ox + x0 * size, oy + y0 * size,
                                ox + x1 * size, oy + y1 * size,
                                fill=cor, width=0)


# ── tema ─────────────────────────────────────────────────────────────────────

def aplicar(root: tk.Tk) -> None:
    """Aplica a paleta na janela e nos estilos ttk. Chamar logo após criar a raiz."""
    root.configure(bg=SURFACE)
    try:
        root.tk_setPalette(background=SURFACE, foreground=INK,
                           activeBackground=ACCENT_L, activeForeground=INK,
                           highlightBackground=SURFACE)
    except tk.TclError:
        pass

    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    style.configure("TNotebook", background=NAVY, borderwidth=0, tabmargins=(6, 6, 6, 0))
    style.configure("TNotebook.Tab", background=NAVY_L, foreground=ON_NAVY,
                    padding=(18, 9), borderwidth=0, font=("Segoe UI", 10))
    style.map("TNotebook.Tab",
              background=[("selected", SURFACE), ("active", NAVY)],
              foreground=[("selected", INK), ("active", ON_NAVY)])
    style.configure("Brand.Horizontal.TProgressbar",
                    troughcolor=NAVY_L, background=ACCENT, borderwidth=0)


# ── splash / loading ─────────────────────────────────────────────────────────

class Splash:
    """Janela de carregamento (sem bordas) com a marca Factus e barra animada."""

    def __init__(self, root: tk.Tk, w: int = 460, h: int = 280):
        self.root = root
        self.win = tk.Toplevel(root)
        self.win.overrideredirect(True)
        self.win.configure(bg=NAVY)
        sw, sh = self.win.winfo_screenwidth(), self.win.winfo_screenheight()
        self.win.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")

        cv = tk.Canvas(self.win, width=w, height=h, bg=NAVY, highlightthickness=0)
        cv.pack(fill="both", expand=True)
        # usa o mesmo PNG do splash nativo (deriva do logo oficial) se disponível;
        # senão, desenha a marca vetorial como fallback.
        self._img = _carregar_imagem("factus_splash.png")
        if self._img is not None:
            cv.create_image(w // 2, h // 2, image=self._img)
        else:
            cv.create_rectangle(0, 0, w, 6, fill=ACCENT, width=0)  # faixa de acento no topo
            desenhar_marca(cv, 66, 92, 92)
            cv.create_text(190, 118, text="Factus", fill=ON_NAVY, anchor="w", font=WORDMARK)
            cv.create_text(192, 158, text="Cont.", fill=MUTED, anchor="w", font=("Segoe UI", 13))
            cv.create_text(w // 2, 214, text="Carregando…", fill=MUTED, font=("Segoe UI", 10))

        self.bar = ttk.Progressbar(self.win, mode="indeterminate", length=320,
                                   style="Brand.Horizontal.TProgressbar")
        self.bar.place(x=(w - 320) // 2, y=234)
        self.bar.start(12)

        self.win.update_idletasks()
        self.win.update()

    def fechar(self) -> None:
        try:
            self.bar.stop()
            self.win.destroy()
        except tk.TclError:
            pass
