import asyncio
from typing import Any, Coroutine

from loguru import logger
from .base_scraper import BaseScraper, handle_exceptions
from .config import ScraperConfig
from .locators import JJIT_OFFER, JJIT_NAV
from .parsers import PracujOfferParser, JustJoinItOfferParser


class JustJoinItScraper(BaseScraper):
    """
    A scraper class for justjoin.it website.

    Handles navigation, job search, cookie acceptance, retrieving job listings,
    extracting job details, and pagination.
    """

    def __init__(self, context, browser, semaphore_value=5):
        super().__init__(context, browser, semaphore_value)
        self.url = "https://justjoin.it/"
        self.nav_locators = JJIT_NAV

    def get_parser(self, page):
        return JustJoinItOfferParser(page, locators=JJIT_OFFER)

    def get_location_dropdown(self, location):
        return self.page.get_by_role("option", name=location)

    async def search(self, keywords, location) -> None:
        """
        Enter keywords and execute job search.

        Args:
            keywords (str): The search keywords.
            location (str): The location for job search (currently unused in method).
        """
        keywords, location = self._validate_scraper_params(keywords, location)
        await self.page.locator(self.nav_locators.search_input).click()
        await self.page.wait_for_timeout(100)
        await self.page.locator(self.nav_locators.search_input).type('a ' + keywords)
        await self.page.locator(self.nav_locators.location_input).type(location)
        await self.get_location_dropdown(location).click()
        await self.page.locator(self.nav_locators.search_button).click()

    async def jobs_list(self) -> list:
        """
        Retrieve a list of job offer elements from the current page.

        Returns:
            list: list of urls in current website view
        """
        locator = self.page.locator(self.nav_locators.offers_list)
        await locator.first.wait_for(timeout=5000)
        all_offers = await locator.all()
        urls = []
        for offer_locator in all_offers:
            href = await offer_locator.get_attribute("href")
            if href:
                urls.append('https://justjoin.it' + self.strip_url(href))

        return urls

    async def sort_offers_from_newest(self):
        await self.page.wait_for_timeout(500)
        dropdown = self.page.locator("[name='sort_filter_button']").first
        await dropdown.click()
        await self.page.locator("[role='menuitem']", has_text='Latest').click()
        await self.page.wait_for_timeout(2000)

    async def extract_job_data(self, offer_links_from_sheet: list) -> list[Any]:
        """
        Iterate through all pages and offers to extract job data.

        Stores extracted jobs in the `all_jobs` attribute.
        """
        MAX_SCROLL_ATTEMPTS = ScraperConfig.scroll_step
        scroll_count = 0
        latest_jobs = await self.jobs_list()
        new_jobs = []
        urls = []
        if set(latest_jobs).issubset(set(offer_links_from_sheet)):
            logger.info(f"No new jobs to scrape.")
        else:
            while scroll_count < MAX_SCROLL_ATTEMPTS:
                await self.page.evaluate("window.scrollBy(0, 400)")
                await self.page.wait_for_timeout(300)
                jobs = await self.jobs_list()

                if latest_jobs == jobs:
                    break
                else:
                    latest_jobs = jobs
                    urls.extend(jobs)
                scroll_count += 1
            urls = set(urls)
            urls = urls.difference(set(offer_links_from_sheet))
            logger.info(f"Urls to scrape {urls}")
            tasks = [self.scrape_single_offer(url) for url in urls]
            results = await asyncio.gather(*tasks)
            for job_data in results:
                if job_data:
                    new_jobs.append(job_data)
        return new_jobs
