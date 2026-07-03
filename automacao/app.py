"""Janela principal do app de automações. Cada módulo vira uma aba do Notebook."""

import threading
import tkinter as tk
from tkinter import messagebox, ttk

from automacao import updater
from automacao.apuracao import ApuracaoPanel
from automacao.premmia import PremmiaPanel
from automacao.santander_postos import SantanderPostosPanel

MODULOS = [
    SantanderPostosPanel,
    ApuracaoPanel,
    PremmiaPanel,
]


def run():
    root = tk.Tk()
    root.title("Automação")
    root.minsize(660, 560)

    _montar_header(root)

    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True)

    for ModuloPanel in MODULOS:
        panel = ModuloPanel(notebook)
        notebook.add(panel, text=ModuloPanel.NOME)

    root.mainloop()


# ── header com versão + botão Atualizar ──────────────────────────────────────

def _montar_header(root):
    header = tk.Frame(root, bd=1, relief="groove")
    header.pack(fill="x", side="top")

    tk.Label(header, text="Automação Factus", font=("", 11, "bold")).pack(
        side="left", padx=10, pady=6)
    tk.Label(header, text=f"v {updater.versao_curta(updater.versao_atual())}",
             fg="gray").pack(side="left")

    btn = tk.Button(header, text="⟳  Atualizar")
    btn.configure(command=lambda: _checar_update(root, btn))
    btn.pack(side="right", padx=10, pady=6)


def _checar_update(root, btn):
    btn.configure(state="disabled", text="Verificando...")

    def reset():
        btn.configure(state="normal", text="⟳  Atualizar")

    def work():
        try:
            tem, rel = updater.ha_atualizacao()
        except Exception as e:
            root.after(0, lambda: (
                messagebox.showerror("Atualização", f"Não foi possível verificar:\n{e}"),
                reset()))
            return
        if not tem:
            root.after(0, lambda: (
                messagebox.showinfo("Atualização", "Você já está na versão mais recente."),
                reset()))
            return
        root.after(0, lambda: _oferecer(root, btn, rel, reset))

    threading.Thread(target=work, daemon=True).start()


def _oferecer(root, btn, rel, reset):
    versao = updater.versao_curta(rel.versao)

    if not updater.modo_exe():
        messagebox.showinfo(
            "Atualização",
            f"Nova versão disponível ({versao}).\n\n"
            "Este app está em modo desenvolvimento — atualize com 'git pull'.")
        reset()
        return

    if not messagebox.askyesno(
            "Atualização",
            f"Nova versão disponível ({versao}).\n\n"
            "Baixar e reiniciar o aplicativo agora?"):
        reset()
        return

    _baixar(root, rel, reset)


def _baixar(root, rel, reset):
    win = tk.Toplevel(root)
    win.title("Atualizando")
    win.transient(root)
    win.resizable(False, False)
    tk.Label(win, text="Baixando atualização...").pack(padx=20, pady=(16, 6))
    barra = ttk.Progressbar(win, length=280, mode="determinate", maximum=1.0)
    barra.pack(padx=20, pady=(0, 16))

    def progresso(frac):
        root.after(0, lambda: barra.configure(value=frac))

    def work():
        try:
            destino = updater.destino_novo_exe()
            updater.baixar_exe(rel.url_exe, destino, progresso=progresso)
            updater.aplicar_e_reiniciar(destino)
            root.after(0, root.destroy)  # fecha; o .bat troca o .exe e reabre
        except Exception as e:
            root.after(0, lambda: (
                win.destroy(),
                messagebox.showerror("Atualização", f"Falha ao atualizar:\n{e}"),
                reset()))

    threading.Thread(target=work, daemon=True).start()
