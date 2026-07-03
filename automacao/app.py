"""Janela principal do app de automações. Cada módulo vira uma aba do Notebook."""

import queue
import threading
import tkinter as tk
from tkinter import messagebox, ttk

from automacao import log, tema, updater

# tempo máximo, em ms, para a verificação de atualização antes de destravar o botão
TIMEOUT_VERIFICACAO_MS = 30000


def run():
    logger = log.instalar()
    # confirma para o updater que esta versão subiu (habilita rollback se não subir)
    if updater.modo_exe():
        updater.marcar_boot_ok()

    root = tk.Tk()
    root.withdraw()  # esconde até a UI estar montada; só a splash aparece
    root.title("Factus — Automações")
    root.minsize(680, 580)
    tema.aplicar(root)
    log.instalar_tk(root)

    splash = tema.Splash(root)
    # fecha o splash nativo do PyInstaller (mostrado durante a extração do onefile)
    try:
        import pyi_splash
        pyi_splash.close()
    except Exception:
        pass

    # os imports pesados (openpyxl, via painéis) só acontecem depois que a splash
    # já está na tela, para o carregamento não parecer travado.
    root.after(30, lambda: _construir(root, splash, logger))
    root.mainloop()


def _construir(root, splash, logger):
    """Importa os painéis fora da main thread (splash segue animando) e, ao
    terminar, monta a interface na main thread via `after`."""

    def _carregar():
        try:
            from automacao.apuracao import ApuracaoPanel
            from automacao.premmia import PremmiaPanel
            from automacao.santander_postos import SantanderPostosPanel
            classes = (SantanderPostosPanel, ApuracaoPanel, PremmiaPanel)
        except Exception:
            logger.exception("Falha ao carregar os módulos")
            root.after(0, lambda: _falha_carregar(root, splash))
            return
        root.after(0, lambda: _montar_ui(root, splash, logger, classes))

    threading.Thread(target=_carregar, daemon=True).start()


def _montar_ui(root, splash, logger, classes):
    _montar_header(root)
    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True)
    for ModuloPanel in classes:
        panel = ModuloPanel(notebook)
        notebook.add(panel, text=ModuloPanel.NOME)

    logger.info("App iniciado (build %s)", updater.versao_curta(updater.versao_atual()))
    splash.fechar()
    root.deiconify()


def _falha_carregar(root, splash):
    splash.fechar()
    root.deiconify()
    messagebox.showerror(
        "Erro ao iniciar",
        f"Não foi possível carregar os módulos.\n\nDetalhes em:\n{log.caminho_log()}")
    root.destroy()


# ── header com marca + versão + botão Atualizar ──────────────────────────────

def _montar_header(root):
    header = tk.Frame(root, bg=tema.NAVY)
    header.pack(fill="x", side="top")

    cv = tk.Canvas(header, width=168, height=48, bg=tema.NAVY, highlightthickness=0)
    cv.pack(side="left", padx=(14, 6), pady=6)
    tema.desenhar_marca(cv, 6, 8, 32)
    cv.create_text(50, 16, text="Factus", fill=tema.ON_NAVY, anchor="w",
                   font=("Segoe UI", 15, "bold"))
    cv.create_text(51, 34, text="Automações", fill=tema.MUTED, anchor="w",
                   font=("Segoe UI", 9))

    tk.Label(header, text=f"build {updater.versao_curta(updater.versao_atual())}",
             bg=tema.NAVY, fg=tema.MUTED, font=("Segoe UI", 8, "bold")).pack(
        side="left", padx=8)

    btn = tk.Button(header, text="⟳  Atualizar", relief="flat", bd=0, cursor="hand2",
                    bg=tema.NAVY_L, fg=tema.ON_NAVY, activebackground=tema.ACCENT,
                    activeforeground=tema.NAVY_D, padx=14, pady=6,
                    font=("Segoe UI", 9, "bold"))
    btn.pack(side="right", padx=12, pady=8)
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
        self.barra = ttk.Progressbar(self.win, length=280, mode="determinate", maximum=1.0,
                                     style="Brand.Horizontal.TProgressbar")
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
