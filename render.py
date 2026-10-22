# -*- coding: utf-8 -*-
"""
رسم المشاهد وتحريكها. كل مشهد = خلفية + طبقات PNG شفافة، يركّبها ffmpeg مع حركة وتوقيت دقيق للصوت.
الحركة: فقاعات عائمة، تحريك الصورة (Ken Burns)، انزلاق اللوحات، تظليل الكلمة المنطوقة، عدّ تفاعلي،
اختبار قصير بعدّاد تنازلي، شريط تقدم، وموسيقى خلفية هادئة.
"""
import asyncio
import hashlib
import math
import os
import random
import re
import subprocess
import time
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

ROOT = Path(__file__).parent
OUT = ROOT / "output"
FPS = 24

CHANNEL_AR = "عالم التعلم"
CHANNEL_EN = "Learning World"
AR_VOICE = os.getenv("AR_VOICE", "ar-SA-ZariyahNeural")
EN_VOICE = os.getenv("EN_VOICE", "en-US-GuyNeural")  # صوت يوسف (ولد)
EN_PITCH = os.getenv("EN_PITCH", "+28Hz")  # رفع النبرة ليشبه صوت طفل

FONT_AR = [
    "/usr/share/fonts/truetype/noto/NotoNaskhArabic-Bold.ttf",
    "/usr/share/fonts/truetype/noto/NotoSansArabic-Bold.ttf",
    "/usr/share/fonts/opentype/noto/NotoNaskhArabic-Bold.ttf",
    "/usr/share/fonts/truetype/hosny-amiri/Amiri-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]
FONT_EN = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
]
EMOJI_FONT = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"

PALETTES = [  # (أعلى، أسفل، لون مميز)
    ((255, 214, 102), (255, 150, 120), (214, 70, 60)),
    ((140, 210, 255), (120, 150, 255), (40, 90, 200)),
    ((170, 235, 170), (90, 200, 170), (20, 130, 100)),
    ((255, 190, 220), (200, 150, 255), (150, 60, 190)),
    ((255, 225, 150), (140, 220, 200), (30, 140, 130)),
    ((190, 200, 255), (255, 180, 200), (190, 70, 120)),
]
INK = (30, 40, 100)
HL = (255, 214, 70)


# ================================================================ أدوات عامة
def sh(cmd):
    r = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    if r.returncode != 0:
        raise RuntimeError("ffmpeg failed: " + r.stderr[-1500:])


def duration(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", str(path)], capture_output=True, text=True)
    return float(r.stdout.strip())


_font_cache = {}


def pick_font(cands, size):
    key = (cands[0], int(size))
    if key not in _font_cache:
        for p in cands:
            if os.path.exists(p):
                _font_cache[key] = ImageFont.truetype(p, int(size))
                break
        else:
            _font_cache[key] = ImageFont.load_default()
    return _font_cache[key]


_raqm = None


def ar_text(s):
    """تشكيل الحروف العربية واتجاهها (يعمل مع raqm أو بدونه)."""
    global _raqm
    if _raqm is None:
        from PIL import features
        _raqm = features.check("raqm")
    if _raqm:
        return s
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display
        return get_display(arabic_reshaper.reshape(s))
    except Exception:
        return s


_emoji_cache = {}


def emoji_img(ch, height):
    """صورة إيموجي شفافة بارتفاع height."""
    key = (ch, int(height))
    if key in _emoji_cache:
        return _emoji_cache[key]
    im = None
    try:
        f = ImageFont.truetype(EMOJI_FONT, 109)
        canvas = Image.new("RGBA", (320, 160), (0, 0, 0, 0))
        ImageDraw.Draw(canvas).text((10, 10), ch, font=f, embedded_color=True)
        bb = canvas.getchannel("A").getbbox()
        if bb:
            im = canvas.crop(bb)
            w = max(1, int(im.width * height / im.height))
            im = im.resize((w, int(height)), Image.LANCZOS)
    except Exception:
        im = None
    _emoji_cache[key] = im
    return im


def split_emoji(s):
    """يقسم سلسلة إيموجي إلى عناصر (يدعم تكرار نفس الإيموجي)."""
    items = [c for c in s if c.strip()]
    out, i = [], 0
    chars = list(s)
    while i < len(chars):
        c = chars[i]
        j = i + 1
        while j < len(chars) and ord(chars[j]) in (0xFE0F, 0x200D, 0x20E3) or \
                (j < len(chars) and 0x1F3FB <= ord(chars[j]) <= 0x1F3FF) or \
                (j < len(chars) and chars[j - 1] == "‍"):
            j += 1
        out.append("".join(chars[i:j]))
        i = j
    return out or items


def gradient(size, top, bottom):
    W, H = size
    col = Image.new("RGB", (1, H))
    for y in range(H):
        k = y / max(1, H - 1)
        col.putpixel((0, y), tuple(int(top[i] * (1 - k) + bottom[i] * k) for i in range(3)))
    return col.resize((W, H))


def rounded_mask(size, radius):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, size[0] - 1, size[1] - 1], radius=radius, fill=255)
    return m


def save_png(im, name):
    p = OUT / name
    im.save(p)
    return p


# ================================================================ الصور المولّدة (مجانية)
STYLE = ("cute 3D cartoon illustration for small children, Pixar style, soft lighting, "
         "vibrant pastel colors, centered subject, clean simple background, high quality, "
         "no text, no letters, no numbers, no watermark")


def _fetch_one(visual):
    h = hashlib.sha1(visual.encode()).hexdigest()[:12]
    path = OUT / "img" / f"{h}.jpg"
    if path.exists():
        return path
    prompt = f"{visual}, {STYLE}"
    for attempt in range(3):
        url = ("https://image.pollinations.ai/prompt/" + requests.utils.quote(prompt) +
               f"?width=1024&height=1024&model=flux&nologo=true&enhance=true&seed={int(h, 16) % 99991 + attempt * 7}")
        try:
            r = requests.get(url, timeout=120)
            if r.ok and r.headers.get("content-type", "").startswith("image") and len(r.content) > 20000:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(r.content)
                Image.open(path).verify()
                return path
            print(f"[image] رمز {r.status_code} (محاولة {attempt + 1})")
        except Exception as e:  # noqa
            print(f"[image] فشل: {type(e).__name__} (محاولة {attempt + 1})")
        time.sleep(6)
    return None


def fetch_images(visuals):
    """يجلب الصور بالتوازي (3 في آن واحد). يرجع {visual: Path|None}."""
    from concurrent.futures import ThreadPoolExecutor
    uniq = sorted(set(v for v in visuals if v))
    if os.getenv("NO_IMAGES") == "1":
        return {v: None for v in uniq}
    with ThreadPoolExecutor(max_workers=3) as ex:
        res = list(ex.map(_fetch_one, uniq))
    got = dict(zip(uniq, res))
    print(f"[image] تم جلب {sum(1 for p in res if p)} من {len(uniq)} صورة")
    return got


# ================================================================ الصوت
def _silence(secs):
    p = OUT / "sfx" / f"sil_{int(secs * 1000)}.mp3"
    if not p.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
        sh(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
            "-t", f"{secs:.3f}", "-c:a", "libmp3lame", "-b:a", "48k", str(p)])
    return p


