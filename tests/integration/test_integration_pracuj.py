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
async def test_scrape_single_offer(scraper_fixture):
    # Arrange
    scraper = scraper_fixture
    fake_page = AsyncMock()
    fake_locator = AsyncMock()
    scraper.browser.new_page = AsyncMock(return_value=fake_page)
    fake_page.goto = AsyncMock()
    fake_page.locator = MagicMock(return_value=fake_locator)
    fake_locator.click = AsyncMock()
    fake_page.close = AsyncMock()
    scraper.get_employer_name = AsyncMock(return_value="Test employer")
    scraper.get_position_name = AsyncMock(return_value="Test position")
    scraper.get_earning_amount = AsyncMock(return_value="1000 PLN")
    scraper.get_job_requirement = AsyncMock(return_value="Test requirements: Python")

    # Act
    result = await scraper.scrape_single_offer('https://example.com/job1')

    # Assert
    fake_page.goto.assert_awaited_once_with('https://example.com/job1')
    scraper.browser.new_page.assert_awaited_once()
    fake_locator.click.assert_awaited_once()
    fake_page.close.assert_awaited_once()
    scraper.get_employer_name.assert_awaited_once_with(fake_page)
    scraper.get_position_name.assert_awaited_once_with(fake_page)
    scraper.get_earning_amount.assert_awaited_once_with(fake_page)
    scraper.get_job_requirement.assert_awaited_once_with(fake_page)
    assert result == {
        "employer": "Test employer",
        "position": "Test position",
        "earning": "1000 PLN",
        "requirements": "Test requirements: Python",
        "url": 'https://example.com/job1'
    }

@pytest.mark.asyncio
@pytest.mark.parametrize("max_page, jobs_list, scrape_single_offer_await_count, next_page_await_count",
                         [(1,['url1'], 1, 0),
                          (4,['url1', 'url3'], 8, 3)])
async def test_extract_job_data_collects_all_jobs_across_pages(scraper_fixture, max_page, jobs_list,
                                                     scrape_single_offer_await_count,
                                                     next_page_await_count):
    # Arrange
    scraper = scraper_fixture
    with (patch.object(PracujScraper, "max_page", new_callable=AsyncMock) as mock_max_page,
        patch.object(PracujScraper, "jobs_list", new_callable=AsyncMock) as mock_jobs_list,
        patch.object(PracujScraper, "scrape_single_offer", new_callable=AsyncMock) as mock_scrape_single_offer,
        patch.object(PracujScraper, "next_page", new_callable=AsyncMock) as mock_next_page):
        mock_max_page.return_value = max_page
        mock_jobs_list.return_value = jobs_list
        mock_next_page.return_value = None
        mock_scrape_single_offer.return_value = {"employer": "test_employer", "position": "test_position", "earning": "test_earning",
                               "requirements": "test_requirements", "url": "test_url"}
    # Act
        await scraper.extract_job_data(['url2'])

    # Assert
        assert mock_scrape_single_offer.await_count == scrape_single_offer_await_count
        assert mock_scrape_single_offer.await_args_list == [call(url) for url in jobs_list * max_page]
        mock_max_page.assert_awaited_once()
        assert mock_next_page.await_count == next_page_await_count
        assert scraper.all_jobs == [{"employer": "test_employer", "position": "test_position", "earning": "test_earning",
                               "requirements": "test_requirements", "url": "test_url"}] * scrape_single_offer_await_count

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

        with patch('scrapers.pracuj_scraper.logger') as mock_logger:
            result = await scraper.get_employer_name(page)

        assert result == "Not found"
        mock_logger.info.assert_called_once_with("Employer name not found")
        await browser.close()
