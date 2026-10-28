# Antigravity report design and wording spec (HTML + PDF)

By Frank, for Tshedi. Brick C hand-off (checklist item C7, due Day 1 21:30). Based on manual §0.8, §0.9, §4.3, §4.9.3, §4.10 and §4.11.

## 1. How to use this spec

Frank owns the design and the wording. Tshedi implements both renderers in the engine: `report.html.j2` (§4.10) and `render/pdf.py` (§4.11). Everything below is meant to be built exactly as written. Where something is a choice I made rather than the manual's rule, it is marked **(my call)**. Open questions are collected in section 8.

The rules that apply to every output (app, HTML, PDF):

- **One source of truth.** Render only from `report.json`. Never compute a status, never re-rank, never sort. Categories stay in the order they arrive (backup, patch, software, protection, recovery) and fixes stay in `top_fixes` order.
- **Status is always icon + word + colour.** Never colour alone, so it survives colour blindness and greyscale printing.
- **Same hex values everywhere** (§4.3 tokens, section 2).
- **Plain English.** Grade 8 reading level, no jargon without a short gloss, no fear language.
- **Dates** read like "13 Nov 2026", in the PC's local date. Spelling is South African English ("licence", "colour").
- **Every fix looks the same on all three surfaces:** rank, title, why, steps, then "\~5 min" and "Needs admin" if `needs_admin` is true.

## 2. Status vocabulary (single table)

These match the app's `StatusBadge` (§4.9.3). Do not invent other words.

| Status | Word | HTML symbol | Text colour | Fill colour |
| --- | --- | --- | --- | --- |
| `red` | Act now | ● | `#b42318` | `#fef3f2` |
| `amber` | Improve | ▲ | `#b54708` | `#fffaeb` |
| `green` | Good | ✓ | `#067647` | `#ecfdf3` |
| `unavailable` | Not checked | ⊘ | `#475467` | `#f2f4f7` |
| `failed` | Check failed | ✕ | `#475467` | `#f2f4f7`, dashed border |

The overall badge uses the same table, driven by `overall` (only red, amber or green).

CSS variables for the HTML template, paste as is:

```
:root {
  --red: #b42318;   --red-bg: #fef3f2;
  --amber: #b54708; --amber-bg: #fffaeb;
  --green: #067647; --green-bg: #ecfdf3;
  --grey: #475467;  --grey-bg: #f2f4f7;
  --ink: #1a1a1a;   --muted: #667085; --line: #e4e7ec;
}
```

## 3. HTML report

### 3.1 Technical rules (from §4.10)

- One file. Inline `<style>`, no `<script>`, no external fonts, images, CDN or links.
- Jinja `autoescape=True`. A `<script>` in a software name must show as plain text.
- `<html lang="en">`, a real `<title>` ("Antigravity - Cyber Health Check - 14 Nov 2026"), one `<h1>`, then `<h2>` per section.
- Font stack: `"Segoe UI", system-ui, Arial, sans-serif`. Body 16 px, line height 1.5.
- Max width 860 px, centred, 24 px side padding. Must read well at 100% zoom on a 1366 × 768 laptop.
- Print: `@media print` sets A4, 15 mm margins, no background colours required, `page-break-inside: avoid` on every category section and every fix. Status still reads without colour because of the symbol and word.

### 3.2 Page structure and exact wording

**Header**

- Line 1: "Antigravity" (bold) and "Cyber Health Check".
- Overall badge (large): symbol + word from the table above.
- `summary` as a 20 px sentence under the badge.
- Small grey line: "Checked on {date}" and, if the licence org is available (see section 8), "Licensed to {org}".
- If `scan.is_admin` is false, a grey note: "Scanned without admin rights, so some checks were skipped."

**Section: Your top fixes** (`id="actions"`)

- Heading: "Your top 3 fixes". If fewer than 3: "Your top 2 fixes" or "Your top fix".
- If `top_fixes` is empty: "Nothing urgent. Re-check monthly."
- Each fix is a numbered block: rank number, title (bold), why, "Steps" as an ordered list, then the meta line "\~5 min" plus "Needs admin" when true.

**Section: Overview** (`id="overview"`)

