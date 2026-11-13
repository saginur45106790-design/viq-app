# VIQ 4.0 — বিস্তারিত আপডেট ও সেটআপ

এই ZIP হলো সম্পূর্ণ সোর্স কোড, প্রস্তুত APK নয়। v3-এর ১৮টি বিভাগ ও আটটি কাজের নিয়ম রাখা হয়েছে। v4-এর নিচের আটটি পরিবর্তন নতুন। এটি আপনার Render সাইটে এখনো ডিপ্লয় করা হয়নি।

## ১. অ্যাডমিন প্রবেশ

নিজের সাইটের ডোমেইনের শেষে `/admin` দিন। `/admin/`, `/admin/login`, `/admin.html`-ও একই অ্যাপ খুলবে। লগইন আলাদা প্রশাসনিক পরিচয় যাচাই করে; সাধারণ ব্যবহারকারী অ্যাডমিন API ব্যবহার করতে পারবেন না। এই route পরিবর্তন কার্যকর হতে নতুন কোড deploy করতে হবে। ভুল service domain বা পুরোনো deployment-এর Not Found শুধুমাত্র ZIP ডাউনলোড করলে ঠিক হবে না।

## ২. ভিডিও দেখে আয়

- অ্যাডমিন → ভিডিও ফিড থেকে MP4 আপলোড, শিরোনাম/ক্যাপশন, চালু/বন্ধ।
- দৈর্ঘ্য সার্ভারে ffmpeg দিয়ে যাচাই: ৬০–৬১ সেকেন্ড, ফাইল সর্বোচ্চ ৮ MB। শেষ ফ্রেমের encoding tolerance-এর জন্য ১ সেকেন্ড ছাড় রাখা হয়েছে; গণনার সময় ৬০ সেকেন্ড।
- উল্লম্ব পূর্ণ পর্দা, play/pause, sound, share, timer/progress, পরবর্তী ভিডিও ও upward swipe। ৬০ সেকেন্ড পূর্ণ না হলে পরবর্তী ভিডিও খুলবে না। অ্যাপ থেকে বের হওয়া সবসময় সম্ভব।
- ট্যাব আড়াল, মাঝপথে বের হওয়া, সময় এগিয়ে নেওয়া অথবা heartbeat বন্ধ হলে দেখা বাতিল। আবার শুরু করতে হবে।
- প্রতি ৩০টি ভিন্ন সম্পূর্ণ ভিডিওতে ১৫ টাকা। একই ভিডিও পুনরায় পুরস্কার দেবে না। মাঝপথে কোনো টাকা নয়; ৩০ পূর্ণ হলে একবারে পুরস্কার।
- সেশন সার্ভারে একজনের জন্য একটিই; পুরস্কার ও ledger একই transaction-এ। Browser heartbeat মানুষ সত্যিই মনোযোগ দিয়ে দেখছে তার প্রমাণ নয়।

## ৩. অডিও লাইভ, কয়েন ও গিফট

- সাদা LIVE directory-তে দুই কলামের কার্ড (ডেস্কটপে চার), প্রকৃত অনলাইন সংখ্যা, ব্যবহারকারীর নিজের ছবি।
- রুমে নীল রাতের আকাশ, চাঁদ, ১০টি আসন, মাইক, শ্রোতা, কমেন্ট, গিফট, আলাদা Live profile। হোস্ট প্রথম আসনে যোগ দেন।
- খালি আসনে ক্লিক করে মাইকের অনুমতি দিলে কথা বলা যায়; আসন ছাড়লে মাইক বন্ধ। অন্যরা শ্রোতা হিসেবে যোগ দিতে পারেন।
- ১০,০০০ কয়েন = ১০ টাকা; মূল ব্যালেন্স ↔ কয়েন। পরিমাণ ১০ কয়েনের গুণিতক; অতিরিক্ত ফি নেই।
- Rose ১০০, Love ৫০০, Crown ২,০০০, Rocket ১০,০০০, Galaxy ৫০,০০০ কয়েন। পুরো গিফটের কয়েন প্রাপক পান; প্রেরক ও প্রাপকের হিসাব একসঙ্গে হয়।
- ব্যানার, বড় স্টিকার ও নিজস্ব red/gold rocket animation। রেফারেন্সের ভাব অনুসারে তৈরি; আসল অ্যাপের proprietary asset বা pixel-perfect নকল নয়।
- আগের host-per-minute admin review ব্যবস্থা বহাল। অন্তত একজন সক্রিয় শ্রোতা ও চালু মাইক প্রয়োজন; Live profile-এ হিসাব, admin live reviews-এ অনুমোদন। প্রতি বক্তার জন্য আলাদা minute reward চালু করা হয়নি।
- সংযোগ WebRTC mesh; সার্ভারে অডিও রেকর্ড হয় না। API সীমা ১০০ উপস্থিত সদস্য হলেও ১০ বক্তা/১০০ শ্রোতার বাস্তব load test করা হয়নি। ব্যবহারযোগ্য সর্বোচ্চ সংখ্যা ডিভাইস/নেটওয়ার্কের ওপর নির্ভরশীল।
- বিভিন্ন মোবাইল নেটওয়ার্কে নির্ভরযোগ্য অডিওর জন্য TURN_URL, TURN_USERNAME, TURN_PASSWORD সেট করুন। বড় জনসমাগমে SFU media server প্রয়োজন; সম্পূর্ণ বিনামূল্যে বড় আকারের লাইভ নিশ্চিত নয়।

