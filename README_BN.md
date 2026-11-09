# VIQ v2 — Android অ্যাপ ও সার্ভার সোর্স

**v1 থেকে আপডেট করতে আগে `UPGRADE_V2_BN.md` পড়ুন।** নতুন dark-navy/lime অ্যাপ ডিজাইন, task search/save, notifications, support conversation, pending-request cancellation, session controls এবং wallet reconciliation যুক্ত হয়েছে।

এই প্যাকেজে কাজ করা ব্যাকএন্ড, মোবাইল-উপযোগী ওয়েব ইন্টারফেস, PostgreSQL ডেটা মডেল, Android WebView অ্যাপের সোর্স এবং APK তৈরির GitHub workflow আছে। এটি শুধু স্ক্রিনের নমুনা নয়: লগইন, কাজ জমা, রিভিউ, ব্যালেন্স, রেফার কমিশন এবং অনুরোধের বাস্তব ডেটা সংরক্ষণের কোড আছে। তবে এটি স্বাধীন অডিট করা আর্থিক ব্যবস্থা নয়। কোনো প্রকৃত পেমেন্ট সেবা এতে আগে থেকে সংযুক্ত নেই।

**এখনো তৈরি APK দেওয়া হয়নি। নিচের ধাপে আপনার লাইভ URL দিয়ে APK তৈরি করতে হবে।** Android কোড এই পরিবেশে compile/install পরীক্ষা করা হয়নি। সার্ভার, PostgreSQL, Android ফোন এবং দুই নেটওয়ার্কে কলের বাস্তব পরীক্ষা শেষ করার পর প্রকাশ করুন।

## ১. প্যাকেজে কী আছে

| ফাইল / ফোল্ডার | কাজ |
|---|---|
| `app.py` | API, লগইন, অনুমতি, ওয়ালেট, কাজ, কলের সিগন্যালিং |
| `models.py` | ডেটাবেস টেবিল ও হিসাবের সীমা |
| `manage.py` | প্রথমবার ডেটাবেস ও অ্যাডমিন তৈরি; পাসওয়ার্ড রিসেট |
| `templates/index.html` | অ্যাপের মূল পেজ |
| `static/app.js` | ১৮ পেজ, ফর্ম, অ্যাডমিন UI, রেকর্ডিং ও WebRTC |
| `static/style.css` | মোবাইল ও ডেস্কটপ ডিজাইন |
| `requirements.txt` | Python প্যাকেজ |
| `render.yaml` | Render সেটআপ |
| `android/` | Android Studio / Gradle প্রজেক্ট |
| `.github/workflows/android.yml` | GitHub দিয়ে APK তৈরি |
| `.github/workflows/tests.yml` | PostgreSQL-সহ ব্যাকএন্ড পরীক্ষা |
| `tests/test_viq.py` | কার্যকারিতা ও অনুমতির পরীক্ষা |
| `.env.example` | প্রয়োজনীয় সেটিংসের নাম; এটি আসল গোপন তথ্য নয় |
| `FEATURES_BN.md` | প্রতিটি ফিচারের কাজ ও সীমা |
| `VERIFICATION.md` | কী পরীক্ষা করা হয়েছে এবং কী বাকি |

## ২. অ্যাপটি কীভাবে চলবে

Android অ্যাপ → আপনার HTTPS Render সার্ভার → আপনার PostgreSQL ডেটাবেস।

অ্যাপটি ইন্টারনেট ছাড়া লেনদেন বা কাজ জমা করবে না। Android-এর মধ্যে VIQ-এর নিজস্ব ওয়েব UI খুলবে; পেমেন্টের সিদ্ধান্ত সার্ভারে হবে। JavaScript-এ ব্যালেন্স বদলে আসল টাকা যোগ করা যাবে না।

GitHub কোড রাখে, Render সার্ভার চালায়। ব্যবহারকারীর তথ্য GitHub-এ রাখা হবে না। SQLite কেবল কম্পিউটারে পরীক্ষা করার জন্য; production মোডে PostgreSQL বাধ্যতামূলক।