- Heading: "The 5 checks at a glance".
- Five equal tiles in a row (wrap to 2 or 3 per row on narrow screens). Each tile is a link to that category's anchor and shows the title, then symbol and word.

**Five category sections** (`id` is the category id, fixed order)

- `<h2>` title with the badge beside it.
- `explanation` paragraph.
- Evidence table with column headers "What we looked at", "What we found", "Status" (use `<th scope="col">`). Third column is the symbol only, with the word as hidden text for screen readers.
- Fix blocks for every id in `fix_ids`, same layout as the top fixes. If that fix is also in `top_fixes`, add a small tag "Top fix 2" **(my call)**. If `fix_ids` is empty, show "Nothing to fix here."
- For `unavailable` categories, add the line "Run Antigravity as administrator for a full check." only when `scan.is_admin` is false **(my call, because some unavailable checks, like BitLocker on Windows Home, cannot be fixed by running as admin)**.

**Footer**

- "Generated locally on this PC. Nothing was uploaded."
- "This is a guidance check, not a full security audit."
- "Engine {engine\_version} · Baseline {baseline\_version} · {os\_caption}" in small grey text.

### 3.3 Evidence rows

| Row `status` | How it looks |
| --- | --- |
| red, amber, green | Normal text, coloured symbol in the third column |
| `unavailable` | Grey italic value (for example "Not checked - needs admin"), grey ⊘ |
| `failed` | Grey italic value starting "Couldn't read:", grey ✕. Do not add the prefix twice if the value already starts with it |
| missing | Neutral, no symbol |

## 4. PDF one-pager

A4 portrait, 210 × 297 mm, 15 mm margins (content width 180 mm). ReportLab canvas, built-in Helvetica only. Exactly one page: one `showPage()` call and nothing that can flow onto page 2.

### 4.1 Two glyph problems you will hit

Helvetica in ReportLab only covers Windows Latin-1 (cp1252) characters. That has two consequences:

1. **The status symbols ● ▲ ✓ ⊘ ✕ cannot be printed as text.** Draw them as small vector shapes with the canvas instead: filled circle (red), triangle (amber), tick path (green), circle with a slash (unavailable), cross (failed). Always draw the word next to the shape.
2. **The arrow "→" in fix steps (for example "Open Start → Windows Security") is not in cp1252** and will render as a box. In the PDF, replace "→" with ">" before drawing. The em dash and the ellipsis are fine.

Add a guard in `pdf.py`: encode every string with `cp1252` after the replacement, and fail the test if anything cannot be encoded.

### 4.2 Layout (distances from the top of the page)

| Block | Position | Content and type |
| --- | --- | --- |
| Header | 15–40 mm | Left: "Antigravity" 20 pt bold, "Cyber Health Action Plan" 12 pt beneath. Under that, 9 pt grey: org (truncate to 40 characters with "…") and the date. Right: overall badge, 45 × 14 mm box with the token fill, a 1 pt border in the token colour, the drawn symbol and the word in 12 pt bold |
| Summary | 42–55 mm | `summary`, 11 pt, maximum 2 lines |
| Category strip | 58–75 mm | Five boxes, each 33.6 mm wide with 3 mm gaps. Title in 8 pt bold (wrap to 2 lines), status symbol and word in 9 pt bold on the last line. Fill and border from the status tokens |
| Fix 1 to 3 | 80–255 mm | Three boxes, each 55 mm tall with 5 mm gaps (80–135, 140–195, 200–255) |
| No fixes | same area | Centred "Nothing urgent. Re-check monthly." in 13 pt with a drawn green tick |
| Footer | 265–282 mm | 8 pt grey: "Generated locally - nothing was uploaded. Guidance only, not a full audit." Second line 7.5 pt: engine, baseline and OS versions |

If there are fewer than 3 fixes, keep the same box positions from the top and leave the rest empty. No placeholder boxes.

### 4.3 Inside one fix box

- A 2 mm vertical stripe on the left in the fix's severity colour, plus the word "Act now" (red) or "Improve" (amber) in 9 pt bold at the top right, so severity is not colour alone.
- Rank number in a filled circle, 8 mm across, at the top left.
- Title: 13 pt bold, one line, truncate with "…".
- Why: 10 pt, at most 2 lines, 12 pt leading.
- Steps: 10 pt, 12 pt leading, numbered "1.", "2.", one line each, truncated with "…" at the box width. Show at most 4. If there are more, replace the fourth with "…see full report".
- Bottom line, 9 pt grey: "\~5 min" and, if `needs_admin`, " · Needs admin".

