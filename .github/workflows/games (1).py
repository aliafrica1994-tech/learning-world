# -*- coding: utf-8 -*-
"""ألعاب تعليمية تُولَّد برمجياً (بلا Gemini ولا إنترنت): عدّ، الشيء المختلف، الأنماط، ألغاز «من أنا؟»."""
import random

# emoji، مفرد، جمع، English مفرد، English جمع
ITEMS = [
    ("🍎", "تفاحة", "تفاحات", "apple", "apples"), ("🐱", "قطة", "قطط", "cat", "cats"),
    ("🎈", "بالونة", "بالونات", "balloon", "balloons"), ("⭐", "نجمة", "نجوم", "star", "stars"),
    ("🐟", "سمكة", "أسماك", "fish", "fish"), ("🌸", "زهرة", "زهرات", "flower", "flowers"),
    ("🚗", "سيارة", "سيارات", "car", "cars"), ("🦆", "بطة", "بطات", "duck", "ducks"),
    ("🍌", "موزة", "موزات", "banana", "bananas"), ("🐶", "كلب", "كلاب", "dog", "dogs"),
    ("🍓", "فراولة", "فراولات", "strawberry", "strawberries"), ("🦋", "فراشة", "فراشات", "butterfly", "butterflies"),
    ("⚽", "كرة", "كرات", "ball", "balls"), ("🐢", "سلحفاة", "سلاحف", "turtle", "turtles"),
    ("🍪", "بسكويتة", "بسكويتات", "cookie", "cookies"), ("🐰", "أرنب", "أرانب", "rabbit", "rabbits"),
]
NUM_AR = {1: "واحد", 2: "اثنان", 3: "ثلاثة", 4: "أربعة", 5: "خمسة", 6: "ستة", 7: "سبعة", 8: "ثمانية", 9: "تسعة",
          10: "عشرة"}
NUM_EN = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine", 10: "ten"}
SHAPES = ["🔴", "🔵", "🟡", "🟢", "🟣", "🟠"]
SHAPE_NAMES = {"🔴": ("أحمر", "red"), "🔵": ("أزرق", "blue"), "🟡": ("أصفر", "yellow"), "🟢": ("أخضر", "green"),
               "🟣": ("بنفسجي", "purple"), "🟠": ("برتقالي", "orange")}

