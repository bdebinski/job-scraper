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
                                              "--disable-infobars"
                                          ])
        context_args = {
            "viewport": {"width": 1920, "height": 1080},
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "locale": "pl-PL"
        }
        # TODO: resolve captcha
        if os.path.exists("state.json") and scraper_class==PracujScraper:
            print("Loading cookies from 'state.json'")
            context_args["storage_state"] = "state.json"
        context = await browser.new_context(
            **context_args
        )
        scraper = scraper_class(context, browser, 10)
        await scraper.navigate()
        await scraper.accept_cookies()
        await scraper.search(config.search_keywords, config.search_location)
        await scraper.sort_offers_from_newest()
        found_jobs = await scraper.extract_job_data(urls)
        await browser.close()
        return found_jobs


async def main():
    config = ScraperConfig.from_env()
    gc = GoogleSheetClient(config.credentials_path)
    gc.open_spreadsheet(config.spreadsheet_name)
    worksheet = gc.spreadsheet.get_worksheet(0)
    pracuj_urls = worksheet.col_values(5)
    worksheet = gc.spreadsheet.get_worksheet(1)
    justjoinit_urls = worksheet.col_values(5)
    tasks = [
        run_scraper(PracujScraper, pracuj_urls, config),
        run_scraper(JustJoinItScraper, justjoinit_urls, config)
    ]
    jobs = await asyncio.gather(*tasks)

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
