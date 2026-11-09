# VIQ v2 verification — 2026-11-09

This record describes executed checks, not an independent security certificate.

## Executed

- Backend regression suite: 36 passed, 1 skipped (SQLite local test database).
- Python compilation: app.py, models.py, manage.py, v2.py.
- JavaScript syntax: static/app.js and static/v2-ui.js.
- Android manifest/theme/icon XML parsing.
- Existing local v1 database initialized successfully with new additive tables.
- Browser inspection of redesigned desktop home, SVG icons, navigation and all 18 categories, grouped into 7 work / 8 community / 3 money services.
- Public home rendered successfully with the new dark navy/lime layout.

## New test coverage (14 scenarios)

1. Dashboard values derived from actual submissions and ledger entries.
2. Saved task/search behavior and user isolation.
3. Literal wildcard characters do not become unintended search wildcards.
4. Notification ownership and read state.
5. Pending cancellation refunds once; processing/completed requests cannot be cancelled.
6. Ticket conversation visibility limited to owner/admin.
7. Other-session revocation preserves the current session.
8. Reusing an idempotency key with changed financial payload is rejected.
9. String values cannot masquerade as JSON booleans.
10. Admin reconciliation detects deliberately introduced balance corruption.
11. CSV export is owner-only and protects user-controlled text from spreadsheet formula injection.
12. Cross-site Fetch Metadata is rejected, including when Origin is missing.
13. Additive initialization preserves existing test balance.
14. Readiness check and request identifiers are returned.

The existing 22 tests continue covering role checks, CSRF, password/login, sessions, task rewards, referral rewards, upload privacy, duplicate deposits, task capacity, deadlines, transfer conservation, withdrawal settlement/refund, recharge, exchange quote, private call access and ledger totals.

## Limits

- PostgreSQL concurrent-withdrawal test skipped locally; GitHub workflow provisions PostgreSQL 16 to execute it. That remote workflow was not run here.
- Authenticated flows verified through API tests; signed-in browser end-to-end testing remains.
- Mobile CSS was implemented, but browser viewport resizing was not available through the supplied control API. An attempted iframe mobile preview was correctly blocked by frame protection; protections were retained and the temporary harness was removed. No physical-phone layout test is claimed.
- Android source updated to version 2.0.0; no APK compile/sign/install or two-device call test was performed here.
- TURN, live media, payment provider APIs, production Render/Neon connectivity, load tests and independent penetration testing remain unverified.
- All original external-service limitations remain listed in FEATURES_BN.md. No new automatic recharge/forex/account-transfer API was added.

Use UPGRADE_V2_BN.md for migration and README_BN.md for first deployment.
