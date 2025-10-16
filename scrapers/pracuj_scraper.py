import asyncio
from typing import Optional, Dict

from playwright.async_api import Locator
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from loguru import logger

from .base_scraper import BaseScraper

class PracujScraper(BaseScraper):
    """
    A scraper class for pracuj.pl website.

    Handles navigation, job search, cookie acceptance, retrieving job listings,
    extracting job details, and pagination.
    """
    search_locator = "[data-test=\"input-kw\"] [data-test=\"input-field\"]"
    search_button = "[data-test=\"search-button\"]"
    cookie_locator = "[data-test=\"button-submitCookie\"]"
    section_offers_locator = "[data-test=\"section-offers\"]"
    next_page_button = "[data-test=\"top-pagination-next-button\"]"
    max_page_locator = "[data-test=\"top-pagination-max-page-number\"]"
    offer_employer_name = "[data-test=\"text-employerName\"]"
    offer_requirements = "[data-test=\"section-requirements\"]"
    offer_salary = "[data-test=\"text-earningAmount\"]"
    offer_position_name = "[data-test=\"text-positionName\"]"

    async def navigate(self) -> None:
        """Navigate to the main page of pracuj.pl."""
        await self.go_to_page("http://pracuj.pl")

    async def search(self, keywords, location) -> None:
        """
        Enter keywords and execute job search.

        Args:
            keywords (str): The search keywords.
            location (str): The location for job search (currently unused in method).
        """
        keywords, location = self._validate_scraper_params(keywords, location)
        try:
            await self.type_text(self.search_locator, keywords)
            await self.click_locator(self.search_button)
        except PlaywrightTimeoutError as e:
            raise PlaywrightTimeoutError(f"Search bar not found: {e}")

    async def accept_cookies(self) -> None:
        """Accept cookie consent on the website."""
        try:
            await self.click_locator(self.cookie_locator)
        except PlaywrightTimeoutError:
            logger.error("Cookie locator not found")


    async def jobs_list(self) -> list[str]:
        """
        Retrieve a list of job offer elements from the current page.

        Returns:
            Locator: Playwright locator containing all job offer elements.
        """
        try:
            locator = self.page.locator(self.section_offers_locator).locator('[data-test="link-offer"]')
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

    async def get_position_name(self, page) -> str:
        """Return the position name of the current job offer."""
        try:
            position = await page.locator(self.offer_position_name).inner_text()
        except PlaywrightTimeoutError:
            logger.warning("Position name not found.")
            position = "Not found"
        return position

    async def get_earning_amount(self, page) -> str:
        """Return the earning amount of the current job offer as a single string."""
        try:
            elements = page.locator(self.offer_salary)
            earning_amount =  await elements.all_inner_texts()
            result = "".join(earning_amount)
        except PlaywrightTimeoutError:
            logger.info("Salary not found.")
            result = "Not found"
        return result

    async def get_job_requirement(self, page) -> str:
        """Return the job requirements of the current job offer."""
        try:
            requirements = await page.locator(self.offer_requirements).inner_text()
        except PlaywrightTimeoutError:
            logger.info("Requirements not found")
            requirements = "Not found"
        return requirements

    async def get_employer_name(self, page) -> str:
        """Return the employer's name of the current job offer."""
        try:
            employer_name = await page.locator(self.offer_employer_name).inner_text()
        except PlaywrightTimeoutError:
            employer_name = "Not found"
            logger.info("Employer name not found")
        return employer_name

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
            max_page = int(await self.page.locator(self.max_page_locator).inner_text(timeout=1000))
        except (PlaywrightTimeoutError, ValueError):
            max_page = 1
        return int(max_page)

    async def next_page(self) -> None:
        """
        Click the button to go to the next page of job listings.

        Raises:
            PlaywrightTimeoutError: if the button is not clickable or not found
        """
        try:
            await self.page.locator(self.next_page_button).click()
        except PlaywrightTimeoutError as e:
            raise PlaywrightTimeoutError(f"Next page button not found or not clickable: {e}")

    async def sort_offers_from_newest(self):
        await self.page.wait_for_timeout(500)
        dropdown = self.page.locator("[data-test='button-sort-type']")
        await dropdown.click()
        await self.page.get_by_role("treeitem", name="Najnowsze").click()

    async def extract_job_data(self, offer_links_from_sheet: list) -> None:
        """
        Iterate through all pages and offers to extract job data.

        Stores extracted jobs in the `all_jobs` attribute.
        """
        max_page = await self.max_page()
        for page_number in range(max_page):
            offer_urls = await self.jobs_list()
            unique_offers_urls = []
            should_continue_scraping = True
            for url in offer_urls:
                if url in offer_links_from_sheet:
                    logger.info(f"URL already exists: {url}. Stopping further scraping on this page.")
                    should_continue_scraping = False
                    break
                unique_offers_urls.append(url)
            tasks = [self.scrape_single_offer(url) for url in unique_offers_urls]
            results = await asyncio.gather(*tasks)
            for job_data in results:
                if job_data:
                    self.all_jobs.append(job_data)
            if not should_continue_scraping:
                break

            if page_number + 1 < max_page:
                await self.next_page()