## ৩. PostgreSQL ডেটাবেস তৈরি

১. https://neon.com এ নিজের অ্যাকাউন্ট খুলুন।
২. একটি Project তৈরি করুন, নাম রাখতে পারেন `viq`।
৩. Dashboard-এর **Connect** থেকে connection string কপি করুন।
৪. URL দেখতে মোটামুটি এমন হবে:

```text
postgresql://USER:PASSWORD@HOST/DB?sslmode=require
```

Neon যে সম্পূর্ণ URL দেবে সেটিই ব্যবহার করুন; password, host, SSL parameters নিজে আন্দাজ করে বদলাবেন না। URL গোপন রাখুন। GitHub-এর ফাইলে বা পাবলিক পোস্টে দেবেন না। Render-এর `DATABASE_URL`-এ বসাতে হবে।

Neon-এর নিজের ব্যবহারসীমা ও বর্তমান প্ল্যান পরীক্ষা করুন। PostgreSQL-এর অন্য provider-ও চলবে। Render-এর ৩০ দিনের ফ্রি Postgres-কে স্থায়ী ডেটাবেস ধরে শুরু করবেন না।

## ৪. GitHub-এ কোড আপলোড

কম্পিউটার থেকে করলে সহজ হবে; ফোনে Chrome-এর Desktop site ব্যবহার করা যায়।

১. ডাউনলোড করা ZIP **Extract** করুন।
২. GitHub → **New repository**। নাম দিন `viq-app`। Public বা Private আপনার পছন্দ; Actions-এর ব্যবহারসীমা আলাদা হতে পারে।
৩. **Add file → Upload files** দিয়ে `VIQ` ফোল্ডারের **ভেতরের ফাইল ও ফোল্ডার** আপলোড করুন। ZIP ফাইলটি শুধু আপলোড করলে Render চালাতে পারবে না।
৪. রিপোজিটরির প্রথম স্তরেই `app.py`, `requirements.txt`, `render.yaml`, `android`, `.github` থাকতে হবে।
৫. লুকানো ফাইল দেখা না গেলে আপনার file manager-এ “Show hidden files” চালু করুন। `.github/workflows/android.yml` এবং `.github/workflows/tests.yml` অবশ্যই রাখুন।
৬. Commit করুন। GitHub-এর Actions tab-এ backend checks শুরু হবে।

ফোল্ডার ভুলভাবে `VIQ/VIQ/` হয়ে গেলে ফাইল ঠিক জায়গায় তুলুন। বিকল্পভাবে Render-এর Root Directory-তে সেই ফোল্ডারের পথ দিতে হবে, কিন্তু Android workflow-এর পথও বদলাতে হবে। শুরুতে root-এ দেওয়া সহজ।

## ৫. Render-এ সার্ভার চালু

১. https://render.com এ GitHub দিয়ে লগইন।
২. **New → Web Service → Git Provider**।
৩. `viq-app` রিপোজিটরি নির্বাচন।
৪. সেটিংস:

| ঘর | মান |
|---|---|
| Name | `viq-app` বা খালি থাকা অন্য নাম |
| Language / Runtime | Python |
| Branch | main |
| Root Directory | খালি, যদি app.py root-এ থাকে |
| Build Command | `pip install -r requirements.txt` |
| Start Command | নিচের সম্পূর্ণ কমান্ড |
| Instance Type | Free |
| Health Check Path | `/ready` |

```bash
python manage.py init && gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 120
```

৫. **Environment**-এ যোগ করুন:

| Key | কী বসাবেন |
|---|---|
| `APP_ENV` | `production` |
| `DATABASE_URL` | PostgreSQL-এর সম্পূর্ণ connection string |
| `SECRET_KEY` | অন্তত ৩২ অক্ষরের random secret; ৬৪ অক্ষর ভালো |
| `PUBLIC_URL` | Render-এর প্রকৃত URL, যেমন `https://viq-name.onrender.com` |
| `ADMIN_EMAIL` | আপনার অ্যাডমিন লগইনের ইমেইল |
| `ADMIN_PASSWORD` | অন্তত ১৬ অক্ষরের অনন্য শক্তিশালী পাসওয়ার্ড |