# ألغاز: (النص العربي، English، emoji الصحيح، اسم عربي، اسم إنجليزي)
RIDDLES = [
    ("أنا حيوان أقول مياو، وأحب شرب الحليب. من أنا؟", "I say meow and I love milk. Who am I?", "🐱", "قطة", "cat"),
    ("أنا حيوان أقول هاو هاو، وأحرس البيت. من أنا؟", "I say woof and I guard the house. Who am I?", "🐶", "كلب", "dog"),
    ("أنا حيوان كبير، ولي خرطوم طويل. من أنا؟", "I am big and I have a long trunk. Who am I?", "🐘", "فيل", "elephant"),
    ("أنا ملك الغابة، وصوتي زئير عالٍ. من أنا؟", "I am the king of the jungle and I roar. Who am I?", "🦁", "أسد", "lion"),
    ("أنا حيوان أعطيكم الحليب، وأقول موو. من أنا؟", "I give you milk and I say moo. Who am I?", "🐮", "بقرة", "cow"),
    ("أنا طائر أسبح في الماء، وأقول كواك. من أنا؟", "I am a bird who swims and says quack. Who am I?", "🦆", "بطة", "duck"),
    ("أنا طائر أُغنّي في الصباح، وأعيش في العش. من أنا؟", "I am a bird that sings in the morning and lives in a nest. Who am I?", "🐦", "عصفور", "bird"),
    ("أنا حيوان صغير أقفز، وأحب أكل الجزر. من أنا؟", "I am small, I hop and I love carrots. Who am I?", "🐰", "أرنب", "rabbit"),
    ("أنا فاكهة حمراء، وأحيانًا خضراء، وطعمي حلو. من أنا؟", "I am a red or green fruit with a sweet taste. Who am I?", "🍎", "تفاحة", "apple"),
    ("أنا فاكهة صفراء، ويقشّرني القرد. من أنا؟", "I am a yellow fruit and the monkey peels me. Who am I?", "🍌", "موزة", "banana"),
    ("أنا خضار برتقالي، ويحبني الأرنب. من أنا؟", "I am an orange vegetable that rabbits love. Who am I?", "🥕", "جزرة", "carrot"),
    ("أنا في السماء في النهار، وأعطيكم الضوء والدفء. من أنا؟", "I am in the sky in the daytime and I give light and warmth. Who am I?", "☀️", "شمس", "sun"),
    ("أنا أظهر في الليل، وأنير السماء مع النجوم. من أنا؟", "I appear at night and shine with the stars. Who am I?", "🌙", "قمر", "moon"),
    ("أنا أنزل من الغيوم، وأسقي الأشجار والزهور. من أنا؟", "I fall from the clouds and water the plants. Who am I?", "🌧️", "مطر", "rain"),
    ("أنا مركبة لها أربع عجلات، وأنقلكم إلى المدرسة. من أنا؟", "I am a vehicle with four wheels that takes you to school. Who am I?", "🚗", "سيارة", "car"),
    ("أنا أطير في السماء، وأحمل المسافرين بين البلدان. من أنا؟", "I fly in the sky and carry travelers between countries. Who am I?", "✈️", "طائرة", "airplane"),
    ("أنا أعيش في البحر، ولي زعانف وأسبح. من أنا؟", "I live in the sea, I have fins and I swim. Who am I?", "🐟", "سمكة", "fish"),
    ("أنا حشرة جميلة، لي أجنحة ملونة وأطير بين الزهور. من أنا؟", "I am a pretty insect with colorful wings flying over flowers. Who am I?", "🦋", "فراشة", "butterfly"),
    ("أنا أقرأ فيّ قصصًا ممتعة، ولي صفحات كثيرة. من أنا؟", "You read fun stories in me and I have many pages. Who am I?", "📚", "كتاب", "book"),
    ("أنا أكتب بي على الورق، ولي رأس مدبب. من أنا؟", "You write on paper with me and I have a sharp tip. Who am I?", "✏️", "قلم", "pencil"),
]
RIDDLES += [
    ("أنا أعيش في الغابة، ولي رقبة طويلة جدًا. من أنا؟", "I live in the jungle and I have a very long neck. Who am I?", "🦒", "زرافة", "giraffe"),
    ("أنا حيوان أعطيكم الصوف، وأقول ماع. من أنا؟", "I give you wool and I say baa. Who am I?", "🐑", "خروف", "sheep"),
    ("أنا طائر أضع البيض، وأوقظكم بصوتي في الصباح. من أنا؟", "I am a bird that lays eggs and wakes you in the morning. Who am I?", "🐔", "دجاجة", "hen"),
    ("أنا حيوان بطيء، وأحمل بيتي على ظهري. من أنا؟", "I am slow and I carry my house on my back. Who am I?", "🐢", "سلحفاة", "turtle"),
    ("أنا حيوان قوي أعيش في الغابة، ولي مخالب وأحب العسل. من أنا؟", "I am a strong forest animal with claws and I love honey. Who am I?", "🐻", "دب", "bear"),
    ("أنا حيوان أقفز وأحمل صغيري في جيبي. من أنا؟", "I hop and I carry my baby in my pocket. Who am I?", "🦘", "كنغر", "kangaroo"),
    ("أنا حشرة صغيرة أصنع العسل اللذيذ. من أنا؟", "I am a small insect that makes delicious honey. Who am I?", "🐝", "نحلة", "bee"),
    ("أنا حيوان أعيش في الماء البارد، وأمشي على الجليد. من أنا؟", "I live in the cold and I walk on the ice. Who am I?", "🐧", "بطريق", "penguin"),
    ("أنا حيوان كبير جدًا أعيش في البحر، وأخرج الماء من رأسي. من أنا؟", "I am a very big sea animal and I spray water from my head. Who am I?", "🐋", "حوت", "whale"),
    ("أنا حيوان مخطط بالأبيض والأسود، وأشبه الحصان. من أنا؟", "I have black and white stripes and look like a horse. Who am I?", "🦓", "حمار وحشي", "zebra"),
    ("أنا فاكهة صفراء حامضة، وأصنع منك العصير. من أنا؟", "I am a sour yellow fruit used to make juice. Who am I?", "🍋", "ليمونة", "lemon"),
    ("أنا فاكهة حمراء صغيرة، وفوقي نقاط صغيرة. من أنا؟", "I am a small red fruit with tiny seeds on me. Who am I?", "🍓", "فراولة", "strawberry"),
    ("أنا فاكهة كبيرة خضراء من الخارج وحمراء من الداخل. من أنا؟", "I am a big fruit, green outside and red inside. Who am I?", "🍉", "بطيخة", "watermelon"),
    ("أنا ألبسك في القدم، وأحميك من الأرض. من أنا؟", "You wear me on your feet to protect them. Who am I?", "👟", "حذاء", "shoe"),
    ("أنا أضيء في الليل في غرفتكم، وأنتم تشعلونني بزر. من أنا؟", "I light your room at night when you press a button. Who am I?", "💡", "مصباح", "lamp"),
    ("أنا أرتفع في السماء بعد المطر، وألواني كثيرة. من أنا؟", "I appear in the sky after rain with many colors. Who am I?", "🌈", "قوس قزح", "rainbow"),
    ("أنا أدق وأعلمكم الوقت، ولي عقربان. من أنا؟", "I tell you the time and I have two hands. Who am I?", "⏰", "ساعة", "clock"),
    ("أنا أحمل ظهرك الكتب، وتذهبون بي إلى المدرسة. من أنا؟", "I carry your books and you take me to school. Who am I?", "🎒", "حقيبة", "backpack"),
    ("أنا أطير وأنا صغير بخيط في يد طفل. من أنا؟", "I fly high on a string held by a child. Who am I?", "🪁", "طائرة ورقية", "kite"),
    ("أنا حار في الصيف وأضيء النهار، ولا أحد يلمسني. من أنا؟", "I am hot in summer and I light the day. Who am I?", "☀️", "شمس", "sun"),
    ("أنا مركبة كبيرة أسير على السكة الحديدية. من أنا؟", "I am a long vehicle that runs on rails. Who am I?", "🚆", "قطار", "train"),
    ("أنا أسبح في الماء وأحمل الناس بين الشواطئ. من أنا؟", "I float on the water and carry people across the sea. Who am I?", "🚢", "سفينة", "ship"),
    ("أنا نجمة النهار، وأعطيكم الضوء. من أنا؟", "I am the star of the day and I give light. Who am I?", "🌞", "شمس", "sun"),
    ("أنا طائر جميل أنشر ريشي الملون كالمروحة. من أنا؟", "I am a pretty bird that spreads colorful feathers like a fan. Who am I?", "🦚", "طاووس", "peacock"),
    ("أنا حيوان أعيش في الصحراء، ولي سنام على ظهري. من أنا؟", "I live in the desert and I have a hump on my back. Who am I?", "🐪", "جمل", "camel"),
]
DISTRACT = [("🐱", "قطة", "cat"), ("🦒", "زرافة", "giraffe"), ("🐢", "سلحفاة", "turtle"), ("🐻", "دب", "bear"),
            ("🐑", "خروف", "sheep"), ("🐧", "بطريق", "penguin"), ("🍋", "ليمونة", "lemon"), ("🍓", "فراولة", "strawberry"), ("🐶", "كلب", "dog"), ("🐘", "فيل", "elephant"), ("🦁", "أسد", "lion"),
            ("🐮", "بقرة", "cow"), ("🦆", "بطة", "duck"), ("🐰", "أرنب", "rabbit"), ("🍎", "تفاحة", "apple"),
            ("🍌", "موزة", "banana"), ("🥕", "جزرة", "carrot"), ("☀️", "شمس", "sun"), ("🌙", "قمر", "moon"),
            ("🚗", "سيارة", "car"), ("✈️", "طائرة", "airplane"), ("🐟", "سمكة", "fish"), ("📚", "كتاب", "book"),
            ("🐦", "عصفور", "bird"), ("🦋", "فراشة", "butterfly")]