def _make_jingle(path):
    """لحن مقدمة قصير مبهج (يُولَّد برمجياً): أربع نغمات صاعدة ثم وتر مشرق."""
    import numpy as np
    import wave
    sr = 24000
    dur = 2.4
    t = np.arange(int(sr * dur)) / sr
    buf = np.zeros_like(t)

    def bell(freq, start, length, amp):
        m = (t >= start) & (t < start + length)
        tt = t[m] - start
        env = np.exp(-tt * 3.2) * np.minimum(1, tt * 90)
        w = (np.sin(2 * np.pi * freq * tt) + 0.35 * np.sin(2 * np.pi * freq * 2 * tt) +
             0.12 * np.sin(2 * np.pi * freq * 3 * tt))
        buf[m] += amp * env * w

    for i, f in enumerate((523.25, 659.25, 783.99, 1046.5)):
        bell(f, 0.0 + i * 0.16, 1.0, 0.30)
    for f in (523.25, 659.25, 783.99, 1046.5):
        bell(f, 0.72, 1.6, 0.20)
    for i, f in enumerate((2093.0, 2637.0, 3136.0)):
        bell(f, 0.9 + i * 0.12, 0.6, 0.07)
    buf = buf / max(1e-6, np.abs(buf).max()) * 0.8
    wav = path.with_suffix(".wav")
    with wave.open(str(wav), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((buf * 32767).astype("<i2").tobytes())
    sh(["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav), "-ar", "24000", "-ac", "1", "-c:a", "libmp3lame",
        "-b:a", "96k", str(path)])


def _sfx(name):
    p = OUT / "sfx" / f"{name}.mp3"
    if not p.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
        if name == "jingle":
            _make_jingle(p)
            return p
        if name == "tick":
            src = "sine=frequency=900:duration=0.12,afade=t=out:st=0.04:d=0.08,volume=0.6"
        elif name == "ding":
            src = "sine=frequency=1320:duration=0.7,afade=t=out:st=0.05:d=0.65,volume=0.7"
        else:  # pop
            src = "sine=frequency=600:duration=0.1,afade=t=out:st=0.02:d=0.08,volume=0.5"
        sh(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", src, "-ar", "24000", "-ac", "1",
            "-c:a", "libmp3lame", str(p)])
    return p


async def _tts_async(text, voice, rate, path, pitch=None):
    import edge_tts
    if pitch:
        await edge_tts.Communicate(text, voice, rate=rate, pitch=pitch).save(str(path))
    else:
        await edge_tts.Communicate(text, voice, rate=rate).save(str(path))


def tts_file(text, lang):
    voice, rate = (AR_VOICE, "-12%") if lang == "ar" else (EN_VOICE, "-6%")
    pitch = None if lang == "ar" else EN_PITCH
    h = hashlib.sha1(f"{voice}|{rate}|{pitch}|{text}".encode()).hexdigest()[:16]
    path = OUT / "tts" / f"{h}.mp3"
    if path.exists():
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    if os.getenv("FAKE_TTS") == "1":
        secs = max(1.2, len(text) * (0.075 if lang == "ar" else 0.06))
        sh(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
            "-t", f"{secs:.2f}", "-c:a", "libmp3lame", "-b:a", "48k", str(path)])
        return path
    last = None
    for attempt in range(3):
        try:
            # آخر محاولة بلا رفع نبرة (احتياط إن رفضه الخادم)
            asyncio.run(_tts_async(text, voice, rate, path, pitch if attempt < 2 else None))
            if path.exists() and path.stat().st_size > 500:
                return path
        except Exception as e:  # noqa
            last = e
            time.sleep(3)
    raise RuntimeError(f"TTS failed: {type(last).__name__}")


_dur_cache = {}


def _dur(p):
    if p not in _dur_cache:
        _dur_cache[p] = duration(p)
    return _dur_cache[p]


def compose_audio(parts, name):
    """parts: ('say', text, lang, label?) | ('sil', secs) | ('sfx', name, label?).
    يرجع (مسار mp3، المدة الكلية، marks{label: (t0, t1)})"""
    files, marks, t = [], {}, 0.0
    for part in parts:
        if part[0] == "say":
            f = tts_file(part[1], part[2])
            label = part[3] if len(part) > 3 else None
        elif part[0] == "sil":
            f, label = _silence(part[1]), None
        else:
            f = _sfx(part[1])
            label = part[2] if len(part) > 2 else None
        d = _dur(f)
        if label:
            marks[label] = (t, t + d)
        files.append(f)
        t += d
    lst = OUT / f"{name}.txt"
    lst.write_text("".join(f"file '{f.resolve()}'\n" for f in files))
    out = OUT / f"{name}.mp3"
    sh(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-ar", "24000",
        "-ac", "1", "-c:a", "libmp3lame", "-b:a", "96k", str(out)])
    return out, duration(out), marks


# ================================================================ التخطيط
class Geo:
    def __init__(self, size):
        self.W, self.H = size
        W, H = size
        self.vertical = H > W
        self.pad = int(W * 0.05)
        self.base = min(W, H)
        f = pick_font(FONT_AR, int(self.base * 0.045))
        self.chip_font = f
        self.chip_h = int(f.size * 1.9)
        self.head_b = self.pad + self.chip_h + int(self.pad * 0.7)
        self.stage = int(H * (0.17 if self.vertical else 0.22))  # ارتفاع منصة الأخوين أسفل الشاشة
        self.bottom = H - 14 - self.stage - int(self.pad * 0.5)  # فوق المنصة وشريط التقدم
        if self.vertical:
            self.box = (self.pad, self.head_b, W - self.pad, self.head_b + int(H * 0.40))
            self.panel = (self.pad, self.box[3] + int(self.pad * 0.7), W - self.pad, self.bottom)
        else:
            bw = int(W * 0.46)
            self.box = (self.pad, self.head_b, self.pad + bw, self.bottom)
            self.panel = (self.box[2] + self.pad, self.head_b, W - self.pad, self.bottom)
        self.bw, self.bh = self.box[2] - self.box[0], self.box[3] - self.box[1]
        self.radius = int(min(self.bw, self.bh) * 0.07)


def make_gradient_bg(geo, pal):
    top, bottom, _ = pal
    return gradient((geo.W, geo.H), top, bottom)


def make_bubbles(geo, seed):
    """طبقة فقاعات بارتفاع 2H لتدور بسلاسة (النمط يتكرر)."""
    W, H = geo.W, geo.H
    rnd = random.Random(seed)
    tile = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dd = ImageDraw.Draw(tile)
    for _ in range(16):
        r = rnd.randint(int(W * 0.02), int(W * 0.065))
        x, y = rnd.randint(0, W), rnd.randint(0, H)
        for dy in (0, -H, H):
            dd.ellipse([x - r, y + dy - r, x + r, y + dy + r], fill=(255, 255, 255, rnd.randint(40, 85)))
    big = Image.new("RGBA", (W, H * 2), (0, 0, 0, 0))
    big.paste(tile, (0, 0))
    big.paste(tile, (0, H))
    return big


