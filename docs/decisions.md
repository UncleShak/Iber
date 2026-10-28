# Decisions log

One line per decision or build/test run: date, brick, what, why.

- 2026-10-28 (D) Placeholder desktop/src/main/license/verify.ts copied from manual 3.11 so main builds before Brick B's verify.ts lands; key map skips the still-empty shared/license/public-key.pem. Brick B owns the file and may overwrite it.
- 2026-10-28 (Integration) Placeholder verify.ts above is superseded: Brick B's offline Ed25519 verify.ts (6efab4c) is on main and shared/license/public-key.pem is populated.
