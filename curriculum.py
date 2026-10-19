# -*- coding: utf-8 -*-
"""
المنهج الدراسي لقناة «عالم التعلم».

كل يوم درس واحد، والأيام تدور على 7 مسارات ثابتة (الأحد ... السبت)، وفي كل مسار تتقدم الدروس بالترتيب:
  0 الحروف العربية (28 درساً)     1 الأرقام والعدّ         2 عالمي من حولي
  3 الحروف الإنجليزية (26 درساً)  4 علوم صغيرة            5 قيم وأخلاق
  6 ألوان وأشكال وأوقات

الدروس الثابتة (الحروف والأرقام) مكتوبة يدوياً بدقة وبتشكيل صحيح للصوت، فلا تعتمد على أي ذكاء اصطناعي.
بقية الدروس تُكتب عبر Gemini بقالب ثابت، مع درس احتياطي إن تعذّر ذلك.
"""
import random
import re

TASHKEEL_RE = re.compile(r"[ً-ْٰـ]")


def strip_tashkeel(s):
    return TASHKEEL_RE.sub("", s)


# ---------------------------------------------------------------- الحروف العربية
# الحرف | اسمه مشكولاً | الاسم الإنجليزي | صوت الحرف | 4 كلمات: عربي مشكول, English, emoji
AR_LETTERS_RAW = """
أ|أَلِفْ|Alif|a|أَرْنَب,rabbit,🐰;أَسَد,lion,🦁;أَنَاناس,pineapple,🍍;أُذُن,ear,👂
ب|بَاءْ|Ba|b|بَطَّة,duck,🦆;بَقَرَة,cow,🐄;بَيْت,house,🏠;بَالُون,balloon,🎈
ت|تَاءْ|Ta|t|تُفَّاحَة,apple,🍎;تِمْسَاح,crocodile,🐊;تَاج,crown,👑;تِلْفَاز,television,📺
ث|ثَاءْ|Tha|th|ثَعْلَب,fox,🦊;ثَلْج,snow,❄️;ثَوْب,dress,👗;ثُعْبَان,snake,🐍
ج|جِيمْ|Jeem|j|جَمَل,camel,🐪;جَزَر,carrot,🥕;جَبَل,mountain,⛰️;جَرَس,bell,🔔
ح|حَاءْ|Haa|h|حِصَان,horse,🐴;حُوت,whale,🐋;حَلِيب,milk,🥛;حَقِيبَة,school bag,🎒
خ|خَاءْ|Khaa|kh|خَرُوف,sheep,🐑;خِيَار,cucumber,🥒;خُبْز,bread,🍞;خَيْمَة,tent,⛺
د|دَالْ|Dal|d|دَجَاجَة,hen,🐔;دُبّ,bear,🐻;دَرَّاجَة,bicycle,🚲;دَلْو,bucket,🪣
ذ|ذَالْ|Thal|dh|ذُرَة,corn,🌽;ذِئْب,wolf,🐺;ذُبَابَة,fly,🪰;ذَهَب,gold,🥇
ر|رَاءْ|Ra|r|رُمَّان,pomegranate,🍎;رِيشَة,feather,🪶;رَقْم,number,🔢;رَسْم,drawing,🎨
ز|زَايْ|Zay|z|زَرَافَة,giraffe,🦒;زَهْرَة,flower,🌸;زَيْتُون,olive,🫒;زُجَاجَة,bottle,🍼
س|سِينْ|Seen|s|سَمَكَة,fish,🐟;سَيَّارَة,car,🚗;سَاعَة,clock,⏰;سُلَحْفَاة,turtle,🐢
ش|شِينْ|Sheen|sh|شَمْس,sun,☀️;شَجَرَة,tree,🌳;شَمْعَة,candle,🕯️;شَاحِنَة,truck,🚚
ص|صَادْ|Saad|s|صَقْر,falcon,🦅;صَابُون,soap,🧼;صُنْدُوق,box,📦;صَارُوخ,rocket,🚀
ض|ضَادْ|Daad|d|ضِفْدَع,frog,🐸;ضَوْء,light bulb,💡;ضِرْس,tooth,🦷;ضَبَاب,fog,🌫️
ط|طَاءْ|Taa|t|طَائِرَة,airplane,✈️;طَاوُوس,peacock,🦚;طَبْل,drum,🥁;طَمَاطِم,tomato,🍅
ظ|ظَاءْ|Zaa|z|ظَرْف,envelope,✉️;ظِلّ,shadow,🌗;ظَبْي,gazelle,🦌;ظُفْر,fingernail,💅
ع|عَيْنْ|Ain|a|عِنَب,grapes,🍇;عُصْفُور,bird,🐦;عَيْن,eye,👁️;عَلَم,flag,🏳️
غ|غَيْنْ|Ghain|gh|غَزَال,deer,🦌;غَيْمَة,cloud,☁️;غَوَّاصَة,submarine,🚢;غُرَاب,crow,🐦
ف|فَاءْ|Fa|f|فِيل,elephant,🐘;فَرَاشَة,butterfly,🦋;فَرَاوِلَة,strawberry,🍓;فَأْر,mouse,🐭
ق|قَافْ|Qaf|q|قِطَّة,cat,🐱;قَمَر,moon,🌙;قَلَم,pencil,✏️;قِرْد,monkey,🐒
ك|كَافْ|Kaf|k|كَلْب,dog,🐶;كِتَاب,book,📖;كُرَة,ball,⚽;كُرْسِيّ,chair,🪑
ل|لَامْ|Lam|l|لَيْمُون,lemon,🍋;لُعْبَة,toy,🧸;لِسَان,tongue,👅;لَوْحَة,painting,🖼️
م|مِيمْ|Meem|m|مَوْز,banana,🍌;مِفْتَاح,key,🔑;مَطَر,rain,🌧️;مَدْرَسَة,school,🏫
ن|نُونْ|Noon|n|نَمِر,tiger,🐅;نَحْلَة,bee,🐝;نَجْمَة,star,⭐;نَظَّارَة,glasses,👓
ه|هَاءْ|Ha|h|هِلَال,crescent moon,🌙;هَدِيَّة,gift,🎁;هَاتِف,phone,📱;هَرَم,pyramid,🔺
و|وَاوْ|Waw|w|وَرْدَة,rose,🌹;وَلَد,boy,👦;وِسَادَة,pillow,🛏️;وَجْه,face,🙂
ي|يَاءْ|Ya|y|يَد,hand,✋;يَاسَمِين,jasmine flower,🌼;يَمَامَة,dove,🕊️;يَقْطِين,pumpkin,🎃
"""

