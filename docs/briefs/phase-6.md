# Phase 6 brief: licence check (`verify.ts`, `store.ts`)

Branch `brick/collector`. Manual §3.11, §5.6 steps 5–7, §7.4 (LIC-01..05). Not committed yet; waiting for `Verified`.

## 1. What was built

| File | What it does and why |
|---|---|
| `desktop/src/main/license/verify.ts` | `verifyLicense(token, nowSec?, keys?)` checks a licence key with no network. It confirms the key is signed with our Ed25519 key (Ed25519 is a digital-signature method; only the holder of the private key can produce a valid signature), that it is inside its date window, and that it allows scanning. Each failure has its own reason code, so the UI can show the right §3.11 message. It runs in the Electron main process, the only place that can block a scan (§3.11 "Where it lives"). |
| `desktop/src/main/license/store.ts` | `readStoredToken(file)` and `saveToken(file, token)` read and write `license.txt`. The caller passes the path (`paths.licenseFile()`, §5.5), so it can be tested in a temp folder. It only stores; it never decides validity. |
| `desktop/src/main/license/verify.test.ts` | 41 tests: the valid key, every reason code, every §3.11 tampering case, LIC-01..05, plus extra edge cases. |
| `desktop/src/main/license/store.test.ts` | 6 tests for reading and writing the licence file. |

## 2. How it works

`verifyLicense` runs these steps in order and stops at the first failure:

1. **Input**: if it isn't a string or is longer than 4,096 characters → `malformed`. Real keys are about 400 characters. This stops a huge paste from being decoded (LIC-01).
2. **Shape**: trim the text and split it on `.`. It needs exactly 3 parts and the prefix `AG1`. Both segments may contain only base64url characters (`A–Z a–z 0–9 - _`); otherwise → `malformed`.
3. **Payload**: decode the middle part from base64url and `JSON.parse` it. It must be an object with `v === 1`, a string `kid` and `lic`, numeric `exp` and `nbf`, a list of strings in `features`, and `org` either a string or absent. Otherwise → `malformed`.
4. **Key**: look up `kid` in the key map, using only the map's own entries, so names like `__proto__` can't match anything → otherwise `unknown_key`. The built-in map holds one entry, `demo-2026`, loaded from `shared/license/public-key.pem` when the app is built.
5. **Signature**: `crypto.verify` (Node's built-in, no extra package) checks the signature against the exact ASCII text `AG1.<payload>`. Any error counts as a failure → `bad_signature`.
6. **Dates**: allowing 24 hours either way for a wrong PC clock, `now + 24h < nbf` → `not_yet_valid` and `now − 24h > exp` → `expired`. The `expired` result includes `exp` so the UI can show "expired on {date}".
7. **Entitlement**: `features` must include `"scan"` → otherwise `not_entitled`.

The crypto is verify-only and uses the **public** key. The private key is never read, and nothing here signs anything. `store.ts` reads and writes one file, at whatever path the caller passes in (`%APPDATA%\Antigravity\license.txt`). It creates the parent folder if needed, and the token is trimmed on save and on read. It makes no network calls and does no logging.

## 3. Tests written

| Test | What it checks | Why it matters |
|---|---|---|
| valid token → ok (+ whitespace trimmed) | Correct `lic`, `org`, `exp` returned | The happy path, and keys pasted from email with spaces or line breaks still work |
| one character changed in the payload JSON | `bad_signature` | LIC-02: an edited payload is caught |
| payload re-encoded with a later `exp` | `bad_signature` | LIC-02: extending your own licence fails |
| payload re-spelled so it decodes to the same bytes | `bad_signature` | The signature covers the exact text, not just its decoded meaning |
| signature swapped from another token | `bad_signature` | LIC-03 |
| `kid` not in the key map | `unknown_key` | LIC-05 |
| `kid` = `__proto__`, `constructor`, `toString`, `hasOwnProperty` | `unknown_key` | Guards against a JavaScript lookup trick where these names match built-in object properties |
| non-base64url characters in either segment | `malformed` | One licence has exactly one valid spelling |
| signed by a different key; truncated or empty signature | `bad_signature` | Forgeries are caught |
| expired by more than 24 h / by less than 24 h | `expired` with `exp` / `ok` | Both sides of the date-tolerance boundary |
| `nbf` more than 24 h ahead / less than 24 h ahead | `not_yet_valid` / `ok` | Both sides of the date-tolerance boundary |
| `features` without `scan` | `not_entitled` | Entitlement is enforced |
| 9 broken-format inputs (empty, `hello`, `AG1.`, wrong prefix, 4 parts, not JSON, `null`, array…) | `malformed` | LIC-01 |
| 9 signed payloads with a missing or wrong-typed field | `malformed` | A validly signed but broken payload can't crash the app later |
| 5,000-character input | `malformed` in under 500 ms | LIC-01: the app stays responsive |
| non-string input (`undefined`, `42`) | `malformed` | IPC (the channel between the UI and the main process) can send anything |
| bundled key map | `demo-2026` is an Ed25519 public key; a forged `demo-2026` token → `bad_signature` | Proves the real bundled key is the one used by default |
| store: missing file / blank file | `null` | No saved licence → licence screen |
| store: save then read back; trims; creates the folder; overwrites | Exact token back | §5.6 step 6 |

## 4. Test results

Tests written before the code existed failed for the right reason:

```
FAIL  src/main/license/store.test.ts
Error: Failed to load url ./store (resolved id: ./store) ... Does the file exist?
FAIL  src/main/license/verify.test.ts
Error: Failed to load url ./verify (resolved id: ./verify) ... Does the file exist?
Test Files  2 failed (2)
```

After Socrates' review, the new charset test also failed first:

```
× non-base64url characters in either segment -> malformed (one licence, one spelling)
  → expected 'ok' to be 'malformed'
Tests  1 failed | 46 passed (47)
```

Final gate:

```
✓ src/main/license/store.test.ts (6 tests)
✓ src/main/license/verify.test.ts (41 tests)
Tests  47 passed (47)
tsc exit 0   (strict type-check of the four files)

== Test-Common (exit 0): 22 passed, 0 failed
== Test-Skeleton (exit 0): 14 passed, 0 failed
== Test-ReadOnlyGuard (exit 0): Passed: 292  Failed: 0
== Test-ReadOnly (exit 0): READ-ONLY OK
== Test-ProbesA (exit 0): 43 passed, 0 failed
== Test-ProbesB (exit 0): 51 passed, 0 failed
== Test-Collector (exit 0): 7 passed, 0 failed
```

**One test was corrected (§4 step 3).** The first version of "one character changed in the payload" swapped a base64 character. That broke the JSON itself, so the code correctly returned `malformed` at step 3, before the signature step. The test was wrong, not the code: §3.11 means a change to the payload *content*. The test now changes `Test Org` → `Test Orh` in the decoded JSON and re-encodes it, which gives `bad_signature`.

## 5. Run it yourself

```powershell
# cwd: antigravity\desktop
npx vitest run src/main/license
```
Expect `Tests 47 passed (47)`. If you see `Failed to load url ...public-key.pem?raw`, the PEM import broke (check that `shared/license/public-key.pem` exists). Any `×` line names the tamper case that got through.

```powershell
# cwd: antigravity
powershell.exe -NoProfile -File .\collector\tests\Test-ReadOnly.ps1
```
Expect `READ-ONLY OK`. This phase didn't touch the collector; the run confirms that.

## 6. Decisions and limits

- **Decisions agreed with the Archon. The manual (§3.11) needs updating to match:**
  1. `verifyLicense` has an optional third parameter, `keys`. The tests sign with a throwaway key pair created in memory, never written to disk, so they never need the real private key. In production it defaults to the bundled `KEYS`.
  2. The `expired` result carries `exp` for the "expired on {date}" message. **Chris (UI) needs to know this.**
  3. Input longer than 4,096 characters → `malformed`.
- **Socrates' review (one round): no bugs.** Notes acted on: a strict base64url check (Node's decoder silently skips stray characters, which let `token!!` pass); tests for inherited `kid` names; a looser timing limit (50 → 500 ms) so slow machines don't fail the test.
- **Limit (Socrates note 4):** `saveToken` doesn't use write-to-temp-then-rename. A crash mid-write leaves a cut-off file; the next launch then returns `malformed` and shows the licence screen. That's safe, so it's left as is.
- **Also beyond the manual's code:** `org` must be a string if present, and `features` must contain only strings.
- **Still to do:**
  - Wire `verifyLicense` and `store` into `scan:run`, `getLicense` and `submitLicense`, and re-check on launch. That's Shamar/Chris's code (§4.6, §5.6), with LIC-06/07 tested in Phase 7.
  - Issue the demo tokens (§3.11 steps 3–5) and fill `shared/license/demo-keys.md`, which is empty now. This needs your private key, so it's yours to do by hand. No test depends on these tokens.
- **Setup note:** `desktop/` has no `tsconfig.node.json` or `electron.vite.config.*` yet, and `npm run typecheck` refers to the former. The `?raw` import works in vitest and passed a strict standalone `tsc` with `vite/client` types. Shamar owns those config files.
- **Known limit (§3.11, LIC-11):** an offline check can be bypassed by patching the app or turning the PC clock back. This is accepted for a free local tool.

## 7. Pitch line

The licence key is checked fully offline with an Ed25519 signature, and 47 tamper tests prove that an edited, swapped, forged or expired key is refused before a scan can start.
