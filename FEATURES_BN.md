# VIQ v4 আপডেট

বর্তমান ফিচার ও সীমার পূর্ণ তালিকা: **UPGRADE_V4_BN.md**। নিচে আগের সংস্করণের তালিকা রাখা হলো।

# v3 পরিবর্তন

আট বিভাগের বর্তমান আচরণ ও সীমা **UPGRADE_V3_BN.md**-এ। নিচের তালিকা আগের সংস্করণের তথ্য; v3-এর নিয়ম অগ্রাধিকার পাবে।

# VIQ ফিচার ও বাস্তব সীমা

| # | বিভাগ | এই কোডে কী আছে | কী আগে থেকে যুক্ত নয় |
|---|---|---|---|
| 1 | লাইক/ফলো/জয়েন | অ্যাডমিনের task, URL, proof, review, reward | Facebook/অন্য platform API দিয়ে engagement verification |
| 2 | ভিডিও তৈরি | brief, media proof/link, review, reward | AI video generator বা unlimited video storage |
| 3 | বিজ্ঞাপন দেখা | sponsor task, minimum elapsed time, response review | AdSense cash rewards, ad network contract/API |
| 4 | ভিডিও দেখা | video link, response/proof, review | মানুষের মনোযোগ বা third-party playback-এর নিশ্চিত যাচাই |
| 5 | রেফার ও টিম | referral link, direct members, approved-task commission | deposit/recruitment-ভিত্তিক কমিশন, বহু স্তরের আয় |
| 6 | ভিডিও কল | booking request, admin-created private WebRTC room | automatic per-minute billing, guaranteed all-network connection |
| 7 | এজেন্সি | আবেদন, approval status, referral team, category tasks | agency-এর নিজস্ব manager login/উপ-অ্যাডমিন বা কাজ প্রকাশ |
| 8 | Facebook পেজ বিক্রি | আলাদা admin task ও proposal/review page | automated marketplace, escrow, password handover বা Meta approval |
| 9 | Gmail বিক্রি | আলাদা admin task ও proposal/review page | Google account তৈরি/হস্তান্তর, credential trading automation |
| 10 | ১৮+ | দৃশ্যমান আলাদা নিষ্ক্রিয় পেজ | adult কার্যক্রম বা age-verification service |
| 11 | প্রশ্নের উত্তর | প্রশ্ন/বিবরণ, text/voice submission, admin review | জটিল branching multi-question survey builder |
| 12 | Facebook গ্রুপ বিক্রি | আলাদা admin task ও proposal/review page | automatic group transfer বা platform authorization |
| 13 | ডেইলি টাস্ক | নতুন task, slots, deadline, একবার জমা | একই task-এ calendar-day repeat; admin নতুন daily task দেবেন |
| 14 | অডিও/ভিডিও লাইভ | admin-created host room, মোট ৫ জন পর্যন্ত WebRTC | বড় broadcast CDN, gifts, automatic streaming income |
| 15 | লেখা থেকে ভয়েস | script, browser recorder, private file, listen/download | AI TTS engine; এখানে মানুষ নিজের কণ্ঠে পড়বে |
| 16 | Cobra | admin-configured external HTTPS URL | Cobra account/wallet sync, iframe guarantee বা return guarantee |
| 17 | রিচার্জ | বাংলাদেশি নম্বর, operator, balance hold, manual fulfilment/refund | automatic telecom recharge API |
| 18 | মানি এক্সচেঞ্জ | VIQ BDT wallet থেকে destination quote, fee, hold, review | external money pull, live forex/crypto market integration |

## সাধারণ ফিচার

- Password hashing, database session, CSRF, basic login rate limit, blocked-user access revocation।
- User/admin-এর আলাদা login entry, role check; শুধু admin কাজ প্রকাশ করে।
- Deposit request, withdrawal hold/refund, internal balance transfer ও unique transaction log।
- Transaction amounts integer paisa; decimal validation; nonnegative balance database constraint।
- Submission, deposit receipt, transfer request ও settlement-এ duplicate control।
- Admin audit trail, category switches, settings, payment review, user block/unblock।
- প্রথম ২০০ user history items; admin list প্রতি পেজ ১০০, pagination আছে।
- PostgreSQL persistent storage; local uploads Render disk-এ রাখা হয় না।
- Android HTTPS-only first-party WebView, explicit media permission, file picker, download।

## যে বিষয়গুলোকে সম্পন্ন বলা হয়নি

এটি delivered source implementation-এর বিবরণ; “সব ফিচার production-certified”, “অসীম ফ্রি”, “১০০% নিরাপদ” বা “APK ফোনে পরীক্ষা করা হয়েছে”—এমন দাবি নয়। Payment provider integrations, production PostgreSQL live deployment, independent audit, release signing ও ফোনে acceptance testing বাকি।

আপনার কাজের তালিকার সব entry আছে, কিন্তু শুধু entry থাকা মানেই সেই বাইরের ব্যবসায়িক সেবা সংযুক্ত হওয়া নয়। উপরের চতুর্থ কলামে অবশিষ্ট integration স্পষ্ট রাখা হয়েছে।

## v2 additions

- New dark navy/lime app interface; custom inline SVG icons; grouped category launcher; mobile bottom navigation and drawer.
- Search/filter/sort/paginate tasks, personal saved task list.
- In-app notifications, request-specific support conversation.
- Cancel own pending request with one-time atomic hold refund.
- Session list and revoke-other-sessions control.
- Own CSV transaction export; admin user search and wallet reconciliation.
- Additional validation, mutation/reauthentication limits, idempotency payload binding, per-user attachment quota, database indexes and readiness endpoint.

See UPGRADE_V2_BN.md. The per-category external integration limits above still apply.
