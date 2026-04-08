# Build status: current state vs target

## Target

- Run locally via **CLI** and/or **browser** (Flask on **port 5001**).
- UI for status, config, results, and **CSV download**.
- Practical **Google Sheets** path: import downloaded CSV (**File → Import → Upload**).

## Shipped on `main` (this revision)

- **Discovery:** Usernames from hashtag / location / explore are resolved by opening **post/reel URLs** and reading the author handle (not `split('/')[1]` on `/p/…`).
- **Web runner:** Same pipeline as CLI — `SafeInstagramScraper.run(..., progress=scraper_status)` from a **daemon thread** with `asyncio.run` (no `create_task` in Flask).
- **Cooperative stop:** `scraper_status['running']` checked during discovery and scraping; `max_profiles_per_session` enforced in the scrape loop.
- **CSV API safety:** `is_safe_csv_filename` + `resolve_csv_path` for `/api/download/` and `/api/results/<filename>`.
- **Overlap guard:** `threading.Lock` + alive check before starting another run.
- **UI:** Lists CSV files with download links + Sheets hint.
- **CI:** `.github/workflows/ci.yml` — `compileall` + `pytest` (no Instagram E2E).
- **Tests:** `tests/test_scraper_utils.py`, `tests/test_web_interface_security.py`.
- **Deps:** Removed unused `beautifulsoup4` / `lxml`.
- **Setup:** `setup.sh` installs **Firefox and Chromium** for Playwright.

## Still manual / fragile

- **Instagram DOM** changes can break login, profile parsing, or author resolution — re-test after IG updates.
- **No automated E2E** against Instagram in CI (by design).
- **Stop** is cooperative (may finish a slow navigation before exiting).

## Quick verify

```bash
pip install -r requirements.txt && pip install pytest
pytest -q && python -m compileall instagram_scraper.py web_interface.py tests
```

Update this file when behavior or scope changes materially.
