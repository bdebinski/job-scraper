from unittest.mock import AsyncMock, MagicMock

import pytest

from scrapers.base_scraper import BaseScraper


class DummyScraper(BaseScraper):
    async def search(self, keywords, location): ...
    async def jobs_list(self): ...
    async def extract_job_data(self, offer_links_from_sheet): ...
    async def next_page(self): ...
    async def accept_cookies(self): ...
    async def max_page(self): ...
    async def scrape_single_offer(self, url): ...

@pytest.fixture
def dummy_scraper():
    fake_browser = MagicMock()
    fake_page = MagicMock()
    fake_page.goto = AsyncMock()
    fake_locator = AsyncMock()
    fake_page.locator.return_value = fake_locator

    scraper = DummyScraper(page=fake_page, browser=fake_browser)
    return scraper

@pytest.mark.parametrize("input_url, expected", [
    ('http://example.com/job?id=123&location=test', 'http://example.com/job'),
    ('http://example.com/job', 'http://example.com/job')
])
def test_strip_url(input_url, expected):
    result = BaseScraper.strip_url(input_url)
    assert result == expected

@pytest.mark.asyncio
async def test_go_to_page():
    fake_page = AsyncMock()
    fake_browser = AsyncMock()

    scraper = DummyScraper(page=fake_page, browser=fake_browser)

    test_url = 'http://example.com/job?id=123&location=test'

    await scraper.go_to_page(test_url)
    fake_page.goto.assert_awaited_once_with(test_url)

@pytest.mark.asyncio
async def test_type_text(dummy_scraper):
    locator_str = "input#test"
    test_text = "blahblah"

    await dummy_scraper.type_text(locator_str, test_text)

    dummy_scraper.page.locator.assert_called_once_with(locator_str)
    dummy_scraper.page.locator.return_value.type.assert_awaited_once_with(test_text)

@pytest.mark.asyncio
async def test_click_locator(dummy_scraper):
    locator_str = "input#test"
    await dummy_scraper.click_locator(locator_str)
    dummy_scraper.page.locator.assert_called_once_with(locator_str)
    dummy_scraper.page.locator.return_value.click.assert_awaited_once()