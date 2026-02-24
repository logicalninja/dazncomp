import asyncio
import httpx
from bs4 import BeautifulSoup
import re

def scrape_app_store(url):
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    response = httpx.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Let's find any text matching X.X out of 5 and X.XK Ratings
    rating_text = soup.find(string=re.compile(r'\d\.\d out of 5'))
    count_text = soup.find(string=re.compile(r'\d+[KM]* Ratings'))
    
    print(f"App Store Rating string found: {rating_text}")
    print(f"App Store Count string found: {count_text}")
    
    if not rating_text:
        # Fallback to look at figure class="we-star-rating"
        star_rating = soup.select_one('.we-customer-ratings__averages__display')
        print(f"Fallback star rating: {star_rating}")

def scrape_play_store(url):
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    response = httpx.get(url, headers=headers)
    
    # Rating is in a div with itemprop="starRating" usually.
    # Reviews contain text like "1.1M reviews"
    match = re.search(r'([\d\.]+)star', response.text)
    print(f"Play Store Rating Regex: {match.group(1) if match else 'None'}")
    
    count_match = re.search(r'([\d\.KM]+)\s*reviews\b', response.text, re.IGNORECASE)
    print(f"Play Store Count Regex: {count_match.group(1) if count_match else 'None'}")

if __name__ == "__main__":
    scrape_app_store("https://apps.apple.com/us/app/dazn-live-sports-streaming/id1129525015")
    scrape_play_store("https://play.google.com/store/apps/details?id=com.dazn")
