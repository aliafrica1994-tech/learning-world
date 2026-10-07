#!/usr/bin/env python3
"""
قناة «عالم التعلم» — توليد ورفع فيديوهات تعليمية للأطفال 5-8 سنوات (عربي فصيح + إنجليزي).

الاستخدام:
    python main.py short      # فيديو قصير عمودي (Shorts)
    python main.py long       # فيديو طويل أفقي (عدة دروس مجمّعة)

متغيرات البيئة (أسرار GitHub):
    GEMINI_API_KEY            مفتاح Gemini المجاني (اختياري؛ بدونه تُستخدم دروس احتياطية)
    YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN   لرفع الفيديو إلى يوتيوب
    DRY_RUN=1                 ينتج الفيديو دون رفعه
    FAKE_TTS=1                صوت صامت للاختبار فقط
    PRIVACY                   public | unlisted | private (الافتراضي public)
"""
import json
import os
import random
import re
import shutil
import subprocess
import sys
import time
import asyncio
import datetime as dt
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFont

from lessons_fallback import FALLBACK_LESSONS

ROOT = Path(__file__).parent
OUT = ROOT / "output"
STATE = ROOT / "state" / "history.json"

CHANNEL_AR = "عالم التعلم"
CHANNEL_EN = "Learning World"

AR_VOICE = os.getenv("AR_VOICE", "ar-SA-ZariyahNeural")
EN_VOICE = os.getenv("EN_VOICE", "en-US-AnaNeural")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

# المجالات التعليمية مقسمة حسب العمر. يدور النظام عليها يومياً.
CATEGORIES = [
    ("الحروف العربية", "5-6"), ("الأرقام والعدّ", "5-6"), ("الألوان", "5-6"),
    ("الحيوانات وأصواتها", "5-8"), ("الفواكه والخضروات", "5-8"),
    ("الأشكال الهندسية", "5-8"), ("أجزاء الجسم والحواس", "5-8"),
    ("القيم والأخلاق (الصدق، الشكر، التعاون)", "7-8"),
    ("العلوم المبسطة (الطقس، النباتات، الفضاء)", "7-8"),
    ("الحروف الإنجليزية والكلمات الأولى", "5-8"),
    ("الجمع والطرح البسيط", "7-8"),
    ("المهن والأماكن من حولنا", "5-8"),
    ("الصحة والنظافة والعادات الجيدة", "5-8"),
    ("أيام الأسبوع والشهور والفصول", "7-8"),
]

BG_COLORS = [(255, 223, 128), (170, 220, 255), (200, 240, 190), (255, 200, 210),
             (220, 200, 255), (255, 210, 160)]


# ---------------------------------------------------------------- الحالة
def load_history():
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except Exception:
        return {"counter": 0, "titles": []}


def save_history(h):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    h["titles"] = h["titles"][-120:]
    STATE.write_text(json.dumps(h, ensure_ascii=False, indent=1), encoding="utf-8")


# ---------------------------------------------------------------- الدروس
PROMPT = """أنت معلم أطفال محترف للوطن العربي. اكتب درساً قصيراً لأطفال بعمر {age} سنوات في موضوع: {cat}.
الشروط:
- عربية فصحى مبسطة جداً وجمل قصيرة (حتى 14 كلمة)، وإنجليزية بسيطة موازية لها.
- {n} مشاهد، كل مشهد فكرة واحدة واضحة مع مثال محسوس.
- محتوى آمن تماماً للأطفال، دون أي عنف أو مخاوف أو إشارات تجارية.
- لا تكرر هذه العناوين السابقة: {prev}
- لكل جملة عربية أضف الحقل "ar_tts": الجملة نفسها حرفياً لكن مشكولة بالكامل (فتحة وضمة وكسرة وسكون وشدة وتنوين) على أصح قواعد الفصحى، لأنها ستُقرأ بصوت آلي. وكذلك "title_ar_tts" للعنوان.
- أرجع JSON فقط بهذا الشكل بالضبط:
{{"title_ar": "...", "title_ar_tts": "...", "title_en": "...", "scenes": [{{"ar": "...", "ar_tts": "...", "en": "...", "emoji": "إيموجي واحد", "visual": "English prompt to draw a cute simple child-friendly cartoon picture for this scene"}}]}}"""