প্রকৃত URL Render যে hostname দেয় সেটি দেখে নিন। অনুমান করা নাম ব্যবহার করবেন না। প্রথমবার URL না জানা থাকলে Web Service তৈরি করে Render-এর URL কপি করুন, Environment ঠিক করে redeploy করুন। `PUBLIC_URL`-এ শেষে `/admin` বা অন্য path দেবেন না।

কম্পিউটারে secret তৈরি করতে:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

৬. **Create Web Service / Deploy** চাপুন।
৭. Logs-এ `VIQ schema and administrator ready` এবং Gunicorn start দেখলে URL খুলুন।
৮. প্রথমবার পেজ খুলতে সময় লাগতে পারে। Free service idle হলে ঘুমিয়ে যায়।

বিকল্প: Render **Blueprint** থেকে `render.yaml` ব্যবহার করুন। তবুও sync:false দেওয়া environment values নিজে পূরণ করতে হবে।

## ৬. প্রথম অ্যাডমিন সেটআপ

১. আপনার URL-এর শেষে `/admin` যোগ করুন। উদাহরণ: `https://YOUR-HOST/admin`।
২. `ADMIN_EMAIL` এবং `ADMIN_PASSWORD` দিয়ে লগইন।
৩. **সেটিংস** থেকে:
   - হোম নোটিশ লিখুন।
   - নিজের প্রকৃত বিকাশ/নগদ পেমেন্ট নির্দেশনা লিখুন।
   - সেটআপ শেষ হলে ডিপোজিট চালু করুন।
   - সর্বনিম্ন উত্তোলন নির্ধারণ করুন।
   - Cobra-র আসল HTTPS URL বসান।
   - সাপোর্ট যোগাযোগ, শর্ত ও গোপনীয়তা নীতি নিজের ব্যবসার জন্য সম্পাদনা করুন।
৪. **কাজ** থেকে বিভাগ, শিরোনাম, বিস্তারিত, reward, referral commission, slots ও সময়সীমা দিন।
৫. ১৮+ বিভাগ এই সংস্করণে চালু করা যায় না; কাজের উদ্দেশ্য ও নিয়ম নির্ধারণের পরে কোড পরিবর্তন করতে হবে।

প্রথম অ্যাডমিন তৈরি হয়ে গেলে Render-এর `ADMIN_PASSWORD` বদলালে আগের অ্যাডমিনের পাসওয়ার্ড বদলাবে না। অ্যাপের Profile থেকে বদলান। প্রাথমিক সেটআপের পরে Render থেকে `ADMIN_PASSWORD` মুছে দিতে পারেন; বিদ্যমান অ্যাডমিন থাকলে init সেটি চাইবে না।

## ৭. কাজ ও পারিশ্রমিকের নিয়ম

১. শুধুমাত্র অ্যাডমিন কাজ প্রকাশ করে।
২. ইউজার বিভাগ থেকে কাজ শুরু করে।
৩. নির্দেশনা পড়ে উত্তর, HTTPS লিংক, ছবি, ছোট ভিডিও বা ভয়েস জমা দেয়।
৪. অ্যাডমিন **কাজ রিভিউ** থেকে পুরোনো জমা আগে দেখতে পাবে।
৫. অনুমোদন হলে reward যোগ হয়; referrer থাকলে কাজের নির্ধারিত commission যোগ হয়।
৬. বাতিল হলে মন্তব্য দেখা যায়; এই সংস্করণে একই কাজ আবার জমা দেওয়া যায় না। প্রয়োজন হলে অ্যাডমিন নতুন সংশোধিত কাজ প্রকাশ করবেন।