def _opt(emo, ar, en):
    return {"emoji": emo, "ar": ar, "ar_tts": ar, "en": en}


def _count(rng):
    emo, s, p, es, ep = rng.choice(ITEMS)
    n = rng.randint(2, 9)
    pool = [x for x in range(1, 11) if x != n]
    opts = [n] + rng.sample(pool, 2)
    rng.shuffle(opts)
    return {"ar": f"كم عدد {p}؟ عدّوا معي!", "ar_tts": f"كَمْ عَدَدُ {p}؟ عُدُّوا مَعِي!",
            "en": f"How many {ep} can you count?", "stimulus": emo * n,
            "options": [{"text": str(x), "ar": NUM_AR[x], "ar_tts": NUM_AR[x], "en": NUM_EN[x]} for x in opts],
            "answer": opts.index(n)}


def _odd(rng):
    a, b, c = rng.sample(ITEMS, 3)
    n = rng.randint(4, 6)
    items = [a[0]] * n
    pos = rng.randint(0, n - 1)
    items[pos] = b[0]
    opts = [b, a, c]
    rng.shuffle(opts)
    return {"ar": "ما هو الشيء المختلف بينهم؟", "ar_tts": "مَا هُوَ الشَّيْءُ المُخْتَلِفُ بَيْنَهُمْ؟",
            "en": "Which one is different?", "stimulus": "".join(items),
            "options": [_opt(o[0], o[1], o[3]) for o in opts], "answer": opts.index(b)}


