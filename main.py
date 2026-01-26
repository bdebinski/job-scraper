import os

from google_sheets_client import GoogleSheetClient
from scrapers.config import ScraperConfig
from scrapers.justjoinit_scraper import JustJoinItScraper
from scrapers.pracuj_scraper import PracujScraper
import asyncio
from playwright.async_api import async_playwright

async def run_scraper(scraper_class, urls, config, sem=None):
    async with async_playwright() as p:

        browser = await p.chromium.launch(headless=False,                                          args=[
                                              "--disable-blink-features=AutomationControlled",
                                              "--no-sandbox",
                                              "--disable-infobars",
                                              "--disable-gpu",
                                              "--disable-dev-shm-usage",
                                          ])
        context_args = {
            "viewport": {"width": 1920, "height": 1080},
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "locale": "pl-PL",
            "record_video_dir": "reports/videos/",
            "record_video_size": {"width": 1920, "height": 1080}
        }

        # TODO: resolve captcha
        if os.path.exists("state.json") and scraper_class==PracujScraper:
            print("Loading cookies from 'state.json'")
            context_args["storage_state"] = "state.json"
        context = await browser.new_context(
            **context_args
        )
        scraper = scraper_class(context, browser, 2)
        print(f"go to {scraper_class}")
        await scraper.navigate()
        print(f"accept cookies {scraper_class}")
        await scraper.accept_cookies()
        print(f"search {scraper_class}")
        await scraper.search(config.search_keywords, config.search_location)
        print(f"sort {scraper_class}")
        await scraper.sort_offers_from_newest()
        print(f"extract {scraper_class}")
        found_jobs = await scraper.extract_job_data(urls)
        print(f"close browser {scraper_class}")
        await browser.close()
        return found_jobs


async def main():
    print("Starting main")
    config = ScraperConfig.from_env()
    gc = GoogleSheetClient(config.credentials_path)
    gc.open_spreadsheet(config.spreadsheet_name)
    print("GC client connected")
    worksheet = gc.spreadsheet.get_worksheet(0)
    pracuj_urls = worksheet.col_values(5)
    worksheet = gc.spreadsheet.get_worksheet(1)
    justjoinit_urls = worksheet.col_values(5)
    tasks = [
        run_scraper(PracujScraper, pracuj_urls, config),
        run_scraper(JustJoinItScraper, justjoinit_urls, config)
    ]
    print("Run scrapers")
    jobs = await asyncio.gather(*tasks)

    print("Add to google sheets")
    for i, job_list in enumerate(jobs):
        columns = ["employer", "position", "salary", "requirements", "url",
                   "status"]
        rows = []
        for offer in job_list:
            offer_dict = offer.model_dump()
            row = [offer_dict.get(col, "") for col in columns]
            rows.append(row)

        worksheet = gc.spreadsheet.get_worksheet(i)
        worksheet.insert_rows(rows, 2)
if __name__ == "__main__":
    asyncio.run(main())