NON_CONNECTING = set("أدذرزو")


def _parse_ar_letters():
    out = []
    for line in AR_LETTERS_RAW.strip().splitlines():
        ch, name_tts, name_en, snd, words = line.split("|")
        ws = []
        for w in words.split(";"):
            ar_tts, en, em = w.split(",")
            ws.append({"ar": strip_tashkeel(ar_tts), "ar_tts": ar_tts, "en": en, "emoji": em,
                       "visual": f"a cute {en}"})
        out.append({"ch": ch, "name_tts": name_tts, "name": strip_tashkeel(name_tts),
                    "name_en": name_en, "snd": snd, "words": ws})
    return out


AR_LETTERS = _parse_ar_letters()


def _quiz_words(correct_pool, others, n=3, rng=None):
    """أسئلة اختيار من متعدد: كلمة صحيحة + كلمتان مشتتتان."""
    rng = rng or random.Random()
    qs = []
    picks = rng.sample(correct_pool, min(n, len(correct_pool)))
    for good in picks:
        bad = rng.sample(others, 2)
        opts = [good] + bad
        rng.shuffle(opts)
        qs.append((good, opts))
    return qs


def arabic_letter_lesson(i):
    L = AR_LETTERS[i % len(AR_LETTERS)]
    ch, name, name_tts, name_en, snd = L["ch"], L["name"], L["name_tts"], L["name_en"], L["snd"]
    rng = random.Random(1000 + i)
    scenes = []
    scenes.append({"kind": "letter", "glyph": ch, "short": True,
                   "ar": f"هذا الحرف اسمه {name}", "ar_tts": f"هَذَا الحَرْفُ اسْمُهُ: {name_tts}",
                   "en": f"This letter is called {name_en}", "emoji": "🔤"})
    scenes.append({"kind": "letter", "glyph": f"{ch}َ  {ch}ُ  {ch}ِ", "small": True,
                   "ar": f"نقول: {ch}َ ، {ch}ُ ، {ch}ِ", "ar_tts": f"نَقُولُ: {ch}َ، {ch}ُ، {ch}ِ",
                   "en": f"We say: {snd}a, {snd}u, {snd}i", "emoji": "🗣️"})
    scenes.append({"kind": "forms", "letter": ch, "connect": ch not in NON_CONNECTING,
                   "ar": "يُكتب الحرف بأشكال مختلفة في الكلمة",
                   "ar_tts": "يُكْتَبُ الحَرْفُ بِأَشْكَالٍ مُخْتَلِفَةٍ فِي الكَلِمَةِ",
                   "en": "The letter has different shapes inside a word", "emoji": "✍️"})
    for k, w in enumerate(L["words"]):
        scenes.append({"kind": "text", "short": k < 2,
                       "ar": f"{w['ar']}. تبدأ بحرف {name}.",
                       "ar_tts": f"{w['ar_tts']}. تَبْدَأُ بِحَرْفِ: {name_tts}.",
                       "en": f"{w['en'].capitalize()}. It starts with {name_en}.",
                       "emoji": w["emoji"], "visual": w["visual"]})
    # أسئلة: أي كلمة تبدأ بهذا الحرف؟
    others = [w for j, X in enumerate(AR_LETTERS) if j != i % len(AR_LETTERS) for w in X["words"]]
    quiz = []
    for good, opts in _quiz_words(L["words"], others, 3, rng):
        quiz.append({"ar": f"أيُّ كلمةٍ تبدأ بحرف {name}؟",
                     "ar_tts": f"أَيُّ كَلِمَةٍ تَبْدَأُ بِحَرْفِ: {name_tts}؟",
                     "en": f"Which word starts with {name_en}?",
                     "options": [{"emoji": o["emoji"], "ar": o["ar"], "en": o["en"], "ar_tts": o["ar_tts"]}
                                 for o in opts],
                     "answer": opts.index(good)})
    return {"category": "الحروف", "age": "5-6", "track": "الحروف العربية",
            "title_ar": f"حرف {('ال' + name)}", "title_ar_tts": f"حَرْفُ: {name_tts}",
            "title_en": f"Arabic Letter {name_en}", "hook_ar": f"هيا نتعلم حرف {name}!",
            "scenes": scenes, "keywords": [dict(w, kind="text") for w in L["words"]],
            "quiz": quiz}


