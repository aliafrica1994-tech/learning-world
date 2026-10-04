# دروس احتياطية تعمل بدون أي مفتاح (تُستخدم إذا فشل Gemini أو انتهت حصته المجانية).
# كل مشهد: ar = نص عربي فصيح، en = English، emoji = الصورة، visual = وصف للصورة

FALLBACK_LESSONS = [
    {
        "category": "الحروف", "age": "5-6",
        "title_ar": "نتعلم الحروف: أ ب ت", "title_en": "Arabic Letters: Alif Ba Ta",
        "scenes": [
            {"ar": "الحرف الأول هو الألف. أرنب يبدأ بحرف الألف.", "en": "The first letter is Alif. Rabbit starts with Alif.", "emoji": "🐰", "visual": "cute rabbit"},
            {"ar": "الحرف الثاني هو الباء. بطة تبدأ بحرف الباء.", "en": "The second letter is Ba. Duck starts with Ba.", "emoji": "🦆", "visual": "cute duck"},
            {"ar": "الحرف الثالث هو التاء. تفاحة تبدأ بحرف التاء.", "en": "The third letter is Ta. Apple starts with Ta.", "emoji": "🍎", "visual": "red apple"},
        ],
    },
    {
        "category": "الأرقام", "age": "5-6",
        "title_ar": "نعدّ من واحد إلى خمسة", "title_en": "Counting One to Five",
        "scenes": [
            {"ar": "واحد. نجمة واحدة في السماء.", "en": "One. One star in the sky.", "emoji": "⭐", "visual": "one yellow star"},
            {"ar": "اثنان. عينان تنظران.", "en": "Two. Two eyes to see.", "emoji": "👀", "visual": "two big eyes"},
            {"ar": "ثلاثة. ثلاث فراشات تطير.", "en": "Three. Three butterflies fly.", "emoji": "🦋", "visual": "three butterflies"},
            {"ar": "أربعة. أربع زهرات جميلة.", "en": "Four. Four pretty flowers.", "emoji": "🌸", "visual": "four flowers"},
            {"ar": "خمسة. خمس أصابع في يدي.", "en": "Five. Five fingers on my hand.", "emoji": "🖐️", "visual": "a hand with five fingers"},
        ],
    },
    {
        "category": "الألوان", "age": "5-6",
        "title_ar": "نتعرف على الألوان", "title_en": "Let's Learn Colors",
        "scenes": [
            {"ar": "التفاحة حمراء.", "en": "The apple is red.", "emoji": "🍎", "visual": "red apple"},
            {"ar": "الموزة صفراء.", "en": "The banana is yellow.", "emoji": "🍌", "visual": "yellow banana"},
            {"ar": "الورقة خضراء.", "en": "The leaf is green.", "emoji": "🍃", "visual": "green leaf"},
            {"ar": "السماء زرقاء.", "en": "The sky is blue.", "emoji": "🌤️", "visual": "blue sky"},
        ],
    },
    {
        "category": "الحيوانات", "age": "5-8",
        "title_ar": "أصوات الحيوانات", "title_en": "Animal Sounds",
        "scenes": [
            {"ar": "القطة تقول مياو.", "en": "The cat says meow.", "emoji": "🐱", "visual": "cute cat"},
            {"ar": "الكلب يقول هاو هاو.", "en": "The dog says woof.", "emoji": "🐶", "visual": "cute dog"},
            {"ar": "البقرة تقول موو.", "en": "The cow says moo.", "emoji": "🐮", "visual": "cute cow"},
            {"ar": "الأسد يزأر بصوت عالٍ.", "en": "The lion roars loudly.", "emoji": "🦁", "visual": "friendly lion"},
        ],
    },
    {
        "category": "الأشكال", "age": "5-8",
        "title_ar": "نتعلم الأشكال", "title_en": "Learning Shapes",
        "scenes": [
            {"ar": "هذه دائرة. الكرة على شكل دائرة.", "en": "This is a circle. A ball is a circle.", "emoji": "⚽", "visual": "a ball"},
            {"ar": "هذا مربع. النافذة على شكل مربع.", "en": "This is a square. A window is a square.", "emoji": "🪟", "visual": "a window"},
            {"ar": "هذا مثلث. الخيمة على شكل مثلث.", "en": "This is a triangle. A tent is a triangle.", "emoji": "⛺", "visual": "a tent"},
        ],
    },
    {
        "category": "القيم", "age": "7-8",
        "title_ar": "نقول شكراً", "title_en": "Saying Thank You",
        "scenes": [
            {"ar": "عندما يساعدني أحد، أقول له شكراً.", "en": "When someone helps me, I say thank you.", "emoji": "🤝", "visual": "two kids helping each other"},
            {"ar": "أشكر أمي على الطعام اللذيذ.", "en": "I thank my mom for the tasty food.", "emoji": "🍲", "visual": "mother serving food"},
            {"ar": "الكلمة الطيبة تجعل الجميع سعداء.", "en": "A kind word makes everyone happy.", "emoji": "😊", "visual": "happy kids smiling"},
        ],
    },
    {
        "category": "العلوم", "age": "7-8",
        "title_ar": "من أين يأتي المطر؟", "title_en": "Where Does Rain Come From?",
        "scenes": [
            {"ar": "الشمس تسخّن ماء البحر فيصعد بخاراً.", "en": "The sun heats sea water and it rises as vapor.", "emoji": "☀️", "visual": "sun over the sea"},
            {"ar": "البخار يتجمع فيصنع سحابة.", "en": "The vapor gathers and makes a cloud.", "emoji": "☁️", "visual": "fluffy cloud"},
            {"ar": "عندما تثقل السحابة تنزل قطرات المطر.", "en": "When the cloud gets heavy, raindrops fall.", "emoji": "🌧️", "visual": "rain falling from cloud"},
        ],
    },
]


