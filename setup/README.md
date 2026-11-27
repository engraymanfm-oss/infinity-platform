# تفعيل المنصة — 4 خطوات

المستودع فيه كل شيء، وبقيت خطوات تحتاج صلاحية لا يملكها تطبيق Pickle على GitHub
(`pages` و`workflows` + إعدادات المستودع)، فتُنفَّذ من حسابك في دقائق.

## 1) تفعيل الموقع (GitHub Pages)

Settings → Pages → **Source: Deploy from a branch** → Branch: `main`، Folder: `/ (root)` → **Save**.

بعد دقيقة تقريبًا يعمل: https://engraymanfm-oss.github.io/infinity-platform/

## 2) سماح الكتابة لمشغّلات Actions

Settings → Actions → General → Workflow permissions → **Read and write permissions** → Save.
(بدونها لا يستطيع المشغّل رفع الأخبار المحدّثة ولا نشر الـAPK في Release.)

## 3) إضافة مشغّل تحديث الأخبار

انسخ محتوى `setup/workflows/update-news.yml` إلى ملف جديد اسمه `.github/workflows/update-news.yml`
(Add file → Create new file، واكتب المسار كاملًا في خانة الاسم)، ثم Commit.

## 4) إضافة مشغّل بناء الـAPK

نفس الطريقة مع `setup/workflows/build-apk.yml` → `.github/workflows/build-apk.yml`.

بعدها: Actions → Build Android APK → Run workflow. الملف يظهر في Release `v1.0` باسم `Infinity.apk`
وفي artifacts.

## ملاحظات

- ملفات هذا المجلد (`setup/`) نسخ للتسهيل فقط؛ GitHub لا يشغّل إلا ما هو داخل `.github/workflows/`.
- حتى تُضاف الخطوة 1 يبقى الموقع 404، وحتى تُضاف 3 و4 لا يوجد تحديث تلقائي ولا بناء على GitHub.
- الـAPK الحالي مبني ومرفق في Release `v1.0` يدويًا من بيئة البناء، ويعمل فور تفعيل الموقع.
