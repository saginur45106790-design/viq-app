# VIQ v2 — বড় আপডেট

## নতুন চেহারা

আগের হালকা রং ও বড় সাধারণ category cards-এর পরিবর্তে নতুন dark navy/lime design। নিজস্ব SVG icon, wallet card, orbit artwork, quick actions, compact app launcher, floating bottom navigation ও mobile drawer আছে। ১৮টি বিভাগ কাজ/ক্রিয়েটর, কমিউনিটি এবং টাকা/সেবা—এই তিন দলে সাজানো। Desktop-এ sidebar, ছোট স্ক্রিনে drawer ও bottom menu দেখা যাবে।

## নতুন কাজের সুবিধা

- কাজের নাম/বিবরণ দিয়ে সার্ভারে search; category filter; reward/new/deadline sorting; প্রতি পেজ ২০টি ফল।
- কাজ save/unsave করা যায়; প্রতিটি ইউজারের saved list আলাদা।
- Dashboard-এ নিজের approved/pending কাজের সংখ্যা ও আসল ledger-ভিত্তিক আয়।
- Wallet balance hide/show (শুধু স্থানীয় display preference)।
- Wallet ও task updates-এর in-app notification এবং read-all control। এটি ফোনে background push notification নয়।
- প্রতিটি request-এর নিজস্ব support conversation। Wallet-এর request ID বা admin request list থেকে খুলুন।
- Pending request নিজে cancel করা যায়; held balance একই transaction-এ ফেরত আসে। Processing বা completed request নিজে cancel করা যায় না।
- নিজের transaction history CSV export (সর্বশেষ ১০,০০০ entry)।
- Active session count এবং বর্তমান session ছাড়া অন্য সব session revoke।
- Admin user search ও ledger reconciliation: balance/held বনাম ledger totals।

## ব্যাকএন্ড পরিবর্তন

- একই request key দিয়ে অর্থ/প্রাপক/নির্দেশনা বদলালে conflict; credential fingerprint হিসেবে password সংরক্ষণ করা হয় না।
- Mutation rate limit; transfer/password reauthentication attempts-এর সীমা।
- Cross-site Fetch Metadata block, আগের CSRF/origin/session/role checks বজায় আছে।
- Boolean setting-এ string "false"/"true" গ্রহণ নয়; প্রকৃত JSON boolean প্রয়োজন।
- Upload সর্বোচ্চ ৮ MB/ফাইল ও ৬৪ MB/ইউজার; আপলোড-সংক্রান্ত মোট storage check-এ user row lock।
- প্রতি API response-এ request ID; অপ্রত্যাশিত error-এ internal exception detail client-এ দেখানো হয় না।
- Database readiness endpoint `/ready`; আগের `/health` liveness endpoint আছে।
- Tasks, review queue, ledger, tickets, session এবং signalling-এর জন্য অতিরিক্ত database indexes।
- সব নতুন টেবিল additive; `manage.py init` পুরোনো tables মুছে ফেলে না।

## আগের সাইট আপডেট করবেন যেভাবে

১. আগে নিজের PostgreSQL backup/export রাখুন এবং পুরোনো কোডের commit রাখুন।
২. ZIP Extract করুন। `VIQ` ফোল্ডারের ভেতরের ফাইলগুলো একই GitHub repository-তে replace/upload করুন।
৩. নতুন `v2.py`, `static/v2-ui.js` ও `tests/test_v2.py` অবশ্যই দিন। পুরোনো ফাইলের সঙ্গে শুধু CSS বদলালে এই আপডেট কাজ করবে না।
৪. পুরোনো `DATABASE_URL`, `PUBLIC_URL`, `SECRET_KEY` এবং admin account বজায় রাখুন। নতুন database বানাবেন না, যদি আগের user data রাখতে চান।
৫. Render Start Command অপরিবর্তিত:

```bash
python manage.py init && gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 120
```

৬. Health Check Path `/ready` করুন। Render deploy চালান। প্রথম startup-এ নতুন টেবিল ও indexes যোগ হবে। বড় database-এ index তৈরিতে সময়/lock লাগতে পারে; কম ব্যবহারের সময় deploy করুন।
৭. Browser reload করুন। CSS ও JS-এ `?v=2` আছে যাতে আগের cached design না থাকে।
৮. Admin → সারসংক্ষেপ → হিসাব পরীক্ষা চালান। ইউজারের পুরোনো balance/hold ও task history যাচাই করুন।
৯. নিজের দুইটি test account দিয়ে cancel/refund, support reply, saved task ও session revoke যাচাই করুন।

**Rollback:** v2-এর অতিরিক্ত tables রেখে পুরোনো server commit deploy করা যায়, কিন্তু v2-তে cancelled request/নতুন notification বা conversation পুরোনো UI-তে ঠিকভাবে নাও দেখা যেতে পারে। আর্থিক কার্যক্রম চালু হওয়ার পরে অন্ধভাবে database restore করবেন না—তাতে পরের লেনদেন হারাবে।

## Android আপডেট

- Android source-এ versionCode 2, versionName 2.0.0, নতুন icon ও dark system bar আছে।
- GitHub Actions → Build VIQ Android APK → Run workflow → নিজের live HTTPS origin দিন।
- Web UI server থেকে load হওয়ায় server update-এর পর নতুন design দেখা যাবে। Native icon/version পরিবর্তনের জন্য নতুন APK install করুন।
- Release APK আপডেটের জন্য আগের একই signing key দরকার। আলাদা debug build-এর signing key বদলালে reinstall লাগতে পারে।
- এই ডেলিভারিতে build করা APK নেই; Android compile/device acceptance test করা হয়নি।

## বাস্তব সীমা

১৮টি বিভাগের আগের কার্যক্রম বজায় আছে। Recharge/exchange এখনও admin fulfilment; বাইরের provider API, account-transfer automation, automatic paid ads বা per-minute call billing এই আপডেটে যোগ হয়নি। ১৮+ আগের মতো বন্ধ। Live room-এর সর্বোচ্চ ৫ জন এবং TURN-এর প্রয়োজনীয়তা অপরিবর্তিত। বিস্তারিত `FEATURES_BN.md`।

“শক্তিশালী” বলতে এই নির্দিষ্ট validation, authorization, transaction, isolation ও test improvements বোঝানো হয়েছে। এটি ১০০% নিরাপত্তা, independent audit বা unlimited free scale-এর নিশ্চয়তা নয়।