# ---------------------------------------------------------------- التشكيل للصوت فقط
# النص المشكول يُقرأ بالصوت الآلي بدقة أكبر، بينما يظهر النص العادي على الشاشة.
TASHKEEL = {
    "نتعلم الحروف: أ ب ت": "نَتَعَلَّمُ الحُرُوفَ: أَلِفْ، بَاءْ، تَاءْ",
    "الحرف الأول هو الألف. أرنب يبدأ بحرف الألف.": "الحَرْفُ الأَوَّلُ هُوَ الأَلِفُ. أَرْنَبٌ يَبْدَأُ بِحَرْفِ الأَلِفِ.",
    "الحرف الثاني هو الباء. بطة تبدأ بحرف الباء.": "الحَرْفُ الثَّانِي هُوَ البَاءُ. بَطَّةٌ تَبْدَأُ بِحَرْفِ البَاءِ.",
    "الحرف الثالث هو التاء. تفاحة تبدأ بحرف التاء.": "الحَرْفُ الثَّالِثُ هُوَ التَّاءُ. تُفَّاحَةٌ تَبْدَأُ بِحَرْفِ التَّاءِ.",
    "نعدّ من واحد إلى خمسة": "نَعُدُّ مِنْ وَاحِدٍ إِلَى خَمْسَةٍ",
    "واحد. نجمة واحدة في السماء.": "وَاحِدٌ. نَجْمَةٌ وَاحِدَةٌ فِي السَّمَاءِ.",
    "اثنان. عينان تنظران.": "اثْنَانِ. عَيْنَانِ تَنْظُرَانِ.",
    "ثلاثة. ثلاث فراشات تطير.": "ثَلَاثَةٌ. ثَلَاثُ فَرَاشَاتٍ تَطِيرُ.",
    "أربعة. أربع زهرات جميلة.": "أَرْبَعَةٌ. أَرْبَعُ زَهْرَاتٍ جَمِيلَةٍ.",
    "خمسة. خمس أصابع في يدي.": "خَمْسَةٌ. خَمْسُ أَصَابِعَ فِي يَدِي.",
    "نتعرف على الألوان": "نَتَعَرَّفُ عَلَى الأَلْوَانِ",
    "التفاحة حمراء.": "التُّفَّاحَةُ حَمْرَاءُ.",
    "الموزة صفراء.": "المَوْزَةُ صَفْرَاءُ.",
    "الورقة خضراء.": "الوَرَقَةُ خَضْرَاءُ.",
    "السماء زرقاء.": "السَّمَاءُ زَرْقَاءُ.",
    "أصوات الحيوانات": "أَصْوَاتُ الحَيَوَانَاتِ",
    "القطة تقول مياو.": "القِطَّةُ تَقُولُ: مِيَاو.",
    "الكلب يقول هاو هاو.": "الكَلْبُ يَقُولُ: هَاو هَاو.",
    "البقرة تقول موو.": "البَقَرَةُ تَقُولُ: مُوو.",
    "الأسد يزأر بصوت عالٍ.": "الأَسَدُ يَزْأَرُ بِصَوْتٍ عَالٍ.",
    "نتعلم الأشكال": "نَتَعَلَّمُ الأَشْكَالَ",
    "هذه دائرة. الكرة على شكل دائرة.": "هَذِهِ دَائِرَةٌ. الكُرَةُ عَلَى شَكْلِ دَائِرَةٍ.",
    "هذا مربع. النافذة على شكل مربع.": "هَذَا مُرَبَّعٌ. النَّافِذَةُ عَلَى شَكْلِ مُرَبَّعٍ.",
    "هذا مثلث. الخيمة على شكل مثلث.": "هَذَا مُثَلَّثٌ. الخَيْمَةُ عَلَى شَكْلِ مُثَلَّثٍ.",
    "نقول شكراً": "نَقُولُ شُكْرًا",
    "عندما يساعدني أحد، أقول له شكراً.": "عِنْدَمَا يُسَاعِدُنِي أَحَدٌ، أَقُولُ لَهُ: شُكْرًا.",
    "أشكر أمي على الطعام اللذيذ.": "أَشْكُرُ أُمِّي عَلَى الطَّعَامِ اللَّذِيذِ.",
    "الكلمة الطيبة تجعل الجميع سعداء.": "الكَلِمَةُ الطَّيِّبَةُ تَجْعَلُ الجَمِيعَ سُعَدَاءَ.",
    "من أين يأتي المطر؟": "مِنْ أَيْنَ يَأْتِي المَطَرُ؟",
    "الشمس تسخّن ماء البحر فيصعد بخاراً.": "الشَّمْسُ تُسَخِّنُ مَاءَ البَحْرِ فَيَصْعَدُ بُخَارًا.",
    "البخار يتجمع فيصنع سحابة.": "البُخَارُ يَتَجَمَّعُ فَيَصْنَعُ سَحَابَةً.",
    "عندما تثقل السحابة تنزل قطرات المطر.": "عِنْدَمَا تَثْقُلُ السَّحَابَةُ تَنْزِلُ قَطَرَاتُ المَطَرِ.",
}

for _l in FALLBACK_LESSONS:
    _l["title_ar_tts"] = TASHKEEL.get(_l["title_ar"], _l["title_ar"])
    for _s in _l["scenes"]:
        _s["ar_tts"] = TASHKEEL.get(_s["ar"], _s["ar"])
