# LATCHI WATCHING — Windows website edition

نسخة Windows مستقلة بواجهة **WPF / .NET 8 / WebView2** وبنفس أسلوب مشغّل
LATCHI PLAY. تفتح مباشرة على ثماني بطاقات مصادر في وسط الشاشة، مع خلفية
كحلية/ذهبية. الصور التسع مولّدة فنيًا، ثم أُضيفت أسماء وشعارات صحيحة، وكل ملف
نهائي **1800×600، نسبة 3:1 فعلية**.

## قرار المنتج

اختار المالك صراحة **مواقع المصادر بأسلوب Play**. لذلك:
- بطاقة المصدر تفتح موقعه الحقيقي في نافذة WebView2 ملء الشاشة.
- الموقع نفسه يقدّم كتالوغه وحلقاته ومشغّله؛ لا نختلق كتالوغًا أو نتائج تشغيل.
- منع نوافذ جديدة و`window.open`، خروج واضح وEsc، إغلاق نظيف للنافذة.
- هذه النسخة **لا تنفّذ إضافات CloudStream `.cs3`، ولا تستعمل TMDB أو vidfast كبديل للمصادر**.
- ليست حزمة Qt السابقة ولا MSI Hello World ولا تطبيق Android.

## المصادر

`3isk`, `eseek`, `Krmzy`, `MyCimaProvider`, `Topcinema`, `TukTukcima`, `Tuniflix`, `Wecima`.
العناوين مأخوذة من ملفات موفّري المستودع العام `Abodabodd/re-3arabi`، ويمكن
تعديلها من الإعدادات إذا انتقل الموقع. وجود العنوان في المصدر لا يضمن استمرار
الموقع أو توفر جميع مقاطعه من كل شبكة.

## الخصوصية والتوافق

ملف مستقل: `%LOCALAPPDATA%\LATCHI\WatchingWindows`. لا يقرأ بيانات Play أو
Electron القديم ولا ينقلها. لا يتضمن مفتاح TMDB أو بيانات مستودع Play الخاصة.
مواقع الأطراف الثالثة وWebView2 لها سياساتها واتصالاتها الخاصة؛ التطبيق نفسه
لا يضيف تحليلات أو تتبعًا. شاهد فقط ما تملك حق الوصول إليه.

Windows 10/11 x64 مع Microsoft Edge WebView2 Evergreen. .NET مضمّن في الحزمة.
المثبّت غير موقّع؛ لا تعطّل حماية Windows. [دليل التثبيت](docs/INSTALL-AR.md).

## البناء والتحقق

```sh
dotnet build -c Release
dotnet test tests/LatchiWatching.Tests -c Release
dotnet publish src/LatchiWatching.App -c Release -r win-x64 --self-contained true -o publish
```

Workflow: `.github/workflows/watching-play-windows.yml`. النشر مشروط باختبارات
الوحدات، عرض البطاقات فعليًا على Windows، فيديو VP8 محلي مولّد قانونيًا
(فك/تصيير/إيقاف/بحث)، منع المنبثقات، وتشغيل النسخة المحمولة والمثبتة ثم إلغاء
التثبيت مع إبقاء ملفات المستخدم. النتائج الفعلية في `WINDOWS-VERIFICATION.json`.
اختبار فيديو محلي لا يثبت تشغيل جميع المواقع أو جهاز صوت/GPU حقيقي.

## المصدر والاعتماد

هذا فرع جديد مستقل، لا ينقل تاريخ المستودع الخاص أو مفتاحه. التصميم ومنطق
حظر المنبثقات ونافذة الشاشة الكاملة مقتبسة من LATCHI PLAY desktop v1.1.0
(مرجع `57a5b54fdaff734ab374776c54623dfbadfeed0a`) المملوك لـLATCHI.
المصدر المقابل منشور مع كل إصدار. حقوق الشعارات لأصحاب المصادر؛ سجل أصلها
في `design/logo-provenance.json`. الخلفيات الأصلية المولدة في `design/art/`،
وإعادة تركيب البطاقات عبر `tools/compose-source-cards.py` مع Pillow وDejaVu Sans.
راجع `LICENSE` و`THIRD-PARTY-NOTICES.md`.