These sizes fit with room to spare (about 41 mm of the 55 mm is used by the worst case).

## 5. Copy rules for the engine's text

The engine writes `explanation`, fix `title`, `why` and `steps` (§2). These limits keep the PDF from truncating and keep the tone consistent. Please make the fixture text follow them.

| Field | Rule |
| --- | --- |
| `summary` | One sentence, at most 90 characters. Say how many urgent issues there are, and mention any "Not checked" or "Check failed" categories |
| `explanation` | One or two short sentences, at most 200 characters (the contract limit). Start with what was found, then why it matters |
| Fix `title` | A verb first: "Turn on…", "Update…", "Install…". At most 50 characters |
| Fix `why` | One sentence, at most 140 characters, about the risk in everyday words |
| Fix `steps` | 1 to 5 steps, each at most 80 characters, starting with a verb. Write paths as "Open Start > Windows Security" |

Gloss the first use of any technical term, in brackets: "BitLocker (disk encryption)", "Controlled Folder Access (stops unknown programs changing your files)", "restore point (a saved snapshot Windows can go back to)".

Avoid: "compromised", "hacked", "critical vulnerability", exclamation marks, and anything that sounds like a guarantee ("you are safe"). The tool gives guidance, not a verdict on the PC.

## 6. Fixed wording bank

| Where | Exact text |
| --- | --- |
| Product line | Antigravity - Cyber Health Check |
| PDF title | Antigravity - Cyber Health Action Plan |
| Fix heading | Your top 3 fixes |
| No fixes | Nothing urgent. Re-check monthly. |
| Overview heading | The 5 checks at a glance |
| Non-admin note | Scanned without admin rights, so some checks were skipped. |
| Unavailable hint | Run Antigravity as administrator for a full check. |
| No fix needed | Nothing to fix here. |
| Footer 1 | Generated locally on this PC. Nothing was uploaded. |
| Footer 2 | This is a guidance check, not a full security audit. |
| Effort | \~5 min |
| Admin flag | Needs admin |

## 7. Acceptance checks for Tshedi

Run all of these against the all-states mock (§4.12) and every `shared/fixtures/report.*.json`.

**HTML**

- Exactly 5 category sections in the fixed order, and a 5-tile overview with working anchors.
- Every status word from section 2 appears at least once for the all-states mock, including "Not checked" and "Check failed".
- No `<script>` tag and no `http://` or `https://` anywhere in the file. A `<script>alert(1)</script>` software name appears as visible text.
- No more than 3 fixes in the "Your top fixes" section, in `top_fixes` order.
- Prints on A4 with no category split across pages. View once in greyscale and confirm every status is still readable.

**PDF**

- File starts with `%PDF` and the canvas reports exactly one `showPage()`.
- Every drawn string encodes as cp1252 after the arrow replacement.
- Steps beyond 4 show "…see full report". A 40+ character org name is truncated with "…".
- The no-fixes fixture shows "Nothing urgent. Re-check monthly."
- Frank and Tshedi look at the first render together and sign it off by Day 1 21:30.

## 8. Open decisions

1. **Licence org is not in `report.json`.** The manual's HTML header and PDF header both show it, but §2.3 says renderers use the report model only, and §0.8 has no org field. Options: (a) add an optional `licence_org` field through the §0.10 contract-change procedure (minor version bump), or (b) drop the org from the HTML and PDF headers. I recommend (a), since the app already shows it. Needs Tshedi and Schwan to agree.
2. **Evidence ID (AG-…)** appears in the app footer and the insurer export but is not in `report.json`, so this spec leaves it out of the HTML and PDF.
3. **Time zone.** `generated_at` is UTC. The spec shows the local date only, so the engine should convert before formatting.
4. **Fix text in fixtures** currently uses "→" in steps (per the §0.8 example). The PDF renderer handles it, so no change is needed unless you would rather use ">" everywhere.