# ---------------------------------------------------------------- الأرقام 1-10
NUMS = [
    # رقم، بالعربية، مشكولة، English، emoji، العبارة العربية، مشكولة، الإنجليزية
    (1, "واحد", "وَاحِدْ", "one", "⭐", "نجمة واحدة", "نَجْمَةٌ وَاحِدَةٌ", "One star", "a single yellow star"),
    (2, "اثنان", "اثْنَانْ", "two", "🐱", "قطتان", "قِطَّتَانِ", "Two cats", "two cute cats"),
    (3, "ثلاثة", "ثَلَاثَةْ", "three", "🎈", "ثلاث بالونات", "ثَلَاثُ بَالُونَاتٍ", "Three balloons", "three colorful balloons"),
    (4, "أربعة", "أَرْبَعَةْ", "four", "🍎", "أربع تفاحات", "أَرْبَعُ تُفَّاحَاتٍ", "Four apples", "four red apples"),
    (5, "خمسة", "خَمْسَةْ", "five", "🌸", "خمس زهرات", "خَمْسُ زَهْرَاتٍ", "Five flowers", "five pretty flowers"),
    (6, "ستة", "سِتَّةْ", "six", "🐟", "ست سمكات", "سِتُّ سَمَكَاتٍ", "Six fish", "six colorful fish"),
    (7, "سبعة", "سَبْعَةْ", "seven", "🦋", "سبع فراشات", "سَبْعُ فَرَاشَاتٍ", "Seven butterflies", "seven butterflies"),
    (8, "ثمانية", "ثَمَانِيَةْ", "eight", "🚗", "ثماني سيارات", "ثَمَانِي سَيَّارَاتٍ", "Eight cars", "eight small toy cars"),
    (9, "تسعة", "تِسْعَةْ", "nine", "🍌", "تسع موزات", "تِسْعُ مَوْزَاتٍ", "Nine bananas", "nine yellow bananas"),
    (10, "عشرة", "عَشَرَةْ", "ten", "⚽", "عشر كرات", "عَشْرُ كُرَاتٍ", "Ten balls", "ten colorful balls"),
]


