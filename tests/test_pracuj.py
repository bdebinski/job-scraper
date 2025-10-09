from unittest.mock import AsyncMock, MagicMock, patch, call
from playwright.async_api import TimeoutError as PlaywrightTimeoutError, Page
import pytest

from scrapers.pracuj_scraper import PracujScraper

@pytest.fixture
def scraper_fixture() -> PracujScraper:
    fake_page = MagicMock(spec=Page)
    fake_browser = AsyncMock()
    scraper = PracujScraper(fake_page, fake_browser)
    return scraper

@pytest.mark.asyncio
async def test_get_position_name_returns_correct_text(scraper_fixture):
    scraper =  scraper_fixture
    fake_locator = AsyncMock()
    scraper.page.locator.return_value = fake_locator
    fake_locator.inner_text.return_value = 'python developer'
    result = await scraper.get_position_name(scraper.page)

    scraper.page.locator.assert_called_once_with(scraper.offer_position_name)
    scraper.page.locator.return_value.inner_text.assert_awaited_once()
    assert result == 'python developer'

@pytest.mark.asyncio
async def test_get_positon_name_raises_exception(scraper_fixture):
    scraper = scraper_fixture
    fake_locator = AsyncMock(spec=['inner_text'])
    fake_locator.inner_text.side_effect = PlaywrightTimeoutError('Timeout')
    scraper.page.locator.return_value = fake_locator
    with pytest.raises(PlaywrightTimeoutError):
        await scraper.get_position_name(scraper.page)


@pytest.mark.asyncio
async def test_get_url_returns_correct_trimmed_url(scraper_fixture):
    scraper = scraper_fixture
    fake_url = "http://test.pl?testy"
    scraper.page.url = fake_url

    result = await scraper.get_url(scraper.page)
    assert result == "http://test.pl"


@pytest.mark.asyncio
async def test_get_employer_name_return_correct_text(scraper_fixture):
    scraper = scraper_fixture
    fake_locator = AsyncMock()
    scraper.page.locator.return_value = fake_locator
    fake_locator.inner_text.return_value = "test_employee"

    result = await scraper.get_employer_name(scraper.page)
    scraper.page.locator.assert_called_once_with(scraper.employer_name)
    scraper.page.locator.return_value.inner_text.assert_awaited_once()
    assert result == "test_employee"

@pytest.mark.asyncio
async def test_get_employer_name_raises_timeout_error(scraper_fixture):
    scraper = scraper_fixture
    fake_locator = AsyncMock()
    scraper.page.locator.return_value = fake_locator
    fake_locator.inner_text.side_effect = PlaywrightTimeoutError('Timeout')

    with pytest.raises(PlaywrightTimeoutError):
        await scraper.get_employer_name(scraper.page)

@pytest.mark.asyncio
@pytest.mark.parametrize("max_page, jobs_list, scrape_single_offer_await_count, next_page_await_count",
                         [(1,['url1'], 1, 0),
                          (4,['url1', 'url3'], 8, 3)])
async def test_extract_job_data_collects_all_jobs_across_pages(scraper_fixture, max_page, jobs_list,
                                                     scrape_single_offer_await_count,
                                                     next_page_await_count):
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
        await scraper.extract_job_data(['url2'])
        assert mock_scrape_single_offer.await_count == scrape_single_offer_await_count
        assert mock_scrape_single_offer.await_args_list == [call(url) for url in jobs_list * max_page]
        mock_max_page.assert_awaited_once()
        assert mock_next_page.await_count == next_page_await_count
        assert scraper.all_jobs == [{"employer": "test_employer", "position": "test_position", "earning": "test_earning",
                               "requirements": "test_requirements", "url": "test_url"}] * scrape_single_offer_await_count

