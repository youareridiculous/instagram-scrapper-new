# Instagram Profile Scraper 🔍

A safety-first Instagram profile scraper that finds users based on customizable filters. Designed to minimize ban risk with built-in rate limiting, human-like behavior, and conservative request patterns.

## ⚠️ Important Safety Notes

1. **Use a separate account** - Never use your main Instagram account
2. **Start conservative** - The default settings are very safe; adjust carefully
3. **Respect rate limits** - The scraper automatically enforces limits
4. **Manual outreach only** - This tool only collects usernames; you handle DMs manually

## 🚀 Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
playwright install firefox
playwright install chromium
```

Or run `./setup.sh`, which installs dependencies and both browsers.

### 2. Configure Credentials

Copy `.env.example` to `.env` and add your Instagram credentials:

```bash
cp .env.example .env
# Edit .env with your credentials
```

**⚠️ Use a separate account, not your main account!**

### 3. Configure Search & Filters

Edit `config.json` to set your search criteria and filters:

```json
{
  "search": {
    "hashtags": ["entrepreneur", "startup"],
    "locations": ["San Francisco, California"],
    "seed_accounts": ["some_account"],
    "use_explore": false
  },
  "filters": {
    "min_followers": 1000,
    "max_followers": 50000,
    "bio_keywords": ["founder", "entrepreneur"],
    "verified_only": false
  }
}
```

## 📖 Usage

### Web Interface (Recommended) 🌐

**Start the web dashboard:**

```bash
source venv/bin/activate
python3 web_interface.py
```

Then open your browser to: **http://localhost:5001**

The web interface provides:
- 📊 Real-time dashboard with progress tracking
- 📋 View all scraped profiles in a table
- ⚙️ Search & filters on the dashboard (save to `config.json`); optional **Advanced JSON** modal
- ▶️ Start/stop the scraper with one click
- 📈 Live statistics and progress updates
- 📥 Download CSV files from the dashboard (see **Google Sheets** below)

### Google Sheets (import from CSV)

1. Run a scrape and download `scraped_data/*.csv` from the web UI (or copy the file from disk).
2. In Google Sheets: **File → Import → Upload** and choose the CSV.
3. Pick “Replace spreadsheet” or “Insert new sheet” as you prefer.

### Manual smoke test (operator)

1. Fill `.env` with a **dedicated** Instagram test account.
2. **CLI:** `python instagram_scraper.py` (omit `--headless` the first time if login is flaky).
3. **Web:** `python web_interface.py` → open **http://localhost:5001** → Start → Stop.
4. Confirm a CSV appears under `scraped_data/` and downloads from the UI.
5. Import that CSV into Sheets using the steps above.

### Automated tests (developers)

```bash
pip install pytest
pytest -q
```

### Command Line Usage

```bash
python instagram_scraper.py
```

### With Command Line Arguments

```bash
python instagram_scraper.py --username your_username --password your_password
```

### Headless Mode (no browser window)

```bash
python instagram_scraper.py --headless
```

## 🔧 Configuration Options

### Search Methods

- **Hashtags**: Search profiles using specific hashtags
- **Locations**: Find profiles in specific locations
- **Seed Accounts**: Get followers of specific accounts
- **Explore Page**: Browse Instagram's explore page

### Filters

- `min_followers` / `max_followers`: Follower count range
- `min_following` / `max_following`: Following count range
- `min_posts` / `max_posts`: Post count range
- `bio_keywords`: Array of keywords that must appear in bio
- `verified_only`: Only verified accounts (true/false)
- `account_type`: "business" or "personal" (null for any)

## 📊 Output

Results are saved to `scraped_data/instagram_profiles_YYYYMMDD_HHMMSS.csv` with columns:

- username
- url
- followers
- following
- posts
- bio
- verified
- account_type
- profile_pic
- scraped_at

## 🛡️ Safety Features

1. **Rate Limiting**: Max 60 requests per hour (configurable)
2. **Random Delays**: 3-8 seconds between actions (mimics human behavior)
3. **Session Breaks**: Automatic breaks every 100 profiles
4. **Human-like Scrolling**: Smooth, random scrolling patterns
5. **Stealth Mode**: Removes automation indicators
6. **Error Handling**: Graceful handling of blocks/errors
7. **Progress Tracking**: Avoids re-scraping same profiles

## ⚙️ Adjusting Safety Settings

Edit the `SafeInstagramScraper` class in `instagram_scraper.py`:

```python
self.min_delay = 3  # Minimum seconds between actions
self.max_delay = 8  # Maximum seconds between actions
self.max_requests_per_hour = 60  # Conservative limit
self.session_break_interval = 100  # Break after N profiles
self.break_duration = 300  # Break duration in seconds
```

**⚠️ Be careful when reducing these values - lower = higher ban risk!**

## 📝 Example Configurations

### Find Local Entrepreneurs

```json
{
  "search": {
    "locations": ["New York, New York"],
    "hashtags": ["entrepreneur", "startup", "founder"]
  },
  "filters": {
    "min_followers": 500,
    "max_followers": 10000,
    "bio_keywords": ["founder", "CEO", "entrepreneur"]
  }
}
```

### Find Influencers in a Niche

```json
{
  "search": {
    "hashtags": ["fitness", "workout", "gym"],
    "seed_accounts": ["fitness_influencer"]
  },
  "filters": {
    "min_followers": 5000,
    "max_followers": 100000,
    "min_posts": 50
  }
}
```

## 🐛 Troubleshooting

### Login Fails
- Check credentials in `.env`
- Try running without `--headless` to see what's happening
- Instagram may require 2FA - handle manually first

### Rate Limited
- The scraper will automatically wait
- Increase delays in safety settings
- Reduce `max_requests_per_hour`

### No Results
- Check your filters aren't too restrictive
- Verify search terms are valid
- Try with fewer filters first

## ⚖️ Legal & Ethical

- This tool is for personal use only
- Respect Instagram's Terms of Service
- Use collected data responsibly
- Don't spam or harass users
- Consider privacy implications

## 📄 License

This tool is provided as-is for educational purposes. Use at your own risk.

