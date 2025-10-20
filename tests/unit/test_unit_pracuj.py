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

@pytest.fixture
def fake_locator():
    return AsyncMock()

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
async def test_get_position_name_handles_exception(scraper_fixture):
    scraper = scraper_fixture
    fake_locator = AsyncMock(spec=['inner_text'])
    fake_locator.inner_text.side_effect = PlaywrightTimeoutError('Timeout')
    scraper.page.locator.return_value = fake_locator
    with patch("scrapers.pracuj_scraper.logger") as mock_logger:
        result  = await scraper.get_position_name(scraper.page)

    assert result == "Not found"
    mock_logger.warning.assert_called_once_with("Position name not found.")

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
    scraper.page.locator.assert_called_once_with(scraper.offer_employer_name)
    scraper.page.locator.return_value.inner_text.assert_awaited_once()
    assert result == "test_employee"

@pytest.mark.asyncio
async def test_get_employer_name_handles_exception(scraper_fixture):
    scraper = scraper_fixture
    fake_locator = AsyncMock()
    scraper.page.locator.return_value = fake_locator
    fake_locator.inner_text.side_effect = PlaywrightTimeoutError('Timeout')

    with patch("scrapers.pracuj_scraper.logger") as mock_logger:
        result = await scraper.get_employer_name(scraper.page)

    assert result == "Not found"
    mock_logger.info.assert_called_once_with("Employer name not found")


@pytest.mark.asyncio
async def test_max_page_returns_number(scraper_fixture):
    # Arrange
    scraper = scraper_fixture
    fake_locator = AsyncMock()
    scraper.page.locator.return_value = fake_locator
    fake_locator.inner_text.return_value = 3

    # Act
    result = await scraper.max_page()

    # Assert
    assert result == 3

@pytest.mark.asyncio
async def test_max_page_returns_default_on_error(scraper_fixture):
    # Arrange
    scraper = scraper_fixture
    fake_locator = AsyncMock()
    scraper.page.locator.return_value = fake_locator
    fake_locator.inner_text.side_effect = PlaywrightTimeoutError('Timeout')

    # Act
    result = await scraper.max_page()

    # Assert
    assert result == 1

@pytest.mark.asyncio
async def test_max_page_returns_default_on_invalid_text(scraper_fixture):
    # Arrange
    scraper = scraper_fixture
    fake_locator = AsyncMock()
    scraper.page.locator.return_value = fake_locator
    fake_locator.inner_text.return_value = 'N/A'

    # Act
    result = await scraper.max_page()

    # Assert
    assert result == 1

@pytest.mark.asyncio
async  def test_next_page_when_button_is_available(scraper_fixture):
    scraper = scraper_fixture
    fake_locator = AsyncMock()
    scraper.page.locator.return_value = fake_locator

    await scraper.next_page()

    scraper.page.locator.assert_called_once_with(scraper.next_page_button)
    scraper.page.locator.return_value.click.assert_awaited_once()

@pytest.mark.asyncio
async def test_next_page_raises_timeout_error(scraper_fixture):
    scraper = scraper_fixture
    fake_locator = AsyncMock()
    scraper.page.locator.return_value = fake_locator
    fake_locator.click.side_effect = PlaywrightTimeoutError('Timeout')
    with pytest.raises(PlaywrightTimeoutError):
        result = await scraper.next_page()

@pytest.mark.asyncio
async def test_jobs_list_returns_urls(scraper_fixture):
    scraper = scraper_fixture
    inner_locator = MagicMock()
    outer_locator = MagicMock()
    scraper.page.locator.return_value = outer_locator
    outer_locator.locator.return_value = inner_locator
    inner_locator.first = MagicMock()
    inner_locator.first.wait_for = AsyncMock()
    fake_offer_1 = MagicMock()
    fake_offer_2 = MagicMock()
    fake_offer_1.get_attribute = AsyncMock(return_value="https://example.com/job1?32132")
    fake_offer_2.get_attribute = AsyncMock(return_value="https://example.com/job2?32132")

    inner_locator.all = AsyncMock(return_value=[fake_offer_1, fake_offer_2])

    result = await scraper.jobs_list()

    assert result == ["https://example.com/job1", "https://example.com/job2"]

@pytest.mark.asyncio
async def test_jobs_list_no_offers_returns_empty_url_list(scraper_fixture):
    scraper = scraper_fixture
    inner_locator = MagicMock()
    outer_locator = MagicMock()
    scraper.page.locator.return_value = outer_locator
    outer_locator.locator.return_value = inner_locator
    inner_locator.first = MagicMock()
    inner_locator.first.wait_for = AsyncMock()

    inner_locator.all = AsyncMock(return_value=[])

    result = await scraper.jobs_list()

    assert result == []
    inner_locator.first.wait_for.assert_awaited_once()
    outer_locator.locator.assert_called_once()
