import asyncio

import httpx
from loguru import logger

from scrapers.models import JobOffer
from scrapers.utills.data_parsers import clean_job_description, extract_salary_pln
from .base_scraper import BaseScraper
from .locators import JJIT_OFFER, JJIT_NAV
from .parsers import JustJoinItOfferParser


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
        except Exception as e:
            logger.error(f"💥 Błąd podczas ładowania wyszukiwarki: {e}")

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
                urls.append("https://justjoin.it" + self.strip_url(href))

        return urls

    async def sort_offers_from_newest(self):
        await self.page.wait_for_timeout(500)
        dropdown = self.page.locator("[name='sort_filter_button']").first
        await dropdown.click()
        await self.page.locator("[role='menuitem']", has_text="Latest").click()
        await self.page.wait_for_timeout(2000)

    async def extract_job_data(self, offer_links_from_sheet: list):
        logger.info("🕵️ Zbieram najnowsze oferty z góry listy...")

        try:
            offer_elements = await self.jobs_list()
            urls = list(dict.fromkeys(offer_elements))

            new_urls = [u for u in urls if u not in offer_links_from_sheet]
            logger.info(
                f"🚀 Znalazłem {len(urls)} ofert na stronie. Z tego NOWYCH: {len(new_urls)}"
            )

            if not new_urls:
                logger.info("💤 Brak nowych ofert. Kończę pracę.")
                return []

            new_jobs = []
            for url in new_urls:
                slug = url.split("/job-offer/")[-1].split("?")[
                    0
                ]  # Wyciągamy czysty slug
                logger.info(f"⬇️ Pobieram dane przez API dla: {slug}")

                # Pobieramy szczegóły przez szybkie API
                job_data = await self.fetch_details_via_api(slug, url)

                if job_data:
                    new_jobs.append(job_data)

                # Oddech dla serwerów JustJoinIT
                await asyncio.sleep(1)

            return new_jobs

        except Exception as e:
            logger.error(f"💥 Błąd podczas wyciągania danych: {e}")
            return []

    async def fetch_details_via_api(self, slug: str, full_url: str):
        """KROK 4: Strzał do API po pełny opis (bez Playwrighta)"""
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
                    # 1. Wyciąganie skilli
                    skills = ", ".join(
                        [s.get("name", "") for s in data.get("requiredSkills", [])]
                    )

                    # 2. Wyciąganie widełek płacowych
                    salary = extract_salary_pln(data.get("employmentTypes", []))

                    # 3. Wyciąganie opisu (kluczowe dla Gemini)
                    description = (
                        clean_job_description(
                            data.get("description") or data.get("body")
                        )
                        or "Brak opisu"
                    )

                    # Zwracamy słownik (dopasuj klucze do swojego arkusza)

                    job_data = {
                        "employer": data.get("companyName"),
                        "position": data.get("title"),
                        "salary": salary,
                        "requirements": skills,
                        "url": full_url,
                        "description": description,
                        "status": "TO_ANALYZE",
                    }

                    # 2. TUTAJ ZMIANA: Zwracamy model, a nie słownik
                    return JobOffer(**job_data)
                else:
                    logger.warning(
                        f"⚠️ API zwróciło status {resp.status_code} dla {slug}"
                    )
            except Exception as e:
                logger.error(f"❌ Błąd połączenia z API dla {slug}: {e}")

        return None
