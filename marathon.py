# -*- coding: utf-8 -*-
"""ماراثون أسبوعي: يجمع آخر دروس الأسبوع في فيديو طويل واحد (للمشاهدة على التلفزيون ولرفع ساعات المشاهدة).
تُحفظ فيديوهات الدروس كملفات في «إصدار» (Release) باسم videos على GitHub، وكل ذلك اختياري: أي فشل لا يمنع الفيديو اليومي."""
import os
import shutil
import subprocess
from pathlib import Path

TAG = "videos"
KEEP = 9          # عدد فيديوهات الدروس المحفوظة
MARATHON_N = 5    # عدد الدروس في الماراثون


def _gh(args, check=True):
    return subprocess.run(["gh"] + args, capture_output=True, text=True, check=check,
                          env=dict(os.environ, GH_TOKEN=os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN") or ""))


def _duration(p):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                         capture_output=True, text=True).stdout.strip()
    return float(out or 0)


def archive(video, day, L, history, out_dir):
    """يحفظ فيديو الدرس في الإصدار ويسجله في history['archive']. يرجع True عند النجاح."""
    try:
        name = f"long_day{day}.mp4"
        dst = Path(out_dir) / name
        shutil.copy(video, dst)
        if _gh(["release", "view", TAG], check=False).returncode != 0:
            _gh(["release", "create", TAG, "--title", "فيديوهات الدروس", "--notes", "أرشيف داخلي لإنتاج الماراثون"])
        _gh(["release", "upload", TAG, str(dst), "--clobber"])
        arch = history.setdefault("archive", [])
        arch[:] = [a for a in arch if a["day"] != day]
        arch.append({"day": day, "name": name, "title_ar": L["title_ar"], "title_en": L["title_en"],
                     "dur": round(_duration(dst))})
        while len(arch) > KEEP:
            old = arch.pop(0)
            _gh(["release", "delete-asset", TAG, old["name"], "--yes"], check=False)
        print(f"[archive] حُفظ {name}")
        return True
    except Exception as e:  # noqa
        print(f"[archive] تعذر الحفظ: {type(e).__name__}: {str(e)[:200]}")
        return False


def build(history, out_dir):
    """يحمّل آخر الدروس ويدمجها. يرجع (ملف، [(عنوان، ثانية)]، قائمة الدروس) أو None."""
    arch = history.get("archive", [])[-MARATHON_N:]
    if len(arch) < 3:
        print("[marathon] عدد الدروس المحفوظة أقل من 3، تخطّي.")
        return None
    d = Path(out_dir) / "arch"
    d.mkdir(parents=True, exist_ok=True)
    got = []
    for a in arch:
        try:
            _gh(["release", "download", TAG, "-p", a["name"], "-D", str(d), "--clobber"])
            if (d / a["name"]).exists():
                got.append(a)
        except Exception as e:  # noqa
            print(f"[marathon] تعذر تحميل {a['name']}: {str(e)[:120]}")
    if len(got) < 3:
        print("[marathon] لم تُحمَّل دروس كافية.")
        return None
    lst = d / "list.txt"
    lst.write_text("".join(f"file '{(d / a['name']).resolve()}'\n" for a in got))
    out = Path(out_dir) / "marathon.mp4"
    r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst),
                        "-c", "copy", str(out)], capture_output=True, text=True)
    if r.returncode != 0 or not out.exists():
        print("[marathon] الدمج بالنسخ فشل، إعادة الترميز...")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst),
                        "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-pix_fmt", "yuv420p",
                        "-c:a", "aac", "-b:a", "160k", str(out)], check=True)
    chapters, t = [], 0.0
    for a in got:
        chapters.append((a["title_ar"], t))
        t += _duration(d / a["name"])
    return out, chapters, got, t


def _ts(sec):
    sec = int(sec)
    return f"{sec // 3600:d}:{sec % 3600 // 60:02d}:{sec % 60:02d}" if sec >= 3600 else f"{sec // 60:02d}:{sec % 60:02d}"


def seo(chapters, got, total):
    mins = max(1, round(total / 60))
    title = f"ماراثون التعلم: {len(got)} دروس متتالية للأطفال | {mins} دقيقة | Learning Marathon"
    if len(title) > 98:
        title = f"ماراثون التعلم: {len(got)} دروس للأطفال | {mins} دقيقة"
    lines = [f"{_ts(t)} {name}" for name, t in chapters]
    desc = "\n\n".join([
        f"ماراثون «عالم التعلم»: {len(got)} دروس متتالية بالعربية والإنجليزية للأطفال، بلا انقطاع. مناسب للمشاهدة على التلفزيون مع الأسرة.",
        f"A {mins}-minute learning marathon for kids: {len(got)} lessons in Arabic and English.",
        "⏱️ محتوى الماراثون:\n" + "\n".join(lines),
        "🔔 اشترك في القناة ليصلك درس جديد كل يوم وماراثون كل جمعة. Subscribe for new lessons every day!",
        "ملاحظة: الصوت والصور مولّدة بالذكاء الاصطناعي. / Voice and images are AI-generated.",
        "#تعليم_الأطفال #ماراثون #عالم_التعلم #KidsLearning #LearnArabic"])
    tags = ["ماراثون للأطفال", "تعليم الأطفال", "عالم التعلم", "Learning World", "kids learning marathon",
            "Arabic for kids", "learn arabic", "فيديو تعليمي للأطفال", "ساعة تعليمية للأطفال"]
    tags += [a["title_ar"] for a in got][:8]
    return title, desc, tags
