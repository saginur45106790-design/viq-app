# VIQ v1 — verification record

Prepared: 2026-11-08. This is an implementation test record, not a security certification.

## Executed successfully

- Python compilation: `app.py`, `models.py`, `manage.py`.
- JavaScript syntax: `node --check static/app.js`.
- Backend tests: **22 passed, 1 skipped**, final run 14.48 seconds.
- Android XML manifest, drawable and style resources parsed successfully.
- Managed preview started successfully at its assigned local URL.
- Browser inspection: home screen rendered, all 18 category links visible, navigation to login and all-categories pages worked.
- Browser console inspection on these public pages found only browser-extension metadata errors; no VIQ application error appeared in the inspected log entries.

## Backend scenarios covered

1. All 18 categories exist; adult category cannot be activated.
2. Ordinary users cannot publish tasks or list admin users.
3. CSRF and cross-origin mutations rejected.
4. Logout invalidates database session.
5. Wrong-password and weak-password rejection.
6. Deposit cannot be approved twice.
7. Reused external deposit transaction reference rejected.
8. Withdrawal holds funds; rejection refunds exactly once.
9. Withdrawal fulfilment removes hold and requires a reference/note.
10. Insufficient balance leaves no partial request.
11. Internal transfer conserves funds and repeated request is idempotent.
12. Negative, fractional-paisa, NaN, self and unauthorized transfers rejected.
13. Task and direct referral rewards credited once.
14. Task capacity and rejection releasing a slot.
15. Minimum elapsed time and deadline enforced.
16. Private file access for owner/admin only; HTML masquerading as image rejected.
17. Exchange quote computed server-side and amount held.
18. Recharge number validation and duplicate-request protection.
19. Blocked user's sessions revoked.
20. Private call room and signalling permissions.
21. Non-HTTPS/script URLs rejected in Cobra setting.
22. User balances/holds reconcile against ledger sums after mixed operations.

## Not executed / not proven

- The PostgreSQL simultaneous-withdrawal test was skipped locally because no PostgreSQL test server was attached. `.github/workflows/tests.yml` provisions PostgreSQL 16 and runs it. That workflow has not been executed in the user's GitHub account here.
- Local functional tests used SQLite. PostgreSQL driver and SQLAlchemy support are supplied; live Neon/Render connection remains unverified.
- Authenticated UI workflows were tested through backend APIs, not through a signed-in browser session.
- Android Gradle build, APK signing, install and real-phone runtime tests were not performed. This delivery contains Android source, not a verified APK binary.
- Microphone/camera, two-device WebRTC, mobile-carrier NAT/TURN, live media and Android file download were not exercised end to end.
- Desktop browser UI was visually inspected; physical mobile-screen and device accessibility tests remain.
- No load test, external penetration test, payment-provider integration test or independent security audit was performed.
- Automatic telecom/MFS/foreign-exchange/advertising integrations are not present. Related operations use reviewed admin fulfilment.

## Operational constraints

Use PostgreSQL for deployment, HTTPS, independent strong administrator credentials and database backups. Maintain real funds backing wallet liabilities. Free hosting and database/media quotas are finite. Call/live reliability requires testing and often TURN; live rooms are capped at five participants. File evidence is limited to 8 MB and stored privately in the database; larger media needs a separate storage service or a share link.

Follow README_BN.md before exposing real-user transactions. Consult FEATURES_BN.md for the precise scope of each category.
