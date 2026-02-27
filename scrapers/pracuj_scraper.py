import asyncio
import random

from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from loguru import logger

from core.models import JobOffer

from .base_scraper import BaseScraper
from .locators import PRACUJ_OFFER, PRACUJ_NAV
from .parsers import PracujOfferParser


class PracujScraper(BaseScraper):
    def __init__(self, page):
        super().__init__(page, nav_locators=PRACUJ_NAV)
        self.url = "https://www.pracuj.pl/"
        self.base_search_url = ""

    def get_parser(self, page):
        return PracujOfferParser(page, locators=PRACUJ_OFFER)

    async def search(self, keywords: str) -> None:
        formattted_keyword = keywords.replace(" ", "%20")
        self.base_search_url = (
            f"https://it.pracuj.pl/praca/{formattted_keyword};kw?sc=0&itth=37"
        )
        await self.page.goto(self.base_search_url, wait_until="domcontentloaded")
        await asyncio.sleep(2)

    async def jobs_list(self) -> list[str]:
        try:
            locator = self.page.locator(self.nav_locators.offers_list)
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

    async def max_page(self) -> int:
        if not self.nav_locators.max_page:
            logger.warning("No selector for max page, returns 1 as max page.")
            return 1
        try:
            element = self.page.locator(self.nav_locators.max_page)
            await element.wait_for(timeout=5000)
            text = await element.inner_text()
            max_page = int(text)
        except (PlaywrightTimeoutError, ValueError, TypeError):
            logger.warning("Unable to read number of pages, max pages set to 1.")
            max_page = 1
        return max_page

    async def next_page(self, page_number) -> None:
        target_url = f"{self.base_search_url}&pn={page_number}"
        logger.info(f"Moving to next page: {page_number}: {target_url}")

        await self.page.goto(target_url, wait_until="domcontentloaded")
        await asyncio.sleep(random.uniform(1.5, 3.0))

    async def extract_job_data(
        self, offer_links_from_sheet: list[str]
    ) -> list[JobOffer]:
        """
        Extracts new job offers by navigating through pages and filtering duplicates.
        """
        all_found_urls: list[str] = []
        max_page = await self.max_page()

        for page_number in range(1, max_page + 1):
            logger.info(f"Scanning page {page_number}/{max_page}...")
            page_urls = await self.jobs_list()
            new_on_this_page = [u for u in page_urls if u not in offer_links_from_sheet]

            all_found_urls.extend(page_urls)

            if len(new_on_this_page) == 0 and page_number > 1:
                logger.info("Found only duplicates on this page. Stopping pagination.")
                break

            if page_number < max_page:
                await self.next_page(page_number + 1)

        unique_new_urls = list(
            set([u for u in all_found_urls if u not in offer_links_from_sheet])
        )
        logger.info(f"Total new unique offers to scrape: {len(unique_new_urls)}")

        tasks = [self.scrape_single_offer(url) for url in unique_new_urls]
        results = await asyncio.gather(*tasks)

        return [res for res in results if res is not None]

    async def accept_cookies(self):
        await super().accept_cookies()
        await self.page.get_by_role("button", name="Zamknij").click()