def number_lesson(i):
    n, w, w_tts, w_en, em, phrase, phrase_tts, phrase_en, vis = NUMS[i % len(NUMS)]
    rng = random.Random(2000 + i)
    counting = "، ".join(x[2] for x in NUMS[:n])
    counting_en = ", ".join(x[3] for x in NUMS[:n])
    scenes = [
        {"kind": "letter", "glyph": str(n), "sub": w, "short": True,
         "ar": f"هذا الرقم {w}", "ar_tts": f"هَذَا الرَّقْمُ: {w_tts}",
         "en": f"This is number {w_en}", "emoji": "🔢"},
        {"kind": "count", "n": n, "emoji": em, "short": True,
         "ar": f"نَعُدُّ معاً: {' ، '.join(x[1] for x in NUMS[:n])}", "ar_tts": f"نَعُدُّ مَعًا: {counting}",
         "en": f"Let's count: {counting_en}", "count_tts": counting},
        {"kind": "text", "short": True, "ar": phrase, "ar_tts": phrase_tts, "en": phrase_en,
         "emoji": em, "visual": vis},
    ]
    if n > 1:
        scenes.append({"kind": "text", "ar": f"الرقم {w} يأتي بعد الرقم {NUMS[n - 2][1]}",
                       "ar_tts": f"الرَّقْمُ {w_tts} يَأْتِي بَعْدَ الرَّقْمِ {NUMS[n - 2][2]}",
                       "en": f"Number {w_en} comes after number {NUMS[n - 2][3]}",
                       "emoji": "➡️", "visual": f"the big number {n} next to the number {n - 1}, colorful"})
    if n < 10:
        scenes.append({"kind": "text", "ar": f"والرقم {NUMS[n][1]} يأتي بعده",
                       "ar_tts": f"وَالرَّقْمُ {NUMS[n][2]} يَأْتِي بَعْدَهُ",
                       "en": f"And number {NUMS[n][3]} comes next",
                       "emoji": "⏭️", "visual": f"the big number {n + 1}, colorful cartoon"})
    scenes.append({"kind": "text", "ar": f"أرفع {w} أصابع" if n > 2 else f"أرفع {phrase.split()[0]} من أصابعي",
                   "ar_tts": f"أَرْفَعُ {w_tts} أَصَابِعَ" if n > 2 else f"أَرْفَعُ {w_tts}",
                   "en": f"I hold up {w_en} fingers", "emoji": "🖐️",
                   "visual": f"a happy child's hand holding up {n} fingers, cartoon"})
    # أسئلة
    def digits(correct):
        pool = [x for x in range(1, 11) if x != correct]
        opts = [correct] + rng.sample(pool, 2)
        rng.shuffle(opts)
        return opts
    quiz = []
    o = digits(n)
    quiz.append({"ar": "كم عدد هذه الأشياء؟", "ar_tts": "كَمْ عَدَدُ هَذِهِ الأَشْيَاءِ؟",
                 "en": "How many are there?", "stimulus": em * n,
                 "options": [{"text": str(x), "ar": NUMS[x - 1][1], "ar_tts": NUMS[x - 1][2], "en": NUMS[x - 1][3]} for x in o],
                 "answer": o.index(n)})
    o = digits(n)
    quiz.append({"ar": f"أيُّ رقمٍ هو {w}؟", "ar_tts": f"أَيُّ رَقْمٍ هُوَ: {w_tts}؟",
                 "en": f"Which number is {w_en}?",
                 "options": [{"text": str(x), "ar": NUMS[x - 1][1], "ar_tts": NUMS[x - 1][2], "en": NUMS[x - 1][3]} for x in o],
                 "answer": o.index(n)})
    o = digits(n)
    quiz.append({"ar": f"أيُّ مجموعةٍ فيها {w}؟", "ar_tts": f"أَيُّ مَجْمُوعَةٍ فِيهَا: {w_tts}؟",
                 "en": f"Which group has {w_en}?",
                 "options": [{"emoji": em * x, "ar": NUMS[x - 1][1], "ar_tts": NUMS[x - 1][2], "en": NUMS[x - 1][3]} for x in o],
                 "answer": o.index(n)})
    kw = [{"ar": w, "ar_tts": w_tts, "en": w_en, "emoji": em, "visual": vis, "kind": "text"}]
    return {"category": "الأرقام", "age": "5-6", "track": "الأرقام والعدّ",
            "title_ar": f"الرقم {w}", "title_ar_tts": f"الرَّقْمُ: {w_tts}",
            "title_en": f"Number {n} - {w_en.capitalize()}", "hook_ar": f"هيا نتعلم الرقم {w}!",
            "scenes": scenes, "keywords": kw, "quiz": quiz}


