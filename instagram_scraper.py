#!/usr/bin/env python3
"""
Instagram Profile Scraper with Safety Features
Safely scrapes Instagram profiles based on customizable filters
"""

import asyncio
import csv
import json
import random
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set
import os
from dotenv import load_dotenv

from playwright.async_api import async_playwright, Page, Browser, BrowserContext
import pandas as pd

# Load environment variables
load_dotenv()

class SafeInstagramScraper:
    """
    Instagram scraper with built-in safety features to minimize ban risk
    """
    
    def __init__(self, username: str, password: str, headless: bool = True):
        self.username = username
        self.password = password
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
        # Safety settings - conservative defaults
        self.min_delay = 3  # Minimum seconds between actions
        self.max_delay = 8  # Maximum seconds between actions
        self.max_profiles_per_session = 50  # Stop after this many profiles
        self.session_break_interval = 100  # Take a break after this many profiles
        self.break_duration = 300  # 5 minutes break
        self.max_requests_per_hour = 60  # Conservative limit
        
        # Tracking
        self.scraped_profiles: Set[str] = set()
        self.request_count = 0
        self.session_start_time = time.time()
        self.profiles_collected: List[Dict] = []
        
        # Output directory
        self.output_dir = Path("scraped_data")
        self.output_dir.mkdir(exist_ok=True)
        
    async def safe_delay(self, min_seconds: Optional[float] = None, max_seconds: Optional[float] = None):
        """Random delay to mimic human behavior"""
        min_delay = min_seconds or self.min_delay
        max_delay = max_seconds or self.max_delay
        delay = random.uniform(min_delay, max_delay)
        await asyncio.sleep(delay)
        
    async def check_rate_limit(self):
        """Check if we're approaching rate limits"""
        elapsed = time.time() - self.session_start_time
        if elapsed > 3600:  # Reset hourly counter
            self.request_count = 0
            self.session_start_time = time.time()
            
        if self.request_count >= self.max_requests_per_hour:
            wait_time = 3600 - elapsed
            print(f"⚠️  Rate limit reached. Waiting {wait_time/60:.1f} minutes...")
            await asyncio.sleep(wait_time)
            self.request_count = 0
            self.session_start_time = time.time()
    
    async def human_like_scroll(self, page: Page, scrolls: int = 3):
        """Scroll like a human would"""
        for _ in range(scrolls):
            await page.evaluate("""
                window.scrollBy({
                    top: Math.random() * 500 + 300,
                    behavior: 'smooth'
                });
            """)
            await self.safe_delay(1, 3)
    
    async def init_browser(self):
        """Initialize browser with human-like settings"""
        try:
            playwright = await async_playwright().start()
            
            # Use Firefox (more stable on macOS) or Chromium
            try:
                # Try Firefox first (more stable on macOS)
                self.browser = await playwright.firefox.launch(
                    headless=self.headless
                )
            except Exception:
                # Fallback to Chromium if Firefox fails
                self.browser = await playwright.chromium.launch(
                    headless=self.headless,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--disable-dev-shm-usage',
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-gpu',
                    ]
                )
        except Exception as e:
            print(f"❌ Error initializing browser: {str(e)}")
            raise
        
        # Create context with realistic settings
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='en-US',
            timezone_id='America/New_York',
        )
        
        # Remove webdriver property
        await self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        self.page = await self.context.new_page()
        
    async def login(self):
        """Login to Instagram with safety delays"""
        print("🔐 Logging in to Instagram...")
        
        await self.page.goto("https://www.instagram.com/accounts/login/", wait_until="networkidle")
        await self.safe_delay(2, 4)
        
        # Enter username
        await self.page.fill('input[name="username"]', self.username)
        await self.safe_delay(1, 2)
        
        # Enter password
        await self.page.fill('input[name="password"]', self.password)
        await self.safe_delay(1, 2)
        
        # Click login
        await self.page.click('button[type="submit"]')
        await self.safe_delay(3, 5)
        
        # Handle "Save Your Login Info?" prompt
        try:
            not_now_button = self.page.locator('button:has-text("Not Now")').first
            if await not_now_button.is_visible(timeout=3000):
                await not_now_button.click()
                await self.safe_delay(2, 3)
        except:
            pass
        
        # Handle "Turn on Notifications" prompt
        try:
            not_now_button = self.page.locator('button:has-text("Not Now")').first
            if await not_now_button.is_visible(timeout=3000):
                await not_now_button.click()
                await self.safe_delay(2, 3)
        except:
            pass
        
        # Verify login
        if "instagram.com/accounts/login" not in self.page.url:
            print("✅ Login successful!")
            return True
        else:
            print("❌ Login failed. Please check credentials.")
            return False
    
    async def get_profile_data(self, username: str) -> Optional[Dict]:
        """Extract profile data from a profile page"""
        try:
            await self.check_rate_limit()
            self.request_count += 1
            
            url = f"https://www.instagram.com/{username}/"
            await self.page.goto(url, wait_until="networkidle", timeout=30000)
            await self.safe_delay(2, 4)
            
            # Wait for profile to load
            await self.page.wait_for_selector('header', timeout=10000)
            
            # Extract profile information
            profile_data = {
                'username': username,
                'url': url,
                'scraped_at': datetime.now().isoformat(),
            }
            
            # Get follower count
            try:
                follower_text = await self.page.locator('a[href*="/followers/"] span').first.inner_text()
                follower_count = self._parse_count(follower_text)
                profile_data['followers'] = follower_count
            except:
                profile_data['followers'] = None
            
            # Get following count
            try:
                following_text = await self.page.locator('a[href*="/following/"] span').first.inner_text()
                following_count = self._parse_count(following_text)
                profile_data['following'] = following_count
            except:
                profile_data['following'] = None
            
            # Get post count
            try:
                post_text = await self.page.locator('div:has-text("posts")').first.inner_text()
                post_count = self._parse_count(post_text.split()[0])
                profile_data['posts'] = post_count
            except:
                profile_data['posts'] = None
            
            # Get bio
            try:
                bio = await self.page.locator('header section div').nth(1).inner_text()
                profile_data['bio'] = bio.strip()
            except:
                profile_data['bio'] = None
            
            # Check if verified
            try:
                verified = await self.page.locator('svg[aria-label*="Verified"]').count() > 0
                profile_data['verified'] = verified
            except:
                profile_data['verified'] = False
            
            # Check account type (try to detect business/creator)
            try:
                category = await self.page.locator('div:has-text("Category")').first.inner_text()
                profile_data['account_type'] = 'business'
            except:
                profile_data['account_type'] = 'personal'
            
            # Get profile picture URL
            try:
                img = await self.page.locator('header img').first.get_attribute('src')
                profile_data['profile_pic'] = img
            except:
                profile_data['profile_pic'] = None
            
            return profile_data
            
        except Exception as e:
            print(f"⚠️  Error scraping {username}: {str(e)}")
            return None
    
    def _parse_count(self, text: str) -> Optional[int]:
        """Parse follower/following/post counts (handles K, M suffixes)"""
        if not text:
            return None
        text = text.replace(',', '').strip()
        if 'K' in text:
            return int(float(text.replace('K', '')) * 1000)
        elif 'M' in text:
            return int(float(text.replace('M', '')) * 1000000)
        else:
            try:
                return int(text)
            except:
                return None
    
    def matches_filters(self, profile: Dict, filters: Dict) -> bool:
        """Check if profile matches all specified filters"""
        if not profile:
            return False
        
        # Follower count filter
        if 'min_followers' in filters and filters['min_followers']:
            if not profile.get('followers') or profile['followers'] < filters['min_followers']:
                return False
        
        if 'max_followers' in filters and filters['max_followers']:
            if not profile.get('followers') or profile['followers'] > filters['max_followers']:
                return False
        
        # Following count filter
        if 'min_following' in filters and filters['min_following']:
            if not profile.get('following') or profile['following'] < filters['min_following']:
                return False
        
        if 'max_following' in filters and filters['max_following']:
            if not profile.get('following') or profile['following'] > filters['max_following']:
                return False
        
        # Post count filter
        if 'min_posts' in filters and filters['min_posts']:
            if not profile.get('posts') or profile['posts'] < filters['min_posts']:
                return False
        
        if 'max_posts' in filters and filters['max_posts']:
            if not profile.get('posts') or profile['posts'] > filters['max_posts']:
                return False
        
        # Bio keywords filter
        if 'bio_keywords' in filters and filters['bio_keywords']:
            bio = (profile.get('bio') or '').lower()
            keywords = [k.lower() for k in filters['bio_keywords']]
            if not any(keyword in bio for keyword in keywords):
                return False
        
        # Verified filter
        if 'verified_only' in filters and filters['verified_only']:
            if not profile.get('verified'):
                return False
        
        # Account type filter
        if 'account_type' in filters and filters['account_type']:
            if profile.get('account_type') != filters['account_type']:
                return False
        
        return True
    
    async def search_by_hashtag(self, hashtag: str, max_profiles: int = 50) -> List[str]:
        """Search for profiles using a hashtag"""
        print(f"🔍 Searching hashtag: #{hashtag}")
        usernames = []
        
        try:
            url = f"https://www.instagram.com/explore/tags/{hashtag}/"
            await self.page.goto(url, wait_until="networkidle")
            await self.safe_delay(3, 5)
            
            # Scroll to load more posts
            for _ in range(5):
                await self.human_like_scroll(self.page, 2)
                await self.safe_delay(2, 4)
            
            # Extract usernames from posts
            post_links = await self.page.locator('a[href*="/p/"]').all()
            for link in post_links[:max_profiles]:
                href = await link.get_attribute('href')
                if href:
                    # Extract username from post URL
                    parts = href.split('/')
                    if len(parts) >= 2:
                        username = parts[1]
                        if username and username not in usernames:
                            usernames.append(username)
            
            print(f"✅ Found {len(usernames)} profiles from hashtag")
            return usernames[:max_profiles]
            
        except Exception as e:
            print(f"⚠️  Error searching hashtag: {str(e)}")
            return []
    
    async def search_by_location(self, location: str, max_profiles: int = 50) -> List[str]:
        """Search for profiles by location"""
        print(f"🔍 Searching location: {location}")
        usernames = []
        
        try:
            # Search for location
            search_url = f"https://www.instagram.com/explore/locations/"
            await self.page.goto(search_url, wait_until="networkidle")
            await self.safe_delay(2, 4)
            
            # Use search bar
            search_input = self.page.locator('input[placeholder*="Search"]').first
            await search_input.fill(location)
            await self.safe_delay(2, 3)
            
            # Click first result
            first_result = self.page.locator('a[href*="/locations/"]').first
            if await first_result.is_visible(timeout=5000):
                await first_result.click()
                await self.safe_delay(3, 5)
                
                # Scroll to load posts
                for _ in range(5):
                    await self.human_like_scroll(self.page, 2)
                    await self.safe_delay(2, 4)
                
                # Extract usernames
                post_links = await self.page.locator('a[href*="/p/"]').all()
                for link in post_links[:max_profiles]:
                    href = await link.get_attribute('href')
                    if href:
                        parts = href.split('/')
                        if len(parts) >= 2:
                            username = parts[1]
                            if username and username not in usernames:
                                usernames.append(username)
            
            print(f"✅ Found {len(usernames)} profiles from location")
            return usernames[:max_profiles]
            
        except Exception as e:
            print(f"⚠️  Error searching location: {str(e)}")
            return []
    
    async def get_followers(self, username: str, max_followers: int = 100) -> List[str]:
        """Get followers of a specific account"""
        print(f"🔍 Getting followers of: @{username}")
        usernames = []
        
        try:
            url = f"https://www.instagram.com/{username}/followers/"
            await self.page.goto(url, wait_until="networkidle")
            await self.safe_delay(3, 5)
            
            # Scroll to load more followers
            scroll_count = 0
            while scroll_count < 10 and len(usernames) < max_followers:
                await self.human_like_scroll(self.page, 1)
                await self.safe_delay(2, 3)
                
                # Extract usernames
                follower_links = await self.page.locator('a[href^="/"]').all()
                for link in follower_links:
                    href = await link.get_attribute('href')
                    if href and href.startswith('/') and not href.startswith('//'):
                        follower_username = href.strip('/').split('/')[0]
                        if follower_username and follower_username not in usernames and follower_username != username:
                            usernames.append(follower_username)
                            if len(usernames) >= max_followers:
                                break
                
                scroll_count += 1
            
            print(f"✅ Found {len(usernames)} followers")
            return usernames[:max_followers]
            
        except Exception as e:
            print(f"⚠️  Error getting followers: {str(e)}")
            return []
    
    async def search_explore_page(self, max_profiles: int = 50) -> List[str]:
        """Get profiles from explore page"""
        print("🔍 Browsing explore page...")
        usernames = []
        
        try:
            await self.page.goto("https://www.instagram.com/explore/", wait_until="networkidle")
            await self.safe_delay(3, 5)
            
            # Scroll to load content
            for _ in range(5):
                await self.human_like_scroll(self.page, 2)
                await self.safe_delay(2, 4)
            
            # Extract usernames
            post_links = await self.page.locator('a[href*="/p/"]').all()
            for link in post_links[:max_profiles]:
                href = await link.get_attribute('href')
                if href:
                    parts = href.split('/')
                    if len(parts) >= 2:
                        username = parts[1]
                        if username and username not in usernames:
                            usernames.append(username)
            
            print(f"✅ Found {len(usernames)} profiles from explore")
            return usernames[:max_profiles]
            
        except Exception as e:
            print(f"⚠️  Error browsing explore: {str(e)}")
            return []
    
    async def scrape_profiles(self, usernames: List[str], filters: Dict) -> List[Dict]:
        """Scrape profile data for a list of usernames"""
        matching_profiles = []
        
        print(f"\n📊 Scraping {len(usernames)} profiles...")
        
        for i, username in enumerate(usernames, 1):
            if username in self.scraped_profiles:
                continue
                
            print(f"[{i}/{len(usernames)}] Scraping @{username}...")
            
            profile = await self.get_profile_data(username)
            await self.safe_delay()  # Delay between profiles
            
            if profile:
                self.scraped_profiles.add(username)
                
                if self.matches_filters(profile, filters):
                    matching_profiles.append(profile)
                    print(f"  ✅ Matches filters!")
                else:
                    print(f"  ⏭️  Doesn't match filters")
            
            # Take a break periodically
            if i % self.session_break_interval == 0:
                print(f"⏸️  Taking a {self.break_duration/60:.1f} minute break...")
                await asyncio.sleep(self.break_duration)
        
        return matching_profiles
    
    def save_to_csv(self, profiles: List[Dict], filename: Optional[str] = None):
        """Save profiles to CSV file"""
        if not profiles:
            print("⚠️  No profiles to save")
            return
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"instagram_profiles_{timestamp}.csv"
        
        filepath = self.output_dir / filename
        
        df = pd.DataFrame(profiles)
        df.to_csv(filepath, index=False)
        
        print(f"✅ Saved {len(profiles)} profiles to {filepath}")
    
    async def run(self, search_config: Dict, filters: Dict):
        """Main execution method"""
        try:
            await self.init_browser()
            
            if not await self.login():
                return
            
            all_usernames = []
            
            # Collect usernames from different search methods
            if 'hashtags' in search_config:
                for hashtag in search_config['hashtags']:
                    usernames = await self.search_by_hashtag(hashtag, search_config.get('max_per_hashtag', 50))
                    all_usernames.extend(usernames)
                    await self.safe_delay(5, 10)  # Longer delay between searches
            
            if 'locations' in search_config:
                for location in search_config['locations']:
                    usernames = await self.search_by_location(location, search_config.get('max_per_location', 50))
                    all_usernames.extend(usernames)
                    await self.safe_delay(5, 10)
            
            if 'seed_accounts' in search_config:
                for account in search_config['seed_accounts']:
                    usernames = await self.get_followers(account, search_config.get('max_per_account', 100))
                    all_usernames.extend(usernames)
                    await self.safe_delay(5, 10)
            
            if 'use_explore' in search_config and search_config['use_explore']:
                usernames = await self.search_explore_page(search_config.get('max_explore', 50))
                all_usernames.extend(usernames)
            
            # Remove duplicates
            unique_usernames = list(dict.fromkeys(all_usernames))
            print(f"\n📋 Found {len(unique_usernames)} unique profiles to check")
            
            # Scrape and filter profiles
            matching_profiles = await self.scrape_profiles(unique_usernames, filters)
            
            # Save results
            if matching_profiles:
                self.save_to_csv(matching_profiles)
            else:
                print("⚠️  No profiles matched your filters")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
        finally:
            if self.browser:
                await self.browser.close()


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Instagram Profile Scraper')
    parser.add_argument('--username', help='Instagram username', default=os.getenv('INSTAGRAM_USERNAME'))
    parser.add_argument('--password', help='Instagram password', default=os.getenv('INSTAGRAM_PASSWORD'))
    parser.add_argument('--config', help='JSON config file', default='config.json')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode')
    
    args = parser.parse_args()
    
    if not args.username or not args.password:
        print("❌ Please provide username and password via --username/--password or .env file")
        print("\nTo set credentials:")
        print("1. Edit .env file and add:")
        print("   INSTAGRAM_USERNAME=your_username")
        print("   INSTAGRAM_PASSWORD=your_password")
        print("\n2. Or use command line:")
        print("   python3 instagram_scraper.py --username your_username --password your_password")
        return
    
    if args.username == "your_username_here" or args.password == "your_password_here":
        print("❌ Please update .env file with your actual Instagram credentials")
        print("⚠️  Remember: Use a separate account, not your main account!")
        return
    
    # Load config
    if Path(args.config).exists():
        with open(args.config, 'r') as f:
            config = json.load(f)
    else:
        print(f"⚠️  Config file {args.config} not found. Using defaults.")
        config = {
            "search": {
                "hashtags": [],
                "locations": [],
                "seed_accounts": [],
                "use_explore": False
            },
            "filters": {}
        }
    
    scraper = SafeInstagramScraper(args.username, args.password, headless=args.headless)
    await scraper.run(config.get('search', {}), config.get('filters', {}))


if __name__ == "__main__":
    asyncio.run(main())

