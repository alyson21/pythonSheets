"""Janela principal do app de automações. Cada módulo vira uma aba do Notebook."""

import tkinter as tk
from tkinter import ttk

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

    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True)

    for ModuloPanel in MODULOS:
        panel = ModuloPanel(notebook)
        notebook.add(panel, text=ModuloPanel.NOME)

    root.mainloop()