def _pattern(rng):
    x, y = rng.sample(SHAPES, 2)
    z = rng.choice([s for s in SHAPES if s not in (x, y)])
    if rng.random() < 0.5:
        seq = [x, y, x, y, x]
        nxt = y
    else:
        seq = [x, x, y, x, x]
        nxt = y
    opts = [nxt] + [s for s in (x, z) if s != nxt][:2]
    rng.shuffle(opts)
    return {"ar": "ما اللون الذي يأتي بعد ذلك؟", "ar_tts": "مَا اللَّوْنُ الَّذِي يَأْتِي بَعْدَ ذَلِكَ؟",
            "en": "Which color comes next?", "stimulus": "".join(seq),
            "options": [_opt(o, SHAPE_NAMES[o][0], SHAPE_NAMES[o][1]) for o in opts], "answer": opts.index(nxt)}


def _riddle(rng, r=None):
    ar, en, emo, nar, nen = r or rng.choice(RIDDLES)
    others = [d for d in DISTRACT if d[0] != emo]
    opts = [(emo, nar, nen)] + rng.sample(others, 2)
    rng.shuffle(opts)
    return {"ar": ar, "ar_tts": ar, "en": en, "options": [_opt(*o) for o in opts], "answer": opts.index((emo, nar, nen))}


def game_lesson(track, k):
    rng = random.Random(1000 + k * 7 + (3 if track in ("ألغاز الذكاء", "تحدي الذكاء") else 0) + (500 if track == "تحدي الذكاء" else 0))
    if track == "ألعاب العدّ والأنماط":
        makers = [_count, _count, _pattern, _odd, _count, _pattern, _odd, _count]
        title_ar, title_en = f"لعبة التحدي: العدّ والأنماط {k + 1}", f"Counting & Patterns Game {k + 1}"
        key = "game"
    else:
        order = list(range(len(RIDDLES)))
        random.Random(77 if track == "تحدي الذكاء" else 1).shuffle(order)
        base = k * 6 + (len(order) // 2 if track == "تحدي الذكاء" else 0)
        rounds = [_riddle(rng, RIDDLES[order[(base + i) % len(order)]]) for i in range(5)]
        rounds += [_odd(rng), _pattern(rng), _riddle(rng, RIDDLES[order[(base + 5) % len(order)]])]
        if track == "تحدي الذكاء":
            title_ar, title_en = f"تحدي الذكاء: خمّن الجواب {k + 1}", f"Brain Challenge: Guess It! {k + 1}"
        else:
            title_ar, title_en = f"ألغاز الذكاء: من أنا؟ {k + 1}", f"Riddle Challenge: Who Am I? {k + 1}"
        key = "riddles"
        makers = None
    quiz = [m(rng) for m in makers] if makers else rounds
    scenes = [
        {"kind": "text", "emoji": "🎮", "ar": "هيا نلعب ونتعلم! في كل جولة سؤال، وعندكم خمس ثوانٍ للتفكير.",
         "ar_tts": "هَيَّا نَلْعَبُ وَنَتَعَلَّمُ! فِي كُلِّ جَوْلَةٍ سُؤَالٌ، وَعِنْدَكُمْ خَمْسُ ثَوَانٍ لِلتَّفْكِيرِ.",
         "en": "Let's play and learn! Each round has a question, and you have five seconds to think."},
        {"kind": "text", "emoji": "🤔", "ar": "استعدوا! كل إجابة صحيحة تساوي نجمة.",
         "ar_tts": "اسْتَعِدُّوا! كُلُّ إِجَابَةٍ صَحِيحَةٍ تُسَاوِي نَجْمَةً.",
         "en": "Get ready! Every right answer is a star."},
    ]
    return {"category": "ألعاب", "age": "5-7", "track": "ألعاب تعليمية", "game": True, "game_key": key,
            "title_ar": title_ar, "title_ar_tts": title_ar, "title_en": title_en,
            "hook_ar": "هيا نلعب ونتعلم!", "scenes": scenes, "keywords": [], "quiz": quiz}