# ---------------------------------------------------------------- الحروف الإنجليزية
# الحرف | كلمات: English,عربي مشكول,emoji
EN_LETTERS_RAW = """
A|apple,تُفَّاحَة,🍎;ant,نَمْلَة,🐜;airplane,طَائِرَة,✈️
B|ball,كُرَة,⚽;banana,مَوْزَة,🍌;bear,دُبّ,🐻
C|cat,قِطَّة,🐱;car,سَيَّارَة,🚗;cake,كَعْكَة,🎂
D|dog,كَلْب,🐶;duck,بَطَّة,🦆;door,بَاب,🚪
E|egg,بَيْضَة,🥚;elephant,فِيل,🐘;eye,عَيْن,👁️
F|fish,سَمَكَة,🐟;flower,زَهْرَة,🌸;frog,ضِفْدَع,🐸
G|giraffe,زَرَافَة,🦒;grapes,عِنَب,🍇;goat,مَاعِز,🐐
H|horse,حِصَان,🐴;hat,قُبَّعَة,👒;house,بَيْت,🏠
I|ice cream,مُثَلَّجَات,🍦;insect,حَشَرَة,🐛;island,جَزِيرَة,🏝️
J|juice,عَصِير,🧃;jacket,سُتْرَة,🧥;jellyfish,قِنْدِيلُ البَحْر,🪼
K|key,مِفْتَاح,🔑;kite,طَائِرَةٌ وَرَقِيَّة,🪁;kangaroo,كَنْغَر,🦘
L|lion,أَسَد,🦁;lemon,لَيْمُون,🍋;leaf,وَرَقَة,🍃
M|monkey,قِرْد,🐒;moon,قَمَر,🌙;milk,حَلِيب,🥛
N|nose,أَنْف,👃;nest,عُشّ,🪺;nurse,مُمَرِّضَة,🧑‍⚕️
O|orange,بُرْتُقَالَة,🍊;owl,بُومَة,🦉;octopus,أُخْطُبُوط,🐙
P|pizza,بِيتْزَا,🍕;penguin,بَطْرِيق,🐧;pear,كُمَّثْرَى,🍐
Q|queen,مَلِكَة,👸;quilt,لِحَاف,🛏️
R|rabbit,أَرْنَب,🐰;rain,مَطَر,🌧️;rainbow,قَوْسُ قُزَح,🌈
S|sun,شَمْس,☀️;star,نَجْمَة,⭐;snake,ثُعْبَان,🐍
T|tiger,نَمِر,🐅;tree,شَجَرَة,🌳;train,قِطَار,🚆
U|umbrella,مِظَلَّة,☂️;unicorn,حِصَانٌ خُرَافِيّ,🦄
V|violin,كَمَان,🎻;vase,مِزْهَرِيَّة,🏺;vegetables,خُضَار,🥦
W|watermelon,بِطِّيخ,🍉;whale,حُوت,🐋;window,نَافِذَة,🪟
X|xylophone,إِكْسِيلُوفُون,🎹;fox,ثَعْلَب,🦊
Y|yo-yo,يُويُو,🪀;yacht,يَخْت,⛵;yogurt,لَبَنٌ زَبَادِي,🥛
Z|zebra,حِمَارٌ وَحْشِيّ,🦓;zoo,حَدِيقَةُ الحَيَوَان,🦁;zipper,سَحَّاب,🧵
"""
EN_NAMES_AR = dict(zip("ABCDEFGHIJKLMNOPQRSTUVWXYZ",
                       "إيه بي سي دي إي إف جي إتش آي جيه كيه إل إم إن أو بي كيو آر إس تي يو في دبليو إكس واي زد".split()))
EN_NAMES_TTS = dict(zip("ABCDEFGHIJKLMNOPQRSTUVWXYZ",
                        "إِيهْ بِي سِي دِي إِي إِفْ جِي إِتْشْ آي جَيْ كَيْ إِلْ إِمْ إِنْ أُو بِي كِيُو آرْ إِسْ تِي يُو فِي دَبْلِيُو إِكْسْ وَايْ زِدْ".split()))


