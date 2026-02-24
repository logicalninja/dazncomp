import os
import json
import asyncio
from loguru import logger
from data.storage import StorageManager
from scrapers.review_scraper import ReviewScraper

def load_competitors(config_path: str = "src/config/competitors.json") -> list[str]:
    with open(config_path, 'r') as f:
        data = json.load(f)
    return data.get("competitors", [])

def run_review_engine():
    logger.add("review_scraping_errors.log", rotation="10 MB", level="ERROR")
    logger.info("Initializing Phase 2: DAZN Deep Review Scraper Engine...")
    
    competitors = load_competitors()
    storage = StorageManager(output_dir="data")
    review_scraper = ReviewScraper()

    try:
        for competitor in competitors:
            logger.info(f"--- Processing Reviews for: {competitor} ---")
            
            # 1. Trustpilot
            tp_reviews = review_scraper.scrape_trustpilot_reviews(competitor, limit=100)
            logger.info(f"Found {len(tp_reviews)} Trustpilot reviews for {competitor}")
            for r in tp_reviews:
                storage.append_review(competitor, "Trustpilot", r['review_date'], r['star_rating'], r['review_text'], r['author'], r.get('response_date', ''), r.get('response_text', ''))
                
            # 2. Google Play Store
            gp_reviews = review_scraper.scrape_play_store_reviews(competitor, limit=100)
            logger.info(f"Found {len(gp_reviews)} Google Play Store reviews for {competitor}")
            for r in gp_reviews:
                storage.append_review(competitor, "Google Play Store", r['review_date'], r['star_rating'], r['review_text'], r['author'], r.get('response_date', ''), r.get('response_text', ''))
                
            # 3. Apple App Store
            as_reviews = review_scraper.scrape_app_store_reviews(competitor, limit=100)
            logger.info(f"Found {len(as_reviews)} Apple App Store reviews for {competitor}")
            for r in as_reviews:
                storage.append_review(competitor, "Apple App Store", r['review_date'], r['star_rating'], r['review_text'], r['author'], r.get('response_date', ''), r.get('response_text', ''))

    finally:
        review_scraper.close()
        logger.info("Deep Review Scraping pipeline completed successfully.")

if __name__ == "__main__":
    run_review_engine()
