import asyncio
from typing import Optional, Dict

from playwright.async_api import Locator
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from .base_scraper import BaseScraper

class JustJoinItScraper(BaseScraper):
    """
    A scraper class for justjoin.it website.

    Handles navigation, job search, cookie acceptance, retrieving job listings,
    extracting job details, and pagination.
    """
    search_locator = 'button[aria-label="Search: Job title, company,"]'
    cookie_locator = "[id=\"cookiescript_accept\"]"
    section_offers_locator = "[data-test=\"section-offers\"]"
    offers_locator = "[data-test=\"link-offer\"]"
    next_page_button = "[data-test=\"top-pagination-next-button\"]"
    max_page_locator = "[data-test=\"top-pagination-max-page-number\"]"
    employer_name = "[data-test=\"text-employerName\"]"
    offer_requirements = "[data-test=\"section-requirements\"]"
    offer_salary = "[data-test=\"text-earningAmount\"]"
    offer_position_name = "[data-test=\"text-positionName\"]"

    @property
    def search_input(self):
        return self.page.get_by_role("button", name="Search: Job title, company,")

    @property
    def location_input(self):
        return self.page.get_by_role("combobox", name="Location")

    @property
    def search_button(self):
        return self.page.get_by_role("button", name="Search", exact=True)

    @property
    def salary_locator(self):
        return self.page.locator('text=Salary').locator('..').locator('div.MuiTypography-h4')
    def get_location_dropdown(self, location):
        return self.page.get_by_role("option", name=location)

    async def navigate(self) -> None:
        """Navigate to the main page of justjoin.it"""
        await self.go_to_page("https://justjoin.it/")

    async def search(self, keywords, location) -> None:
        """
        Enter keywords and execute job search.

        Args:
            keywords (str): The search keywords.
            location (str): The location for job search (currently unused in method).
        """
        await self.search_input.click()
        await self.page.wait_for_timeout(100)
        await self.search_input.type('a ' + keywords)
        await self.location_input.type(location)
        await self.get_location_dropdown(location).click()
        await self.search_button.click()

    async def accept_cookies(self) -> None:
        """Accept cookie consent on the website."""
        await self.click_locator(self.cookie_locator)

    async def jobs_list(self) -> list:
        """
        Retrieve a list of job offer elements from the current page.

        Returns:
            list: list of urls in current website view
        """
        locator = self.page.locator('a.offer-card')
        await locator.first.wait_for(timeout=5000)
        all_offers = await locator.all()
        urls = []
        for offer_locator in all_offers:
            href = await offer_locator.get_attribute("href")
            if href:
                urls.append('https://justjoin.it/' + self.strip_url(href))

        return urls

    async def scrape_single_offer(self, url:str) -> Optional[Dict]:
        """
        Scrapes data from a single job offer page.

        The method opens a new browser page, accepts cookies, and extracts
        relevant information about the job offer such as employer name,
        position, salary, and requirements. After scraping, the page is closed
        and the extracted data is returned as a dictionary.

        Args:
            url (str): URL of the job offer page to scrape.

        Returns:
            Optional[Dict]: A dictionary containing the scraped job data with the keys:
                - "employer" (str | None): Name of the employer.
                - "position" (str | None): Name of the job position.
                - "earning" (str | None): Salary or earning information.
                - "requirements" (List[str] | None): List of job requirements.
                - "url" (str): The original job offer URL.
              Returns None if scraping fails or no data is found.
        """
        async with self.sem:
            offer_page = await self.browser.new_page()
            await offer_page.goto(url)
            await offer_page.locator(self.cookie_locator).click()
            job_data = {
                "employer": await self.get_employer_name(offer_page),
                "position": await self.get_position_name(offer_page),
                "earning": await self.get_earning_amount(offer_page),
                "requirements": await self.get_job_requirement(offer_page),
                "url": url
            }
            # TODO: replace print with logger
            print(job_data)
            await offer_page.close()
            return job_data

    async def get_position_name(self, page) -> str:
        """Return the position name of the current job offer."""
        return await page.locator('h1').inner_text()

    async def get_earning_amount(self, page) -> str:
        """Return the earning amount of the current job offer as a single string."""
        try:
            salary_text =  await self.salary_locator.inner_text(timeout=5000)
        except PlaywrightTimeoutError:
            salary_text = "Not found"
        return salary_text

    async def get_job_requirement(self, page) -> str:
        """Return the job requirements of the current job offer."""
        texts =  await page.locator('text=Tech stack').locator('..').locator('h4').all_inner_texts()
        return "\n".join(texts)

    async def get_employer_name(self, page) -> str:
        """Return the employer's name of the current job offer."""
        return await page.locator("p:has(svg)").nth(1).inner_text()

    async def get_url(self, page) -> str:
        """Return the URL of the current job offer."""
        return self.strip_url(page.url)

    async def next_page(self) -> None:
        """Click the button to go to the next page of job listings."""
        await self.page.locator(self.next_page_button).click()

    async def sort_offers_from_newest(self):
        await self.page.wait_for_timeout(500)
        dropdown = self.page.locator("[name='sort_filter_button']").first
        await dropdown.click()
        await self.page.locator("[role='menuitem']", has_text='Latest').click()
        await self.page.wait_for_selector('.offer-card', timeout=5000)

    async def extract_job_data(self, offer_links_from_sheet: list) -> None:
        """
        Iterate through all pages and offers to extract job data.

        Stores extracted jobs in the `all_jobs` attribute.
        """
        latest_jobs = await self.jobs_list()
        urls = []
        while True:
            await self.page.evaluate("window.scrollBy(0, 400)")
            await self.page.wait_for_timeout(100)
            jobs = await self.jobs_list()
            if latest_jobs == jobs:
                break
            else:
                latest_jobs = jobs
                urls.extend(jobs)
        urls = set(urls)
        urls = urls.difference(set(offer_links_from_sheet))
        tasks = [self.scrape_single_offer(url) for url in urls]
        results = await asyncio.gather(*tasks)
        for job_data in results:
            if job_data:
                self.all_jobs.append(job_data)
