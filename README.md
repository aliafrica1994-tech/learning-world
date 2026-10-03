# عالم التعلم — قناة يوتيوب تعمل وحدها 🎓

كل يوم: فيديو **Short** تعليمي. كل جمعة: فيديو **طويل** (4 دروس). عربي فصيح + إنجليزي، لأعمار 5–8.
كل شيء مجاني: GitHub Actions + Gemini + edge-tts + ffmpeg.

## الإعداد (يمكن من الهاتف، مرة واحدة)

### 1) مستودع GitHub
1. github.com ← New repository ← اسمه `learning-world` (اجعله **Public** ليكون وقت التشغيل مجانياً بلا حد).
2. ارفع كل الملفات إلى المستودع كما هي، مع الحفاظ على مسار `.github/workflows/daily.yml`.

### 2) مفتاح Gemini (للدروس)
1. aistudio.google.com/apikey ← Create API key.
2. احفظه لاحقاً باسم `GEMINI_API_KEY`.
(بدونه يعمل النظام بدروس احتياطية قليلة، وتتكرر.)

### 3) صلاحية الرفع إلى يوتيوب
1. console.cloud.google.com ← مشروع جديد ← فعّل **YouTube Data API v3**.
2. APIs & Services ← OAuth consent screen: نوع External، أضف بريدك في Test users، واضغط **Publish app** (حتى لا ينتهي الرمز بعد 7 أيام).
3. Credentials ← Create credentials ← OAuth client ID ← نوع **Web application**، وأضف في Authorized redirect URIs:
   `https://developers.google.com/oauthplayground`
4. انسخ `Client ID` و`Client secret`.
5. افتح developers.google.com/oauthplayground ← الترس ⚙️ ← فعّل **Use your own OAuth credentials** وألصق القيمتين.
6. في الخطوة 1 اكتب النطاق: `https://www.googleapis.com/auth/youtube.upload` ← Authorize APIs ← سجّل الدخول بحساب قناتك.
7. في الخطوة 2 اضغط **Exchange authorization code for tokens** وانسخ `Refresh token`.

### 4) الأسرار في GitHub
المستودع ← Settings ← Secrets and variables ← Actions ← New repository secret:
`GEMINI_API_KEY` · `YT_CLIENT_ID` · `YT_CLIENT_SECRET` · `YT_REFRESH_TOKEN`

### 5) التجربة
Actions ← «عالم التعلم - نشر تلقائي» ← Run workflow ← `dry_run = 1`.
بعد دقائق تجد الفيديو في Artifacts للمعاينة. إذا أعجبك شغّله بـ `dry_run = 0` ليُرفع فعلاً.
بعدها يعمل وحده يومياً.

## مهم أن تعرفه
- **التدقيق:** مشاريع Google الجديدة تُرفع فيديوهاتها **خاصة (Private)** حتى تطلب تدقيقاً من يوتيوب (نموذج Audit في وثائق API). حتى ذلك الحين ادخل YouTube Studio وانشر الفيديوهات بضغطة، أو تقدّم بالطلب.
- **التصنيف:** كل فيديو يُرفع كـ«مخصص للأطفال»، ومعلَّم أن الصوت والصور بالذكاء الاصطناعي.
- **الجودة:** راجع أول فيديوهات بنفسك. يوتيوب قد يرفض الربح للمحتوى المكرر الآلي، لذلك زوّد التنويع بتغيير `CATEGORIES` في `main.py`.
- **التوقف:** GitHub يوقف الجدولة بعد 60 يوماً دون نشاط في المستودع؛ السجل اليومي يُحدَّث تلقائياً فيبقى نشطاً، وتحقق من تبويب Actions من حين لآخر.
- **حد Gemini المجاني:** إن تغيّر اسم النموذج، عدّل المتغير `GEMINI_MODEL` (Settings ← Variables).
- **الصور:** تأتي من Pollinations المجاني؛ إن تعذّر، يرسم النظام بطاقة بإيموجي كبير بدلاً منها.
- **الأصوات:** `ar-SA-ZariyahNeural` للعربية و`en-US-AnaNeural` للإنجليزية، وتُغيَّر عبر `AR_VOICE` و`EN_VOICE`.
