"""Janela principal do app de automações. Cada módulo vira uma aba do Notebook."""

import queue
import threading
import tkinter as tk
from tkinter import messagebox, ttk

from automacao import log, updater
from automacao.apuracao import ApuracaoPanel
from automacao.premmia import PremmiaPanel
from automacao.santander_postos import SantanderPostosPanel

MODULOS = [
    SantanderPostosPanel,
    ApuracaoPanel,
    PremmiaPanel,
]

# tempo máximo, em ms, para a verificação de atualização antes de destravar o botão
TIMEOUT_VERIFICACAO_MS = 30000


def run():
    logger = log.instalar()
    # confirma para o updater que esta versão subiu (habilita rollback se não subir)
    if updater.modo_exe():
        updater.marcar_boot_ok()

    root = tk.Tk()
    root.title("Automação")
    root.minsize(660, 560)
    log.instalar_tk(root)
    logger.info("App iniciado (build %s)", updater.versao_curta(updater.versao_atual()))

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
    tk.Label(header, text=f"build {updater.versao_curta(updater.versao_atual())}",
             fg="#555", font=("", 9, "bold")).pack(side="left", pady=6)

    btn = tk.Button(header, text="⟳  Atualizar")
    btn.pack(side="right", padx=10, pady=6)
    # mantém o gerenciador vivo (evita coleta de lixo) e liga o botão
    root._atualizador = _Atualizador(root, btn)
    btn.configure(command=root._atualizador.iniciar)


class _Atualizador:
    """Gerencia a verificação/baixa de atualização sem tocar no Tk fora da main thread.

    A thread de trabalho só coloca mensagens numa fila; a interface faz polling
    dessa fila via root.after. Um watchdog destrava o botão se a rede não responder.
    """

    def __init__(self, root, btn):
        self.root = root
        self.btn = btn
        self.fila = queue.Queue()
        self.geracao = 0  # invalida trabalhos antigos (ex.: após timeout)

    # ── verificação ──
    def iniciar(self):
        self.geracao += 1
        g = self.geracao
        self.btn.configure(state="disabled", text="Verificando...")
        threading.Thread(target=self._verificar, args=(g,), daemon=True).start()
        self.root.after(100, lambda: self._poll_verificacao(g))
        self.root.after(TIMEOUT_VERIFICACAO_MS, lambda: self._watchdog(g))

    def _verificar(self, g):
        try:
            tem, rel = updater.ha_atualizacao()
            self.fila.put((g, "ok", (tem, rel)))
        except Exception as e:
            self.fila.put((g, "erro", str(e)))

    def _poll_verificacao(self, g):
        if g != self.geracao:
            return
        try:
            _, tipo, payload = self.fila.get_nowait()
        except queue.Empty:
            self.root.after(150, lambda: self._poll_verificacao(g))
            return

        if tipo == "erro":
            self._reset()
            messagebox.showerror("Atualização", f"Não foi possível verificar:\n{payload}")
            return

        tem, rel = payload
        if not tem:
            self._reset()
            messagebox.showinfo("Atualização", "Você já está na versão mais recente.")
        else:
            self._oferecer(rel)

    def _watchdog(self, g):
        # se ainda estamos nesta geração e o botão continua travado, a rede não respondeu
        if g == self.geracao and str(self.btn["state"]) == "disabled":
            self.geracao += 1  # ignora resultado que chegar atrasado
            self._reset()
            messagebox.showerror(
                "Atualização",
                "A verificação demorou demais.\nVerifique a conexão com a internet "
                "(ou se a rede bloqueia o acesso ao GitHub).")

    def _reset(self):
        self.btn.configure(state="normal", text="⟳  Atualizar")

    # ── oferta / download ──
    def _oferecer(self, rel):
        versao = updater.versao_curta(rel.versao)
        if not updater.modo_exe():
            self._reset()
            messagebox.showinfo(
                "Atualização",
                f"Nova versão disponível ({versao}).\n\n"
                "Este app está em modo desenvolvimento — atualize com 'git pull'.")
            return
        if not messagebox.askyesno(
                "Atualização",
                f"Nova versão disponível ({versao}).\n\n"
                "Baixar e reiniciar o aplicativo agora?"):
            self._reset()
            return
        self._baixar(rel)

    def _baixar(self, rel):
        g = self.geracao
        self.win = tk.Toplevel(self.root)
        self.win.title("Atualizando")
        self.win.transient(self.root)
        self.win.resizable(False, False)
        tk.Label(self.win, text="Baixando atualização...").pack(padx=20, pady=(16, 6))
        self.barra = ttk.Progressbar(self.win, length=280, mode="determinate", maximum=1.0)
        self.barra.pack(padx=20, pady=(0, 16))
        self.fila_dl = queue.Queue()

        threading.Thread(target=self._baixar_worker, args=(rel, g), daemon=True).start()
        self.root.after(100, lambda: self._poll_download(g))

    def _baixar_worker(self, rel, g):
        try:
            destino = updater.destino_novo_exe()
            updater.baixar_exe(rel.url_exe, destino,
                               progresso=lambda f: self.fila_dl.put((g, "prog", f)))
            self.fila_dl.put((g, "ok", None))
        except Exception as e:
            self.fila_dl.put((g, "erro", str(e)))

    def _poll_download(self, g):
        if g != self.geracao:
            return
        try:
            while True:
                _, tipo, val = self.fila_dl.get_nowait()
                if tipo == "prog":
                    self.barra.configure(value=val)
                elif tipo == "ok":
                    updater.aplicar_e_reiniciar(updater.destino_novo_exe())
                    self.root.destroy()  # fecha; o .bat troca o .exe e reabre
                    return
                elif tipo == "erro":
                    self.win.destroy()
                    self._reset()
                    messagebox.showerror("Atualização", f"Falha ao atualizar:\n{val}")
                    return
        except queue.Empty:
            pass
        self.root.after(100, lambda: self._poll_download(g))
