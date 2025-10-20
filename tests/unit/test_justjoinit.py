from logging import warning
from unittest.mock import patch, AsyncMock, MagicMock

from loguru import logger
from playwright.async_api import TimeoutError as PlaywrightTimeoutError, Page, Browser, Locator

import pytest

from scrapers.justjoinit_scraper import JustJoinItScraper

@pytest.fixture
def browser():
    return MagicMock(spec=Browser)

@pytest.fixture
def fake_page():
    return MagicMock(spec=Page)

@pytest.fixture
def fake_locator():
    return MagicMock(spec=Locator)

@pytest.mark.parametrize("property_name, role_args", [
    ("search_input", {"role": "button", "name": "Search: Job title, company,"},),
    ("location_input", {"role": "combobox", "name": "Location"},),
    ("search_button", {"role": "button", "name": "Search", "exact": True},),

     ])
def test_justjoinit_properties(browser, fake_page, property_name, role_args):
    fake_locator = AsyncMock(spec=Locator)
    fake_page.get_by_role.return_value = fake_locator
    scraper = JustJoinItScraper(fake_page, browser)

    # Act
    result = getattr(scraper, property_name)

    # Assert
    assert result is fake_locator
    fake_page.get_by_role.assert_called_once_with(**role_args)

def test_salary_locator(browser, fake_page):
    # Arrange
    first_locator = MagicMock()
    second_locator = MagicMock()
    result_locator = MagicMock()
    fake_page.locator.return_value = first_locator
    first_locator.locator.return_value = second_locator
    second_locator.locator.return_value = result_locator
    scraper = JustJoinItScraper(fake_page, browser)

    # Act
    result = scraper.salary_locator

    # Assert
    assert result is result_locator
    fake_page.locator.assert_called_once_with('text=Salary')
    first_locator.locator.assert_called_once_with('..')
    second_locator.locator.assert_called_once_with('div.MuiTypography-h4')

def test_get_location_dropdown(browser, fake_page):
    # Arrange
    mock_get_by_role = MagicMock()
    fake_page.get_by_role.return_value = mock_get_by_role
    scraper = JustJoinItScraper(fake_page, browser)
    fake_location = "fake_location"
    # Act
    result = scraper.get_location_dropdown(fake_location)

    # Assert
    assert result is mock_get_by_role
    fake_page.get_by_role.assert_called_once_with("option", name=fake_location)

async def test_navigate(fake_page, browser):
    # Arrange
    scraper = JustJoinItScraper(fake_page, browser)
    scraper.go_to_page = AsyncMock()

    # Act
    await scraper.navigate()

    # Assert
    scraper.go_to_page.assert_awaited_once_with("https://justjoin.it/")



async def test_get_position_name_should_return_position_name_when_element_found(browser, fake_page, fake_locator):
    # Arrange
    fake_page.locator.return_value = fake_locator
    fake_locator.inner_text = AsyncMock(return_value="employer name")
    scraper = JustJoinItScraper(fake_page, browser)

    # Act
    with (patch("scrapers.base_scraper.logger") as mock_logger):
        result = await scraper.get_position_name(fake_page)

    # Assert
        mock_logger.info.assert_called_once_with(f"Position found: employer name")
    assert result == "employer name"
    fake_page.locator.assert_called_once_with("h1")
    fake_locator.inner_text.assert_awaited_once()

@pytest.mark.parametrize("exception, logger_type, logger_message",
                         [(PlaywrightTimeoutError('timeout'), "warning", 'Position name not found'),
                          (Exception('unexpected'), "error", "Unexpected error getting Position field:  unexpected")])
async def test_get_position_name_should_return_not_found_on_exception(browser, fake_page, fake_locator, exception, logger_type, logger_message):
    # Arrange
    fake_page.locator.return_value = fake_locator
    fake_locator.inner_text = AsyncMock(side_effect=exception)
    scraper = JustJoinItScraper(fake_page, browser)

    # Act
    with patch("scrapers.base_scraper.logger") as mock_logger:
        result = await scraper.get_position_name(fake_page)

    # Assert
        getattr(mock_logger, logger_type).assert_called_once_with(logger_message)
    assert result == "Not found"
    scraper.page.locator.assert_called_once()
    fake_locator.inner_text.assert_awaited_once()

@pytest.mark.asyncio
async def test_get_earning_amount_should_return_salary_when_element_found(browser, fake_page, fake_locator):
    # Arrange
    scraper = JustJoinItScraper(fake_page, browser)

    # Act
    with (patch("scrapers.base_scraper.logger") as mock_logger,
          patch.object(JustJoinItScraper, 'salary_locator', new_callable=AsyncMock) as mock_salary_locator):
        mock_salary_locator.inner_text.return_value = '1000'
        result = await scraper.get_earning_amount(fake_page)

    # Assert
        mock_logger.info.assert_called_once_with(f"Salary found: 1000")
    assert result == "1000"
    mock_salary_locator.inner_text.assert_awaited_once()

@pytest.mark.parametrize("exception, logger_type, logger_message",
                         [(PlaywrightTimeoutError('timeout'), "warning", 'Salary name not found'),
                          (Exception('unexpected'), "error", "Unexpected error getting Salary field:  unexpected")])
async def test_get_earning_amount_should_return_not_found_on_exception(browser, fake_page, fake_locator, exception, logger_type, logger_message):
    # Arrange
    scraper = JustJoinItScraper(fake_page, browser)

    # Act
    with (patch("scrapers.base_scraper.logger") as mock_logger,
          patch.object(JustJoinItScraper, 'salary_locator', new_callable=AsyncMock) as mock_salary_locator):
        mock_salary_locator.inner_text = AsyncMock(side_effect=exception)
        result = await scraper.get_earning_amount(fake_page)

    # Assert
        getattr(mock_logger, logger_type).assert_called_once_with(logger_message)
    assert result == "Not found"

async def test_get_employer_name_should_return_name_when_element_found(browser, fake_page):
    # Arrange
    fake_inner_text = AsyncMock(return_value="Employer name")
    fake_nth_locator = MagicMock()
    fake_nth_locator.inner_text = fake_inner_text
    fake_base_locator = MagicMock()
    fake_base_locator.nth.return_value = fake_nth_locator
    fake_page.locator.return_value = fake_base_locator
    scraper = JustJoinItScraper(fake_page, browser)

    # Act
    with patch("scrapers.base_scraper.logger") as mock_logger:
        result = await scraper.get_employer_name(fake_page)

    # Assert
        mock_logger.info.assert_called_once_with("Employer found: Employer name")
    assert result == "Employer name"
    fake_page.locator.assert_called_once_with("p:has(svg)")
    fake_base_locator.nth.assert_called_once_with(1)
    fake_nth_locator.inner_text.assert_awaited_once()


