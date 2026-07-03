"""Gera automacao/assets/factus_splash.png (splash nativo do PyInstaller).

Uso (dev): python tools/gerar_assets.py
Requer Pillow (apenas para gerar; não é dependência de runtime). O PNG fica
versionado, então o build não precisa do Pillow. Reaproveita a mesma marca do
app (automacao.tema.MARCA) para o splash ficar idêntico ao loading em Tk.
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from automacao import tema

W, H = 480, 300
SAIDA = Path(__file__).resolve().parents[1] / "automacao" / "assets" / "factus_splash.png"


def _fonte(tamanho: int, negrito: bool = True):
    candidatas = (
        ["DejaVuSans-Bold.ttf", "arialbd.ttf", "Arial_Bold.ttf"] if negrito
        else ["DejaVuSans.ttf", "arial.ttf", "Arial.ttf"]
    )
    for nome in candidatas:
        try:
            return ImageFont.truetype(nome, tamanho)
        except OSError:
            continue
    return ImageFont.load_default()


def gerar() -> Path:
    img = Image.new("RGB", (W, H), tema.NAVY)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 6], fill=tema.ACCENT)  # faixa de acento no topo

    size, ox, oy = 112, 70, 84
    for x0, y0, x1, y1, cor in tema.MARCA:
        d.rectangle([ox + x0 * size, oy + y0 * size, ox + x1 * size, oy + y1 * size], fill=cor)

    d.text((206, 92), "Factus", fill=tema.ON_NAVY, font=_fonte(40))
    d.text((208, 150), "Cont.", fill=tema.MUTED, font=_fonte(18, negrito=False))
    d.text((W // 2, 252), "Carregando…", fill=tema.MUTED, font=_fonte(15, negrito=False), anchor="mm")

    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    img.save(SAIDA)
    return SAIDA


if __name__ == "__main__":
    print("Gerado:", gerar())