প্রতি অ্যাকাউন্ট প্রতি কাজ একবার। কাজের slots পূর্ণ হলে জমা বন্ধ। কেবল “শুরু” করা slots ধরে রাখে না; চূড়ান্ত জমা দিলে slot ব্যবহৃত হয়।

পারিশ্রমিক server-side কাজ থেকে নেওয়া হয়। ইউজারের পাঠানো reward বিশ্বাস করা হয় না। প্রকাশিত কাজের reward পরিবর্তনের বদলে পুরোনো কাজ বন্ধ করে নতুন কাজ প্রকাশ করুন, যাতে আগে গ্রহণ করা শর্ত বদলে না যায়।

ভিডিও দেখার সময় গণনা শুধু জমা দেওয়ার আগে সময় পেরিয়েছে কি না যাচাই করে। এটি মানুষের সত্যিকারের মনোযোগ বা বাইরের ভিডিও সম্পূর্ণ দেখা প্রমাণ করে না। প্রশ্ন/ফিডব্যাক ও অ্যাডমিন যাচাই ব্যবহার করুন।

## ৮. পেমেন্ট, উইথড্র ও সেন্ড ব্যালেন্স

**ডিপোজিট:** ইউজার বাইরে পেমেন্ট করে Transaction ID দেয়। অ্যাডমিন নিজের provider account-এ টাকা আসা যাচাই করে approve করেন। শুধু screenshot বিশ্বাস করবেন না। একই transaction reference দ্বিতীয়বার জমা হতে বাধা আছে।

**উইথড্র:** আবেদন করলে ব্যবহারযোগ্য ব্যালেন্স থেকে অর্থ hold-এ যায়। অ্যাডমিন প্রথমে Processing করবেন, তারপর বাইরে প্রকৃত পেমেন্ট করবেন, reference লিখে Approve করবেন। Reject করলে একই অর্থ ফেরত আসে। একই অনুরোধ আবার approve বা reject করা যায় না।

**সেন্ড ব্যালেন্স:** প্রাপকের VIQ আইডি ও নিজের পাসওয়ার্ড দিয়ে পাঠানো যায়। দুই পক্ষের ledger একই database transaction-এ লেখা হয়। এটি VIQ-এর ভেতরের হিসাব স্থানান্তর; বিকাশ বা নগদে টাকা পাঠানো নয়।

সিস্টেম বাস্তব ব্যাংক/MFS reserve যাচাই করে না। কাজের reward ও referral commission দেওয়ার জন্য ব্যবসার বাস্তব অর্থ প্রয়োজন। মোট wallet liability-এর জন্য পর্যাপ্ত অর্থ নিজের হিসাবে রাখুন।

## ৯. মোবাইল রিচার্জ

প্রথম সংস্করণে বাংলাদেশি নম্বর: GP, Robi, Airtel, Banglalink, Teletalk।

ইউজার নম্বর, operator, টাকা ও prepaid/postpaid নির্দেশনা দেবে। টাকা hold হবে। অ্যাডমিন নিজের অনুমোদিত recharge channel দিয়ে recharge করে reference লিখে সম্পন্ন করবেন। ব্যর্থ হলে Reject করলে hold ফেরত যাবে।

**স্বয়ংক্রিয় recharge API যুক্ত নয়।** Provider-এর merchant/API account, credentials, callback verification ও idempotent fulfilment আলাদাভাবে যুক্ত করতে হবে।

## ১০. মানি এক্সচেঞ্জ

উৎস VIQ-এর BDT ওয়ালেট। অ্যাডমিন destination route, rate, fixed fee ও destination unit প্রকাশ করবেন। যেমন `VIQ → নগদ`, rate `1`, fee `5`, unit `BDT`।

ইউজার ১০০ টাকা দিলে quote হবে `(100 − 5) × 1 = 95 BDT`। ১০০ টাকা hold হবে, অ্যাডমিন বাইরে ৯৫ টাকা পাঠিয়ে সম্পন্ন করবেন। Reject করলে সম্পূর্ণ ১০০ টাকা ফেরত।