def gemini_lesson(cat, age, n, history):
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        return None
    prompt = PROMPT.format(age=age, cat=cat, n=n, prev=" | ".join(history["titles"][-25:]) or "لا يوجد")
    body = {"contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseMimeType": "application/json", "temperature": 0.9}}
    for model in gemini_models(key)[:8]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
        for attempt in range(2):
            try:
                r = requests.post(url, json=body, timeout=90)
                if r.status_code in (404, 400, 403):  # النموذج غير متاح لهذا المفتاح: جرّب التالي
                    print(f"[gemini] النموذج {model} غير متاح ({r.status_code})")
                    break
                r.raise_for_status()
                text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
                data = json.loads(text)
                if isinstance(data, list):
                    data = data[0]
                scenes = [s for s in data["scenes"] if s.get("ar") and s.get("en")]
                if len(scenes) < 2:
                    raise ValueError("مشاهد قليلة")
                data["scenes"] = scenes
                data["category"], data["age"] = cat, age
                print(f"[gemini] تم باستخدام النموذج {model}")
                return data
            except Exception as e:  # noqa
                # لا نطبع نص الخطأ لأنه يتضمن الرابط والمفتاح؛ نكتفي بنوعه ورمز الحالة
                code = getattr(getattr(e, "response", None), "status_code", "")
                print(f"[gemini] {model} محاولة {attempt + 1} فشلت: {type(e).__name__} {code}")
                time.sleep(6)
    return None


def gemini_models(key):
    """النماذج المرشّحة بالترتيب: المحدد يدوياً، ثم أسماء شائعة، ثم ما تعرضه Google لمفتاحك."""
    names = []
    if os.getenv("GEMINI_MODEL"):
        names.append(os.getenv("GEMINI_MODEL"))
    names += ["gemini-flash-latest", "gemini-2.5-flash", "gemini-2.0-flash-001"]
    try:
        r = requests.get("https://generativelanguage.googleapis.com/v1beta/models",
                         params={"key": key, "pageSize": 200}, timeout=30)
        found = []
        for m in r.json().get("models", []):
            n = m.get("name", "").split("/")[-1]
            if ("generateContent" in m.get("supportedGenerationMethods", []) and "flash" in n
                    and not any(x in n for x in ("image", "tts", "live", "audio", "embed", "lite"))):
                found.append(n)
        stable = sorted([n for n in found if "preview" not in n and "exp" not in n], reverse=True)
        found = stable + sorted([n for n in found if n not in stable], reverse=True)
        print("[gemini] نماذج متاحة:", ", ".join(found[:8]) or "لا شيء")
        names += found
    except Exception as e:  # noqa
        print(f"[gemini] تعذر جلب قائمة النماذج: {type(e).__name__}")
    seen, out = set(), []
    for n in names:
        if n not in seen:
            seen.add(n)
            out.append(n)
    return out


def fallback_lesson(history):
    used = set(history["titles"])
    pool = [l for l in FALLBACK_LESSONS if l["title_ar"] not in used] or FALLBACK_LESSONS
    return random.choice(pool)


def get_lesson(history, n_scenes):
    cat, age = CATEGORIES[history["counter"] % len(CATEGORIES)]
    lesson = gemini_lesson(cat, age, n_scenes, history) or fallback_lesson(history)
    return lesson


# ---------------------------------------------------------------- النصوص والخطوط
FONT_AR_CANDIDATES = [
    "/usr/share/fonts/truetype/noto/NotoNaskhArabic-Bold.ttf",
    "/usr/share/fonts/truetype/noto/NotoSansArabic-Bold.ttf",
    "/usr/share/fonts/opentype/noto/NotoNaskhArabic-Bold.ttf",
    "/usr/share/fonts/truetype/hosny-amiri/Amiri-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]
FONT_EN_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
]
EMOJI_FONT = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"


def pick_font(cands, size):
    for p in cands:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def ar_text(s):
    """تشكيل الحروف العربية واتجاه الكتابة (يعمل مع أو بدون raqm)."""
    try:
        from PIL import features
        if features.check("raqm"):  # Pillow يشكّل العربية بنفسه
            return s
        import arabic_reshaper
        from bidi.algorithm import get_display
        return get_display(arabic_reshaper.reshape(s))
    except Exception:
        return s


