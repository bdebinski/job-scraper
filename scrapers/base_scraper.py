import asyncio
from abc import ABC, abstractmethod
from typing import Any

import playwright.async_api
from playwright.async_api import Page
from loguru import logger

from scrapers.locators import NavigationLocators
from core.models import JobOffer


class BaseScraper(ABC):
    """
    Base class for web scrapers.

    Provides basic page interaction methods and defines the interface
    for scraper subclasses that implement job search, listing retrieval,
    and pagination.
    """

    cookie_locator: str | None = None

    def __init__(
        self, page: Page, nav_locators: NavigationLocators, semaphore_value: int = 5
    ) -> None:
        """
        Initialize the scraper with a Playwright page instance.

        Args:
            page: Playwright Page object used for web interactions.
            nav_locators: NavigationLocators for specific web scraper.
            semaphore_value: number of pages which can be open at once
        """
        self.page = page
        self.nav_locators = nav_locators
        self.url = None
        self.all_jobs: list[str] = []
        self.sem = asyncio.Semaphore(semaphore_value)

    async def navigate(self) -> None:
        await self.go_to_page(self.url)

    @abstractmethod
    async def search(self, keywords: str) -> None:
        """
        Perform a job search on the website.

        Args:
            keywords (str): Search keywords.

        Raises:
            NotImplementedError: Must be implemented in subclass.
        """
        ...

    @abstractmethod
    async def jobs_list(self) -> list[str]:
        """
        Retrieve a list of job elements from the search results.

        Raises:
            NotImplementedError: Must be implemented in subclass.
        """
        ...

    @abstractmethod
    async def extract_job_data(
        self, offer_links_from_sheet: list
    ) -> list[JobOffer]: ...

    async def accept_cookies(self) -> None:
        """
        Accept cookie consent on the website.

        Raises:
            NotImplementedError: Must be implemented in subclass.
        """
        try:
            await self.click_locator(self.nav_locators.cookie_locator)
        except playwright.async_api.TimeoutError:
            logger.info("No cookie banner visible - assuming cookies already accepted.")

    async def go_to_page(self, url: str) -> None:
        """
        Navigate to a specific URL.

        Args:
            url (str): The URL to navigate to.
        """
        await self.page.goto(url)

    async def type_text(self, locator: str, text: str) -> None:
        """
        Type text into an input field.

        Args:
            locator (str): The locator of the input element.
            text (str): The text to type.
        """
        await self.page.locator(locator).fill(text)

    async def click_locator(self, locator: str) -> None:
        """
        Click on an element.

        Args:
            locator (str): The locator of the element to click.
        """
        await self.page.locator(locator).click()

    async def get_url(self, page: Page) -> str:
        """
        Return the URL of the current job offer.

        Args:
            page (Page): page object
        """
        return self.strip_url(page.url)

    @staticmethod
    def strip_url(url: str) -> str:
        """
        Strip url to remove random generated content in the link.

        Args:
            url (str): url of the offer.
        """
        return url.split("?", 1)[0]

    @abstractmethod
    def get_parser(self, page: Page) -> Any: ...

    async def scrape_single_offer(self, url: str) -> JobOffer | None:
        """
        Scrapes data from a single job offer page.

        The method opens a new browser page, accepts cookies, and extracts
        relevant information about the job offer such as employer name,
        position, salary, and requirements. After scraping, the page is closed
        and the extracted data is returned as a dictionary.

        Args:
            url (str): URL of the job offer page to scrape.

        Returns:
            JobOffer or None if there is no JobOffers
        """
        async with self.sem:
            offer_page = await self.page.context.new_page()
            try:
                await offer_page.goto(url)
                parser = self.get_parser(offer_page)
                job_data = await parser.parse()
                logger.info(f"Scraped: {job_data.position} in {job_data.employer}")
                return job_data
            except Exception as e:
                logger.error(f"Failed to scrape {url}: {e}")
                return None
            finally:
                await offer_page.close()

    @staticmethod
    def _validate_scraper_params(keywords, location) -> tuple[str, str]:
        """
        Check if keywords and location are non empty or whitespace

        Args:
            keywords (str): job position keywods.
            location (str): city name.
        """
        if not keywords or not keywords.strip():
            raise ValueError("Keywords can't be empty or whitespace")
        if not location or not location.strip():
            raise ValueError("Location can't be empty or whitespace")
        return keywords, location

    async def setup_network_interception(self) -> None:
        """
        Setup newtork interception to block redundant content from website. Blocks images, media, font, imageset, beacon and stylesheet.

        """
        excluded_resources = [
            "image",
            "media",
            "font",
            "imageset",
            "beacon",
            "ad",
            "stylesheet",
        ]

        async def intercept(route):
            if route.request.resource_type in excluded_resources:
                # logger.debug(f"Blocked: {route.request.resource_type} - {route.request.url[:50]}...")
                await route.abort()
            else:
                await route.continue_()

        await self.page.context.route("**/*", intercept)
        logger.info(f"Network interception active for {self.__class__.__name__}")
