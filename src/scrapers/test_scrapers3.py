import httpx
from bs4 import BeautifulSoup
import re
import urllib.parse

def test_play_search(term):
    url = f"https://play.google.com/store/search?q={urllib.parse.quote(term)}&c=apps"
    headers = {"User-Agent": "Mozilla/5.0"}
    res = httpx.get(url, headers=headers)
    
    # find the first app link
    soup = BeautifulSoup(res.text, 'html.parser')
    link = soup.select_one('a[href^="/store/apps/details?id="]')
    if link:
        print(f"Found match: {link['href']}")
    else:
        print("No match found")

if __name__ == "__main__":
    test_play_search("DAZN")
    test_play_search("Sky Sports")
