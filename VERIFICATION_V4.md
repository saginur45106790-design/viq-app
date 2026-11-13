# VIQ v4 verification — 13 November 2026 (Bangladesh)

## Executed

- Python / Flask / SQLite suite: **69 passed, 1 skipped**, 45.42 seconds.
- Node component render checks: **25 passed** (13 existing + 12 v4).
- JavaScript syntax checks: app.js and v4-ui.js passed.
- Python compilation checks: app.py, models.py, v2.py, v3.py, v4.py, manage.py passed.
- Existing local database: manage.py init completed, without changing existing passwords.
- Browser: public home loaded; recharge component fixture visually inspected in Chrome at desktop width. Screenshot was a fixture, not a completed real recharge.

## New tests (11)

Admin route aliases; recharge 20/500 boundaries; coins round trip, insufficient funds and duplicate retry; FX buy at 100 BDT and sell at 120 BDT with stale quote rejection; escrow hold/release and replay; cancellation/relisting with old refund preserving a new deal; private chat access control; live seat conflict/bounds and gift conservation; thirtieth complete clip earning 15 BDT exactly once; seeking/hidden/abandoned video rejected; actual ffmpeg-generated 1-second clip rejected and 60-second MP4 accepted with admin-only publishing.

## Not executed / limits

The skipped test requires PostgreSQL concurrency. GitHub CI has PostgreSQL 16 configured, but this environment's run used SQLite. No actual GitHub push or Render deployment took place. No real payment/recharge, external account ownership transfer, Android APK build/install, mobile viewport browser run, cross-network WebRTC session, ten-speaker load test, penetration test or independent security audit was performed. Other v4 screens have component render tests, not full visual/end-to-end browser coverage. Do not describe this as 100% error-free or production-audited.

The current design uses original SVG/CSS assets based on the supplied layout references. Operator badges are stylized wordmarks, not official logo asset downloads. Gift animations are original, not the reference app's exact source assets. Currency balances are internal VIQ accounting, not external custody. Recharge and payments are admin-mediated manual workflows.
