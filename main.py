#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
قناة «عالم التعلم» — منهج يومي: فيديو طويل + Short واحد من نفس الدرس.

الاستخدام:
    python main.py daily      # الدرس التالي في المنهج: فيديو طويل + Short (الافتراضي)
    python main.py long       # الفيديو الطويل فقط (للتجربة)
    python main.py short      # الـ Short فقط (للتجربة)

متغيرات البيئة:
    GEMINI_API_KEY, YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN
    DRY_RUN=1   ينتج الفيديو دون رفعه        FAKE_TTS=1 / NO_IMAGES=1  للاختبار السريع
    PRIVACY     public | unlisted | private
    DAY=N       يفرض رقم يوم المنهج (للتجربة)
"""
import json
import os
import random
import re
import shutil
import sys
import time
from pathlib import Path

import requests

import curriculum
import render
from lessons_fallback import FALLBACK_LESSONS

ROOT = Path(__file__).parent
OUT = render.OUT
STATE = ROOT / "state" / "history.json"


# ---------------------------------------------------------------- الحالة
def load_history():
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except Exception:
        return {"day": 0, "titles": []}


def save_history(h):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    h["titles"] = h.get("titles", [])[-200:]
    STATE.write_text(json.dumps(h, ensure_ascii=False, indent=1), encoding="utf-8")


# ---------------------------------------------------------------- الدروس من Gemini
PROMPT = """أنت معلم أطفال محترف للوطن العربي ومصمم مناهج. اكتب درساً كاملاً ومنظماً لأطفال بعمر {age} سنوات
في موضوع: «{topic}» (من مسار: {track}). {style}
سيُعرض في فيديو تعليمي مدته نحو 5 دقائق.

الشروط:
- عربية فصحى مبسطة جداً وجمل قصيرة (حتى 12 كلمة)، وإنجليزية بسيطة موازية لها.
- "scenes": {n} مشاهد مرتبة من الأسهل إلى الأصعب، كل مشهد فكرة واحدة مع مثال محسوس يعرفه الطفل.
  المشهد الأول يعرّف بالموضوع، والأخير يلخّص الفكرة.
- "keywords": خمس كلمات أو أشياء رئيسية من الدرس للمراجعة (كلمة أو كلمتان فقط لكل واحدة).
- "quiz": 3 أسئلة اختيار من متعدد عن الدرس، لكل سؤال 3 خيارات، كل خيار: emoji واحد + كلمة عربية قصيرة + ترجمتها،
  و"answer" رقم الخيار الصحيح (0 أو 1 أو 2) ووزّع الإجابات الصحيحة بين الأرقام الثلاثة.
- النص العربي (ar و ar_tts) بلا أي حرف لاتيني إطلاقاً؛ اكتب أسماء الحروف بالعربية.
- محتوى آمن تماماً للأطفال، بلا عنف ولا مخاوف ولا إشارات تجارية، ودقيق علمياً.
- لا تكرر هذه العناوين السابقة: {prev}
- لكل نص عربي أضف الحقل المقابل المنتهي بـ _tts: النص نفسه حرفياً لكن مشكولاً بالكامل (فتحة وضمة وكسرة وسكون وشدة وتنوين)
  على أصح قواعد الفصحى، لأنه سيُقرأ بصوت آلي.