## ৪. মোবাইল রিচার্জ

সাদা/নীল UI, পাঁচ অপারেটরের নাম ও নিজস্ব রঙের wordmark badge, ২০/৫০/১০০/২০০/৫০০ quick amount। সার্ভার ও ফর্মে ২০–৫০০ টাকা সীমা। নম্বর ও অপারেটর যাচাই। টাকা সংরক্ষণ, admin process/approve/reject ও রসিদ। এটি manual recharge workflow; কোনো telecom recharge API যুক্ত নয়। অ্যাডমিন বাস্তবে রিচার্জ করে তারপর approve করবেন। আনুষ্ঠানিক কোম্পানি logo files চাইলে `static/brands/`-এর SVG বদলাতে হবে।

## ৫. মানি এক্সচেঞ্জ ও রিজার্ভ

USD, EUR, GBP, CHF, JPY, CAD, AUD, NZD, SGD, HKD, CNY, KRW, AED, SAR, KWD, BHD, OMR, QAR, SEK, NOK — নাম, দেশ/অঞ্চলের পতাকা ও symbol। এগুলো নির্বাচিত ২০টি মুদ্রা; শক্তির ranked তালিকা নয়।

অ্যাডমিন → কারেন্সি রেট: ১ ইউনিটের BDT মূল্য ও enabled। প্রথমে সব রেট বন্ধ/শূন্য; কোনো বাস্তব বাজারদর বানিয়ে দেওয়া হয়নি। রেট সেট করে চালু করতে হবে। ইউজার buy, holdings/reserve, বর্তমান মূল্য/ক্রয় খরচের পার্থক্য ও sell দেখতে পাবেন। উদাহরণ: ১০০ টাকায় ১ USD কেনা, রেট ১২০ হলে বিক্রি = ১২০ টাকা। একই buy/sell rate, কোনো fee নয়। সর্বোচ্চ ছয় দশমিক কারেন্সি quantity; BDT-তে buy উপরে ও sell নিচে পয়সায় rounding হয়। confirm-এর আগে rate বদলালে নতুন quote প্রয়োজন।

এটি VIQ-এর অভ্যন্তরীণ ব্যালেন্স ও কারেন্সি হিসাব। বাস্তব USD custody, ব্যাংক, ব্রোকার, live FX feed বা বাইরের currency transfer যুক্ত নয়। রেট বাড়ালে ব্যবহারকারীদের পাওনা বাড়ে; পরিশোধের অর্থ মালিককে বাস্তবে রাখতে হবে।

## ৬–৮. Facebook Page / Facebook Group / Gmail মার্কেটপ্লেস

তিনটি পৃথক marketplace। ছবি, শিরোনাম, চাওয়া মূল্য ও বিবরণ; Page/Group-এ Facebook HTTPS link বাধ্যতামূলক। Gmail-এর প্রকাশ্য পোস্টে password/OTP/recovery code দেওয়া যাবে না। কোনো external account স্বয়ংক্রিয় login/transfer হয় না।

১. বিক্রেতা পোস্ট দেন; অন্যরা search করে দেখতে পারেন।
২. Deal নাও → মূল্য দেখিয়ে নিশ্চিতকরণ → পর্যাপ্ত মূল ব্যালেন্স থাকলে টাকা held হয়। একটি live listing একসঙ্গে একটি active deal-ই নিতে পারে।
৩. ক্রেতা, বিক্রেতা ও বিভাগীয় অ্যাডমিনের জন্য private chat, সময়, deal ID, status, held amount। Messenger-ধাঁচের bubble UI; chat ৪ সেকেন্ডে refresh হয়।
৪. বিক্রেতা হস্তান্তর জানান, ক্রেতা বুঝে পাওয়ার কথা জানান, অ্যাডমিন যাচাই করে seller balance-এ ছাড়েন। ব্যবহারকারী নিজে held টাকা সরাতে পারেন না।
৫. ক্রেতা/বিক্রেতা cancel করলে পোস্ট আবার live হয়; পুরোনো টাকা admin refund পর্যন্ত held থাকে। পুরোনো refund নতুন deal-কে বদলায় না।
৬. সমস্যা জানালে disputed; admin release/refund দিয়ে নিষ্পত্তি করেন। completed পোস্ট marketplace থেকে সরে যায়, deal/chat/হিসাব থেকে মুছে যায় না।
৭. অ্যাডমিন → মার্কেট অ্যাডমিন: তিনটি বিভাগীয় profile/card, আলাদা chat list, pending/active/completed/refund-pending counts ও সংরক্ষিত balance। এটি তিনটি আলাদা admin password/account নয়; একই অনুমোদিত admin-এর তিন বিভাগ।

