# Build status: current state vs target

This document reflects the **codebase as it exists in this repo** and what is still needed to reach the intended product. It is separate from older planning docs and should be updated when major pieces land.

## Target (where we want the scraper to be)

- **Run locally** from the **terminal** (CLI) and/or from a **web browser** (dashboard on localhost).
- **UI** to start/stop (or monitor), view progress, edit search/filters, and inspect scraped rows.
- **Easy export** of scraped username/profile lists to **CSV** and a practical path to **Google Sheets** (e.g. download CSV and import, or optional API-based push if configured).

---

## Current build (what exists today)

### Terminal / CLI (`instagram_scraper.py`)

- `SafeInstagramScraper` with Playwright: browser init (Firefox, Chromium fallback), login flow, delays and hourly request counting.
- Profile detail scraping (`get_profile_data`), filter matching (`matches_filters`), CSV write via pandas (`save_to_csv`).
- `run()` wires: hashtags → locations → seed-account followers → optional explore → dedupe → scrape → save.
- CLI entry point: loads `config.json` and `.env` / args, `--headless` flag.

### Web / UI (`web_interface.py` + `templates/index.html`)

- Flask app on **port 5001** (not 5000).
- Dashboard: status polling, start/stop buttons, JSON config editor, table of latest results.
- APIs: `/api/status`, `/api/config` (GET/POST), `/api/results`, per-file results, `/api/download/<filename>` for CSV.

### Config & setup

- `config.json` for search + filters; `.env.example` for credentials; `setup.sh` for venv + deps + `playwright install chromium`.

### Tests

- `test_browser.py` only verifies Playwright can open a page (Google); it does **not** test Instagram flows.

---

## Gaps (why it is not fully “there” yet)

### 1. Discovery → username list (core pipeline risk)

Hashtag, location, and explore helpers collect links to posts (`/p/<shortcode>/`) but derive a “username” from `href.split('/')[1]`, which is **`p`**, not a profile handle. **As written, discovery likely does not produce real usernames** unless Instagram serves different URL shapes than this code assumes.

**Implication:** Terminal and web runs may find few or wrong handles until discovery is fixed (e.g. resolve author from each post/reel page, or use profile links / embedded data with correct parsing).

### 2. Web runner ≠ CLI runner

`web_interface.py` duplicates scraper orchestration in `run_scraper_async` and only runs **hashtags and locations**, then profile scraping. It does **not** run **seed-account follower collection** or **explore** the way `SafeInstagramScraper.run()` does.

**Implication:** Browser UI and CLI are not equivalent; config keys for `seed_accounts` / `use_explore` are effectively ignored when starting from the web.

### 3. Starting the scraper from Flask

`/api/start` uses `asyncio.create_task(...)` from a synchronous Flask view. With a typical `app.run()` setup there is **often no running asyncio event loop**, so **background start may fail or behave unreliably**.

**Implication:** “Run from browser” may be broken or flaky until start is wired with a thread + `asyncio.run()`, Quart/async Flask, or similar.

### 4. Stop behavior

Stop sets a shared `running` flag; the scraper loop can exit on the next iteration but **does not cancel** active Playwright navigation. Comment in code acknowledges this.

**Implication:** Stop is “cooperative,” not immediate.

### 5. Safety knob not wired

`max_profiles_per_session` is defined on the class but **never used** in `scrape_profiles` or `run()`.

**Implication:** Session cap described in spirit is not enforced in code.

### 6. CSV today; Google Sheets not in code

CSV files land under `scraped_data/` and the UI can download via `/api/download/<filename>` **if** the user knows the filename. There is **no** built-in “push to Google Sheets” (would need service account or OAuth, env vars, and an API route or script).

**Implication:** Sheets is “manual import CSV” unless you add integration.

### 7. Dependencies vs usage

`beautifulsoup4` and `lxml` are in `requirements.txt` but **not imported** by the Python source; `csv` is imported in `instagram_scraper.py` but unused.

**Implication:** Optional cleanup; no functional blocker.

### 8. Fragile selectors

All Instagram interaction depends on **current DOM**. No automated regression tests against Instagram.

**Implication:** Login, profile parsing, and discovery may break after UI changes; fixes will be ongoing.

---

## Work remaining (checklist toward the target)

Use this as an implementation backlog; order can be adjusted.

| Priority | Item | Purpose |
|----------|------|--------|
| P0 | Fix username discovery from hashtag/location/explore (correct handle resolution) | Makes terminal + web runs actually populate real usernames |
| P0 | Make `/api/start` run async scraper reliably (e.g. daemon thread + `asyncio.run`) | Browser-based runs work on a normal Flask dev server |
| P1 | Unify web path with `SafeInstagramScraper.run()` (or shared helper) so seed accounts + explore match CLI | Same behavior from UI and terminal |
| P1 | Surface CSV export in the UI (list files, prominent “Download CSV” per run) | “Easy download” without guessing filenames |
| P2 | Enforce `max_profiles_per_session` in `scrape_profiles` (and/or config) | Matches safety expectations |
| P2 | Optional Google Sheets: document File → Import workflow **or** add `gspread` + service account + env-configured sheet ID | Sheets path without pretending CSV is enough for everyone |
| P3 | Stronger stop (cancel tasks / close browser promptly) | Better UX when stopping mid-run |
| P3 | Align docs: README port **5001** vs **5000**, or change code to 5000 | Less confusion |
| P3 | Real tests (smoke against Instagram or mocked pages) | Catch selector/discovery regressions |
| P3 | Remove unused deps/imports or use them | Tidier project |

---

## Quick verdict

- **Shell and features are largely sketched:** CLI module, Flask UI, config, CSV on disk.
- **End-to-end usability** depends on fixing **discovery**, **Flask/async start**, and **web–CLI parity**, then **polishing export** (UI + optional Sheets).

Update this file when P0/P1 items close so the “current build” section stays accurate.
