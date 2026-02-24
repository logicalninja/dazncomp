import asyncio
import json
import os
from loguru import logger

from scrapers.http_scraper import LightweightScraper
from scrapers.stealth_scraper import StealthScraper
from data.storage import StorageManager

async def run_engine():
    logger.add("scraping_errors.log", rotation="10 MB", level="ERROR")
    logger.info("Initializing DAZN Competitor Analysis Scraper Engine...")

    # Load Config
    config_path = os.path.join(os.path.dirname(__file__), 'config/competitors.json')
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return

    competitors = config.get("competitors", [])
    
    # Initialize Core Components
    storage = StorageManager(output_dir="data")
    http_scraper = LightweightScraper()
    stealth_scraper = StealthScraper()

    try:
        # Phase 1: Lightweight HTTP Scraping (e.g. Trustpilot, Play Store)
        logger.info("Starting Lightweight HTTP Scraping pass...")
        for competitor in competitors:
            # Trustpilot
            logger.info(f"Processing Trustpilot for: {competitor}")
            tp_metrics = http_scraper.scrape_trustpilot(competitor)
            if tp_metrics:
                storage.append_metric(competitor, "Trustpilot", "star_rating", tp_metrics.get("star_rating", 0))
                storage.append_metric(competitor, "Trustpilot", "review_count", tp_metrics.get("review_count", 0))
                
            await asyncio.sleep(2)
            
            # Google Play Store
            logger.info(f"Processing Google Play Store for: {competitor}")
            gp_metrics = http_scraper.scrape_play_store(competitor)
            if gp_metrics:
                storage.append_metric(competitor, "Google Play Store", "star_rating", gp_metrics.get("star_rating", 0))
                storage.append_metric(competitor, "Google Play Store", "review_count", gp_metrics.get("review_count", 0))
                
            await asyncio.sleep(2)

        # Phase 2: Stealth Playwright Scraping (e.g. Twitter/X, Instagram, etc)
        logger.info("Starting Heavy Stealth Scraping pass...")
        for competitor in competitors:
            logger.info(f"Processing Stealth Targets for: {competitor}")
            
            # Twitter
            t_metrics = await stealth_scraper.scrape_twitter(competitor)
            if t_metrics: storage.append_metric(competitor, "Twitter", "follower_count", t_metrics.get("follower_count", 0))
            await asyncio.sleep(2)
            
            # Instagram
            i_metrics = await stealth_scraper.scrape_instagram(competitor)
            if i_metrics: storage.append_metric(competitor, "Instagram", "follower_count", i_metrics.get("follower_count", 0))
            await asyncio.sleep(2)
            
            # TikTok
            tk_metrics = await stealth_scraper.scrape_tiktok(competitor)
            if tk_metrics: storage.append_metric(competitor, "TikTok", "follower_count", tk_metrics.get("follower_count", 0))
            await asyncio.sleep(2)
            
            # YouTube
            y_metrics = await stealth_scraper.scrape_youtube(competitor)
            if y_metrics: storage.append_metric(competitor, "YouTube", "follower_count", y_metrics.get("follower_count", 0))
            await asyncio.sleep(2)
            
            # Facebook
            f_metrics = await stealth_scraper.scrape_facebook(competitor)
            if f_metrics: storage.append_metric(competitor, "Facebook", "follower_count", f_metrics.get("follower_count", 0))
            await asyncio.sleep(2)
            
            # LinkedIn
            l_metrics = await stealth_scraper.scrape_linkedin(competitor)
            if l_metrics: storage.append_metric(competitor, "LinkedIn", "follower_count", l_metrics.get("follower_count", 0))
            await asyncio.sleep(2)
            
            # App Store
            a_metrics = await stealth_scraper.scrape_app_store(competitor)
            if a_metrics: 
                storage.append_metric(competitor, "Apple App Store", "star_rating", a_metrics.get("star_rating", 0))
                storage.append_metric(competitor, "Apple App Store", "review_count", a_metrics.get("review_count", 0))
            
            await asyncio.sleep(5)  # Delay between competitors for stealth pass

    finally:
        # Cleanup
        logger.info("Cleaning up resources...")
        http_scraper.close()
        await stealth_scraper.close()
        
        # Output summary
        storage.export_summary()
        logger.info("Scraping Engine run complete.")

if __name__ == "__main__":
    asyncio.run(run_engine())