## অতিরিক্ত ও নিরাপত্তা

- Balance, holdings ও coin-এর ledger; টাকা integer paisa, currency integer millionths।
- Buy/sell, coin conversion, gift ও deal-start-এ request key এবং duplicate retry protection।
- PostgreSQL row locks, insufficient-balance check, transactional release/refund, role check, private chat membership, CSRF, escaped user text, audit log।
- ছবি/ভিডিও PostgreSQL-এ থাকে; Render-এর অস্থায়ী disk-এ হারায় না। প্রতি account media cap ২৫৬ MB; database-এর প্রকৃত quota আলাদা। বড় video library-র জন্য object storage migration প্রয়োজন।
- ১৮+ বিভাগ বন্ধ রাখা হয়েছে; পরবর্তী বিস্তারিত ছাড়া নতুন adult service যোগ করা হয়নি।
- UI-তে পৃথক recharge, exchange, video, audio, marketplace ও inbox theme; responsive layout, SVG icons, Bengali copy, reduced-motion handling।

## আগের সাইটে আপডেট করার ধাপ

১. PostgreSQL database-এর backup নিন। GitHub repository-তে আগের source-এর ওপর এই ZIP-এর project files বসান। ZIP নিজে repository-তে আপলোড করে রাখলেই deploy হবে না—ভেতরের ফাইল লাগবে।
২. `app.py`, `models.py`, `v4.py`, `manage.py`, `requirements.txt`, `static/`, `templates/` সহ সব সংশ্লিষ্ট ফাইল commit করুন। `.env` বা local database আপলোড করবেন না।
৩. Render-এর আগের Web Service ও একই DATABASE_URL রাখুন। SECRET_KEY বদলাবেন না।
৪. Build command: `pip install -r requirements.txt`
৫. Start command: `python manage.py init && gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 120`
৬. Manual Deploy → Deploy latest commit। init নতুন tables/currencies যোগ করে; পুরোনো account/password/balance মুছে না।
৭. নিজের domain-এর `/admin` খুলে ADMIN_EMAIL-এর account দিয়ে login করুন। পুরোনো admin password init বদলায় না।
৮. Currency rates দিন, একটি ৬০ সেকেন্ডের MP4 দিন, দুইটি test user দিয়ে listing/deal/refund এবং দুটি আলাদা ডিভাইসে live audio পরীক্ষা করুন। বাস্তব ব্যবহারকারীর টাকা নিয়ে পরীক্ষা করবেন না।
৯. পুরোনো browser asset দেখালে refresh/cache clear করুন।

নতুন সাইট হলে README_BN.md-এর DATABASE_URL, PUBLIC_URL, ADMIN_EMAIL, ADMIN_PASSWORD, SECRET_KEY সেটআপ অনুসরণ করুন। PUBLIC_URL-এ নিজের actual Render domain দিন।

## Android অ্যাপ

`android/`-এ WebView source version 4.0.0। `.github/workflows/android.yml`-এ workflow-এর নাম/inputs দেখুন; repository Actions থেকে নিজের HTTPS VIQ URL দিয়ে build চালান। সফল build-এর artifact থেকে debug APK ডাউনলোড করে নিজের ফোনে পরীক্ষা করুন। এই পরিবেশে Android APK build বা real-device install হয়নি। Play Store প্রকাশের জন্য নিজের release signing ও পৃথক যাচাই প্রয়োজন।

## যাচাইয়ের সীমা

VERIFICATION_V4.md-এ পরীক্ষার ফল আছে। automated test pass মানে ১০০% bug-free বা production audit নয়। আপনার live Render domain, বাস্তব recharge/payment, external account handover, ১০-device audio এবং Android APK এখানে end-to-end যাচাই করা হয়নি। GitHub repository link দিলে deployment logs ও actual admin route নির্দিষ্টভাবে মিলিয়ে দেখা যাবে।