প্রাপকের তথ্য ও quote আবেদনেই স্থির হয়। পরে রুট বদলালে পুরোনো আবেদন বদলায় না। Rate পরিবর্তন করতে পুরোনো route বন্ধ করে নতুন route যোগ করুন।

এটি স্বয়ংক্রিয় বৈদেশিক মুদ্রা বা crypto exchange নয়, বাজার থেকে live rate নেয় না। MFS-to-MFS সরাসরি debit অথবা বাইরের wallet-এর টাকা টেনে আনার কোড নেই। কোন exchange service চালাবেন তা নির্ধারণের পরে সংশ্লিষ্ট provider ও প্রযোজ্য নিয়ম যাচাই করুন।

## ১১. কল, লাইভ ও ভয়েস

**ভয়েস কাজ:** Voice বিভাগে অ্যাডমিন script দেবেন। ইউজার “কাজ শুরু” → “প্রমাণ / উত্তর” → “ভয়েস রেকর্ড শুরু” চাপবে। সর্বোচ্চ ৩ মিনিট রেকর্ড। মাইক্রোফোন অনুমতি প্রয়োজন। বিকল্পভাবে ফোনে রেকর্ড করে ফাইল upload করা যায়।

**ফাইল:** সর্বোচ্চ ৮ MB, প্রতি submission-এ একটি ফাইল; প্রতি ইউজার মোট ৬৪ MB পর্যন্ত। PNG/JPG, WebM, MP4, OGG, WAV। ফাইল database-এ private রাখা হয়; submitter ও admin দেখতে পারে। Admin শুনতে/দেখতে এবং download করতে পারেন। বড় ভিডিওর জন্য HTTPS share link ব্যবহার করুন। অনেক মিডিয়া হলে PostgreSQL-এর free storage দ্রুত পূর্ণ হবে; production media storage migration প্রয়োজন।

**ব্যক্তিগত কল:** অ্যাডমিন “কল / লাইভ” থেকে দুইজন user ID দিয়ে room তৈরি করবেন। শুধু ওই দুইজন দেখতে ও যোগ দিতে পারবেন। সাধারণ user-ও host হতে পারবেন, যদি admin তাঁর ID দেন।

**লাইভ:** অ্যাডমিন host ID দিয়ে live room তৈরি করবেন। লগইন করা অন্য সদস্যরা viewer হিসেবে যোগ দেবেন। মোট সর্বোচ্চ ৫ জন; এটি ছোট WebRTC live room, বড় livestreaming service নয়। দর্শকের camera/mic চাওয়া হয় না।

Camera/microphone permission ছাড়া call host করা যায় না। WebRTC মিডিয়া browser-to-browser যায়; server শুধু signalling করে। Server কোনো recording করে না। ভিন্ন নেটওয়ার্কে নির্ভরযোগ্য সংযোগের জন্য TURN লাগতে পারে।

Render Environment-এ প্রয়োজনে:

```text
STUN_URL=stun:stun.l.google.com:19302
TURN_URL=turns:YOUR-TURN-HOST:5349
TURN_USERNAME=YOUR_USER
TURN_PASSWORD=YOUR_PASSWORD
```

এই static TURN credential রুমে যোগ দেওয়া client পাবে, তাই সীমিত account/quota ব্যবহার করুন; production-এ short-lived TURN credentials যোগ করুন। TURN bandwidth সাধারণত বিনামূল্যে সীমাহীন নয়।

কল থেকে অর্থ automatic প্রতি মিনিটে credit হয় না। অ্যাডমিন call/live বিভাগের paid task তৈরি করবেন, session শেষে কাজের প্রমাণ যাচাই করে credit করবেন। Background-এ app নিলে privacy-র জন্য media বন্ধ হয়; সামনে এসে room ছেড়ে আবার যোগ দিন।

## ১২. GitHub থেকে APK বানানো — ফোন দিয়েও সম্ভব

আগে Render URL browser-এ খুলে login ও কাজ পরীক্ষা করুন। তারপর:

