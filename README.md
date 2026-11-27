# Infinity ∞ — THE ENGINEER

منصة الأخبار والمقارنات، منشورة كصفحة ويب حية تُحدَّث تلقائيًا.

- **الموقع:** https://engraymanfm-oss.github.io/infinity-platform/
- **الكود:** https://github.com/engraymanfm-oss/infinity-platform

## كيف تعمل

| الجزء | الوصف |
| --- | --- |
| `index.html` | المنصة كاملة في ملف واحد: الأخبار، المقارنات، الأقسام، وكل الميزات كما هي. |
| `scripts/update_news.py` | يجلب خلاصات RSS من الخادم (بلا وسطاء CORS) ويكتب `CURATED` و`SNAPSHOT` ووقت التحديث `CURATED_AT` داخل `index.html`. |
| `.github/workflows/update-news.yml` | يشغّل السكربت كل 4 ساعات وعند الطلب، ثم يرفع التغيير ويعيد بناء الصفحة. |
| `android/` | تطبيق أندرويد خفيف (WebView) باسم Infinity يفتح الموقع الحي. |
| `.github/workflows/build-apk.yml` | يبني الـAPK وينشره في Release باسم `v1.0` (ملف `Infinity.apk`). |

## الأوامر

```bash
# تحديث الأخبار يدويًا من جهازك
python3 scripts/update_news.py

# تشغيل مشغّل التحديث على GitHub
gh workflow run update-news.yml --repo engraymanfm-oss/infinity-platform

# بناء الـAPK
gh workflow run build-apk.yml --repo engraymanfm-oss/infinity-platform
```

## قواعد ثابتة

- لا يُحذف أو يُعاد ترتيب أي قسم قائم، بما فيه تصنيف +18.
- الأقسام المحرّرة يدويًا (`barca`، `selfdev`) لا يلمسها المشغّل.
- المشغّل يحدّث فقط المفاتيح التي لها خلاصة في `FEEDS` وموجودة أصلًا في الصفحة.
