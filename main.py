from google_sheets_client import GoogleSheetClient
from scrapers.config import ScraperConfig
from scrapers.justjoinit_scraper import JustJoinItScraper
from scrapers.pracuj_scraper import PracujScraper
import asyncio
from playwright.async_api import async_playwright

async def run_scraper(scraper_class, urls, config, sem=None):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        scraper = scraper_class(page, browser, config.max_open_pages)
        await scraper.navigate()
        await scraper.accept_cookies()
        await scraper.search(config.search_keywords, "Łódź")
        await scraper.sort_offers_from_newest()
        await scraper.extract_job_data(urls)
        await browser.close()
        return scraper.all_jobs


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
        columns = ["employer", "position", "earning", "requirements", "url", "status"]
        rows = [[offer.get(col, "") for col in columns] for offer in job_list]
        worksheet = gc.spreadsheet.get_worksheet(i)
        worksheet.insert_rows(rows, 2)

asyncio.run(main())

