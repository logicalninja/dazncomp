import httpx
import re

def scrape_app_store(url):
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    response = httpx.get(url, headers=headers)
    
    # Try generic JSON-LD matching
    match = re.search(r'"ratingValue"\s*:\s*([\d\.]+)', response.text)
    print(f"App Store ratingValue JSON-LD: {match.group(1) if match else 'None'}")
    
    match_count = re.search(r'"reviewCount"\s*:\s*([\d]+)', response.text)
    print(f"App Store reviewCount JSON-LD: {match_count.group(1) if match_count else 'None'}")

def scrape_play_store(url):
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    response = httpx.get(url, headers=headers)
    
    match = re.search(r'"ratingValue"\s*:\s*"?([\d\.]+)"?', response.text)
    print(f"Play Store ratingValue JSON-LD: {match.group(1) if match else 'None'}")
    
    match_count = re.search(r'"ratingCount"\s*:\s*"?([\d\.]+)"?', response.text)
    print(f"Play Store ratingCount JSON-LD: {match_count.group(1) if match_count else 'None'}")

if __name__ == "__main__":
    scrape_app_store("https://apps.apple.com/us/app/dazn-live-sports-streaming/id1129525015")
    scrape_play_store("https://play.google.com/store/apps/details?id=com.dazn")
