import asyncio

import pytest
from playwright.async_api import async_playwright

from scrapers.pracuj_scraper import PracujScraper


@pytest.fixture
async def browser():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        yield browser

@pytest.fixture
async def page(browser):
    page = await browser.new_page()
    yield page
    await page.close()

@pytest.fixture
def pracuj_scraper(browser, page):
    return PracujScraper(page, browser)
