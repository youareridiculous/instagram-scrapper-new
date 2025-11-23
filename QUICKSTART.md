# Quick Start Guide 🚀

## To See the Scraper in Action (Visible Browser)

### Step 1: Install Dependencies

```bash
cd /Users/ericlarson/Downloads/instagram-scraper

# Option A: Use the setup script
./setup.sh

# Option B: Manual setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

### Step 2: Add Your Instagram Credentials

Edit the `.env` file (use a **separate account**, not your main!):

```bash
nano .env
# or
open -e .env
```

Add:
```
INSTAGRAM_USERNAME=your_username_here
INSTAGRAM_PASSWORD=your_password_here
```

### Step 3: Configure Your Search (Optional)

Edit `config.json` to set what you want to search for and filter by.

### Step 4: Run the Scraper (Visible Mode)

**By default, the scraper runs in VISIBLE mode** (you'll see the browser):

```bash
# Activate virtual environment (if using venv)
source venv/bin/activate

# Run the scraper
python3 instagram_scraper.py
```

You'll see:
- A Chrome browser window open
- It will log into Instagram
- Navigate through pages
- Scroll and collect profiles
- All actions visible in real-time

### To Run in Headless Mode (No Browser Window)

If you want to run it without seeing the browser:

```bash
python3 instagram_scraper.py --headless
```

### Example with Command Line Credentials

```bash
python3 instagram_scraper.py --username your_username --password your_password
```

## What You'll See

When running, you'll see output like:
```
🔐 Logging in to Instagram...
✅ Login successful!
🔍 Searching hashtag: #entrepreneur
✅ Found 50 profiles from hashtag
📊 Scraping 50 profiles...
[1/50] Scraping @username1...
  ✅ Matches filters!
[2/50] Scraping @username2...
  ⏭️  Doesn't match filters
...
✅ Saved 15 profiles to scraped_data/instagram_profiles_20241121_092000.csv
```

## Troubleshooting

**If you see "ModuleNotFoundError":**
- Make sure you activated the virtual environment: `source venv/bin/activate`
- Install dependencies: `pip install -r requirements.txt`

**If login fails:**
- Check your credentials in `.env`
- Try running without `--headless` to see what's happening
- Instagram may require 2FA - handle that manually first

**To see more details:**
- Run without `--headless` to watch the browser
- Check the console output for progress

