# تفعيل المنصة — 3 خطوات

المستودع فيه كل شيء، وبقيت خطوتان تحتاجان صلاحية لا يملكها تطبيق Pickle على GitHub
(`pages` و`workflows`)، فتُنفَّذان من حسابك في ثوانٍ.

## 1) تفعيل الموقع (GitHub Pages)

Settings → Pages → **Source: Deploy from a branch** → Branch: `main`، Folder: `/ (root)` → **Save**.

بعد دقيقة تقريبًا يعمل: https://engraymanfm-oss.github.io/infinity-platform/

## 2) إضافة مشغّل تحديث الأخبار

انسخ محتوى `setup/workflows/update-news.yml` إلى ملف جديد اسمه `.github/workflows/update-news.yml`
(Add file → Create new file، واكتب المسار كاملًا في خانة الاسم)، ثم Commit.

## 3) إضافة مشغّل بناء الـAPK

نفس الطريقة مع `setup/workflows/build-apk.yml` → `.github/workflows/build-apk.yml`.

بعدها: Actions → Build Android APK → Run workflow. الملف يظهر في Release `v1.0` باسم `Infinity.apk`
وفي artifacts.

## ملاحظات

- ملفات هذا المجلد (`setup/`) نسخ للتسهيل فقط؛ GitHub لا يشغّل إلا ما هو داخل `.github/workflows/`.
- حتى تُضاف الخطوتان، الموقع يبقى 404، والتحديث التلقائي وبناء الـAPK على GitHub لا يعملان.
- الـAPK الحالي مبني ومرفق في Release `v1.0` يدويًا من بيئة البناء.
