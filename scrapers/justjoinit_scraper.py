import asyncio

import httpx
from loguru import logger
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from core.models import JobOffer
from scrapers.utils.data_parsers import clean_job_description, extract_salary_pln
from .base_scraper import BaseScraper
from .locators import JJIT_OFFER, JJIT_NAV
from .parsers import JustJoinItOfferParser


class JustJoinItScraper(BaseScraper):
    """
    A scraper class for justjoin.it website.

    Handles navigation, job search, cookie acceptance, retrieving job listings,
    extracting job details, and pagination.
    """

    def __init__(self, page):
        super().__init__(page, nav_locators=JJIT_NAV)
        self.nav_locators = JJIT_NAV

    def get_parser(self, page):
        return JustJoinItOfferParser(page, locators=JJIT_OFFER)

    async def search(self, keywords: str, location: str = "all-locations") -> None:
        """
        Enter keywords and execute job search.

        Args:
            keywords (str): The search keywords.
            location (str): The location for job search (currently unused in method).
        """
        formattted_keyword = keywords.replace(" ", "%20")
        search_url = f"https://justjoin.it/job-offers/{location}/python?keyword={formattted_keyword}&orderBy=DESC&sortBy=newest"
        try:
            await self.page.goto(search_url, wait_until="domcontentloaded")
            await self.page.wait_for_selector(
                self.nav_locators.offers_list, timeout=15000
            )
            await asyncio.sleep(2)
        except PlaywrightTimeoutError as e:
            logger.error(f"Can't find new offers {e}")

    async def jobs_list(self) -> list[str]:
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
                urls.append("https://justjoin.it" + self.strip_url(href))

        return urls

    async def extract_job_data(
        self, offer_links_from_sheet: list[str]
    ) -> list[JobOffer] | list:
        """
        Collect offers from website and fetch them via candidate API.

        Args:
            offer_links_from_sheet (list[str]): urls from google sheets to avoid offer duplication

        Returns:
            list[JobOffer]: list with offer's data
            list: empty list when exception is raised or there is no new offers.
        """
        logger.info("Colecting new offers.")
        try:
            offer_elements = await self.jobs_list()
            urls = list(dict.fromkeys(offer_elements))

            new_urls = [u for u in urls if u not in offer_links_from_sheet]
            logger.info(f"{len(urls)} offers found, new offers: {len(new_urls)}")

            if not new_urls:
                logger.info("There is no new offers")
                return []

            new_jobs = []
            for url in new_urls:
                slug = url.split("/job-offer/")[-1].split("?")[0]
                logger.info(f"Fetching API data for: {slug}")
                job_data = await self.fetch_details_via_api(slug, url)

                if job_data:
                    new_jobs.append(job_data)
                await asyncio.sleep(1)

            return new_jobs

        except Exception as e:
            logger.error(f"Error during fetch: {e}")
            return []

    async def fetch_details_via_api(self, slug: str, full_url: str) -> JobOffer | None:
        api_url = f"https://justjoin.it/api/candidate-api/offers/{slug}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Referer": full_url,
            "Accept": "application/json",
        }

        async with httpx.AsyncClient(timeout=10) as client:
            try:
                resp = await client.get(api_url, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    skills = ", ".join(
                        [s.get("name", "") for s in data.get("requiredSkills", [])]
                    )

                    salary = extract_salary_pln(data.get("employmentTypes", []))

                    description = (
                        clean_job_description(
                            data.get("description") or data.get("body")
                        )
                        or "No description"
                    )

                    job_data = {
                        "employer": data.get("companyName"),
                        "position": data.get("title"),
                        "salary": salary,
                        "requirements": skills,
                        "url": full_url,
                        "description": description,
                        "status": "TO_ANALYZE",
                    }
                    return JobOffer(**job_data)
                else:
                    logger.warning(f"API returned {resp.status_code} for {slug}")
            except Exception as e:
                logger.error(f"Connection issue with API for {slug}: {e}")

        return None
