from google_sheets_client import GoogleSheetClient
from scrapers.justjoinit_scraper import JustJoinItScraper
from scrapers.pracuj_scraper import PracujScraper

import asyncio
from playwright.async_api import async_playwright

async def run_scraper(scraper_class, urls):
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        scraper = scraper_class(page, browser)
        await scraper.navigate()
        await scraper.accept_cookies()
        await scraper.search("test python", None)
        await scraper.sort_offers_from_newest()
        await scraper.extract_job_data(urls)
        await browser.close()
        return scraper.all_jobs


async def main():


    gc = GoogleSheetClient()
    gc.open_spreadsheet('job-offers')
    worksheet = gc.spreadsheet.get_worksheet(0)
    pracuj_urls = worksheet.col_values(5)
    worksheet = gc.spreadsheet.get_worksheet(1)
    justjoinit_urls = worksheet.col_values(5)
    tasks = [
        run_scraper(PracujScraper, pracuj_urls),
        run_scraper(JustJoinItScraper, justjoinit_urls)
    ]
    jobs = await asyncio.gather(*tasks)

    for i, job_list in enumerate(jobs):
        columns = ["employer", "position", "earning", "requirements", "url", "status"]
        rows = [[offer.get(col, "") for col in columns] for offer in job_list]
        worksheet = gc.spreadsheet.get_worksheet(i)
        worksheet.insert_rows(rows, 2)

asyncio.run(main())

