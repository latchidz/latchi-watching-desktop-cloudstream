# تثبيت LATCHI WATCHING Windows

- Windows 10/11 x64، مع **Microsoft Edge WebView2 Evergreen Runtime**.
- حزمة .NET مضمنة، لا تحتاج تثبيت SDK أو Java أو Qt.
- هذا الإصدار يعمل بمواقع المصادر كما اخترت، وليس بإضافات `.cs3`.

## التحميل
اختر `LATCHI-WATCHING-1.0.0-Windows-x64-Setup.exe` للتثبيت لحسابك، أو فك ZIP
كاملًا ثم شغّل `LATCHI-WATCHING.exe`. لا تشغّل EXE من داخل الأرشيف.

المثبّت غير موقّع رقميًا. قارن بصمته مع `SHA256SUMS.txt` قبل تثبيته ولا تعطّل
مضاد الفيروسات أو حماية Windows:

```powershell
Get-FileHash .\LATCHI-WATCHING-1.0.0-Windows-x64-Setup.exe -Algorithm SHA256
```

إذا ظهرت رسالة WebView2 مفقود، حمّله من صفحة Microsoft الرسمية:
https://developer.microsoft.com/microsoft-edge/webview2/#download-section

## الاستخدام
تظهر ثماني بطاقات مباشرة. اختر مصدرًا لفتحه في شاشة كاملة مع مشغّله الأصلي.
زر «خروج» أو Esc يرجع للبطاقات. الإعلانات المنبثقة والنوافذ الجديدة ممنوعة،
لكن ذلك لا يعني إزالة كل إعلان داخل صفحات المواقع.

إذا تغيّر نطاق الموقع، اضغط ⚙ وعدّل عنوان HTTPS للمصدر. توقف الموقع، تحدياته،
أو منع الشبكة ليست نتائج نجاح؛ لا ندّعي اختبار تشغيل كل مقاطع المصادر الثمانية.

البيانات في `%LOCALAPPDATA%\LATCHI\WatchingWindows`، منفصلة عن Play وElectron.
إلغاء التثبيت لا يمس هذا الملف. أسماء الاختصارات والمجلدات مستقلة: LATCHI WATCHING Windows.