১. GitHub repository → **Actions**।
২. **Build VIQ Android APK** workflow খুলুন।
৩. **Run workflow** চাপুন।
৪. `app_url` ঘরে Render-এর সম্পূর্ণ HTTPS origin দিন: `https://YOUR-HOST.onrender.com`। `/admin` বা `/#home` নয়।
৫. Run workflow → build সবুজ হওয়া পর্যন্ত অপেক্ষা।
৬. সেই run খুলে নিচের **Artifacts → VIQ-Android-Debug-APK** download করুন। GitHub-এ লগইন থাকতে হবে।
৭. Download করা ZIP extract করুন। ভেতরের `app-debug.apk` ফোনে খুলুন।
৮. Android চাইলে যে browser/file manager থেকে install করছেন, শুধু সেটির জন্য “Install unknown apps” অনুমতি দিন।
৯. VIQ খুলে নতুন user তৈরি করুন। Admin দরকার হলে profile থেকে admin panel-এ যান, বা server URL-এর `/admin` browser-এ ব্যবহার করুন।

এটি পরীক্ষার debug APK। Play Store release নয়। আলাদা build-এ debug signing key বদলালে update install নাও হতে পারে; সে ক্ষেত্রে debug app uninstall করে install করতে হবে। সার্ভারের অ্যাকাউন্টের তথ্য থাকবে, কিন্তু ফোনের login মুছে যাবে। নিয়মিত ব্যবহার ও বিতরণের জন্য স্থায়ী release signing key ব্যবহার করুন।

## ১৩. Android Studio দিয়ে APK / release

১. কম্পিউটারে Android Studio ও JDK 17 install করুন।
২. এই প্যাকেজের `android` ফোল্ডার open করুন। Android SDK Platform 35 install করুন।
৩. Gradle 8.9 ব্যবহার করুন; প্রজেক্টে Android Gradle Plugin 8.7.3 নির্ধারিত।
৪. প্রথমে wrapper তৈরি করতে installed Gradle দিয়ে:

```bash
gradle wrapper --gradle-version 8.9
```

৫. `android/gradle.properties`-এ নিজের URL যোগ করুন:

```text
VIQ_URL=https://YOUR-HOST.onrender.com
```

৬. Terminal-এ:

```bash
./gradlew assembleDebug
```

Windows-এ `gradlew.bat assembleDebug`। APK: `android/app/build/outputs/apk/debug/app-debug.apk`।

৭. Public release-এর জন্য Android Studio → **Generate Signed App Bundle / APK** থেকে নিজের keystore তৈরি করুন। Keystore ও password নিরাপদ backup রাখুন; GitHub-এ upload করবেন না।
৮. CLI release signing চাইলে `VIQ_KEYSTORE`, `VIQ_STORE_PASSWORD`, `VIQ_KEY_ALIAS`, `VIQ_KEY_PASSWORD` environment values দিন এবং `assembleRelease` চালান।

Play Store account, review, বর্তমান target SDK requirement ও publishing policy আলাদা বিষয়। এই প্যাকেজ দিয়ে Store approval নিশ্চয়তা দেওয়া হয়নি।

## ১৪. কম্পিউটারে পরীক্ষা

```bash
python -m venv .venv
```

Linux/macOS:

