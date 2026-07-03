"""Testes das partes puras do updater — inclui a proteção do restart no Windows."""

from automacao import updater


def test_versao_curta_encurta_sha():
    assert updater.versao_curta("ee2a0081234567890") == "ee2a008"


def test_versao_curta_dev():
    assert updater.versao_curta("") == "dev"
    assert updater.versao_curta("dev") == "dev"


def test_env_scrub_remove_variaveis_pyinstaller(monkeypatch):
    # Se estas variáveis vazarem para o processo filho, o exe reaberto falha com
    # 'Failed to load Python DLL'. O scrub tem que removê-las.
    monkeypatch.setenv("_MEIPASS2", "/tmp/_MEI123")
    monkeypatch.setenv("_PYI_ARCHIVE_FILE", "x")
    monkeypatch.setenv("_PYINSTALLER_FOO", "y")
    monkeypatch.setenv("PATH", "manter")

    env = updater._env_sem_pyinstaller()

    assert "_MEIPASS2" not in env
    assert "_PYI_ARCHIVE_FILE" not in env
    assert "_PYINSTALLER_FOO" not in env
    assert env.get("PATH") == "manter"
