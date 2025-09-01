from pracuj_scraper import PracujScraper

import asyncio
from playwright.async_api import async_playwright


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        pracuj_scraper = PracujScraper(page, browser)
        await pracuj_scraper.navigate()
        await pracuj_scraper.accept_cookies()
        await pracuj_scraper.search("test python", None)
        await pracuj_scraper.extract_job_data()
        jobs = pracuj_scraper.all_jobs
        print(jobs)

asyncio.run(main())