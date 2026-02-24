import httpx
from bs4 import BeautifulSoup
from loguru import logger
from typing import Dict, Any, Optional
import urllib.parse
import re

class LightweightScraper:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
        self.client = httpx.Client(headers=self.headers, follow_redirects=True, timeout=15.0)

    def scrape_trustpilot(self, competitor_name: str) -> Optional[Dict[str, float]]:
        """Scraps Trustpilot for a given competitor name by searching their domain."""
        try:
            # Clean name for search (DAZN -> dazn.com usually)
            search_term = urllib.parse.quote(f"{competitor_name}")
            search_url = f"https://www.trustpilot.com/search?query={search_term}"
            
            response = self.client.get(search_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find the first search result link
            first_result = soup.select_one('a[name="business-unit-card"]')
            if not first_result:
                logger.warning(f"Could not find Trustpilot profile for {competitor_name}")
                return None
                
            profile_url = f"https://www.trustpilot.com{first_result['href']}"
            logger.info(f"Targeting Trustpilot profile: {profile_url}")
            
            # Fetch actual profile
            profile_response = self.client.get(profile_url)
            profile_response.raise_for_status()
            profile_soup = BeautifulSoup(profile_response.text, 'html.parser')
            
            # TrustScore
            score_element = profile_soup.select_one(".styles_trustScore__bQ5vk") or profile_soup.find("p", string=re.compile(r"TrustScore"))
            score = 0.0
            if score_element:
                # E.g. "TrustScore 1.2"
                match = re.search(r'[\d.]+', score_element.text)
                if match:
                    score = float(match.group())

            # Review count
            count_element = profile_soup.select_one(".styles_reviewsCount__zHyn8") or profile_soup.find("p", {"data-reviews-count-typography": True})
            count = 0.0
            if count_element:
                match = re.search(r'[\d,]+', count_element.text)
                if match:
                    count = float(match.group().replace(',', ''))
                    
            return {
                "star_rating": score,
                "review_count": count
            }
        except Exception as e:
            logger.error(f"Trustpilot scrape failed for {competitor_name}: {e}")
            return None
            
    def scrape_play_store(self, competitor_name: str) -> Optional[Dict[str, float]]:
        """Scraps Google Play Store for a given competitor name by searching their app."""
        try:
            # First search for the app
            search_term = urllib.parse.quote(competitor_name)
            search_url = f"https://play.google.com/store/search?q={search_term}&c=apps"
            
            response = self.client.get(search_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            link = soup.select_one('a[href^="/store/apps/details?id="]')
            if not link:
                logger.warning(f"Could not find Google Play Store app match for {competitor_name}")
                return None
                
            app_url = f"https://play.google.com{link['href']}"
            logger.info(f"Targeting Google Play Store profile: {app_url}")
            
            # Fetch actual app profile
            app_response = self.client.get(app_url)
            app_response.raise_for_status()
            
            # Using JSON-LD regex matching which is stable for Google Play
            rating_match = re.search(r'"ratingValue"\s*:\s*"?([\d\.]+)"?', app_response.text)
            count_match = re.search(r'"ratingCount"\s*:\s*"?([\d\.]+)"?', app_response.text)
            
            star_rating = float(rating_match.group(1)) if rating_match else 0.0
            review_count = float(count_match.group(1)) if count_match else 0.0
                    
            return {
                "star_rating": star_rating,
                "review_count": review_count
            }
        except Exception as e:
            logger.error(f"Google Play Store scrape failed for {competitor_name}: {e}")
            return None

    def close(self):
        self.client.close()
