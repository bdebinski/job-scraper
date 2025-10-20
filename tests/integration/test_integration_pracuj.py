from unittest.mock import AsyncMock, MagicMock, patch, call
from playwright.async_api import TimeoutError as PlaywrightTimeoutError, Page, async_playwright, expect
import pytest

from scrapers.pracuj_scraper import PracujScraper

@pytest.fixture
def scraper_fixture() -> PracujScraper:
    fake_page = MagicMock(spec=Page)
    fake_browser = AsyncMock()
    scraper = PracujScraper(fake_page, fake_browser)
    return scraper


@pytest.mark.asyncio
async def test_get_employer_name_missing_element(tmp_path):
    html_path = tmp_path / "missing_employer_selector.html"
    html_path.write_text("""
            <!DOCTYPE html>
            <html><body><div id="job-title">Python Developer</div></body></html>
        """)
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        await page.goto(f"file://{html_path}")

        scraper = PracujScraper(page, browser)
        scraper.offer_employer_name = "#employer"

        with patch('scrapers.base_scraper.logger') as mock_logger:
            result = await scraper.get_employer_name(page)

        assert result == "Not found"
        mock_logger.warning.assert_called_once_with("Employer name not found")
        await browser.close()