- "visual": وصف إنجليزي قصير ومحدد لصورة كرتونية بسيطة تناسب الطفل لهذا المشهد (شيء واحد واضح، بلا نصوص).
- أرجع JSON فقط بهذا الشكل بالضبط:
{{"title_ar": "...", "title_ar_tts": "...", "title_en": "...",
 "scenes": [{{"ar": "...", "ar_tts": "...", "en": "...", "emoji": "إيموجي", "visual": "..."}}],
 "keywords": [{{"ar": "...", "ar_tts": "...", "en": "...", "emoji": "إيموجي", "visual": "..."}}],
 "quiz": [{{"ar": "...", "ar_tts": "...", "en": "...",
            "options": [{{"emoji": "إيموجي", "ar": "...", "ar_tts": "...", "en": "..."}}, {{...}}, {{...}}],
            "answer": 0}}]}}"""


def _post_gemini(prompt, key):
    body = {"contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseMimeType": "application/json", "temperature": 0.8}}
    for model in gemini_models(key)[:8]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
        for attempt in range(2):
            try:
                r = requests.post(url, json=body, timeout=120)
                if r.status_code in (404, 400, 403):
                    print(f"[gemini] النموذج {model} غير متاح ({r.status_code})")
                    break
                r.raise_for_status()
                text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
                data = json.loads(text)
                if isinstance(data, list):
                    data = data[0]
                print(f"[gemini] تم باستخدام النموذج {model}")
                return data
            except Exception as e:  # noqa
                code = getattr(getattr(e, "response", None), "status_code", "")
                print(f"[gemini] {model} محاولة {attempt + 1} فشلت: {type(e).__name__} {code}")
                time.sleep(6)
    return None


def gemini_lesson(spec, history, n_scenes=10):
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        return None
    prompt = PROMPT.format(age=spec["age"], topic=spec["topic"], track=spec["track"], style=spec.get("style", ""), n=n_scenes,
                           prev=" | ".join(history.get("titles", [])[-25:]) or "لا يوجد")
    data = _post_gemini(prompt, key)
    if not data:
        return None
    try:
        data["scenes"] = [s for s in data["scenes"] if s.get("ar") and s.get("en")]
        if len(data["scenes"]) < 5 or not data.get("title_ar"):
            raise ValueError("درس ناقص")
        for s in data["scenes"]:
            s["kind"] = "text"
        data["keywords"] = [dict(k, kind="text") for k in data.get("keywords", []) if k.get("ar") and k.get("en")][:6]
        good = []
        for q in data.get("quiz", []):
            opts = q.get("options", [])
            if (len(opts) == 3 and isinstance(q.get("answer"), int) and 0 <= q["answer"] < 3
                    and all(o.get("ar") and o.get("en") and o.get("emoji") for o in opts)):
                good.append(q)
        data["quiz"] = good
        data["category"], data["age"], data["track"] = spec["track"], spec["age"], spec["track"]
        data["topic"] = spec["topic"]
        return data
    except Exception as e:  # noqa
        print(f"[gemini] رد غير صالح: {type(e).__name__}")
        return None


def fallback_lesson(spec, history):
    """درس احتياطي جاهز بلا ذكاء اصطناعي (يُحوَّل لنفس الشكل الحديث)."""
    used = set(history.get("titles", []))
    pool = [l for l in FALLBACK_LESSONS if l["title_ar"] not in used] or FALLBACK_LESSONS
    L = json.loads(json.dumps(random.choice(pool), ensure_ascii=False))
    for s in L["scenes"]:
        s["kind"] = "text"
    L["keywords"] = [dict(s) for s in L["scenes"][:5]]
    L["track"] = spec["track"]
    return L


LATIN_NAMES = dict(zip("ABCDEFGHIJKLMNOPQRSTUVWXYZ",
                       "إيه بي سي دي إي إف جي إتش آي جيه كيه إل إم إن أو بي كيو آر إس تي يو في دبليو إكس واي زد".split()))


def _arabize(text):
    """الخط العربي لا يحوي أحرفاً لاتينية فتظهر مربعات؛ نحوّل الحرف المفرد لاسمه العربي ونحذف الباقي."""
    if not text:
        return text
    def one(m):
        w = m.group(0)
        return LATIN_NAMES.get(w.upper(), "") if len(w) == 1 else ""
    text = re.sub(r"[A-Za-z]+", one, text)
    return re.sub(r"\s{2,}", " ", text).strip()


def clean_lesson(ls):
    """تنظيف نصوص Gemini: لا لاتينية في العربي، وأسئلة سليمة."""
    def fix(d, keys):
        for k in keys:
            if k in d and isinstance(d[k], str):
                d[k] = _arabize(d[k])
    fix(ls, ("title_ar", "title_ar_tts"))
    if not ls.get("title_ar"):
        ls["title_ar"] = "درس جديد للأطفال"
        ls["title_ar_tts"] = "دَرْسٌ جَدِيدٌ لِلْأَطْفَالِ"
    for coll in ("scenes", "keywords"):
        for s in ls.get(coll, []):
            fix(s, ("ar", "ar_tts"))
    for q in ls.get("quiz", []):
        fix(q, ("ar", "ar_tts"))
        for o in q.get("options", []):
            fix(o, ("ar", "ar_tts"))
    return ls


def ensure_quiz(ls):
    """إن لم يوجد اختبار نبنيه من الكلمات الرئيسية."""
    if ls.get("quiz"):
        return ls
    kws = [k for k in ls.get("keywords", []) if k.get("emoji")]
    if len(kws) < 3:
        kws = [s for s in ls["scenes"] if s.get("emoji")]
    rng = random.Random(len(ls["title_ar"]))
    quiz = []
    for good in rng.sample(kws, min(3, len(kws))):
        bad = rng.sample([k for k in kws if k is not good], min(2, len(kws) - 1))
        if len(bad) < 2:
            break
        opts = [good] + bad
        rng.shuffle(opts)
        quiz.append({"ar": f"أيُّ صورةٍ تناسبُ: {good['ar']}", "ar_tts": f"أَيُّ صُورَةٍ تُنَاسِبُ: {good.get('ar_tts') or good['ar']}",
                     "en": f"Which picture matches: {good['en']}",
                     "options": [{"emoji": o["emoji"], "ar": o["ar"][:22], "ar_tts": o.get("ar_tts") or o["ar"],
                                  "en": o["en"]} for o in opts], "answer": opts.index(good)})
    ls["quiz"] = quiz
    return ls


def get_lesson(day):
    track, k, spec = curriculum.pick(day)
    if spec.get("gemini"):
        history = load_history()
        lesson = gemini_lesson(spec, history)
        lesson = clean_lesson(lesson) if lesson else fallback_lesson(spec, history)
    else:
        lesson = spec
    lesson["track_key"] = track
    return ensure_quiz(lesson)


def next_title(day):
    track, k, spec = curriculum.pick(day + 1)
    return spec.get("title_ar") or spec.get("topic")


# ---------------------------------------------------------------- تخطيط الفيديو (من الدرس إلى مشاهد)
def _tts(d):
    return d.get("ar_tts") or d["ar"]


def plan_long(L, day):
    plan = []

    def add(sec, **sc):
        sc["sec"] = sec
        plan.append(sc)

    plan.append({"kind": "intro", "sec": "المقدمة"})
    add(None, kind="title", emoji="👋",
        ar=f"مرحباً يا أصدقاء! درسنا اليوم: {L['title_ar']}",
        ar_tts=f"مَرْحَبًا يَا أَصْدِقَاءُ! دَرْسُنَا اليَوْمَ: {L.get('title_ar_tts') or L['title_ar']}",
        en=f"Hello friends! Today's lesson: {L['title_en']}")
    for i, s in enumerate(L["scenes"]):
        add("الدرس" if i else None, **{k: v for k, v in s.items() if k not in ("short", "sec")})
        plan[-1]["sec"] = "الدرس" if i == 0 else None
    kws = L.get("keywords") or []
    if kws:
        add("كرّروا معي", kind="title", emoji="🗣️", ar="كرروا معي!", ar_tts="كَرِّرُوا مَعِي!", en="Repeat after me!")
        for k in kws:
            sc = {"kind": "text", "ar": k["ar"], "ar_tts": _tts(k), "en": k["en"], "emoji": k.get("emoji", "⭐"),
                  "visual": k.get("visual"), "tail": 0.35}
            add(None, **sc)
    if L.get("quiz"):
        add("اختبار قصير", kind="title", emoji="🎯", ar="وقت الاختبار! هل تعرفون الإجابة؟",
            ar_tts="وَقْتُ الِاخْتِبَارِ! هَلْ تَعْرِفُونَ الإِجَابَةَ؟", en="Quiz time! Do you know the answer?")
        for q in L["quiz"]:
            add(None, kind="quiz", **q)
    if kws:
        add("ملخص الدرس", kind="title", emoji="🏆",
            ar="أحسنتم! تعلمنا اليوم: " + "، ".join(k["ar"] for k in kws[:5]),
            ar_tts="أَحْسَنْتُمْ! تَعَلَّمْنَا اليَوْمَ: " + "، ".join(_tts(k) for k in kws[:5]),
            en="Great job! Today we learned: " + ", ".join(k["en"] for k in kws[:5]), tail=1.0)
    nxt = next_title(day)
    add("الختام", kind="title", emoji="🌟",
        ar=f"أحسنتم يا أبطال! اشتركوا في القناة. وغداً: {nxt}",
        ar_tts=f"أَحْسَنْتُمْ يَا أَبْطَالُ! اشْتَرِكُوا فِي القَنَاةِ. وَغَدًا: {nxt}",
        en="Great job, heroes! Subscribe, and see you tomorrow for a new lesson!", tail=1.2)
    return plan


def plan_short(L):
    plan = []
    chosen = [s for s in L["scenes"] if s.get("short")][:4] or [s for s in L["scenes"] if s.get("kind", "text") == "text"][:4]
    plan.append({"kind": "title", "emoji": "✨", "ar": f"درس اليوم: {L['title_ar']}",
                 "ar_tts": f"دَرْسُ اليَوْمِ: {L.get('title_ar_tts') or L['title_ar']}", "en": f"Today: {L['title_en']}",
                 "tail": 0.3})
    for s in chosen:
        plan.append({k: v for k, v in s.items() if k not in ("short", "sec")})
    if L.get("quiz"):
        plan.append(dict(L["quiz"][0], kind="quiz"))
    plan.append({"kind": "title", "emoji": "▶️", "ar": "شاهدوا الدرس الكامل على القناة، واشتركوا!",
                 "ar_tts": "شَاهِدُوا الدَّرْسَ الكَامِلَ عَلَى القَنَاةِ، وَاشْتَرِكُوا!",
                 "en": "Watch the full lesson on our channel and subscribe!", "tail": 0.8})
    return plan


def build_video(plan, size, name, images):
    """يرسم كل مشهد ثم يدمجها. يرجع (الملف، الفصول [(عنوان، ثانية)])."""
    ctx = render.Ctx(size, images)
    clips, chapters, t, N = [], [], 0.0, len(plan)
    for i, sc in enumerate(plan):
        sc = dict(sc)
        sec = sc.pop("sec", None)
        prog = (i / N, (i + 1) / N)
        clip, dur = render.render_scene(ctx, sc, i, prog)
        if sec:
            chapters.append((sec, t))
        clips.append(clip)
        t += dur
        print(f"  [{name}] مشهد {i + 1}/{N} ({sc.get('kind', 'text')}) {dur:.1f}ث")
    out = OUT / f"{name}.mp4"
    render.finalize(clips, out, with_music=os.getenv("NO_MUSIC") != "1")
    print(f"الفيديو جاهز: {out} ({t:.0f} ثانية)")
    return out, chapters, t


def all_visuals(plan):
    return [s.get("visual") for s in plan if s.get("kind", "text") == "text" and s.get("visual")]


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
TRACK_SEO = {
    "ar_letters": ("تعلّم الحروف العربية للأطفال", ["الحروف العربية", "تعليم الحروف", "حروف الهجاء", "Arabic alphabet", "learn Arabic letters"], "#الحروف_العربية"),
    "numbers": ("تعلّم الأرقام والعدّ للأطفال", ["الأرقام للأطفال", "تعليم العد", "تعلم الأرقام", "counting for kids", "learn numbers"], "#الأرقام"),
    "en_letters": ("تعلّم الحروف الإنجليزية للأطفال", ["الحروف الإنجليزية", "تعليم الانجليزية للاطفال", "English alphabet for kids", "ABC phonics"], "#الإنجليزية_للأطفال"),
    "عالمي من حولي": ("اكتشف العالم من حولك", ["تعليم الأطفال المفردات", "الحيوانات للأطفال", "كلمات للأطفال", "kids vocabulary", "learn words"], "#عالمي_من_حولي"),
    "علوم صغيرة": ("علوم مبسطة للأطفال", ["علوم للأطفال", "معلومات علمية للأطفال", "science for kids", "kids science"], "#علوم_الأطفال"),
    "قيم وأخلاق": ("قيم وأخلاق للأطفال", ["قيم وأخلاق", "تربية الأطفال", "آداب الأطفال", "good manners for kids", "kids values"], "#قيم_وأخلاق"),
    "ألوان وأشكال وأوقات": ("الألوان والأشكال والأوقات للأطفال", ["الألوان للأطفال", "الأشكال الهندسية", "أيام الأسبوع", "colors for kids", "shapes for kids"], "#الألوان_والأشكال"),
}
BASE_TAGS = ["تعليم الأطفال", "تعلم العربية", "عالم التعلم", "Learning World", "Arabic for kids", "kids learning",
             "learn arabic", "learn english", "أطفال", "فيديو تعليمي للأطفال", "تعليم الأطفال العربية والانجليزية",
             "روضة", "ما قبل المدرسة", "educational videos for kids"]


def _ts(sec):
    sec = int(sec)
    return f"{sec // 60:02d}:{sec % 60:02d}"


def make_seo(L, kind, chapters=None, long_url=None, day=0):
    tagline, kw, hashtag = TRACK_SEO.get(L.get("track_key"), ("دروس للأطفال", [], "#تعليم"))
    age = str(L.get("age", "5-8")).replace("-", " إلى ")
    if kind == "short":
        title = f"{L['title_ar']} في دقيقة | {L['title_en']} #Shorts"
        if len(title) > 98:
            title = f"{L['title_ar']} | {L['title_en']} #Shorts"
    else:
        title = f"{L['title_ar']} | {tagline} | {L['title_en']}"
        if len(title) > 98:
            title = f"{L['title_ar']} | {tagline}"
        if len(title) > 98:
            title = L["title_ar"] + " | " + L["title_en"]
    kws = [k["ar"] + " — " + k["en"] for k in (L.get("keywords") or [])[:6]]
    parts = [f"{L['title_ar']} — {L['title_en']}",
             f"درس مصوّر للأطفال من {age} سنوات بالعربية الفصحى والإنجليزية، ضمن منهج «عالم التعلم»: {tagline}.",
             f"Educational lesson for kids aged {L.get('age', '5-8')} in Arabic and English."]
    if kind == "short" and long_url:
        parts.append(f"▶️ شاهد الدرس الكامل (مع الاختبار): {long_url}")
    if kind == "long" and chapters and len(chapters) >= 3:
        parts.append("⏱️ محتوى الدرس:\n" + "\n".join(f"{_ts(t)} {name}" for name, t in chapters))
    if kws:
        parts.append("📚 كلمات الدرس / Key words:\n" + "\n".join("• " + k for k in kws))
    parts.append("🔔 اشترك في القناة ليصلك درس جديد كل يوم: فيديو طويل + Short.\n"
                 "Subscribe for a new lesson every day!")
    parts.append("ملاحظة: الصوت والصور مولّدة بالذكاء الاصطناعي. / Voice and images are AI-generated.")
    parts.append(f"#تعليم_الأطفال {hashtag} #عالم_التعلم #KidsLearning #LearnArabic")
    tags = []
    for t in kw + [L["title_ar"], L["title_en"]] + BASE_TAGS:
        if t not in tags:
            tags.append(t)
    while sum(len(t) + 1 for t in tags) > 480:
        tags.pop()
    return title, "\n\n".join(parts), tags


# ---------------------------------------------------------------- التشغيل
def main():
    kind = sys.argv[1] if len(sys.argv) > 1 else "daily"
    if kind not in ("daily", "long", "short"):
        sys.exit("الاستخدام: python main.py daily|long|short")
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    history = load_history()
    day = int(os.getenv("DAY") or history.get("day", 0))
    L = get_lesson(day)
    print(f"اليوم {day}: [{L.get('track_key')}] {L['title_ar']} / {L['title_en']}")

    want_long = kind in ("daily", "long")
    want_short = kind in ("daily", "short")
    every = int(os.getenv("SHORT_EVERY") or 3)
    if kind == "daily" and day % every != 0:
        want_short = False  # فيديو قصير واحد فقط كل عدة دروس
    long_plan = plan_long(L, day)
    short_plan = plan_short(L)
    images = render.fetch_images(all_visuals(long_plan if want_long else short_plan) +
                                 all_visuals(short_plan))

    dry = os.getenv("DRY_RUN") == "1" or not os.getenv("YT_REFRESH_TOKEN")
    long_url, uploaded = None, False

    if want_long:
        video, chapters, total = build_video(long_plan, (1920, 1080), "long", images)
        title, desc, tags = make_seo(L, "long", chapters, None, day)
        print("العنوان:", title)
        if dry:
            print(desc)
        else:
            vid = upload(video, title, desc, tags)
            long_url, uploaded = f"https://youtu.be/{vid}", True
    if want_short:
        video, _, total = build_video(short_plan, (1080, 1920), "short", images)
        title, desc, tags = make_seo(L, "short", None, long_url, day)
        print("العنوان:", title)
        if dry:
            print(desc)
        else:
            try:
                upload(video, title, desc, tags)
                uploaded = True
            except Exception as e:  # noqa
                print(f"[short] فشل الرفع: {type(e).__name__}")
    if dry:
        print("وضع تجريبي: لن يتم الرفع ولن يتقدم المنهج.")
        return
    if uploaded and kind == "daily":
        history["day"] = day + 1
        history.setdefault("titles", []).append(L["title_ar"])
        save_history(history)


if __name__ == "__main__":
    main()
