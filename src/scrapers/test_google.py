import asyncio
from playwright.async_api import async_playwright
import urllib.parse
import re

async def test_google_dork():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        # Test Instagram
        query = urllib.parse.quote('"DAZN" site:instagram.com')
        await page.goto(f"https://www.google.com/search?q={query}")
        await page.wait_for_timeout(2000)
        
        # Extract snippets
        snippets = await page.query_selector_all('div.VwiC3b')
        for s in snippets:
            text = await s.inner_text()
            print(f"Insta Snippet: {text}")
            
        # Test LinkedIn
        query = urllib.parse.quote('"DAZN" site:linkedin.com/company')
        await page.goto(f"https://www.google.com/search?q={query}")
        await page.wait_for_timeout(2000)
        
        snippets = await page.query_selector_all('div.VwiC3b')
        for s in snippets:
            text = await s.inner_text()
            print(f"LinkedIn Snippet: {text}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_google_dork())
