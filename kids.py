# -*- coding: utf-8 -*-
"""الأخوان: نور ويوسف. شخصيتان كرتونيتان مرسومتان بالكود، فمهما وعيونهما متحركة."""
from PIL import Image, ImageDraw
SS = 2
N = 900
INK = (70, 40, 40)

def _c(d, cx, cy, rx, ry, fill, outline=None, w=0):
    d.ellipse([cx-rx, cy-ry, cx+rx, cy+ry], fill=fill, outline=outline, width=w)

def draw_kid(who="noor", mouth="closed", eyes="open", wave=False, size=N):
    W = N * SS; s = SS
    im = Image.new("RGBA", (W, W), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    girl = who == "noor"
    SKIN = (255, 214, 178) if girl else (244, 200, 160); SKIN_D = (236, 175, 135)
    HAIR = (70, 45, 35) if girl else (95, 60, 40)
    TOP = (255, 196, 60) if girl else (70, 140, 230)
    TOP_D = (230, 160, 30) if girl else (45, 105, 195)
    # جسم
    d.rounded_rectangle([230*s, 660*s, 670*s, 940*s], radius=130*s, fill=TOP)
    if girl:
        d.polygon([(230*s, 860*s), (670*s, 860*s), (720*s, 940*s), (180*s, 940*s)], fill=TOP_D)
    else:
        d.rectangle([230*s, 790*s, 670*s, 810*s], fill=TOP_D)
        d.rectangle([230*s, 840*s, 670*s, 860*s], fill=TOP_D)
    # أذرع
    if wave:
        d.line([(640*s, 740*s), (775*s, 560*s)], fill=TOP, width=90*s); _c(d, 780*s, 535*s, 54*s, 54*s, SKIN)
    else:
        d.line([(650*s, 750*s), (725*s, 850*s)], fill=TOP, width=90*s); _c(d, 728*s, 862*s, 50*s, 50*s, SKIN)
    d.line([(260*s, 750*s), (190*s, 850*s)], fill=TOP, width=90*s); _c(d, 188*s, 862*s, 50*s, 50*s, SKIN)
    # رقبة
    d.rounded_rectangle([400*s, 590*s, 500*s, 700*s], radius=30*s, fill=SKIN_D)
    # شعر خلفي
    if girl:
        _c(d, 175*s, 470*s, 82*s, 120*s, HAIR); _c(d, 725*s, 470*s, 82*s, 120*s, HAIR)
        _c(d, 175*s, 330*s, 20*s, 20*s, HAIR)
    _c(d, 450*s, 330*s, 280*s, 300*s, HAIR)
    # الوجه
    _c(d, 450*s, 410*s, 255*s, 270*s, SKIN)
    # أذنان
    _c(d, 195*s, 420*s, 34*s, 44*s, SKIN); _c(d, 705*s, 420*s, 34*s, 44*s, SKIN)
    # غرّة
    if girl:
        d.pieslice([200*s, 95*s, 700*s, 405*s], 180, 360, fill=HAIR)
        d.rectangle([205*s, 250*s, 695*s, 275*s], fill=HAIR)
        for fx in (275, 365, 455, 545, 635):
            _c(d, fx*s, 275*s, 50*s, 42*s, HAIR)
        d.polygon([(560*s, 130*s), (650*s, 90*s), (650*s, 190*s)], fill=(255, 110, 150))
        d.polygon([(560*s, 130*s), (470*s, 90*s), (470*s, 190*s)], fill=(255, 110, 150))
        _c(d, 560*s, 130*s, 26*s, 26*s, (230, 70, 120))
    else:
        d.pieslice([195*s, 90*s, 705*s, 420*s], 180, 360, fill=HAIR)
        d.rectangle([200*s, 250*s, 700*s, 285*s], fill=HAIR)
        _c(d, 300*s, 285*s, 105*s, 52*s, HAIR); _c(d, 520*s, 280*s, 130*s, 46*s, HAIR)
    # الخدود
    cheek = Image.new("RGBA", (W, W), (0, 0, 0, 0)); cd = ImageDraw.Draw(cheek)
    _c(cd, 300*s, 500*s, 48*s, 30*s, (255, 130, 130, 140)); _c(cd, 600*s, 500*s, 48*s, 30*s, (255, 130, 130, 140))
    im.alpha_composite(cheek); d = ImageDraw.Draw(im)
    # الحواجب
    d.arc([300*s, 345*s, 410*s, 390*s], 200, 340, fill=INK, width=9*s)
    d.arc([490*s, 345*s, 600*s, 390*s], 200, 340, fill=INK, width=9*s)
    # العيون
    for ex in (355, 545):
        if eyes == "open":
            _c(d, ex*s, 425*s, 54*s, 64*s, (255, 255, 255), INK, 5*s)
            _c(d, ex*s, 430*s, 38*s, 46*s, (110, 70, 40)); _c(d, ex*s, 432*s, 21*s, 27*s, INK)
            _c(d, (ex-12)*s, 410*s, 12*s, 12*s, (255, 255, 255))
        else:
            d.arc([(ex-48)*s, 410*s, (ex+48)*s, 460*s], 10, 170, fill=INK, width=9*s)
    d.arc([430*s, 460*s, 470*s, 500*s], 20, 160, fill=SKIN_D, width=6*s)
    # الفم
    cx, cy = 450, 535
    if mouth == "closed":
        d.arc([(cx-70)*s, (cy-45)*s, (cx+70)*s, (cy+35)*s], 20, 160, fill=(190, 70, 80), width=9*s)
    elif mouth == "open":
        d.chord([(cx-62)*s, (cy-30)*s, (cx+62)*s, (cy+60)*s], 0, 180, fill=(150, 40, 55))
        d.pieslice([(cx-36)*s, (cy+20)*s, (cx+36)*s, (cy+90)*s], 180, 360, fill=(240, 110, 120))
        d.rectangle([(cx-46)*s, (cy-4)*s, (cx+46)*s, (cy+10)*s], fill=(255, 255, 255))
    else:
        _c(d, cx*s, (cy+18)*s, 30*s, 38*s, (150, 40, 55)); _c(d, cx*s, (cy+34)*s, 18*s, 16*s, (240, 110, 120))
    return im.resize((size, size), Image.LANCZOS)

if __name__ == "__main__":
    import sys
    out = sys.argv[1]
    sheet = Image.new("RGBA", (1600, 800), (200, 230, 255, 255))
    spec = [("noor", "open", "open", False), ("yousef", "open", "open", True),
            ("noor", "closed", "closed", False), ("yousef", "wide", "open", False)]
    pos = [(0, 0), (400, 0), (800, 0), (1200, 0)]
    for (w, m, e, wv), p in zip(spec, pos):
        sheet.alpha_composite(draw_kid(w, m, e, wv, 400), p)
    sheet2 = Image.new("RGBA", (1600, 1200), (200, 230, 255, 255)); sheet2.alpha_composite(sheet.crop((0, 0, 1600, 400)), (0, 0))
    sheet2.alpha_composite(draw_kid("noor", "open", "open", False, 700), (200, 420))
    sheet2.alpha_composite(draw_kid("yousef", "closed", "open", True, 700), (780, 420))
    sheet = sheet2
    sheet.save(out)
