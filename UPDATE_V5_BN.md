# VIQ v5 — ৩৬টি রেফারেন্স অনুযায়ী মোবাইল UI

এই ZIP-এ আগের Flask/PostgreSQL ব্যাকএন্ড, Android WebView সোর্স এবং নতুন পেজ-ভিত্তিক UI আছে।

## বাস্তবে যা পরিবর্তন হয়েছে

- প্রতিটি বিভাগের নিজস্ব রঙ, ফন্ট, কার্ড, মেনু ও হেডার। বাংলা ফন্ট লোকালি অন্তর্ভুক্ত; CDN প্রয়োজন নেই।
- প্রোফাইলের membership card, হোমের ব্যালেন্স ও দ্রুত মেনু, ১৮ সেবার grid।
- আলাদা `#deposit`, `#withdraw`, `#send` পেজ। আগের সার্ভার যাচাই, CSRF ও ledger ব্যবহার করা হয়েছে।
- ডিল চ্যাটে অ্যাডমিনের বার্তা আলাদা সোনালি রঙে; টাকা সংরক্ষণের অবস্থা দৃশ্যমান। টাকা ছাড়ার অনুমতি সার্ভারেও আগের মতো অ্যাডমিনের জন্য সীমিত।
- সাদা রিচার্জ পেজ, কারেন্সির সবুজ terminal, অ্যাডমিনের বিভাগীয় ডিল কার্ড।
- নতুন login/register/settings/support, কাজের history, notifications এবং আলাদা live profile।
- ছবির কিছু decorative artwork একই মূল ছবি থেকে SVG viewport-এর মাধ্যমে ব্যবহার হয়েছে। সব বোতাম, লেখা, ইনপুট এবং আসল ডেটা HTML। পুরো screenshot বসিয়ে ওয়েবসাইট সাজানো হয়নি।

## ছবির সঙ্গে মিলের সীমা

এটি ছবিভিত্তিক responsive implementation; ৩৬টি ছবি pixel-for-pixel হুবহু হয়েছে বলে দাবি করা হচ্ছে না। বিশেষত সব 3D illustration, avatar, decorative logo variant, live scene এবং card spacing এখনও প্রতিটি ছবির সমান নয়। আসল কাজ/পোস্ট/ডিল না থাকলে খালি তালিকা দেখাবে; ছবির নমুনা user, balance, বিক্রির পোস্ট বা অনলাইন মানুষ বানিয়ে দেখানো হয়নি। UI-এর content বদলালে উচ্চতাও বদলাবে।

মূল ৩৬টি রেফারেন্স `static/design/01.png` থেকে `36.png` পর্যন্ত রাখা হয়েছে। `SCREEN_MAP_BN.md` দিয়ে প্রতিটি ছবি ও পেজ মেলানো যাবে।

## যাচাই

- আগের backend suite: 69 passed; PostgreSQL concurrency-এর একটি পরীক্ষা skipped (এই পরীক্ষায় PostgreSQL ছিল না)।
- পুরনো frontend component checks: 25 passed, নতুন UI load করেই।
- ৩৬টি workspace fixture render পরীক্ষা পাস।
- browser-এ 320, 390, 430 px frame width: 108টি layout check; body horizontal overflow পাওয়া যায়নি।
- অর্থ/রিওয়ার্ডের integration tests আলাদা local test database-এ। Live Render site, বাস্তব bKash/Nagad transfer, দুই ফোনের WebRTC বা Android APK এই সংস্করণে end-to-end পরীক্ষা করা হয়নি।
- Screenshot-এর সঙ্গে automated pixel diff বা ১০০% সমতার পরীক্ষা করা হয়নি।

## পুরনো ওয়েবসাইট আপডেট

1. GitHub repository-এর বর্তমান কোডের backup এবং database backup রাখুন।
2. ZIP extract করুন। ভিতরের ফাইল/ফোল্ডার GitHub repository root-এ দিন; ZIP ফাইল নিজে upload করবেন না।
3. পুরনো `DATABASE_URL`, `SECRET_KEY`, `PUBLIC_URL`, `ADMIN_EMAIL`, `ADMIN_PASSWORD` অপরিবর্তিত রাখুন।
4. Render-এর build command: `pip install -r requirements.txt`
5. Start command: `python manage.py init && gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 120`
6. Deploy শেষ হলে browser cache refresh করুন। `/admin` থেকে আগের admin account দিয়ে ঢুকুন।
7. নতুন sample কাজ বা বানানো balance production database-এ যোগ করা হয় না। কাজ, ভিডিও, পোস্ট ও রেট আপনার আসল admin data থেকেই আসবে।

## অ্যাপ

`android/` আগের WebView app source বহাল আছে। একই সাইটের নতুন responsive UI সেখানে দেখাবে। নিজের HTTPS URL দিয়ে workflow চালিয়ে নতুন APK তৈরি করুন; build/setup-এর বিস্তারিত আগের README-তে আছে। এই ZIP একটি APK নয়।

## চালু করার আগে

পুরনো ১৮+ বিভাগ বন্ধ রাখা হয়েছে। Cobra আলাদা সাইটের লিংক; shared balance নয়। রিচার্জ ও deposit/withdraw manual admin workflow; স্বয়ংক্রিয় telecom/payment provider API যোগ হয়নি। Live-এর জন্য আগের TURN/STUN configuration প্রয়োজন হতে পারে।