def wrap(draw, text, font, max_w, arabic):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        t = (cur + " " + w).strip()
        shown = ar_text(t) if arabic else t
        if draw.textlength(shown, font=font) <= max_w or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def draw_lines(draw, lines, font, cx, y, arabic, fill, stroke=(0, 0, 0)):
    lh = font.size * 1.35
    for ln in lines:
        shown = ar_text(ln) if arabic else ln
        w = draw.textlength(shown, font=font)
        draw.text((cx - w / 2, y), shown, font=font, fill=fill,
                  stroke_width=max(2, font.size // 16), stroke_fill=stroke)
        y += lh
    return y


def emoji_image(ch, size):
    try:
        f = ImageFont.truetype(EMOJI_FONT, 109)
        im = Image.new("RGBA", (136, 128), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((0, 0), ch, font=f, embedded_color=True)
        return im.resize((size, int(size * 128 / 136)), Image.LANCZOS)
    except Exception:
        return None


# ---------------------------------------------------------------- الصور والتصميم
PALETTES = [  # (أعلى، أسفل، لون مميز)
    ((255, 214, 102), (255, 150, 120), (214, 70, 60)),
    ((140, 210, 255), (120, 150, 255), (40, 90, 200)),
    ((170, 235, 170), (90, 200, 170), (20, 130, 100)),
    ((255, 190, 220), (200, 150, 255), (150, 60, 190)),
    ((255, 225, 150), (140, 220, 200), (30, 140, 130)),
    ((190, 200, 255), (255, 180, 200), (190, 70, 120)),
]
STYLE = ("cute 3D cartoon illustration for small children, Pixar style, soft lighting, "
         "vibrant pastel colors, centered subject, clean simple background, high quality, "
         "no text, no letters, no watermark")


def fetch_image(visual, seed):
    """صورة مربعة 1024 من Pollinations مع إعادة المحاولة؛ None عند الفشل."""
    prompt = f"{visual}, {STYLE}"
    for attempt in range(3):
        url = ("https://image.pollinations.ai/prompt/" + requests.utils.quote(prompt) +
               f"?width=1024&height=1024&model=flux&nologo=true&enhance=true&seed={seed + attempt * 7}")
        try:
            r = requests.get(url, timeout=90)
            if r.ok and r.headers.get("content-type", "").startswith("image") and len(r.content) > 20000:
                tmp = OUT / f"dl_{seed}.img"
                tmp.write_bytes(r.content)
                return Image.open(tmp).convert("RGB")
            print(f"[image] رمز {r.status_code} (محاولة {attempt + 1})")
        except Exception as e:  # noqa
            print(f"[image] فشل: {type(e).__name__} (محاولة {attempt + 1})")
        time.sleep(5)
    return None


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


def fit_text(draw, text, font_paths, max_w, max_h, start, minimum, arabic):
    """أكبر خط يجعل النص كله داخل المربع."""
    size = start
    while size >= minimum:
        f = pick_font(font_paths, size)
        lines = wrap(draw, text, f, max_w, arabic)
        if len(lines) * size * 1.4 <= max_h:
            return f, lines
        size -= 4
    f = pick_font(font_paths, minimum)
    return f, wrap(draw, text, f, max_w, arabic)


def make_card(scene, size, idx, kind="scene"):
    """إطار كامل: خلفية متدرجة + صورة مدوّرة (أو إيموجي) + لوحة نص عربي/إنجليزي."""
    import math
    W, H = size
    vertical = H > W
    top, bottom, accent = PALETTES[idx % len(PALETTES)]
    im = gradient(size, top, bottom).convert("RGBA")
    rnd = random.Random(idx * 31 + 7)
    deco = Image.new("RGBA", size, (0, 0, 0, 0))
    dd = ImageDraw.Draw(deco)
    for _ in range(14):  # فقاعات زخرفية
        r = rnd.randint(int(W * 0.02), int(W * 0.07))
        x, y = rnd.randint(0, W), rnd.randint(0, H)
        dd.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255, rnd.randint(40, 90)))
    im = Image.alpha_composite(im, deco)

    pad = int(W * 0.05)
    # رأس القناة
    f_ch = pick_font(FONT_AR_CANDIDATES, int(min(W, H) * 0.045))
    tag = ar_text(CHANNEL_AR) + "  •  " + CHANNEL_EN
    d = ImageDraw.Draw(im)
    tw = d.textlength(tag, font=f_ch)
    chip_h = int(f_ch.size * 1.9)
    chip = [W / 2 - tw / 2 - 36, pad, W / 2 + tw / 2 + 36, pad + chip_h]
    d.rounded_rectangle(chip, radius=chip_h // 2, fill=(255, 255, 255, 235))
    d.text((W / 2 - tw / 2, pad + chip_h * 0.17), tag, font=f_ch, fill=accent)
    head_b = pad + chip_h + int(pad * 0.7)

    if vertical:
        box = (pad, head_b, W - pad, head_b + int(H * 0.44))
        panel = (pad, box[3] + int(pad * 0.7), W - pad, H - pad)
    else:
        box_w = int(W * 0.46)
        box = (pad, head_b, pad + box_w, H - pad)
        panel = (box[2] + pad, head_b, W - pad, H - pad)
    bw, bh = box[2] - box[0], box[3] - box[1]

    # الصورة أو الإيموجي
    pic = None
    if kind == "scene" and os.getenv("NO_IMAGES") != "1":
        raw = fetch_image(scene.get("visual", "a happy smiling cartoon child"), rnd.randint(1, 10**6))
        if raw is not None:
            from PIL import ImageOps, ImageFilter
            pic = ImageOps.fit(raw, (bw, bh), Image.LANCZOS).filter(
                ImageFilter.UnsharpMask(radius=1.2, percent=60, threshold=3)).convert("RGBA")
    if pic is None:
        pic = Image.new("RGBA", (bw, bh), (255, 255, 255, 215))
        pd = ImageDraw.Draw(pic)
        cx, cy, R = bw // 2, bh // 2, int(min(bw, bh) * 0.42)
        pd.ellipse([cx - R, cy - R, cx + R, cy + R], fill=tuple(list(top) + [255]))
        em = emoji_image(scene.get("emoji", "⭐"), int(R * 1.5))
        if em:
            pic.paste(em, (cx - em.width // 2, cy - em.height // 2), em)

    radius = int(min(bw, bh) * 0.07)
    shadow = Image.new("RGBA", size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle([box[0] + 8, box[1] + 14, box[2] + 8, box[3] + 14],
                                             radius=radius, fill=(0, 0, 0, 90))
    from PIL import ImageFilter as _IF
    im = Image.alpha_composite(im, shadow.filter(_IF.GaussianBlur(14)))
    frame = Image.new("RGBA", (bw + 24, bh + 24), (255, 255, 255, 255))
    im.paste(frame, (box[0] - 12, box[1] - 12), rounded_mask(frame.size, radius + 8))
    im.paste(pic, (box[0], box[1]), rounded_mask((bw, bh), radius))

    # لوحة النص
    d = ImageDraw.Draw(im)
    pw, ph = panel[2] - panel[0], panel[3] - panel[1]
    d.rounded_rectangle([panel[0] + 6, panel[1] + 10, panel[2] + 6, panel[3] + 10],
                        radius=int(pad * 0.9), fill=(0, 0, 0, 55))
    d.rounded_rectangle(panel, radius=int(pad * 0.9), fill=(255, 255, 255, 245),
                        outline=accent, width=6)
    inner_w, inner_h = pw - 2 * int(pad * 0.8), ph - 2 * int(pad * 0.6)
    base = min(W, H)
    f_ar, ar_lines = fit_text(d, scene["ar"], FONT_AR_CANDIDATES, inner_w, inner_h * 0.62,
                              int(base * (0.085 if vertical else 0.075)), 30, True)
    f_en, en_lines = fit_text(d, scene["en"], FONT_EN_CANDIDATES, inner_w, inner_h * 0.34,
                              int(base * 0.05), 22, False)
    ar_h = len(ar_lines) * f_ar.size * 1.35
    en_h = len(en_lines) * f_en.size * 1.35
    y = panel[1] + (ph - (ar_h + en_h + 18)) / 2
    cx = (panel[0] + panel[2]) / 2
    y = draw_lines(d, ar_lines, f_ar, cx, y, True, (30, 40, 100), stroke=(255, 255, 255))
    # فاصل صغير
    d.rounded_rectangle([cx - 60, y + 2, cx + 60, y + 8], radius=3, fill=accent)
    draw_lines(d, en_lines, f_en, cx, y + 18, False, accent, stroke=(255, 255, 255))

    path = OUT / f"card_{idx:03d}.png"
    im.convert("RGB").save(path)
    return path


# ---------------------------------------------------------------- الصوت
async def _tts(text, voice, path):
    import edge_tts
    await edge_tts.Communicate(text, voice, rate="-12%").save(str(path))


def sh(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def duration(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", str(path)], capture_output=True, text=True)
    return float(r.stdout.strip())


def silence(path, secs):
    sh(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", str(secs),
        "-c:a", "libmp3lame", str(path)])


def make_audio(scene, idx):
    ar, en, out = OUT / f"a_ar_{idx}.mp3", OUT / f"a_en_{idx}.mp3", OUT / f"a_{idx}.mp3"
    if os.getenv("FAKE_TTS") == "1":
        silence(ar, max(2.0, len(scene["ar"]) * 0.07))
        silence(en, max(2.0, len(scene["en"]) * 0.06))
    else:
        # النص المشكول للصوت فقط؛ على الشاشة يظهر النص العادي
        asyncio.run(_tts(scene.get("ar_tts") or scene["ar"], AR_VOICE, ar))
        asyncio.run(_tts(scene["en"], EN_VOICE, en))
    gap = OUT / "gap.mp3"
    if not gap.exists():
        silence(gap, 0.5)
    lst = OUT / f"a_{idx}.txt"
    lst.write_text("".join(f"file '{p.name}'\n" for p in (ar, gap, en, gap)))
    sh(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-ar", "24000",
        "-ac", "1", "-c:a", "libmp3lame", str(out)])
    return out


# ---------------------------------------------------------------- الفيديو
def make_clip(card, audio, size, idx, fps=24):
    W, H = size
    out = OUT / f"clip_{idx:03d}.mp4"
    d = duration(audio)
    frames = int(d * fps) + 1
    # حركة تكبير خفيفة لإبقاء انتباه الطفل
    vf = (f"scale={W * 3 // 2}:{H * 3 // 2}:flags=lanczos,zoompan=z='min(zoom+0.0005,1.10)':d={frames}:"
          f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={W}x{H}:fps={fps},format=yuv420p")
    sh(["ffmpeg", "-y", "-loop", "1", "-i", str(card), "-i", str(audio), "-vf", vf,
        "-t", f"{d:.2f}", "-c:v", "libx264", "-preset", "faster", "-crf", "19",
        "-c:a", "aac", "-b:a", "128k", "-ar", "44100", "-ac", "2", "-shortest", str(out)])
    return out


def concat(clips, out):
    lst = OUT / "clips.txt"
    lst.write_text("".join(f"file '{c.name}'\n" for c in clips))
    sh(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(out)])


def build_video(lessons, size, kind):
    """kind = short: درس واحد | long: عدة دروس."""
    clips, idx = [], 0

    def add(scene, card_kind="scene"):
        nonlocal idx
        card = make_card(scene, size, idx, card_kind)
        audio = make_audio(scene, idx)
        clips.append(make_clip(card, audio, size, idx))
        idx += 1

    first = lessons[0]
    def tt(ls):  # عنوان مشكول للصوت إن وُجد
        return ls.get("title_ar_tts") or ls["title_ar"]

    add({"ar": f"مرحباً يا أصدقاء! درسنا اليوم: {first['title_ar']}",
         "ar_tts": f"مَرْحَبًا يَا أَصْدِقَاءُ! دَرْسُنَا اليَوْمَ: {tt(first)}",
         "en": f"Hello friends! Today: {first['title_en']}", "emoji": "👋"}, "title")
    for i, ls in enumerate(lessons):
        if kind == "long" and i > 0:
            add({"ar": f"الدرس التالي: {ls['title_ar']}",
                 "ar_tts": f"الدَّرْسُ التَّالِي: {tt(ls)}",
                 "en": f"Next lesson: {ls['title_en']}", "emoji": "➡️"}, "title")
        for sc in ls["scenes"]:
            add(sc)
        if kind == "long":  # مراجعة سريعة بعد كل درس
            add({"ar": "أحسنتم! هل تذكرون ما تعلمناه؟ فكروا قليلاً.",
                 "ar_tts": "أَحْسَنْتُمْ! هَلْ تَتَذَكَّرُونَ مَا تَعَلَّمْنَاهُ؟ فَكِّرُوا قَلِيلًا.",
                 "en": "Well done! Do you remember what we learned? Think for a moment.",
                 "emoji": "🤔"}, "title")
    add({"ar": "أحسنتم يا أبطال! اشتركوا في القناة لنتعلم معاً كل يوم.",
         "ar_tts": "أَحْسَنْتُمْ يَا أَبْطَالُ! اشْتَرِكُوا فِي القَنَاةِ لِنَتَعَلَّمَ مَعًا كُلَّ يَوْمٍ.",
         "en": "Great job, heroes! Subscribe to learn with us every day.", "emoji": "🌟"}, "title")
    out = OUT / f"{kind}.mp4"
    concat(clips, out)
    return out


# ---------------------------------------------------------------- يوتيوب
def upload(video, title, description, tags, thumb=None):
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from googleapiclient.http import MediaFileUpload

    creds = Credentials(None, refresh_token=os.environ["YT_REFRESH_TOKEN"],
                        token_uri="https://oauth2.googleapis.com/token",
                        client_id=os.environ["YT_CLIENT_ID"],
                        client_secret=os.environ["YT_CLIENT_SECRET"],
                        scopes=["https://www.googleapis.com/auth/youtube.upload"])
    yt = build("youtube", "v3", credentials=creds, cache_discovery=False)
    status = {"privacyStatus": os.getenv("PRIVACY", "public"),
              "selfDeclaredMadeForKids": True, "containsSyntheticMedia": True}
    body = {"snippet": {"title": title[:98], "description": description, "tags": tags[:25],
                        "categoryId": "27", "defaultLanguage": "ar"}, "status": status}
    media = MediaFileUpload(str(video), chunksize=8 * 1024 * 1024, resumable=True)
    try:
        req = yt.videos().insert(part="snippet,status", body=body, media_body=media)
        resp = None
        while resp is None:
            _, resp = req.next_chunk()
    except HttpError as e:
        if "containsSyntheticMedia" in str(e):
            status.pop("containsSyntheticMedia")
            req = yt.videos().insert(part="snippet,status", body=body, media_body=media)
            resp = None
            while resp is None:
                _, resp = req.next_chunk()
        else:
            raise
    vid = resp["id"]
    print(f"تم الرفع: https://youtu.be/{vid}")
    if thumb:
        try:
            yt.thumbnails().set(videoId=vid, media_body=MediaFileUpload(str(thumb))).execute()
        except Exception as e:  # noqa  (يتطلب قناة موثقة)
            print(f"[thumbnail] تخطي: {e}")
    return vid



# ---------------------------------------------------------------- السيو
CAT_KEYWORDS = {
    "الحروف": (["حروف", "الحروف العربية", "تعليم الحروف", "Arabic alphabet", "learn Arabic letters"], "#الحروف_العربية"),
    "الأرقام": (["أرقام", "تعليم العد", "العد للاطفال", "counting for kids", "learn numbers"], "#الأرقام"),
    "الألوان": (["ألوان", "تعليم الألوان", "colors for kids", "learn colors"], "#الألوان"),
    "الحيوانات": (["حيوانات", "أصوات الحيوانات", "animals for kids", "animal sounds"], "#الحيوانات"),
    "الأشكال": (["أشكال", "الأشكال الهندسية", "shapes for kids", "learn shapes"], "#الأشكال"),
    "القيم": (["قيم وأخلاق", "تربية الأطفال", "good manners for kids", "kids values"], "#قيم_وأخلاق"),
    "العلوم": (["علوم للأطفال", "تجارب علمية", "science for kids", "kids science"], "#علوم_الأطفال"),
}
BASE_TAGS = ["تعليم الأطفال", "تعلم العربية", "عالم التعلم", "Learning World", "Arabic for kids",
             "kids learning", "learn arabic", "learn english", "أطفال", "فيديو تعليمي للأطفال",
             "تعليم الأطفال العربية والانجليزية", "روضة", "ما قبل المدرسة", "educational videos for kids"]


def make_seo(lessons, kind):
    first = lessons[0]
    cat = first.get("category", "")
    kw, cat_hash = CAT_KEYWORDS.get(cat, ([], "#تعليم"))
    age = first.get("age", "5-8")
    if kind == "short":
        title = f"{first['title_ar']} | {first['title_en']} - تعليم الأطفال #Shorts"
        if len(title) > 98:
            title = f"{first['title_ar']} | {first['title_en']} #Shorts"
    else:
        names = " + ".join(l["title_ar"] for l in lessons[:3])
        title = f"{names} | دروس للأطفال Kids Learning"
        if len(title) > 98:
            title = f"دروس للأطفال: {lessons[0]['title_ar']} وأكثر | Kids Learning"
    lines = "\n".join(f"• {l['title_ar']} — {l['title_en']}" for l in lessons)
    desc = (f"{first['title_ar']} — {first['title_en']}\n"
            f"فيديو تعليمي للأطفال من {age.replace('-', ' إلى ')} سنوات بالعربية الفصحى والإنجليزية: "
            f"{'، '.join(kw[:3]) if kw else 'تعليم الأطفال'}.\n"
            f"Educational video for kids aged {age} in Arabic and English.\n\n"
            f"📚 في هذا الفيديو / In this video:\n{lines}\n\n"
            "🔔 اشترك في قناة عالم التعلم ليصلك درس جديد كل يوم، وفيديو طويل كل أسبوع.\n"
            "Subscribe to Learning World for a new lesson every day!\n\n"
            "🎓 شاهد المزيد: فيديوهات الحروف والأرقام والألوان والحيوانات والعلوم والقيم.\n\n"
            "ملاحظة: الصوت والصور مولّدة بالذكاء الاصطناعي. / Voice and images are AI-generated.\n\n"
            f"#تعليم_الأطفال {cat_hash} #عالم_التعلم #KidsLearning #LearnArabic")
    tags = []
    for t in kw + [first["title_ar"], first["title_en"]] + BASE_TAGS:
        if t not in tags:
            tags.append(t)
    while sum(len(t) + 1 for t in tags) > 480:
        tags.pop()
    return title, desc, tags

# ---------------------------------------------------------------- التشغيل
def main():
    kind = sys.argv[1] if len(sys.argv) > 1 else "short"
    if kind not in ("short", "long"):
        sys.exit("الاستخدام: python main.py short|long")
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    history = load_history()
    n_lessons = 1 if kind == "short" else int(os.getenv("LONG_LESSONS", "4"))
    n_scenes = 4 if kind == "short" else 6
    lessons = []
    for _ in range(n_lessons):
        ls = get_lesson(history, n_scenes)
        if kind == "short":
            ls["scenes"] = ls["scenes"][:5]
        lessons.append(ls)
        history["titles"].append(ls["title_ar"])
        history["counter"] += 1
        print("درس:", ls["title_ar"])

    size = (1080, 1920) if kind == "short" else (1920, 1080)
    video = build_video(lessons, size, kind)
    total = duration(video)
    print(f"الفيديو جاهز: {video} ({total:.0f} ثانية)")

    first = lessons[0]
    title, desc, tags = make_seo(lessons, kind)

    if os.getenv("DRY_RUN") == "1" or not os.getenv("YT_REFRESH_TOKEN"):
        print("وضع تجريبي: لن يتم الرفع.\nالعنوان:", title)
    else:
        thumb = OUT / "card_001.png" if kind == "long" else None
        upload(video, title, desc, tags, thumb)
        save_history(history)
        return
    # في الوضع التجريبي لا نحفظ التقدم حتى لا تضيع الدروس
    return


if __name__ == "__main__":
    main()
