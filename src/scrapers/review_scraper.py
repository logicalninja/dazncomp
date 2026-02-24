import httpx
from bs4 import BeautifulSoup
from loguru import logger
from typing import List, Dict, Any, Optional
from datetime import datetime
import urllib.parse
from google_play_scraper import Sort, reviews as gplay_reviews

class ReviewScraper:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
        # Using longer timeout for paginated scraping
        self.client = httpx.Client(headers=self.headers, follow_redirects=True, timeout=25.0)

    def scrape_trustpilot_reviews(self, competitor_name: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Scrape text reviews from Trustpilot with pagination."""
        collected_reviews = []
        try:
            domain = self._get_trustpilot_domain(competitor_name)
            if not domain:
                return []
                
            page = 1
            while len(collected_reviews) < limit:
                url = f"https://www.trustpilot.com/review/{domain}?page={page}"
                logger.info(f"Targeting Trustpilot (Page {page}): {url}")
                
                response = self.client.get(url)
                if response.status_code != 200:
                    break
                    
                soup = BeautifulSoup(response.text, 'html.parser')
                review_cards = soup.select('article')
                
                if not review_cards:
                    break # No more reviews
                    
                for card in review_cards:
                    if len(collected_reviews) >= limit:
                        break
                        
                    # Extract Rating
                    rating_img = card.select_one('img[alt^="Rated"]')
                    star_rating = 0.0
                    if rating_img:
                        alt_text = rating_img['alt']
                        if 'out of 5' in alt_text:
                            star_rating = float(alt_text.split(' ')[1])
                            
                    # Extract Review Text
                    content_p = card.select_one('p[data-service-review-text-typography="true"]')
                    review_text = content_p.text.strip() if content_p else ""
                    
                    if not review_text: continue # Skip empty reviews
                    
                    # Extract Date
                    date_element = card.select_one('time')
                    review_date = date_element['datetime'] if date_element and 'datetime' in date_element.attrs else datetime.now().isoformat()
                    
                    # Extract Author
                    author_span = card.select_one('span[data-consumer-name-typography="true"]')
                    author = author_span.text.strip() if author_span else "Anonymous"
                    
                    # Extract Developer Response
                    response_text, response_date = "", ""
                    reply_p = card.select_one('p[data-service-review-business-reply-text-typography="true"]')
                    if reply_p:
                        response_text = reply_p.text.strip()
                        times = card.select('time')
                        if len(times) > 1 and 'datetime' in times[1].attrs:
                            response_date = times[1]['datetime']
                        else:
                            response_date = datetime.now().isoformat()
                    
                    collected_reviews.append({
                        "review_date": review_date,
                        "star_rating": star_rating,
                        "review_text": review_text,
                        "author": author,
                        "response_text": response_text,
                        "response_date": response_date
                    })
                page += 1
                
        except Exception as e:
            logger.error(f"Trustpilot review scrape failed for {competitor_name}: {e}")
            
        return collected_reviews

    def _get_trustpilot_domain(self, competitor_name: str) -> Optional[str]:
        """Helper to find Trustpilot domain."""
        try:
            search_url = f"https://www.trustpilot.com/search?query={urllib.parse.quote(competitor_name)}"
            response = self.client.get(search_url)
            soup = BeautifulSoup(response.text, 'html.parser')
            link = soup.select_one('a[name="business-unit-card"]')
            if link and 'href' in link.attrs:
                return link['href'].split('/')[-1]
            return None
        except:
            return None

    def scrape_play_store_reviews(self, competitor_name: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Scrape text reviews from Google Play Store using google-play-scraper."""
        collected_reviews = []
        try:
            app_id = self._get_play_store_id(competitor_name)
            if not app_id:
                return []
                
            logger.info(f"Targeting Google Play Store App ID: {app_id}")
            result, _ = gplay_reviews(
                app_id,
                lang='en', 
                country='us', 
                sort=Sort.NEWEST, 
                count=limit
            )
            
            for item in result:
                collected_reviews.append({
                    "review_date": item.get('at').isoformat() if item.get('at') else datetime.now().isoformat(),
                    "star_rating": float(item.get('score', 0)),
                    "review_text": item.get('content', ''),
                    "author": item.get('userName', 'Anonymous'),
                    "response_text": item.get('replyContent', ''),
                    "response_date": item.get('repliedAt').isoformat() if item.get('repliedAt') else ""
                })
                
        except Exception as e:
            logger.error(f"Play Store review scrape failed for {competitor_name}: {e}")
            
        return collected_reviews

    def _get_play_store_id(self, competitor_name: str) -> Optional[str]:
        """Helper to find Play Store package ID."""
        try:
            search_url = f"https://play.google.com/store/search?q={urllib.parse.quote(competitor_name)}&c=apps"
            response = self.client.get(search_url)
            soup = BeautifulSoup(response.text, 'html.parser')
            link = soup.select_one('a[href^="/store/apps/details?id="]')
            if link:
                return link['href'].split('id=')[-1].split('&')[0]
            return None
        except:
            return None

    def scrape_app_store_reviews(self, competitor_name: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Scrape text reviews from Apple App Store using iTunes RSS feed."""
        collected_reviews = []
        try:
            # 1. Get App ID from iTunes Search API
            app_id = self._get_app_store_id(competitor_name)
            if not app_id:
                return []
                
            logger.info(f"Targeting Apple App Store App ID: {app_id}")
            
            # 2. Fetch from RSS feed (50 reviews per page max, up to 10 pages)
            max_pages = min(10, (limit // 50) + 1)
            for page in range(1, max_pages + 1):
                url = f"https://itunes.apple.com/us/rss/customerreviews/page={page}/id={app_id}/sortby=mostrecent/json"
                response = self.client.get(url)
                if response.status_code != 200:
                    break
                    
                data = response.json()
                entries = data.get('feed', {}).get('entry', [])
                if not entries:
                    break
                    
                # Skip the first entry if it's the app metadata (usually has no rating)
                if page == 1 and entries and not entries[0].get('im:rating'):
                    entries = entries[1:]
                    
                for item in entries:
                    if len(collected_reviews) >= limit:
                        break
                        
                    star_rating = float(item.get('im:rating', {}).get('label', 0))
                    review_text = item.get('content', {}).get('label', '')
                    author = item.get('author', {}).get('name', {}).get('label', 'Anonymous')
                    review_date = item.get('updated', {}).get('label', datetime.now().isoformat())
                    
                    collected_reviews.append({
                        "review_date": review_date,
                        "star_rating": star_rating,
                        "review_text": review_text,
                        "author": author
                    })
                
                if len(collected_reviews) >= limit:
                    break
                    
        except Exception as e:
            logger.error(f"App Store review scrape failed for {competitor_name}: {e}")
            
        return collected_reviews

    def _get_app_store_id(self, competitor_name: str) -> Optional[str]:
        """Helper to find App Store ID."""
        try:
            search_url = f"https://itunes.apple.com/search?term={urllib.parse.quote(competitor_name)}&entity=software&limit=1"
            response = self.client.get(search_url)
            data = response.json()
            if data.get('resultCount', 0) > 0:
                return str(data['results'][0]['trackId'])
            return None
        except:
            return None

    def close(self):
        self.client.close()
