"""Gera os assets visuais a partir do logo oficial (automacao/assets/factus_logo.png).

Uso (dev): python tools/gerar_assets.py

Deriva tudo do logo oficial recortando automaticamente o conteúdo (lockup) e o
símbolo (à esquerda). Se o logo faltar, cai na marca vetorial de automacao.tema.
Saídas (versionadas, para o build não depender de Pillow):
  - factus_splash.png  splash nativo do PyInstaller (--splash) e loading em Tk
  - factus_header.png  lockup pequeno para o cabeçalho do app
  - factus_icon.png    ícone quadrado da janela (iconphoto)
  - factus.ico         ícone do executável / barra de tarefas (--icon)
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from automacao import tema

ASSETS = Path(__file__).resolve().parents[1] / "automacao" / "assets"
LOGO = ASSETS / "factus_logo.png"
SPLASH = ASSETS / "factus_splash.png"
HEADER = ASSETS / "factus_header.png"
ICON_PNG = ASSETS / "factus_icon.png"
ICO = ASSETS / "factus.ico"

W, H = 480, 300
NAVY = tuple(int(tema.NAVY[i:i + 2], 16) for i in (1, 3, 5))


def _fonte(tam, negrito=True):
    for nome in (["DejaVuSans-Bold.ttf"] if negrito else ["DejaVuSans.ttf"]):
        try:
            return ImageFont.truetype(nome, tam)
        except OSError:
            pass
    return ImageFont.load_default()


def _bbox(im, x0, x1):
    """Caixa do conteúdo (pixels que destoam do fundo) na faixa [x0, x1) de colunas."""
    px = im.load()
    fundo = px[1, 1][:3]
    xs, ys = [], []
    for y in range(im.height):
        for x in range(x0, min(x1, im.width)):
            p = px[x, y]
            if any(abs(p[i] - fundo[i]) > 22 for i in range(3)):
                xs.append(x)
                ys.append(y)
    if not xs:
        return None
    return min(xs), min(ys), max(xs) + 1, max(ys) + 1


def _recorte(im, box, margem=0):
    x0, y0, x1, y1 = box
    x0 = max(0, x0 - margem)
    y0 = max(0, y0 - margem)
    x1 = min(im.width, x1 + margem)
    y1 = min(im.height, y1 + margem)
    return im.crop((x0, y0, x1, y1))


def _escala_altura(im, altura):
    return im.resize((max(1, round(im.width * altura / im.height)), altura), Image.LANCZOS)


def _tem_logo():
    return LOGO.exists()


# ── com logo oficial ─────────────────────────────────────────────────────────

def _gerar_do_logo():
    logo = Image.open(LOGO).convert("RGBA")
    lockup = _recorte(logo, _bbox(logo, 0, logo.width), margem=2)
    marca_box = _bbox(logo, 0, round(logo.width * 0.27))
    marca = _recorte(logo, marca_box, margem=2)

    # splash: lockup centrado no navy, com "Carregando…"
    img = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 6], fill=tema.ACCENT)
    lk = lockup if lockup.width <= 380 else lockup.resize(
        (380, round(lockup.height * 380 / lockup.width)), Image.LANCZOS)
    img.paste(lk, ((W - lk.width) // 2, (H - lk.height) // 2 - 16), lk)
    d.text((W // 2, 252), "Carregando…", fill=tema.MUTED, font=_fonte(15, False), anchor="mm")
    img.save(SPLASH)

    # header: lockup pequeno sobre navy (emenda com o cabeçalho navy do app)
    hdr = _escala_altura(lockup, 34)
    fundo = Image.new("RGB", (hdr.width + 8, hdr.height + 8), NAVY)
    fundo.paste(hdr, (4, 4), hdr)
    fundo.save(HEADER)

    # ícone: símbolo centrado em quadrado navy
    S = 256
    m = _escala_altura(marca, 168)
    ic = Image.new("RGBA", (S, S), NAVY + (255,))
    ic.paste(m, ((S - m.width) // 2, (S - m.height) // 2), m)
    ic.convert("RGB").save(ICON_PNG)
    ic.save(ICO, sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])


# ── fallback: marca vetorial ─────────────────────────────────────────────────

def _desenhar_marca(d, size, ox, oy):
    for x0, y0, x1, y1, cor in tema.MARCA:
        d.rectangle([ox + x0 * size, oy + y0 * size, ox + x1 * size, oy + y1 * size], fill=cor)


def _gerar_desenhado():
    img = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 6], fill=tema.ACCENT)
    _desenhar_marca(d, 112, 70, 84)
    d.text((206, 92), "Factus", fill=tema.ON_NAVY, font=_fonte(40))
    d.text((208, 150), "Cont.", fill=tema.MUTED, font=_fonte(18, False))
    d.text((W // 2, 252), "Carregando…", fill=tema.MUTED, font=_fonte(15, False), anchor="mm")
    img.save(SPLASH)

    hdr = Image.new("RGBA", (168, 48), (0, 0, 0, 0))
    dh = ImageDraw.Draw(hdr)
    _desenhar_marca(dh, 32, 6, 8)
    dh.text((50, 8), "Factus", fill=tema.ON_NAVY, font=_fonte(17))
    dh.text((51, 30), "Automações", fill=tema.MUTED, font=_fonte(10, False))
    hdr.save(HEADER)

    S = 256
    ic = Image.new("RGB", (S, S), NAVY)
    _desenhar_marca(ImageDraw.Draw(ic), 150, 58, 24)
    ic.save(ICON_PNG)
    ic.save(ICO, sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])


def gerar():
    ASSETS.mkdir(parents=True, exist_ok=True)
    if _tem_logo():
        _gerar_do_logo()
        return "logo oficial (factus_logo.png)"
    _gerar_desenhado()
    return "marca vetorial (fallback)"


if __name__ == "__main__":
    print("Gerado a partir de:", gerar())
    print("Saídas em:", ASSETS)
