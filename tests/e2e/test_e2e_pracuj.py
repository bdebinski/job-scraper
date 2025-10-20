from unittest.mock import AsyncMock, MagicMock, patch, call
from playwright.async_api import TimeoutError as PlaywrightTimeoutError, Page, async_playwright, expect
import pytest

from scrapers.pracuj_scraper import PracujScraper


async def test_home_page_locators_are_available(browser, page, pracuj_scraper):
        # Act
        await pracuj_scraper.navigate()

        # Assert
        await expect(page.locator(pracuj_scraper.search_locator)).to_be_visible(timeout=3000)
        await expect(page.locator(pracuj_scraper.search_button)).to_be_visible(timeout=3000)
        await expect(page.locator(pracuj_scraper.cookie_locator)).to_be_visible(timeout=3000)

async def test_search_results_locators_are_available(browser, page, pracuj_scraper):
        # Act
        await pracuj_scraper.navigate()
        await pracuj_scraper.accept_cookies()
        await pracuj_scraper.search('python', 'Łódź')

        # Assert
        await expect(page.locator(pracuj_scraper.section_offers_locator)).to_be_visible(timeout=5000)
        await expect(page.locator(pracuj_scraper.next_page_button)).to_be_visible(timeout=5000)
        await expect(page.locator(pracuj_scraper.max_page_locator)).to_be_visible(timeout=5000)

async def test_offer_locators_are_available(browser, page, pracuj_scraper):
        # Act
        await pracuj_scraper.navigate()
        await pracuj_scraper.accept_cookies()
        await pracuj_scraper.search('python', 'Łódź')
        urls = await pracuj_scraper.jobs_list()
        await pracuj_scraper.go_to_page(urls[0])

        # Assert
        await expect(page.locator(pracuj_scraper.offer_employer_name)).to_be_visible(timeout=5000)
        await expect(page.locator(pracuj_scraper.offer_requirements)).to_be_visible(timeout=5000)
        await expect(page.locator(pracuj_scraper.offer_position_name)).to_be_visible(timeout=5000)
