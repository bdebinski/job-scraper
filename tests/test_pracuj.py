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
async def test_get_positon_name_handles_exception(scraper_fixture):
    scraper = scraper_fixture
    fake_locator = AsyncMock(spec=['inner_text'])
    fake_locator.inner_text.side_effect = PlaywrightTimeoutError('Timeout')
    fake_logger = MagicMock()
    fake_logger.warning = MagicMock()
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

@pytest.mark.asyncio
async def test_scrape_single_offer(scraper_fixture):
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


    result = await scraper.scrape_single_offer('https://example.com/job1')

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

@pytest.mark.asyncio
async def test_home_page_locators_are_available():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        scraper = PracujScraper(page, browser)

        await scraper.navigate()

        await expect(page.locator(scraper.search_locator)).to_be_visible(timeout=3000)
        await expect(page.locator(scraper.search_button)).to_be_visible(timeout=3000)
        await expect(page.locator(scraper.cookie_locator)).to_be_visible(timeout=3000)

@pytest.mark.asyncio
async def test_search_results_locators_are_available():
    async with async_playwright() as p:
        # Arrange
        browser = await p.chromium.launch()
        page = await browser.new_page()
        scraper = PracujScraper(page, browser)

        # Act
        await scraper.navigate()
        await scraper.accept_cookies()
        await scraper.search('python', 'Łódź')

        # Assert
        await expect(page.locator(scraper.section_offers_locator)).to_be_visible(timeout=5000)
        await expect(page.locator(scraper.next_page_button)).to_be_visible(timeout=5000)
        await expect(page.locator(scraper.max_page_locator)).to_be_visible(timeout=5000)

@pytest.mark.asyncio
async def test_offer_locators_are_available():
    async with async_playwright() as p:
        # Arrange
        browser = await p.chromium.launch()
        page = await browser.new_page()
        scraper = PracujScraper(page, browser)

        # Act
        await scraper.navigate()
        await scraper.accept_cookies()
        await scraper.search('python', 'Łódź')
        urls = await scraper.jobs_list()
        await scraper.go_to_page(urls[0])

        # Assert
        await expect(page.locator(scraper.offer_employer_name)).to_be_visible(timeout=5000)
        await expect(page.locator(scraper.offer_requirements)).to_be_visible(timeout=5000)
        await expect(page.locator(scraper.offer_position_name)).to_be_visible(timeout=5000)