```bash
source .venv/bin/activate
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

তারপর:

```bash
pip install -r requirements.txt
```

Environment-এ `ADMIN_EMAIL` ও ১৬+ অক্ষরের `ADMIN_PASSWORD` দিন। স্থানীয় পরীক্ষায় `APP_ENV=production` দেবেন না; `DATABASE_URL` না থাকলে local SQLite হবে। `.env.example` নিজে থেকে load হয় না।

Linux/macOS উদাহরণ (নিজের password বসাবেন):

```bash
export ADMIN_EMAIL='owner@example.com'
export ADMIN_PASSWORD='YOUR_UNIQUE_LONG_PASSWORD'
python manage.py init
python app.py
```

Windows PowerShell:

```powershell
$env:ADMIN_EMAIL='owner@example.com'
$env:ADMIN_PASSWORD='YOUR_UNIQUE_LONG_PASSWORD'
python manage.py init
python app.py
```

Browser: http://127.0.0.1:5000

পরীক্ষা:

```bash
pip install pytest==8.4.2
python -m pytest -q
```

PostgreSQL concurrency পরীক্ষা চালাতে আলাদা, খালি, disposable test database-এর URL `TEST_DATABASE_URL`-এ দিন। **নিজের live database দেবেন না; tests টেবিল মুছে নতুন করে তৈরি করে।** GitHub backend checks workflow একটি আলাদা temporary Postgres service ব্যবহার করে।

## ১৫. সমস্যা হলে

| সমস্যা | করণীয় |
|---|---|
| Render build fail | `requirements.txt` root-এ আছে এবং Python runtime নির্বাচিত কি না দেখুন |
| Production requires… | DATABASE_URL, SECRET_KEY, PUBLIC_URL ঠিক করুন |
| Database SSL error | provider-এর সম্পূর্ণ SSL-enabled URL দিন |
| Login-এ origin error | PUBLIC_URL এবং browser-এর origin একই করুন; redeploy |
| অ্যাডমিন লগইন হয় না | প্রথম init-এর email/password দিন; environment পরে বদলালেই password বদলায় না |
| পাসওয়ার্ড হারিয়েছেন | নিজের কম্পিউটারে সঠিক DATABASE_URL দিয়ে `python manage.py reset-password`; এটি interactive |
| প্রথমে ধীরে খুলছে | Render Free cold start হতে পারে |
| Call দেখা যায় না | room-এর host/guest ID এবং category enabled কিনা দেখুন |
| Call সংযোগ হয় না | camera/mic permission, অন্য নেটওয়ার্ক ও TURN পরীক্ষা |
| Actions tab-এ workflow নেই | `.github/workflows/android.yml` সঠিক জায়গায় আপলোড করুন |
| APK-এ ভুল URL | সঠিক app_url দিয়ে workflow আবার চালান |
| APK upgrade হয় না | debug signing key বদলেছে কি না দেখুন; production-এ স্থায়ী release key প্রয়োজন |

## ১৬. প্রকাশের আগে নিজের পরীক্ষার তালিকা

- Owner ও দুইজন সাধারণ user তৈরি করুন।
- সাধারণ user admin API/পেজ ব্যবহার করতে পারে না যাচাই করুন।
- একটি ছোট প্রকৃত deposit যাচাই, কাজ approval, referral, transfer ও withdrawal পরীক্ষা করুন।
- একই approval আবার দিলে টাকা না বাড়ে দেখুন।
- ভুল recharge/exchange request reject করে refund দেখুন।
- দুইটি ফোন এবং দুইটি নেটওয়ার্কে call পরীক্ষা করুন।
- Android-এ file upload, voice, download, logout ও ফিরে আসা পরীক্ষা করুন।
- PostgreSQL backup/export রাখুন। Sensitive data কারা দেখতে পারে এবং কতদিন রাখা হবে ঠিক করুন।
- Free tier-র বাইরে যাওয়ার আগে storage, concurrent users, TURN ও hosting খরচ মূল্যায়ন করুন।

## ১৭. সূত্র

- Render Flask deploy: https://render.com/docs/deploy-flask
- Render Free limitations: https://render.com/docs/free
- Neon connection: https://neon.com/docs/connect/connect-from-any-app
- Android Gradle Plugin 8.7 compatibility: https://developer.android.com/build/releases/agp-8-7-0-release-notes
- Google rewarded ads rules: https://support.google.com/adsense/answer/9121589

Google ads দেখার বিনিময়ে cash reward এই কোডে সংযুক্ত নয়। Ads বিভাগ সরাসরি sponsor-funded কাজের জন্য; নিজস্ব campaign-এর অনুমোদন ও প্রকৃত অর্থায়ন প্রয়োজন।