def _parse_en_letters():
    out = []
    for line in EN_LETTERS_RAW.strip().splitlines():
        ch, words = line.split("|")
        ws = []
        for w in words.split(";"):
            en, ar_tts, em = w.split(",")
            ws.append({"ar": strip_tashkeel(ar_tts), "ar_tts": ar_tts, "en": en, "emoji": em,
                       "visual": f"a cute {en}"})
        out.append({"ch": ch, "words": ws})
    return out


EN_LETTERS = _parse_en_letters()


def english_letter_lesson(i):
    L = EN_LETTERS[i % len(EN_LETTERS)]
    ch = L["ch"]
    nm, nm_tts = EN_NAMES_AR[ch], EN_NAMES_TTS[ch]
    rng = random.Random(3000 + i)
    scenes = [
        {"kind": "letter", "glyph": f"{ch}{ch.lower()}", "latin": True, "short": True,
         "ar": f"هذا الحرف الإنجليزي {nm}", "ar_tts": f"هَذَا الحَرْفُ الإِنْجِلِيزِيُّ: {nm_tts}",
         "en": f"This is the letter {ch}", "en_tts": f"This is the letter {ch}.", "emoji": "🔠"},
    ]
    for k, w in enumerate(L["words"]):
        scenes.append({"kind": "text", "short": k < 2,
                       "ar": f"{w['ar']}", "ar_tts": w["ar_tts"],
                       "en": f"{ch} is for {w['en']}", "emoji": w["emoji"], "visual": w["visual"]})
    others = [w for j, X in enumerate(EN_LETTERS) if j != i % len(EN_LETTERS) for w in X["words"]]
    quiz = []
    for good, opts in _quiz_words(L["words"], others, min(3, len(L["words"])), rng):
        quiz.append({"ar": f"أيُّ كلمةٍ إنجليزيةٍ تبدأ بحرف {nm}؟",
                     "ar_tts": f"أَيُّ كَلِمَةٍ إِنْجِلِيزِيَّةٍ تَبْدَأُ بِحَرْفِ: {nm_tts}؟",
                     "en": f"Which word starts with {ch}?",
                     "options": [{"emoji": o["emoji"], "ar": o["en"], "en": o["en"], "ar_tts": o["ar_tts"]} for o in opts],
                     "answer": opts.index(good), "answer_en_only": True})
    return {"category": "الإنجليزية", "age": "5-8", "track": "الحروف الإنجليزية",
            "title_ar": f"الحرف الإنجليزي {nm}", "title_ar_tts": f"الحَرْفُ الإِنْجِلِيزِيُّ: {nm_tts}",
            "title_en": f"English Letter {ch}", "hook_ar": f"هيا نتعلم الحرف الإنجليزي {nm}!",
            "scenes": scenes, "keywords": [dict(w, kind="text") for w in L["words"]], "quiz": quiz}


