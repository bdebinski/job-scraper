import json
from asyncio import timeout

import playwright
from playwright.sync_api import sync_playwright

from pracuj_scraper import PracujScraper

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    pracuj_scraper = PracujScraper(page)
    pracuj_scraper.navigate()
    pracuj_scraper.accept_cookies()
    pracuj_scraper.search("test python", None)
    pracuj_scraper.get_offer_data()
    pracuj_scraper.page.pause()
    jobs = pracuj_scraper.all_jobs

    import gspread

    gc = gspread.oauth()
    columns = ["employer", "position", "earning", "requirements", "url", "status"]

    rows = [[job.get(col, "") for col in columns] for job in jobs]
    sh = gc.open("Example spreadsheet")
    worksheet = sh.get_worksheet(0)
    worksheet.insert_rows(columns, 1)
    # check if offer is unique
    worksheet.insert_rows(rows, 2)
    # pracuj_scraper.page.pause()
    # print(pracuj_scraper.page.locator("[data-test=\"top-pagination-max-page-number\"]").inner_text())