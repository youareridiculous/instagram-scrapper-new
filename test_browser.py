#!/usr/bin/env python3
"""Simple test to verify browser works"""
import asyncio
from playwright.async_api import async_playwright

async def test():
    print("🌐 Testing browser...")
    playwright = await async_playwright().start()
    browser = await playwright.firefox.launch(headless=False)
    page = await browser.new_page()
    await page.goto("https://www.google.com")
    print("✅ Browser works! You should see Google in the browser window.")
    await asyncio.sleep(3)
    await browser.close()
    print("✅ Test complete!")

if __name__ == "__main__":
    asyncio.run(test())

