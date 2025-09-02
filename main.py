from google_sheets_client import GoogleSheetClient
from pracuj_scraper import PracujScraper

import asyncio
from playwright.async_api import async_playwright


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        pracuj_scraper = PracujScraper(page, browser)
        await pracuj_scraper.navigate()
        await pracuj_scraper.accept_cookies()
        await pracuj_scraper.search("test python", None)
        await pracuj_scraper.sort_offers_from_newest()
        gc = GoogleSheetClient()
        gc.open_spreadsheet('job-offers')
        links = gc.get_worksheet(0).col_values(5)
        await pracuj_scraper.extract_job_data(links)
        jobs = pracuj_scraper.all_jobs
        gc = GoogleSheetClient()
        gc.open_spreadsheet('Example spreadsheet')
        columns = ["employer", "position", "earning", "requirements", "url", "status"]
        rows = [[job.get(col, "") for col in columns] for job in jobs]
        gc.get_worksheet(0).insert_rows(rows, 2)
asyncio.run(main())

