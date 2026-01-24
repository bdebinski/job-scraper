from unittest.mock import AsyncMock, MagicMock, patch, call
from playwright.async_api import TimeoutError as PlaywrightTimeoutError, Page, async_playwright, expect
import pytest

from scrapers.locators import PRACUJ_NAV, PRACUJ_OFFER
from scrapers.pracuj_scraper import PracujScraper


async def test_home_page_locators_are_available(page_fixture, pracuj_scraper):
        # Arrange
        pracuj_scraper.page = page_fixture

        #Act
        await pracuj_scraper.navigate()

        # Assert
        await expect(page_fixture.locator(pracuj_scraper.nav_locators.search_input)).to_be_visible(timeout=3000)
        await expect(page_fixture.locator(pracuj_scraper.nav_locators.search_button)).to_be_visible(timeout=3000)
        await expect(page_fixture.locator(pracuj_scraper.nav_locators.cookie_locator)).to_be_visible(timeout=3000)


@pytest.mark.asyncio
async def test_search_results_locators_are_available(page_fixture, pracuj_scraper):
        pracuj_scraper.page = page_fixture

        # Act
        await pracuj_scraper.navigate()
        await pracuj_scraper.accept_cookies()
        await pracuj_scraper.search('python', 'Warszawa')  # Użyj dużego miasta dla pewności wyników

        # Assert
        await expect(page_fixture.locator(PRACUJ_NAV.offers_list).first).to_be_visible(timeout=10000)

        offers_count = await page_fixture.locator(pracuj_scraper.nav_locators.offers_list).count()
        assert offers_count > 0, "Offers not found"


@pytest.mark.asyncio
async def test_offer_locators_are_available(page_fixture, pracuj_scraper):
        pracuj_scraper.page = page_fixture

        # Act
        await pracuj_scraper.navigate()
        await pracuj_scraper.accept_cookies()
        await pracuj_scraper.search('python', 'Warszawa')


        #TODO: implement wait for reload
        await pracuj_scraper.page.wait_for_timeout(4000)
        urls = await pracuj_scraper.jobs_list()
        assert len(urls) > 0, "No offers found"

        await page_fixture.goto(urls[0])

        # Assert
        await expect(page_fixture.locator(PRACUJ_OFFER.employer)).to_be_visible(timeout=10000)
        await expect(page_fixture.locator(PRACUJ_OFFER.position)).to_be_visible()
