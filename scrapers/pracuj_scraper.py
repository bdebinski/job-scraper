import asyncio
import random
from typing import Any

from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from loguru import logger

from scrapers.models import JobOffer

from .base_scraper import BaseScraper
from .locators import PRACUJ_OFFER, PRACUJ_NAV
from .parsers import PracujOfferParser


class PracujScraper(BaseScraper):
    def __init__(self, page):
        super().__init__(page, nav_locators=PRACUJ_NAV)
        self.base_search_url = ""

    def get_parser(self, page):
        return PracujOfferParser(page, locators=PRACUJ_OFFER)

    async def search(self, keywords: str) -> None:
        formattted_keyword = keywords.replace(" ", "%20")
        self.base_search_url = f"https://it.pracuj.pl/praca/{formattted_keyword};kw?sc=0&itth=37"
        await self.page.goto(self.base_search_url, wait_until="domcontentloaded")
        await asyncio.sleep(2)
      

    async def jobs_list(self) -> list[str]:
        """Pobieranie listy ofert z delikatnym przewijaniem."""
        try:
            # Delikatny scroll, żeby Cloudflare widział ruch
            await self.page.evaluate("window.scrollBy(0, 400)")
            await asyncio.sleep(random.uniform(0.8, 1.5))

            locator = self.page.locator(self.nav_locators.offers_list)
            # await locator.first.wait_for(timeout=10000)
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
            logger.warning("Nie udało się odczytać max_page, ustawiam 1.")
            max_page = 1
        return max_page

    async def go_to_page(self, page_number) -> None:
        target_url = f"{self.base_search_url}&pn={page_number}"
        logger.info(f"Moving to next page: {page_number}: {target_url}")
        
        await self.page.goto(target_url, wait_until="domcontentloaded")
        await asyncio.sleep(random.uniform(1.5, 3.0))
        

    async def sort_offers_from_newest(self):
        try:
            await asyncio.sleep(random.uniform(1.0, 2.0))
            dropdown = self.page.locator(self.nav_locators.sort_button)
            await dropdown.click()
            await asyncio.sleep(random.uniform(0.5, 1.0))
            await self.page.locator(self.nav_locators.sort_option).click()
            await self.page.wait_for_load_state("networkidle")
            logger.info("Oferty posortowane od najnowszych.")
        except Exception as e:
            logger.warning(f"Nie udało się posortować ofert: {e}")

    async def extract_job_data(self, offer_links_from_sheet: list) -> list[Any]:
        """Szybsze skrapowanie z użyciem semafory (3 oferty naraz)."""
        consecutive_duplicates = 0
        DUPLICATE_LIMIT = 10
        new_jobs: list[JobOffer] = []

        sem = asyncio.Semaphore(20)

        async def throttled_scrape(url):
            async with sem:
                await asyncio.sleep(random.uniform(1.0, 2.5))
                result = await self.scrape_single_offer(url)
                await asyncio.sleep(random.uniform(1.5, 3.0))
                return result

        max_page = await self.max_page()
        for page_number in range(1, max_page+1):
            logger.info(
                f"Strona {page_number }/{max_page} | Zebrano: {len(new_jobs)}"
            )
            offer_urls = await self.jobs_list()

            unique_urls_to_scrape = []
            for url in offer_urls:
                if url in offer_links_from_sheet:
                    consecutive_duplicates += 1
                    if consecutive_duplicates >= DUPLICATE_LIMIT:
                        logger.info("Limit duplikatów - kończę portal.")
                        return new_jobs
                    continue

                consecutive_duplicates = 0
                unique_urls_to_scrape.append(url)

            if unique_urls_to_scrape:
                tasks = [throttled_scrape(url) for url in unique_urls_to_scrape]
                results = await asyncio.gather(*tasks)

                for res in results:
                    if res:
                        new_jobs.append(res)

            if page_number >= max_page:
                break

            await self.go_to_page(page_number+1)

        return new_jobs

    async def handle_pracuj_popups(self):
        """Zamykanie uciążliwych popupów na Pracuj.pl."""
        try:
            close_btn = self.page.get_by_role("button", name="Zamknij").first
            await close_btn.wait_for(state="visible", timeout=10000)

            await close_btn.click()
            logger.info("Zamknięto pop-up reklamowy.")
        except PlaywrightTimeoutError:
            logger.info("Nie znaleziono popupu")