def make_deco(geo, pal, with_box=True):
    """طبقة ثابتة: شريط اسم القناة + إطار وظل مكان الصورة."""
    W, H = geo.W, geo.H
    accent = pal[2]
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    f_ar = geo.chip_font
    f_en = pick_font(FONT_EN, int(f_ar.size * 0.9))
    parts = [(CHANNEL_EN, f_en), ("  •  ", f_en), (ar_text(CHANNEL_AR), f_ar)]
    tw = sum(d.textlength(t, font=f) for t, f in parts)
    chip = [W / 2 - tw / 2 - 36, geo.pad, W / 2 + tw / 2 + 36, geo.pad + geo.chip_h]
    d.rounded_rectangle(chip, radius=geo.chip_h // 2, fill=(255, 255, 255, 235))
    x = W / 2 - tw / 2
    for t, f in parts:
        d.text((x, geo.pad + geo.chip_h * 0.17), t, font=f, fill=accent)
        x += d.textlength(t, font=f)
    if with_box:
        box = geo.box
        sh_l = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(sh_l).rounded_rectangle([box[0] + 8, box[1] + 14, box[2] + 8, box[3] + 14],
                                               radius=geo.radius, fill=(0, 0, 0, 90))
        im = Image.alpha_composite(sh_l.filter(ImageFilter.GaussianBlur(14)), im)
        d = ImageDraw.Draw(im)
        d.rounded_rectangle([box[0] - 12, box[1] - 12, box[2] + 12, box[3] + 12],
                            radius=geo.radius + 8, fill=(255, 255, 255, 255))
    return im


# ---------------------------------------------------------------- نص عربي كلمة بكلمة
def _space(font):
    return font.size * 0.27


def _layout_words(d, words, font, max_w):
    sp, lines, cur, curw = _space(font), [], [], 0
    for w in words:
        ww = d.textlength(ar_text(w), font=font)
        add = ww + (sp if cur else 0)
        if cur and curw + add > max_w:
            lines.append((cur, curw))
            cur, curw = [(w, ww)], ww
        else:
            cur.append((w, ww))
            curw += add
    if cur:
        lines.append((cur, curw))
    return lines


def _wrap_latin(d, text, font, max_w):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if d.textlength(t, font=font) <= max_w or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def render_panel(pw, ph, ar, en, accent, base):
    """لوحة النص: ترجع الصورة + مواضع كلمات العربية لإبرازها لاحقاً."""
    m = 14
    img = Image.new("RGBA", (pw + 2 * m, ph + 2 * m), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    r = int(min(pw, ph) * 0.12)
    d.rounded_rectangle([m + 6, m + 10, m + pw + 6, m + ph + 10], radius=r, fill=(0, 0, 0, 55))
    d.rounded_rectangle([m, m, m + pw, m + ph], radius=r, fill=(255, 255, 255, 246), outline=accent, width=6)
    inner_w, inner_h = pw - int(pw * 0.1), ph - int(ph * 0.12)
    words = ar.split()
    size = int(base * 0.085)
    while True:
        f_ar = pick_font(FONT_AR, size)
        lines = _layout_words(d, words, f_ar, inner_w)
        if len(lines) * size * 1.35 <= inner_h * 0.62 or size <= 30:
            break
        size -= 4
    size_en = int(base * 0.05)
    while True:
        f_en = pick_font(FONT_EN, size_en)
        en_lines = _wrap_latin(d, en, f_en, inner_w)
        if len(en_lines) * size_en * 1.3 <= inner_h * 0.34 or size_en <= 22:
            break
        size_en -= 3
    lh_ar, lh_en = size * 1.35, size_en * 1.3
    block = len(lines) * lh_ar + 22 + len(en_lines) * lh_en
    y = m + (ph - block) / 2
    cx = m + pw / 2
    word_boxes = []
    sp = _space(f_ar)
    for line, total in lines:
        right = cx + total / 2
        for w, ww in line:
            x = right - ww
            d.text((x, y), ar_text(w), font=f_ar, fill=INK, stroke_width=max(2, size // 18), stroke_fill=(255, 255, 255))
            word_boxes.append({"text": w, "x": x, "y": y, "w": ww, "lh": lh_ar})
            right = x - sp
        y += lh_ar
    d.rounded_rectangle([cx - 60, y + 2, cx + 60, y + 8], radius=3, fill=accent)
    y += 20
    en_boxes = []
    for ln in en_lines:
        w = d.textlength(ln, font=f_en)
        d.text((cx - w / 2, y), ln, font=f_en, fill=accent, stroke_width=max(2, size_en // 16),
               stroke_fill=(255, 255, 255))
        en_boxes.append({"text": ln, "x": cx - w / 2, "y": y, "w": w, "lh": lh_en})
        y += lh_en
    return {"img": img, "m": m, "words": word_boxes, "en": en_boxes, "f_ar": f_ar, "f_en": f_en}


def word_highlight(box, font, accent):
    px = int(font.size * 0.14)
    w, h = int(box["w"] + 2 * px), int(box["lh"])
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, int(font.size * 0.1), w - 1, h - int(font.size * 0.04)], radius=int(font.size * 0.25),
                        fill=HL + (255,))
    d.text((px, 0), ar_text(box["text"]), font=font, fill=INK, stroke_width=max(2, font.size // 18),
           stroke_fill=HL)
    return im, int(box["x"] - px), int(box["y"])


def en_highlight(box, font, accent):
    px = int(font.size * 0.5)
    w, h = int(box["w"] + 2 * px), int(box["lh"])
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=h // 2, fill=accent + (255,))
    d.text((px, (h - font.size) / 2 - font.size * 0.12), box["text"], font=font, fill=(255, 255, 255))
    return im, int(box["x"] - px), int(box["y"])


def word_windows(words, t0, t1):
    """يوزّع زمن الجملة على كلماتها بنسبة طولها (مع وقفة عند علامات الترقيم)."""
    weights = []
    for b in words:
        t = b["text"]
        wgt = len(re.sub(r"[^\w]", "", t)) + 1.0
        if t[-1:] in "،,.:؟?!؛":
            wgt += 2.0
        weights.append(wgt)
    total = sum(weights) or 1
    # ترتيب النطق: logical order = ترتيب words (أول كلمة أولاً)
    out, cur = [], t0
    for b, wgt in zip(words, weights):
        d = (t1 - t0) * wgt / total
        out.append((cur, cur + d))
        cur += d
    return out


# ---------------------------------------------------------------- بطاقات الصورة
def card_base(bw, bh, radius, accent):
    im = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, bw - 1, bh - 1], radius=radius, fill=(255, 255, 255, 255), outline=accent, width=8)
    return im


def fit_font(cands, text, max_w, max_h, start, d, arabic):
    size = int(start)
    while size > 20:
        f = pick_font(cands, size)
        t = ar_text(text) if arabic else text
        bb = d.textbbox((0, 0), t, font=f)
        if bb[2] - bb[0] <= max_w and bb[3] - bb[1] <= max_h:
            return f
        size -= 6
    return pick_font(cands, 20)


def letter_card(geo, scene, accent):
    bw, bh = geo.bw, geo.bh
    im = card_base(bw, bh, geo.radius, accent)
    d = ImageDraw.Draw(im)
    glyph = scene["glyph"]
    latin = scene.get("latin")
    sub = scene.get("sub")
    area_h = bh * (0.62 if sub else 0.8)
    f = fit_font(FONT_EN if latin else FONT_AR, glyph, bw * 0.78, area_h * 0.78, bh * 0.75, d, not latin)
    t = glyph if latin else ar_text(glyph)
    bb = d.textbbox((0, 0), t, font=f)
    gx = (bw - (bb[2] - bb[0])) / 2 - bb[0]
    gy = (area_h - (bb[3] - bb[1])) / 2 - bb[1] + bh * 0.06
    d.text((gx, gy), t, font=f, fill=accent, stroke_width=4, stroke_fill=(255, 255, 255))
    if sub:
        f2 = fit_font(FONT_AR, sub, bw * 0.7, bh * 0.2, bh * 0.2, d, True)
        t2 = ar_text(sub)
        bb2 = d.textbbox((0, 0), t2, font=f2)
        d.text(((bw - (bb2[2] - bb2[0])) / 2 - bb2[0], bh * 0.74), t2, font=f2, fill=INK)
    return im


def forms_card(geo, scene, accent):
    bw, bh = geo.bw, geo.bh
    ch = scene["letter"]
    im = card_base(bw, bh, geo.radius, accent)
    d = ImageDraw.Draw(im)
    if scene.get("connect", True):
        cells = [("وحده", ch), ("أول الكلمة", ch + "‍"), ("وسط الكلمة", "‍" + ch + "‍"),
                 ("آخر الكلمة", "‍" + ch)]
        cols = 2
    else:
        cells = [("وحده", ch), ("آخر الكلمة", "‍" + ch)]
        cols = 2
    rows = math.ceil(len(cells) / cols)
    cw, chh = bw / cols, bh / rows
    for i, (label, g) in enumerate(cells):
        cx0, cy0 = (i % cols) * cw, (i // cols) * chh
        f = pick_font(FONT_AR, int(min(cw, chh) * 0.46))
        t = ar_text(g)
        bb = d.textbbox((0, 0), t, font=f)
        gh = bb[3] - bb[1]
        d.text((cx0 + (cw - (bb[2] - bb[0])) / 2 - bb[0], cy0 + chh * 0.06 + (chh * 0.66 - gh) / 2 - bb[1]), t,
               font=f, fill=accent, stroke_width=3, stroke_fill=(255, 255, 255))
        fl = pick_font(FONT_AR, int(min(cw, chh) * 0.14))
        tl = ar_text(label)
        bl = d.textbbox((0, 0), tl, font=fl)
        d.text((cx0 + (cw - (bl[2] - bl[0])) / 2 - bl[0], cy0 + chh * 0.78), tl, font=fl, fill=INK)
    d.line([bw / 2, bh * 0.08, bw / 2, bh * 0.92], fill=(220, 220, 235, 255), width=3)
    if rows > 1:
        d.line([bw * 0.06, bh / 2, bw * 0.94, bh / 2], fill=(220, 220, 235, 255), width=3)
    return im


def emoji_grid_positions(n, bw, bh):
    cols = 5 if n > 6 else max(1, math.ceil(n / 2))
    if n <= 3:
        cols = n
    rows = math.ceil(n / cols)
    cell = min(bw * 0.86 / cols, bh * 0.8 / rows)
    size = cell * 0.82
    x0 = (bw - cols * cell) / 2
    y0 = (bh - rows * cell) / 2
    pos = []
    for i in range(n):
        r, c = divmod(i, cols)
        # توسيط الصف الأخير
        in_row = cols if r < rows - 1 else n - (rows - 1) * cols
        off = (cols - in_row) * cell / 2 if r == rows - 1 else 0
        pos.append((x0 + off + c * cell + (cell - size) / 2, y0 + r * cell + (cell - size) / 2, size))
    return pos


def circle_card(geo, pal):
    bw, bh = geo.bw, geo.bh
    im = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, bw - 1, bh - 1], radius=geo.radius, fill=(255, 255, 255, 235))
    R = int(min(bw, bh) * 0.40)
    d.ellipse([bw / 2 - R, bh / 2 - R, bw / 2 + R, bh / 2 + R], fill=pal[0] + (255,), outline=pal[2], width=8)
    return im, R


# ---------------------------------------------------------------- مكوّنات الاختبار
def option_tile(w, h, opt, accent, radius):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=radius, fill=(255, 255, 255, 250), outline=accent, width=6)
    label_h = h * 0.28 if opt.get("ar") else 0
    area_h = h - label_h
    if opt.get("emoji"):
        items = split_emoji(opt["emoji"])
        n = len(items)
        if n == 1:
            size = min(area_h * 0.72, w * 0.5)
            e = emoji_img(items[0], size)
            if e:
                im.alpha_composite(e, (int((w - e.width) / 2), int((area_h - e.height) / 2)))
        else:
            cols = min(n, 5)
            rows = math.ceil(n / cols)
            cell = min(w * 0.9 / cols, area_h * 0.86 / rows)
            for i, it in enumerate(items):
                r, c = divmod(i, cols)
                in_row = cols if r < rows - 1 else n - (rows - 1) * cols
                off = (cols - in_row) * cell / 2 if r == rows - 1 else 0
                e = emoji_img(it, cell * 0.8)
                if e:
                    im.alpha_composite(e, (int((w - cols * cell) / 2 + off + c * cell + (cell - e.width) / 2),
                                           int((area_h - rows * cell) / 2 + r * cell + (cell - e.height) / 2)))
    elif opt.get("text"):
        f = fit_font(FONT_EN, opt["text"], w * 0.7, area_h * 0.7, area_h * 0.75, d, False)
        bb = d.textbbox((0, 0), opt["text"], font=f)
        d.text(((w - (bb[2] - bb[0])) / 2 - bb[0], (area_h - (bb[3] - bb[1])) / 2 - bb[1]), opt["text"], font=f,
               fill=accent, stroke_width=3, stroke_fill=(255, 255, 255))
    if opt.get("ar"):
        label = opt["ar"] if not opt.get("show_en") else opt["en"]
        arabic = not opt.get("show_en")
        f = fit_font(FONT_AR if arabic else FONT_EN, label, w * 0.86, label_h * 0.8, label_h * 0.8, d, arabic)
        t = ar_text(label) if arabic else label
        bb = d.textbbox((0, 0), t, font=f)
        d.text(((w - (bb[2] - bb[0])) / 2 - bb[0], area_h + (label_h - (bb[3] - bb[1])) / 2 - bb[1] - 4), t,
               font=f, fill=INK)
    return im