# ---------------------------------------------------------------- مسارات يقودها Gemini
TOPICS = {
    "عالمي من حولي": ("5-8", [
        "الحيوانات الأليفة (القطة، الكلب، الأرنب، الحصان)", "حيوانات المزرعة وما تعطينا",
        "حيوانات الغابة والصحراء", "الفواكه ولونها وطعمها", "الخضروات وفوائدها",
        "أجزاء الجسم", "الحواس الخمس", "أفراد العائلة", "المهن (الطبيب، المعلم، الشرطي، الخباز)",
        "الأماكن من حولنا (المدرسة، المستشفى، السوق، الحديقة)", "وسائل المواصلات",
        "الطيور وأصواتها", "الحيوانات البحرية", "الحشرات الصغيرة", "أدوات المدرسة", "غرف البيت وأثاثه",
        "الملابس حسب الطقس", "الطعام الصحي"]),
    "علوم صغيرة": ("7-8", [
        "من أين يأتي المطر؟", "الشمس وفائدتها", "القمر والنجوم", "كيف ينمو النبات؟", "الماء وأهميته",
        "الفصول الأربعة", "الكرة الأرضية", "الجاذبية: لماذا تسقط الأشياء؟", "الصوت: كيف نسمع؟",
        "الضوء والظل", "الهواء حولنا", "حالات الماء: ثلج وماء وبخار", "النحلة والعسل", "دورة حياة الفراشة",
        "الكواكب الثمانية", "البراكين", "الأسنان والعناية بها", "ما الذي يطفو وما الذي يغرق؟"]),
    "قيم وأخلاق": ("5-8", [
        "الصدق", "قول شكراً", "التعاون", "النظافة", "احترام الكبار", "بر الوالدين", "الاعتذار والتسامح",
        "المشاركة مع الآخرين", "الأمانة", "الصبر", "الرفق بالحيوان", "المحافظة على البيئة",
        "السلام والتحية", "الأدب على المائدة", "مساعدة المحتاج", "احترام الوقت", "الشجاعة", "الكلمة الطيبة"]),
    "ألوان وأشكال وأوقات": ("5-6", [
        "الألوان الأساسية: أحمر وأزرق وأصفر", "خلط الألوان: كيف نصنع الأخضر والبرتقالي؟",
        "الألوان في الطبيعة", "الأشكال: الدائرة والمربع والمثلث", "المستطيل والنجمة والقلب",
        "أشكال من حولنا في البيت", "أيام الأسبوع", "شهور السنة", "الصباح والظهر والمساء والليل",
        "كبير وصغير، طويل وقصير", "فوق وتحت، أمام وخلف", "الأضداد البسيطة", "الأعداد الزوجية والفردية",
        "الجمع البسيط حتى 5", "الطرح البسيط حتى 5", "العد من 11 إلى 20", "العشرات: 10، 20، 30", "الجمع حتى 10"]),
}

TOPICS["قصة اليوم"] = (5, [
    "قصة الأرنب الصغير الذي تعلّم الصدق", "قصة النملة المجتهدة", "قصة السلحفاة والأرنب", "قصة الطفل الذي شارك لعبته",
    "قصة القطة التي ضاعت وعادت", "قصة الشجرة الكريمة", "قصة العصفور وعشه الجديد", "قصة الفيل الصغير والأدب",
    "قصة الطفل الذي ساعد جاره", "قصة السمكة الصغيرة الشجاعة", "قصة النحلة العاملة", "قصة الطفل ونظافة الأسنان"])
TOPICS["قصة اليوم"][1].append("قصة الأخ والأخت وحديقة الأحلام")
TOPICS["ألغاز وألعاب"] = (5, [
    "ألغاز الحيوانات: من أنا؟", "ألغاز الفواكه والخضروات", "لعبة أين الشيء المختلف؟", "ألغاز الأشكال والألوان",
    "لعبة خمّن الصوت", "ألغاز الأعداد البسيطة", "لعبة أكمل الكلمة", "ألغاز الطبيعة: من أنا؟",
    "لعبة الذاكرة: ماذا اختفى؟", "ألغاز الأدوات في البيت", "لعبة الأضداد", "ألغاز المهن: من أنا؟"])
STYLE = {
    "قصة اليوم": "اجعل الدرس قصة قصيرة مشوّقة بشخصيات لطيفة وبداية وحدث وحل، كل مشهد جزء من القصة، وتنتهي بحكمة بسيطة.",
    "ألغاز وألعاب": "اجعل الدرس لعبة تفاعلية: كل مشهد لغز قصير من نوع «من أنا؟» بثلاثة تلميحات ثم الجواب، بأسلوب حماسي مرح.",
}

# أيام الأسبوع -> مسار (يبدأ العدّاد من 0)
TRACKS = ["ar_letters", "numbers", "عالمي من حولي", "en_letters", "علوم صغيرة", "قيم وأخلاق",
          "ألوان وأشكال وأوقات", "قصة اليوم", "ألغاز وألعاب"]


def pick(day):
    """يرجع (اسم المسار، رقم الدرس داخل المسار، وصف الدرس) لليوم رقم day."""
    track = TRACKS[day % len(TRACKS)]
    k = day // len(TRACKS)
    if track == "ar_letters":
        return track, k, arabic_letter_lesson(k)
    if track == "numbers":
        return track, k, number_lesson(k)
    if track == "en_letters":
        return track, k, english_letter_lesson(k)
    age, topics = TOPICS[track]
    topic = topics[k % len(topics)]
    return track, k, {"gemini": True, "track": track, "age": age, "topic": topic, "style": STYLE.get(track, "")}
