import asyncio
from typing import Optional, Dict, Any, Coroutine

from playwright.async_api import Locator
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from loguru import logger

from .base_scraper import BaseScraper, handle_exceptions
from .locators import PRACUJ_OFFER, PRACUJ_NAV
from .parsers import PracujOfferParser


class PracujScraper(BaseScraper):
    """
    A scraper class for pracuj.pl website.

    Handles navigation, job search, cookie acceptance, retrieving job listings,
    extracting job details, and pagination.
    """


    def __init__(self, context, browser, semaphore_value=5):
        super().__init__(context, browser, semaphore_value)
        self.url = "https://pracuj.pl/"
        self.nav_locators = PRACUJ_NAV


    def get_parser(self, page):
        return PracujOfferParser(page, locators=PRACUJ_OFFER)

    async def search(self, keywords, location) -> None:
        """
        Enter keywords and execute job search.

        Args:
            keywords (str): The search keywords.
            location (str): The location for job search (currently unused in method).
        """
        keywords, location = self._validate_scraper_params(keywords, location)
        try:
            await self.type_text(self.nav_locators.search_input, keywords)
            await self.click_locator(self.nav_locators.search_button)
        except PlaywrightTimeoutError as e:
            raise PlaywrightTimeoutError(f"Search bar not found: {e}")


    async def jobs_list(self) -> list[str]:
        """
        Retrieve a list of job offer elements from the current page.

        Returns:
            Locator: Playwright locator containing all job offer elements.
        """
        try:
            locator = self.page.locator(self.nav_locators.offers_list)
            await locator.first.wait_for(timeout=1000)
            all_offers = await locator.all()
        except PlaywrightTimeoutError:
            logger.error("Jobs offers not found.")
            all_offers = []
        urls = []
        for offer_locator in all_offers:
            href = await offer_locator.get_attribute("href")
            if href:
                urls.append(self.strip_url(href))

        return urls

    async def get_url(self, page) -> str:
        """Return the URL of the current job offer."""
        return self.strip_url(page.url)

    async def max_page(self):
        """
        Retrieve the maximum number of pages available for the search.

        Returns:
            int: Maximum page number. Defaults to 1 if not found.
        """
        try:
            max_page = int(await self.page.locator(self.nav_locators.max_page).inner_text(timeout=1000))
        except (PlaywrightTimeoutError, ValueError):
            max_page = 1
        return int(max_page)

    @handle_exceptions("Next page")
    async def next_page(self) -> None:
        """
        Click the button to go to the next page of job listings.

        Raises:
            PlaywrightTimeoutError: if the button is not clickable or not found
        """
        return await self.page.locator(self.nav_locators.next_page).click()



    async def sort_offers_from_newest(self):
        await self.page.wait_for_timeout(500)
        dropdown = self.page.locator(self.nav_locators.sort_button)
        await dropdown.click()
        await self.page.locator(self.nav_locators.sort_option).click()

    async def extract_job_data(self, offer_links_from_sheet: list) -> list[Any]:
        """
        Iterate through all pages and offers to extract job data.

        Stores extracted jobs in the `all_jobs` attribute.
        """
        consecutive_duplicates = 0
        DUPLICATE_LIMIT = 10
        new_jobs = []
        max_page = await self.max_page()
        for page_number in range(max_page):
            offer_urls = await self.jobs_list()
            unique_offers_urls = []
            should_stop_scraping = False
            for url in offer_urls:
                if url in offer_links_from_sheet:
                    consecutive_duplicates += 1
                    logger.info(f"URL already exists: {url}")
                    if consecutive_duplicates >= DUPLICATE_LIMIT:
                        logger.info("Duplicate limit reached. Stopping.")
                        should_stop_scraping = True
                        break
                else:
                    unique_offers_urls.append(url)
            tasks = [self.scrape_single_offer(url) for url in unique_offers_urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for job_data in results:
                if job_data:
                    new_jobs.append(job_data)
            if should_stop_scraping:
                break

            if page_number + 1 < max_page:
                await self.next_page()
                await self.page.wait_for_timeout(500)
        return new_jobs
