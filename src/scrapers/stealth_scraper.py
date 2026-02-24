import asyncio
from playwright.async_api import async_playwright
from loguru import logger
from typing import Dict, Any, Optional
import urllib.parse
import re

class StealthScraper:
    def __init__(self):
        self.playwright = None
        self.browser = None
        
    async def initialize(self):
        """Starts the browser with stealth-like arguments."""
        if not self.playwright:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-infobars",
                    "--window-size=1920,1080"
                ]
            )

    async def scrape_twitter(self, competitor_name: str) -> Optional[Dict[str, float]]:
        """Scrape Twitter/X for follower counts. (Highly susceptible to blocks without auth)"""
        await self.initialize()
        context = await self.browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
    async def _extract_count(self, url: str, selector: str, context, competitor_name: str, regex: str = None) -> float:
        """Helper to navigate and extract a count based on a generic selector or regex."""
        page = await context.new_page()
        try:
            logger.info(f"Targeting: {url}")
            await page.goto(url, wait_until="domcontentloaded", timeout=25000)
            await page.wait_for_timeout(3000) # Give SPA time to render
            
            count = 0.0
            html = await page.content()
            
            # Try regex on whole page first if provided (good for JSON-LD embedded data)
            if regex:
                match = re.search(regex, html, re.IGNORECASE)
                if match:
                    text = match.group(1).upper()
                    if 'M' in text: count = float(text.replace('M', '')) * 1000000
                    elif 'K' in text: count = float(text.replace('K', '')) * 1000
                    else:
                        clean_match = re.search(r'[\d\.,]+', text)
                        if clean_match: count = float(clean_match.group().replace(',', ''))
                    return count
            
            # Try CSS Selector
            if selector:
                element = await page.query_selector(selector)
                if element:
                    text = await element.inner_text()
                    text = text.upper()
                    if 'M' in text: count = float(text.replace('M', '')) * 1000000
                    elif 'K' in text: count = float(text.replace('K', '')) * 1000
                    else:
                        clean_match = re.search(r'[\d\.,]+', text)
                        if clean_match: count = float(clean_match.group().replace(',', ''))
                    return count

        except Exception as e:
            logger.error(f"Scrape failed for {competitor_name} at {url}: {e}")
        finally:
            await page.close()
            
        return 0.0

    async def scrape_twitter(self, competitor_name: str) -> Optional[Dict[str, float]]:
        await self.initialize()
        context = await self.browser.new_context(user_agent="Mozilla/5.0")
        url = f"https://x.com/{competitor_name.replace(' ', '')}"
        # Twitter regex looks for "followers_count":123456
        count = await self._extract_count(url, "a[href$='/followers'] span", context, competitor_name, r'"followers_count"\s*:\s*(\d+)')
        await context.close()
        return {"follower_count": count}
        
    async def scrape_instagram(self, competitor_name: str) -> Optional[Dict[str, float]]:
        await self.initialize()
        context = await self.browser.new_context(user_agent="Mozilla/5.0")
        url = f"https://www.instagram.com/{competitor_name.replace(' ', '')}"
        
        page = await context.new_page()
        try:
            logger.info(f"Targeting Instagram: {url}")
            await page.goto(url, wait_until="domcontentloaded", timeout=25000)
            await page.wait_for_timeout(3000)
            
            count = 0.0
            meta = await page.query_selector('meta[name="description"]')
            if meta:
                content = await meta.get_attribute('content')
                match = re.search(r'([\d\.,KMkm]+)\s*[Ff]ollowers', content)
                if match:
                    text = match.group(1).upper()
                    if 'M' in text: count = float(text.replace('M', '').replace(',','')) * 1000000
                    elif 'K' in text: count = float(text.replace('K', '').replace(',','')) * 1000
                    else:
                        clean_match = re.search(r'[\d\.,]+', text)
                        if clean_match: count = float(clean_match.group().replace(',', ''))
            return {"follower_count": count}
        except Exception as e:
            logger.error(f"Insta Scrape failed for {competitor_name}: {e}")
            return {"follower_count": 0.0}
        finally:
            await page.close()
            await context.close()

    async def scrape_tiktok(self, competitor_name: str) -> Optional[Dict[str, float]]:
        await self.initialize()
        context = await self.browser.new_context(user_agent="Mozilla/5.0")
        url = f"https://www.tiktok.com/@{competitor_name.replace(' ', '')}"
        count = await self._extract_count(url, "strong[data-e2e='followers-count']", context, competitor_name, r'"followerCount"\s*:\s*(\d+)')
        await context.close()
        return {"follower_count": count}

    async def scrape_youtube(self, competitor_name: str) -> Optional[Dict[str, float]]:
        await self.initialize()
        context = await self.browser.new_context(user_agent="Mozilla/5.0")
        url = f"https://www.youtube.com/@{competitor_name.replace(' ', '')}"
        # YouTube usually has "1.2M subscribers" text
        count = await self._extract_count(url, None, context, competitor_name, r'"subscriberCountText"\s*:\s*\{\s*"simpleText"\s*:\s*"([\d\.KM]+)\s*subscribers"')
        await context.close()
        return {"follower_count": count}

    async def scrape_facebook(self, competitor_name: str) -> Optional[Dict[str, float]]:
        await self.initialize()
        context = await self.browser.new_context(user_agent="Mozilla/5.0")
        url = f"https://www.facebook.com/{competitor_name.replace(' ', '')}"
        count = await self._extract_count(url, "a[href$='/followers/']", context, competitor_name, r'([\d\.KM]+)\s*followers')
        await context.close()
        return {"follower_count": count}

    async def scrape_linkedin(self, competitor_name: str) -> Optional[Dict[str, float]]:
        await self.initialize()
        context = await self.browser.new_context(user_agent="Mozilla/5.0")
        url = f"https://www.linkedin.com/company/{competitor_name.replace(' ', '-').lower()}"
        count = await self._extract_count(url, "div.org-top-card-summary-info-list__info-item", context, competitor_name, r'([\d\.,]+)\s*followers')
        await context.close()
        return {"follower_count": count}

    async def scrape_app_store(self, competitor_name: str) -> Optional[Dict[str, float]]:
        await self.initialize()
        context = await self.browser.new_context(user_agent="Mozilla/5.0")
        search_term = urllib.parse.quote(f"{competitor_name} app itunes")
        search_url = f"https://duckduckgo.com/?q={search_term}&t=h_&ia=web"
        
        page = await context.new_page()
        try:
            logger.info(f"Targeting Apple App Store via search: {competitor_name}")
            await page.goto(search_url, wait_until="domcontentloaded")
            await page.wait_for_timeout(2000)
            
            link = await page.query_selector("a[href*='apps.apple.com']")
            if not link:
                return None
            app_url = await link.get_attribute("href")
            
            star_rating = await self._extract_count(app_url, ".we-customer-ratings__averages__display", context, competitor_name, r'"ratingValue"\s*:\s*([\d\.]+)')
            review_count = await self._extract_count(app_url, ".we-customer-ratings__count", context, competitor_name, r'"reviewCount"\s*:\s*(\d+)')
            
            return {"star_rating": star_rating, "review_count": review_count}
        except Exception as e:
            logger.error(f"App Store scrape failed for {competitor_name}: {e}")
            return None
        finally:
            await page.close()
            await context.close()

    async def close(self):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