def reveal_overlay(w, h, correct, radius):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if correct:
        d.rounded_rectangle([0, 0, w - 1, h - 1], radius=radius, fill=(70, 210, 120, 70), outline=(30, 170, 90, 255),
                            width=14)
        r = int(min(w, h) * 0.13)
        d.ellipse([w - 2 * r - 8, 8, w - 8, 2 * r + 8], fill=(30, 170, 90, 255))
        d.line([w - 2 * r + r * 0.25, 8 + r, w - r - 8 - r * 0.1, 8 + r * 1.45], fill="white", width=max(6, r // 4))
        d.line([w - r - 8 - r * 0.1, 8 + r * 1.45, w - 8 - r * 0.25, 8 + r * 0.55], fill="white", width=max(6, r // 4))
    else:
        d.rounded_rectangle([0, 0, w - 1, h - 1], radius=radius, fill=(255, 255, 255, 170))
    return im


def badge(num, size, accent):
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse([0, 0, size - 1, size - 1], fill=accent + (255,), outline=(255, 255, 255, 255), width=8)
    f = pick_font(FONT_EN, int(size * 0.62))
    bb = d.textbbox((0, 0), str(num), font=f)
    d.text(((size - (bb[2] - bb[0])) / 2 - bb[0], (size - (bb[3] - bb[1])) / 2 - bb[1]), str(num), font=f,
           fill=(255, 255, 255))
    return im


def banner_img(w, h, ar, en, accent):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=h // 2, fill=(30, 170, 90, 255), outline=(255, 255, 255, 255),
                        width=6)
    f = fit_font(FONT_AR, ar, w * 0.88, h * 0.4, h * 0.45, d, True)
    t = ar_text(ar)
    bb = d.textbbox((0, 0), t, font=f)
    d.text(((w - (bb[2] - bb[0])) / 2 - bb[0], h * 0.1 - bb[1]), t, font=f, fill=(255, 255, 255))
    f2 = fit_font(FONT_EN, en, w * 0.8, h * 0.28, h * 0.3, d, False)
    bb2 = d.textbbox((0, 0), en, font=f2)
    d.text(((w - (bb2[2] - bb2[0])) / 2 - bb2[0], h * 0.62 - bb2[1]), en, font=f2, fill=(255, 245, 190))
    return im


# ================================================================ تركيب مقطع بـ ffmpeg
def render_clip(out, geo, dur, audio, bubbles, deco, gradient_bg, layers, kb=None, progress=None):
    """
    layers: [{img: Path, x, y, t0, t1?, anim: fade|slide|pop|bob|static}]
    kb: {pic: Path, mask: Path, x, y, w, h}  صورة متحركة (تكبير/تحريك) داخل إطار مدوّر
    progress: (p0, p1) نسبة التقدم في الفيديو كله.
    """
    W, H = geo.W, geo.H
    args, n = [], 0

    def add(path, loop=True):
        nonlocal n
        args.extend(["-loop", "1", "-framerate", str(FPS), "-t", f"{dur:.3f}", "-i", str(path)])
        n += 1
        return n - 1

    ib = add(gradient_bg)
    ibub = add(bubbles)
    idc = add(deco)
    f = [f"[{ib}:v]format=yuv420p[s0]",
         f"[{ibub}:v]format=rgba[bub]",
         f"[s0][bub]overlay=x=0:y='-mod(t*24,{H})':format=auto[s1]",
         f"[{idc}:v]format=rgba[dc]",
         f"[s1][dc]overlay=0:0:format=auto[s2]"]
    cur, k = "s2", 3
    if kb:
        ip = add(kb["pic"])
        im_ = add(kb["mask"])
        ph = random.Random(hash(str(kb["pic"])) & 0xFFFF).random() * 6
        S0, S1 = 0.80, 0.92
        f.append(f"[{ip}:v]scale=w='trunc(iw*({S0}+({S1}-{S0})*t/{dur:.3f})/2)*2':"
                 f"h='trunc(ih*({S0}+({S1}-{S0})*t/{dur:.3f})/2)*2':eval=frame:flags=bilinear,"
                 f"crop=w={kb['w']}:h={kb['h']}:x='(iw-ow)*(0.5+0.45*sin(t*0.5+{ph:.2f}))':"
                 f"y='(ih-oh)*(0.5+0.45*cos(t*0.4+{ph:.2f}))',format=rgba[kp]")
        f.append(f"[{im_}:v]format=gray[km]")
        f.append(f"[kp][km]alphamerge,fade=t=in:st=0:d=0.35:alpha=1[kpic]")
        f.append(f"[{cur}][kpic]overlay=x={kb['x']}:y={kb['y']}:format=auto[s{k}]")
        cur, k = f"s{k}", k + 1
    for L in layers:
        i = add(L["img"])
        t0 = L.get("t0", 0.0)
        anim = L.get("anim", "slide")
        x, y = L["x"], L["y"]
        t1 = L.get("t1")
        chain = "format=rgba"
        d_in = 0.15 if anim == "pop" else 0.35
        if anim != "static":
            chain += f",fade=t=in:st={t0:.3f}:d={d_in}:alpha=1"
        f.append(f"[{i}:v]{chain}[l{k}]")
        if anim == "slide":
            yexpr = f"{y}+70*pow(max(0,1-(t-{t0:.3f})/{d_in}),2)"
        elif anim == "pop":
            yexpr = f"{y}+25*pow(max(0,1-(t-{t0:.3f})/{d_in}),2)"
        elif anim == "bob":
            yexpr = f"{y}-{int(L.get('amp', 22))}*abs(sin((t-{t0:.3f})*3.4))"
        elif anim == "breathe":
            yexpr = f"{y}+{int(L.get('amp', 5))}*sin(t*2.3)"
        elif anim == "hop":
            yexpr = f"{y}-{int(L.get('amp', 26))}*abs(sin(t*6.5))"
        elif anim == "fall":
            yexpr = f"{y}+{int(L.get('speed', 900))}*(t-{t0:.3f})"
        else:
            yexpr = f"{y}"
        end = f"{t1:.3f}" if t1 is not None else f"{dur + 1:.3f}"
        en = f"between(t,{t0:.3f},{end})"
        if L.get("gate"):
            en = f"({en})*({L['gate']})"
        f.append(f"[{cur}][l{k}]overlay=x={x}:y='{yexpr}':enable='{en}':format=auto[s{k}]")
        cur, k = f"s{k}", k + 1
    if progress:
        p0, p1 = progress
        ipr = n
        args.extend(["-f", "lavfi", "-t", f"{dur:.3f}", "-i", f"color=c=0xFFB300:s=16x16:r={FPS}"])
        n += 1
        f.append(f"[{ipr}:v]scale=w='max(2,trunc({W}*({p0:.5f}+({p1 - p0:.5f})*t/{dur:.3f})/2)*2)':h=14:eval=frame,"
                 f"format=rgba[pb]")
        f.append(f"[{cur}][pb]overlay=x=0:y={H - 14}:format=auto[s{k}]")
        cur, k = f"s{k}", k + 1
    f.append(f"[{cur}]format=yuv420p[v]")
    ia = n
    args.extend(["-i", str(audio)])
    script = OUT / (Path(out).stem + ".filter")
    script.write_text(";\n".join(f), encoding="utf-8")
    cmd = (["ffmpeg", "-y", "-loglevel", "error"] + args +
           ["-filter_complex_script", str(script), "-map", "[v]", "-map", f"{ia}:a", "-t", f"{dur:.3f}",
            "-r", str(FPS), "-c:v", "libx264", "-preset", os.getenv("X264_PRESET", "veryfast"), "-crf", "19",
            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-ar", "44100", "-ac", "2", str(out)])
    sh(cmd)
    return out


# ================================================================ الأخوان نور ويوسف
def _kid_sprites(geo, h=None):
    """يرجع {(who, state, wave): Path} بارتفاع h. الحالات: base, open, wide, blink."""
    import kids
    h = int(h or geo.stage)
    cache = getattr(geo, "_sprites", None)
    if cache is None:
        cache = geo._sprites = {}
    if h in cache:
        return cache[h]
    out = {}
    for who in ("noor", "yousef"):
        for wave in (False, True):
            for state, (m, e) in {"base": ("closed", "open"), "open": ("open", "open"),
                                  "wide": ("wide", "open"), "blink": ("closed", "closed")}.items():
                im = kids.draw_kid(who, m, e, wave, 900).crop((0, 50, 900, 900))
                im = im.resize((int(im.width * h / im.height), h), Image.LANCZOS)
                out[(who, state, wave)] = save_png(im, f"kid_{who}_{state}_{int(wave)}_{h}.png")
    cache[h] = out
    return out


def _gate(wins):
    if not wins:
        return "0"
    return "(" + "+".join(f"between(t,{a:.3f},{b:.3f})" for a, b in wins) + ")"


def kid_layers(geo, speech, wave=False, h=None, xs=None, y=None, cheer=None):
    """speech: {'noor': [(t0,t1),...], 'yousef': [...]}. يرجع طبقات الشخصيتين مع حركة الفم والرمش.
    cheer: نوافذ زمنية يقفز فيها الأخوان فرحاً ويرفعان اليد."""
    h = int(h or geo.stage)
    sp = _kid_sprites(geo, h)
    sw = Image.open(sp[("noor", "base", False)]).width
    y = geo.H - 14 - h if y is None else y
    xs = xs or {"noor": int(geo.pad * 0.4), "yousef": geo.W - sw - int(geo.pad * 0.4)}
    cg = _gate(cheer) if cheer else None
    layers = []
    for who, x in xs.items():
        talk = _gate(speech.get(who, []))
        phase = 0.0 if who == "noor" else 1.3
        calm = f"(1-{cg})*" if cg else ""
        gates = {"base": (f"(1-{cg})" if cg else None),
                 "open": f"{calm}{talk}*lt(mod(t,0.26),0.13)",
                 "wide": f"{calm}{talk}*between(mod(t,0.78),0.39,0.52)",
                 "blink": f"{calm}lt(mod(t+{phase},3.6),0.12)"}
        for state in ("base", "open", "wide", "blink"):
            L = {"img": sp[(who, state, wave)], "x": x, "y": y, "t0": 0.0, "anim": "breathe", "amp": 5}
            if gates[state]:
                L["gate"] = gates[state]
            layers.append(L)
        if cg:
            layers.append({"img": sp[(who, "base", True)], "x": x, "y": y, "t0": 0.0, "anim": "hop", "amp": 24,
                           "gate": cg})
            layers.append({"img": sp[(who, "open", True)], "x": x, "y": y, "t0": 0.0, "anim": "hop", "amp": 24,
                           "gate": f"{cg}*lt(mod(t,0.30),0.15)"})
    return layers


def confetti_layer(geo, t0, length=3.2, seed=1):
    """قصاصات ملوّنة تتساقط على الشاشة (للاحتفال)."""
    W, H = geo.W, geo.H
    r = random.Random(seed)
    im = Image.new("RGBA", (W, H * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cols = [(255, 80, 100), (255, 200, 40), (60, 190, 120), (70, 140, 240), (190, 90, 220), (255, 140, 60)]
    for _ in range(int(150 * W / 1080)):
        x, y = r.randint(0, W), r.randint(0, H * 2)
        w, h = r.randint(10, 24), r.randint(10, 24)
        c = r.choice(cols)
        if r.random() < 0.5:
            d.ellipse([x, y, x + w, y + w], fill=c)
        else:
            d.rectangle([x, y, x + w, y + h], fill=c)
    return {"img": save_png(im, f"confetti_{seed}_{W}.png"), "x": 0, "y": -2 * H, "t0": t0, "t1": t0 + length,
            "anim": "fall", "speed": int(H * 3.0 / length) + 5}


# ================================================================ الصورة المصغّرة (Thumbnail)
def make_thumbnail(title_ar, title_en, emoji, day, out):
    """صورة 1280x720: نور ويوسف على اليسار، العنوان الكبير والإيموجي على اليمين."""
    import kids
    W, H = 1280, 720
    top, bot, acc = PALETTES[day % len(PALETTES)]
    im = Image.new("RGBA", (W, H))
    px = ImageDraw.Draw(im)
    for y in range(H):
        k = y / (H - 1)
        px.line([(0, y), (W, y)], fill=tuple(int(top[i] * (1 - k) + bot[i] * k) for i in range(3)) + (255,))
    r = random.Random(day)
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    for _ in range(14):
        c, x, y = r.randint(40, 150), r.randint(0, W), r.randint(0, H)
        od.ellipse([x - c, y - c, x + c, y + c], fill=(255, 255, 255, 38))
    im = Image.alpha_composite(im, ov)
    # الأخوان
    kh = 470
    for who, x in (("noor", -70), ("yousef", 210)):
        k = kids.draw_kid(who, "open", "open", True, 900).crop((0, 50, 900, 900))
        k = k.resize((int(k.width * kh / k.height), kh), Image.LANCZOS)
        im.alpha_composite(k, (x, H - kh + 30))
    d = ImageDraw.Draw(im)
    # العنوان العربي (سطران كحد أقصى)
    box_l, box_r = 600, W - 40
    words = title_ar.split()
    lines = [title_ar]
    if len(words) > 2:
        mid = (len(words) + 1) // 2
        lines = [" ".join(words[:mid]), " ".join(words[mid:])]
    f = None
    for st in range(150, 40, -6):
        f = pick_font(FONT_AR, st)
        if all(d.textbbox((0, 0), ar_text(t), font=f, stroke_width=10)[2] <= box_r - box_l for t in lines):
            break
    y = 40
    for t in lines:
        tx = ar_text(t)
        bb = d.textbbox((0, 0), tx, font=f, stroke_width=10)
        x = box_r - (bb[2] - bb[0]) - bb[0]
        d.text((x, y - bb[1]), tx, font=f, fill=(255, 255, 255), stroke_width=10, stroke_fill=(40, 30, 70))
        y += int((bb[3] - bb[1]) * 1.12)
    # الإيموجي الكبير
    e = emoji_img(emoji or "⭐", 230)
    if e:
        im.alpha_composite(e, (int((box_l + box_r) / 2 - e.width / 2), max(y + 10, 330)))
    # شريط الإنجليزية
    fe = pick_font(FONT_EN, 46)
    te = (title_en or "")[:40]
    bb = d.textbbox((0, 0), te, font=fe)
    pw, ph = bb[2] - bb[0] + 50, 80
    px0 = box_r - pw
    d.rounded_rectangle([px0, 570, box_r, 570 + ph - 12], radius=30, fill=(255, 255, 255, 235), outline=acc, width=5)
    d.text((px0 + 25 - bb[0], 570 + (ph - 12 - (bb[3] - bb[1])) / 2 - bb[1]), te, font=fe, fill=acc)
    # شارة القناة
    fc = pick_font(FONT_AR, 40)
    tc = ar_text("عالم التعلم")
    bb = d.textbbox((0, 0), tc, font=fc)
    d.rounded_rectangle([20, 20, 40 + bb[2] - bb[0], 90], radius=30, fill=acc)
    d.text((30 - bb[0], 55 - (bb[3] - bb[1]) / 2 - bb[1]), tc, font=fc, fill=(255, 255, 255))
    im.convert("RGB").save(out, quality=92)
    return out


# ================================================================ المقدمة الثابتة للفيديوهات الطويلة
def render_intro(ctx, idx, progress=None):
    geo, W, H = ctx.geo, ctx.geo.W, ctx.geo.H
    pre = f"s{idx:03d}"
    pal = ((140, 210, 255), (255, 190, 220), (214, 70, 60))
    parts = [("sfx", "jingle", "jg"), ("say", "أَهْلًا بِكُمْ فِي عَالَمِ التَّعَلُّمِ!", "ar", "a1"),
             ("sil", 0.25), ("say", "Welcome to Learning World!", "en", "e1"), ("sil", 0.9)]
    audio, dur, marks = compose_audio(parts, pre + "_a")
    gbg = save_png(make_gradient_bg(geo, pal), pre + "_bg.png")
    bub = save_png(make_bubbles(geo, 77), pre + "_bub.png")
    blank = save_png(Image.new("RGBA", (W, H), (0, 0, 0, 0)), pre + "_deco.png")
    # بطاقة الشعار
    vertical = geo.vertical
    cw, ch = (int(W * 0.88), int(H * 0.2)) if vertical else (int(W * 0.60), int(H * 0.42))
    m = 40
    card = Image.new("RGBA", (cw + 2 * m, ch + 2 * m), (0, 0, 0, 0))
    d = ImageDraw.Draw(card)
    d.rounded_rectangle([m + 8, m + 14, m + cw + 8, m + ch + 14], radius=int(ch * 0.18), fill=(0, 0, 0, 70))
    card = card.filter(ImageFilter.GaussianBlur(10))
    d = ImageDraw.Draw(card)
    d.rounded_rectangle([m, m, m + cw, m + ch], radius=int(ch * 0.18), fill=(255, 255, 255, 245),
                        outline=pal[2], width=8)
    f1 = fit_font(FONT_AR, "عالم التعلم", cw * 0.8, ch * 0.42, ch * 0.5, d, True)
    t1 = ar_text("عالم التعلم")
    bb = d.textbbox((0, 0), t1, font=f1)
    d.text((m + (cw - (bb[2] - bb[0])) / 2 - bb[0], m + ch * 0.07 - bb[1]), t1, font=f1, fill=pal[2],
           stroke_width=3, stroke_fill=(255, 235, 200))
    f2 = fit_font(FONT_AR, "نتعلّم، نلعب، نكتشف", cw * 0.7, ch * 0.16, ch * 0.2, d, True)
    t2 = ar_text("نتعلّم، نلعب، نكتشف")
    bb = d.textbbox((0, 0), t2, font=f2)
    d.text((m + (cw - (bb[2] - bb[0])) / 2 - bb[0], m + ch * 0.55 - bb[1]), t2, font=f2, fill=(40, 90, 200))
    f3 = fit_font(FONT_EN, "Learning World", cw * 0.5, ch * 0.13, ch * 0.16, d, False)
    bb = d.textbbox((0, 0), "Learning World", font=f3)
    d.text((m + (cw - (bb[2] - bb[0])) / 2 - bb[0], m + ch * 0.80 - bb[1]), "Learning World", font=f3,
           fill=(90, 90, 130))
    cx, cy = int((W - cw) / 2 - m), int(H * (0.06 if not vertical else 0.08))
    layers = [{"img": save_png(card, pre + "_logo.png"), "x": cx, "y": cy, "t0": 0.3, "anim": "pop"}]
    # نجوم وأيقونات
    for k, (emo, fx, fy, sz) in enumerate((("✨", 0.07, 0.12, 0.13), ("⭐", 0.84, 0.10, 0.12),
                                           ("📚", 0.06, 0.5, 0.12), ("🔤", 0.86, 0.5, 0.12))):
        e = emoji_img(emo, H * sz)
        if e:
            layers.append({"img": save_png(e, f"{pre}_e{k}.png"), "x": int(W * fx), "y": int(H * fy),
                           "t0": 0.5 + 0.12 * k, "anim": "bob", "amp": 16})
    # الأخوان بحجم كبير
    h_k = int(H * (0.42 if not vertical else 0.30))
    sw = Image.open(_kid_sprites(geo, h_k)[("noor", "base", True)]).width
    gap = int(W * 0.04)
    xs = {"noor": int(W / 2 - sw - gap / 2), "yousef": int(W / 2 + gap / 2)}
    layers += kid_layers(geo, {"noor": [marks["a1"]], "yousef": [marks["e1"]]}, wave=True, h=h_k, xs=xs,
                         y=H - h_k + int(H * 0.02))
    layers.append(confetti_layer(geo, 0.1, 2.8, seed=11))
    out = OUT / f"{pre}.mp4"
    render_clip(out, geo, dur, audio, bub, blank, gbg, layers, None, progress)
    return out, dur


# ================================================================ مشهد كامل
class Ctx:
    def __init__(self, size, images):
        self.size = size
        self.geo = Geo(size)
        self.images = images  # {visual: Path|None}
        self.n = 0


def _paste_layer(img, name):
    return save_png(img, name)


def render_scene(ctx, scene, idx, progress):
    geo, W, H = ctx.geo, ctx.geo.W, ctx.geo.H
    pal = PALETTES[idx % len(PALETTES)]
    accent = pal[2]
    kind = scene.get("kind", "text")
    pre = f"s{idx:03d}"
    if kind == "intro":
        return render_intro(ctx, idx, progress)
    if kind == "quiz":
        return render_quiz(ctx, scene, idx, progress)

    # ---------- الصوت
    parts = [("sil", 0.45), ("say", scene.get("ar_tts") or scene["ar"], "ar", "ar"), ("sil", 0.35),
             ("say", scene.get("en_tts") or scene["en"], "en", "en"), ("sil", scene.get("tail", 0.7))]
    audio, dur, marks = compose_audio(parts, pre + "_a")
    t_ar, t_en = marks["ar"], marks["en"]

    gbg = save_png(make_gradient_bg(geo, pal), pre + "_bg.png")
    bub = save_png(make_bubbles(geo, idx * 13 + 5), pre + "_bub.png")
    deco = save_png(make_deco(geo, pal, with_box=True), pre + "_deco.png")
    layers, kb = [], None
    bx, by = geo.box[0], geo.box[1]

    # ---------- الصورة / البطاقة
    if kind == "text":
        path = ctx.images.get(scene.get("visual")) if scene.get("visual") else None
        if path:
            raw = Image.open(path).convert("RGB")
            big = ImageOps.fit(raw, (int(geo.bw * 1.3), int(geo.bh * 1.3)), Image.LANCZOS)
            big = big.filter(ImageFilter.UnsharpMask(radius=1.2, percent=60, threshold=3))
            kb = {"pic": save_png(big, pre + "_pic.png"),
                  "mask": save_png(rounded_mask((geo.bw, geo.bh), geo.radius), pre + "_mask.png"),
                  "x": bx, "y": by, "w": geo.bw, "h": geo.bh}
        else:
            card, R = circle_card(geo, pal)
            layers.append({"img": save_png(card, pre + "_card.png"), "x": bx, "y": by, "t0": 0.05, "anim": "pop"})
            e = emoji_img(scene.get("emoji", "⭐"), R * 1.35)
            if e:
                layers.append({"img": save_png(e, pre + "_emo.png"), "x": int(bx + (geo.bw - e.width) / 2),
                               "y": int(by + (geo.bh - e.height) / 2 + 10), "t0": 0.25, "anim": "bob", "amp": 18})
    elif kind == "title":
        card, R = circle_card(geo, pal)
        layers.append({"img": save_png(card, pre + "_card.png"), "x": bx, "y": by, "t0": 0.05, "anim": "pop"})
        e = emoji_img(scene.get("emoji", "🌟"), R * 1.35)
        if e:
            layers.append({"img": save_png(e, pre + "_emo.png"), "x": int(bx + (geo.bw - e.width) / 2),
                           "y": int(by + (geo.bh - e.height) / 2 + 14), "t0": 0.25, "anim": "bob", "amp": 26})
    elif kind == "letter":
        layers.append({"img": save_png(letter_card(geo, scene, accent), pre + "_card.png"), "x": bx, "y": by,
                       "t0": 0.1, "anim": "pop"})
        e = emoji_img(scene.get("emoji", "✨"), geo.bh * 0.16) if scene.get("emoji") else None
        if e:
            layers.append({"img": save_png(e, pre + "_emo.png"), "x": bx + geo.bw - e.width - 24, "y": by + 20,
                           "t0": 0.5, "anim": "bob", "amp": 10})
    elif kind == "forms":
        layers.append({"img": save_png(forms_card(geo, scene, accent), pre + "_card.png"), "x": bx, "y": by,
                       "t0": 0.1, "anim": "pop"})
    elif kind == "count":
        n = scene["n"]
        layers.append({"img": save_png(card_base(geo.bw, geo.bh, geo.radius, accent), pre + "_card.png"),
                       "x": bx, "y": by, "t0": 0.05, "anim": "pop"})
        pos = emoji_grid_positions(n, geo.bw, geo.bh)
        a0, a1 = t_ar[0] + (t_ar[1] - t_ar[0]) * 0.22, t_ar[1]
        for i, (px, py, size) in enumerate(pos):
            e = emoji_img(scene["emoji"], size)
            if e:
                ti = a0 + (a1 - a0) * (i / max(1, n))
                layers.append({"img": save_png(e, f"{pre}_c{i}.png"), "x": int(bx + px), "y": int(by + py),
                               "t0": ti, "anim": "pop"})

    # ---------- لوحة النص
    px0, py0, px1, py1 = geo.panel
    pnl = render_panel(px1 - px0, py1 - py0, scene["ar"], scene["en"], accent, geo.base)
    m = pnl["m"]
    layers.append({"img": save_png(pnl["img"], pre + "_panel.png"), "x": px0 - m, "y": py0 - m, "t0": 0.2,
                   "anim": "slide"})
    # إبراز الكلمة المنطوقة
    wins = word_windows(pnl["words"], t_ar[0] + 0.05, t_ar[1] - 0.05)
    for i, (b, (w0, w1)) in enumerate(zip(pnl["words"], wins)):
        him, hx, hy = word_highlight(b, pnl["f_ar"], accent)
        layers.append({"img": save_png(him, f"{pre}_w{i}.png"), "x": px0 - m + hx, "y": py0 - m + hy,
                       "t0": w0, "t1": w1, "anim": "static"})
    for i, b in enumerate(pnl["en"]):
        him, hx, hy = en_highlight(b, pnl["f_en"], accent)
        layers.append({"img": save_png(him, f"{pre}_e{i}.png"), "x": px0 - m + hx, "y": py0 - m + hy,
                       "t0": t_en[0], "t1": t_en[1] + 0.1, "anim": "static"})

    celebrate = kind == "title" and scene.get("emoji") in ("🏆", "🌟")
    layers += kid_layers(geo, {"noor": [(t_ar[0], t_ar[1])], "yousef": [(t_en[0], t_en[1])]},
                         wave=(kind == "title" and not celebrate),
                         cheer=[(0.3, dur - 0.2)] if celebrate else None)
    if celebrate:
        layers.append(confetti_layer(geo, 0.3, min(3.2, dur - 0.5), seed=idx + 3))
    out = OUT / f"{pre}.mp4"
    render_clip(out, geo, dur, audio, bub, deco, gbg, layers, kb, progress)
    return out, dur


def render_quiz(ctx, q, idx, progress):
    geo, W, H = ctx.geo, ctx.geo.W, ctx.geo.H
    pal = PALETTES[idx % len(PALETTES)]
    accent = pal[2]
    pre = f"s{idx:03d}"
    opts = q["options"]
    ans = q["answer"]
    show_en = q.get("answer_en_only", False)
    for o in opts:
        o["show_en"] = show_en
    right = opts[ans]
    # ---------- الصوت
    parts = [("sil", 0.4), ("say", q.get("ar_tts") or q["ar"], "ar", "q_ar"), ("sil", 0.3),
             ("say", q["en"], "en", "q_en"), ("sil", 0.4)]
    for i, o in enumerate(opts):
        if show_en:
            parts.append(("say", o["en"], "en", f"o{i}"))
        else:
            parts.append(("say", o.get("ar_tts") or o["ar"], "ar", f"o{i}"))
        parts.append(("sil", 0.25))
    parts += [("sil", 0.2), ("say", "فَكِّرُوا!", "ar", "think"), ("sil", 0.3)]
    for c in (5, 4, 3, 2, 1):
        parts += [("sfx", "tick", f"c{c}"), ("sil", 0.88)]
    parts += [("sfx", "ding", "ding"), ("sil", 0.2)]
    if show_en:
        parts += [("say", "الإِجَابَةُ الصَّحِيحَةُ:", "ar", "ans_ar"), ("sil", 0.15),
                  ("say", right["en"], "en", "ans_w"), ("sil", 0.7)]
    else:
        parts += [("say", "الإِجَابَةُ الصَّحِيحَةُ: " + (right.get("ar_tts") or right["ar"]), "ar", "ans_ar"),
                  ("sil", 0.3), ("say", f"The answer is {right['en']}", "en", "ans_en"), ("sil", 0.8)]
    audio, dur, marks = compose_audio(parts, pre + "_a")

    gbg = save_png(make_gradient_bg(geo, pal), pre + "_bg.png")
    bub = save_png(make_bubbles(geo, idx * 13 + 5), pre + "_bub.png")
    deco = save_png(make_deco(geo, pal, with_box=False), pre + "_deco.png")
    layers = []
    pad = geo.pad
    top = geo.head_b
    avail = geo.bottom - top
    if geo.vertical:
        qh = int(avail * (0.30 if q.get("stimulus") else 0.20))
        th = int(avail * 0.20)
        gap = int(pad * 0.55)
        tiles_xy = [(pad, top + qh + gap + i * (th + gap)) for i in range(3)]
        tw = W - 2 * pad
        cd_y = tiles_xy[-1][1] + th + gap
        cd_h = geo.bottom - cd_y
    else:
        qh = int(avail * (0.52 if q.get("stimulus") else 0.31))
        gap = int(pad * 0.5)
        tw = int((W - 2 * pad - 2 * gap) / 3)
        th = int(avail * (0.30 if q.get("stimulus") else 0.37))
        ty = top + qh + gap
        tiles_xy = [(pad + (2 - i) * (tw + gap), ty) for i in range(3)]
        cd_y = ty + th + gap
        cd_h = geo.bottom - cd_y
    # لوحة السؤال
    pnl = render_panel(W - 2 * pad, qh, q["ar"], q["en"], accent, geo.base * (0.72 if q.get("stimulus") else 0.78))
    m = pnl["m"]
    qimg = pnl["img"]
    if q.get("stimulus"):
        # إيموجي الصورة تحت السؤال: نعيد رسم اللوحة بنص أصغر في الجزء العلوي
        qimg = Image.new("RGBA", pnl["img"].size, (0, 0, 0, 0))
        d = ImageDraw.Draw(qimg)
        r = int(min(W - 2 * pad, qh) * 0.12)
        d.rounded_rectangle([m + 6, m + 10, m + W - 2 * pad + 6, m + qh + 10], radius=r, fill=(0, 0, 0, 55))
        d.rounded_rectangle([m, m, m + W - 2 * pad, m + qh], radius=r, fill=(255, 255, 255, 246), outline=accent,
                            width=6)
        f = fit_font(FONT_AR, q["ar"], (W - 2 * pad) * 0.9, qh * 0.2, geo.base * 0.07, d, True)
        t = ar_text(q["ar"])
        bb = d.textbbox((0, 0), t, font=f)
        d.text((m + (W - 2 * pad - (bb[2] - bb[0])) / 2 - bb[0], m + qh * 0.07 - bb[1]), t, font=f, fill=INK,
               stroke_width=3, stroke_fill=(255, 255, 255))
        items = split_emoji(q["stimulus"])
        n = len(items)
        cols = min(n, 10) if not geo.vertical else min(n, 5)
        rows = math.ceil(n / cols)
        area_w, area_h = (W - 2 * pad) * 0.9, qh * 0.62
        cell = min(area_w / cols, area_h / rows)
        y0 = m + qh * 0.32 + (area_h - rows * cell) / 2
        for i, it in enumerate(items):
            r_, c_ = divmod(i, cols)
            in_row = cols if r_ < rows - 1 else n - (rows - 1) * cols
            off = (cols - in_row) * cell / 2 if r_ == rows - 1 else 0
            e = emoji_img(it, cell * 0.82)
            if e:
                qimg.alpha_composite(e, (int(m + ((W - 2 * pad) - cols * cell) / 2 + off + c_ * cell +
                                             (cell - e.width) / 2), int(y0 + r_ * cell + (cell - e.height) / 2)))
    layers.append({"img": save_png(qimg, pre + "_q.png"), "x": pad - m, "y": top - m, "t0": 0.2, "anim": "slide"})
    # بطاقات الخيارات
    for i, o in enumerate(opts):
        tile = option_tile(tw, th, o, accent, int(min(tw, th) * 0.12))
        t_i = marks[f"o{i}"][0] - 0.05
        layers.append({"img": save_png(tile, f"{pre}_t{i}.png"), "x": tiles_xy[i][0], "y": tiles_xy[i][1],
                       "t0": t_i, "anim": "pop"})
    # عدّاد تنازلي
    bs = int(min(cd_h * 0.9, W * 0.18))
    if bs > 40:
        for c in (5, 4, 3, 2, 1):
            t0 = marks[f"c{c}"][0]
            layers.append({"img": save_png(badge(c, bs, accent), f"{pre}_b{c}.png"), "x": int((W - bs) / 2),
                           "y": int(cd_y + (cd_h - bs) / 2), "t0": t0, "t1": t0 + 0.95, "anim": "pop"})
    # كشف الإجابة
    t_ans = marks["ding"][0]
    for i in range(3):
        ov = reveal_overlay(tw, th, i == ans, int(min(tw, th) * 0.12))
        layers.append({"img": save_png(ov, f"{pre}_r{i}.png"), "x": tiles_xy[i][0], "y": tiles_xy[i][1],
                       "t0": t_ans, "anim": "fade"})
    bw_, bh_ = int(W * 0.8), int(min(cd_h * 0.9, W * 0.2))
    if bh_ > 50:
        lab_ar = ("الإجابة: " + right.get("en", "")) if show_en else ("الإجابة: " + right["ar"])
        ban = banner_img(bw_, bh_, lab_ar if not show_en else "الإجابة الصحيحة", right["en"], accent)
        layers.append({"img": save_png(ban, pre + "_ban.png"), "x": int((W - bw_) / 2),
                       "y": int(cd_y + (cd_h - bh_) / 2), "t0": t_ans + 0.1, "anim": "slide"})
    noor_l = ["q_ar", "think", "ans_ar"] + ([] if show_en else [f"o{i}" for i in range(len(opts))])
    yousef_l = ["q_en", "ans_en", "ans_w"] + ([f"o{i}" for i in range(len(opts))] if show_en else [])
    speech = {"noor": [marks[k] for k in noor_l if k in marks], "yousef": [marks[k] for k in yousef_l if k in marks]}
    layers += kid_layers(geo, speech, cheer=[(t_ans + 0.1, min(dur - 0.1, t_ans + 2.9))])
    layers.append(confetti_layer(geo, t_ans + 0.1, 2.8, seed=idx + 50))
    out = OUT / f"{pre}.mp4"
    render_clip(out, geo, dur, audio, bub, deco, gbg, layers, None, progress)
    return out, dur


# ================================================================ موسيقى خلفية هادئة (تُولَّد برمجياً)
def make_music(path, seconds=48, seed=7):
    import numpy as np
    import wave
    sr = 24000
    rnd = random.Random(seed)
    bpm = 92
    beat = 60 / bpm
    notes = {"C": 261.63, "D": 293.66, "E": 329.63, "G": 392.0, "A": 440.0, "F": 349.23, "B": 493.88}
    chords = [("C", ["C", "E", "G"]), ("A", ["A", "C", "E"]), ("F", ["F", "A", "C"]), ("G", ["G", "B", "D"])]
    pent = [523.25, 587.33, 659.25, 783.99, 880.0, 1046.5]
    total = int(sr * seconds)
    buf = np.zeros(total, dtype=np.float32)

    def tone(freq, dur, amp):
        n = int(sr * dur)
        t = np.arange(n) / sr
        env = np.exp(-t * 4.5) * np.minimum(1, t * 200)
        y = np.sin(2 * np.pi * freq * t) + 0.3 * np.sin(2 * np.pi * freq * 2 * t) + 0.1 * np.sin(2 * np.pi * freq * 3 * t)
        return (y * env * amp).astype(np.float32)

    t_cur, step = 0.0, 0
    while t_cur < seconds - 1:
        name, tri = chords[(step // 8) % 4]
        # الجهير: نغمة على أول كل مقياس
        if step % 8 == 0:
            f0 = {"C": 130.8, "A": 110.0, "F": 87.3, "G": 98.0}[name]
            seg = tone(f0, 2.4, 0.5)
            i0 = int(t_cur * sr)
            buf[i0:i0 + len(seg)] += seg[:max(0, total - i0)]
        # لحن صندوق الموسيقى
        if rnd.random() < 0.75:
            f = rnd.choice(pent)
            seg = tone(f, 1.2, 0.28)
            i0 = int(t_cur * sr)
            buf[i0:i0 + len(seg)] += seg[:max(0, total - i0)]
        t_cur += beat / 2
        step += 1
    buf /= max(0.01, np.abs(buf).max())
    fade = int(sr * 1.0)
    buf[:fade] *= np.linspace(0, 1, fade)
    buf[-fade:] *= np.linspace(1, 0, fade)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((buf * 32767 * 0.9).astype("<i2").tobytes())
    return path


def finalize(clips, out, with_music=True):
    """يدمج المقاطع ثم يضيف موسيقى خفيفة تحت الصوت."""
    lst = OUT / (Path(out).stem + "_list.txt")
    lst.write_text("".join(f"file '{Path(c).resolve()}'\n" for c in clips))
    raw = OUT / (Path(out).stem + "_raw.mp4")
    sh(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(raw)])
    if not with_music:
        os.replace(raw, out)
        return out
    try:
        mus = OUT / "music.wav"
        if not mus.exists():
            make_music(mus)
        sh(["ffmpeg", "-y", "-loglevel", "error", "-i", str(raw), "-stream_loop", "-1", "-i", str(mus),
            "-filter_complex",
            "[1:a]volume=0.11,aformat=sample_rates=44100:channel_layouts=stereo[m];"
            "[0:a]aformat=sample_rates=44100:channel_layouts=stereo[v];"
            "[v][m]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.95[a]",
            "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest", str(out)])
    except Exception as e:  # noqa
        print(f"[music] تخطي الموسيقى: {str(e)[:200]}")
        os.replace(raw, out)
    return out
