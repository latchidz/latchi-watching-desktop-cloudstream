namespace LatchiWatching.App;

/// <summary>
/// حواجز الحماية المشتركة بين كل نوافذ WebView2 — هدف واحد:
/// لا تُفتح أي صفحة منبثقة (popup) إطلاقاً، مهما ضغط المستخدم.
///
/// الطبقات (تعمل معاً في كل إطار):
///   1) C#‎  : CoreWebView2.NewWindowRequested → Handled = true
///            (يمنع كل نافذة متصفح جديدة: target=_blank، window.open، popunder)
///   2) JS  : استبدال window.open بدالة لا تُعيد شيئاً — قبل تشغيل أي كود صفحة
///   3) C#‎  : تعطيل حوارات alert/confirm/prompt الافتراضية (Settings)
///
/// وفي نافذة المشغّل فقط (PlayerGuardScript):
///   4) زر «خروج» يُحقن داخل الصفحة نفسها — يظهر فوق محتوى المشغل دائماً
///      (بلا مشكلة airspace: هو جزء من الصفحة، لا عنصر WPF فوق HwndHost)
///   5) Esc: يخرج من ملء شاشة الصفحة أولاً إن كانت مفعّلة، ثم يغلق النافذة —
///      يعمل حتى والتركيز داخل مشغل الويب
/// </summary>
internal static class WebGuards
{
    /// <summary>لنافذة الواجهة الرئيسية — منع المنبثقات فقط (بلا زر خروج).</summary>
    public const string PopupBlockScript = """
        (function () {
          if (window.__LATCHI_GUARD__) { return; }
          window.__LATCHI_GUARD__ = true;
          try { window.open = function () { return null; }; } catch (e) {}
        })();
        """;

    /// <summary>
    /// لنافذة المشغّل — منع المنبثقات في كل الإطارات + زر خروج داخل الصفحة العليا + Esc ذكي.
    /// الزر يُبنى عبر CSSOM (style properties) لا innerHTML — لا يعترضه CSP مهما كان صارماً.
    /// </summary>
    public const string PlayerGuardScript = """
        (function () {
          if (window.__LATCHI_GUARD__) { return; }
          window.__LATCHI_GUARD__ = true;

          // ─── 1) لا نوافذ منبثقة إطلاقاً (في كل إطار) ───
          try { window.open = function () { return null; }; } catch (e) {}

          var isTop = false;
          try { isTop = (window.top === window); } catch (e) { isTop = true; }
          if (!isTop) {
            document.addEventListener("keydown", function (ev) {
              if (ev.key === "Escape") {
                try { window.chrome.webview.postMessage("latchi-player-exit"); } catch (e) {}
              }
            }, true);
            return;
          }

          // ─── 2) زر الخروج — داخل الصفحة نفسها، فوق كل شيء دائماً ───
          try {
            var btn = document.createElement("div");
            btn.id = "__latchi_exit__";
            var s = btn.style;
            s.position = "fixed"; s.top = "16px"; s.left = "16px";
            s.zIndex = "2147483647";
            s.padding = "10px 20px"; s.borderRadius = "12px";
            s.background = "rgba(26,31,46,0.85)"; s.color = "#FFFFFF";
            s.font = "600 14px system-ui, -apple-system, 'Segoe UI', sans-serif";
            s.border = "1px solid rgba(255,255,255,0.5)";
            s.boxShadow = "0 4px 18px rgba(0,0,0,0.5)";
            s.cursor = "pointer"; s.direction = "rtl";
            s.userSelect = "none"; s.MozUserSelect = "none"; s.msUserSelect = "none";
            s.webkitUserSelect = "none";
            s.webkitTouchCallout = "none";
            btn.appendChild(document.createTextNode("✕  خروج"));
            btn.title = "خروج من المشغّل (Esc)";
            btn.addEventListener("click", function (ev) {
              ev.stopPropagation();
              ev.preventDefault();
              try { window.chrome.webview.postMessage("latchi-player-exit"); } catch (err) {}
            });

            var add = function () {
              try {
                if (!document.getElementById("__latchi_exit__")) document.body.appendChild(btn);
              } catch (e) {}
            };
            if (document.body) { add(); }
            else { document.addEventListener("DOMContentLoaded", add); }

            // إعادة الإلحاق إن أزالتها الصفحة (فحص كل ثانيتين، 30 محاولة)
            var tries = 0;
            var keep = setInterval(function () {
              if (document.getElementById("__latchi_exit__") || ++tries > 30) {
                clearInterval(keep); return;
              }
              add();
            }, 2000);
          } catch (e) {}

          // ─── 3) Esc: خروج من ملء شاشة الصفحة أولاً، ثم إغلاق المشغّل ───
          try {
            document.addEventListener("keydown", function (ev) {
              if (ev.key !== "Escape") { return; }
              if (document.fullscreenElement) {
                try { document.exitFullscreen(); } catch (e) {}
                return;
              }
              try { window.chrome.webview.postMessage("latchi-player-exit"); } catch (err) {}
            }, true);
          } catch (e) {}
        })();
        """;
}
