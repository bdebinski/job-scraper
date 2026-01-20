import asyncio

import pytest
from playwright.async_api import async_playwright

from scrapers.pracuj_scraper import PracujScraper


@pytest.fixture
async def browser_fixture():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False,
    args=[
        "--disable-blink-features=AutomationControlled",
        "--no-sandbox",
        "--disable-infobars"
    ])
        yield browser

@pytest.fixture
async def context_fixture(browser_fixture):
    context = await browser_fixture.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        viewport={"width": 1920, "height": 1080},
        locale="pl-PL"
    )
    yield context
    await context.close()

@pytest.fixture
async def page_fixture(context_fixture):
    page = await context_fixture.new_page()
    yield page
    await page.close()

@pytest.fixture
def pracuj_scraper(context_fixture, browser_fixture):
    return PracujScraper(context_fixture, browser_fixture)
