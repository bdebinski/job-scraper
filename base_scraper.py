import asyncio
from abc import ABC, abstractmethod


class BaseScraper(ABC):
    """
    Base class for web scrapers.

    Provides basic page interaction methods and defines the interface
    for scraper subclasses that implement job search, listing retrieval,
    and pagination.
    """

    def __init__(self, page, browser):
        """
        Initialize the scraper with a Playwright page instance.

        Args:
            page: Playwright Page object used for web interactions.
        """
        self.page = page
        self.browser = browser
        self.all_jobs = []

    @abstractmethod
    async def search(self, keywords, location):
        """
        Perform a job search on the website.

        Args:
            keywords (str): Search keywords.
            location (str): Job location.

        Raises:
            NotImplementedError: Must be implemented in subclass.
        """
        ...

    @abstractmethod
    async def jobs_list(self):
        """
        Retrieve a list of job elements from the search results.

        Raises:
            NotImplementedError: Must be implemented in subclass.
        """
        ...

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
                    print(f"URL already exists: {url}. Stopping further scraping on this page.")
                    should_continue_scraping = False
                    break
                unique_offers_urls.append(url)
            if not should_continue_scraping:
                break
            tasks = [self.scrape_single_offer(url) for url in offer_urls]
            results = await asyncio.gather(*tasks)
            for job_data in results:
                if job_data:
                    self.all_jobs.append(job_data)

            if page_number + 1 < max_page:
                await self.next_page()

    @abstractmethod
    async def next_page(self):
        """
        Navigate to the next page of search results.

        Raises:
            NotImplementedError: Must be implemented in subclass.
        """
        ...

    @abstractmethod
    async def accept_cookies(self):
        """
        Accept cookie consent on the website.

        Raises:
            NotImplementedError: Must be implemented in subclass.
        """
        ...

    @abstractmethod
    async def max_page(self):
        """
        Get the maximum number of pages available in search results.

        Raises:
            NotImplementedError: Must be implemented in subclass.
        """
        ...

    async def go_to_page(self, url):
        """
        Navigate to a specific URL.

        Args:
            url (str): The URL to navigate to.
        """
        await self.page.goto(url)

    async def type_text(self, locator, text):
        """
        Type text into an input field.

        Args:
            locator (str): The locator of the input element.
            text (str): The text to type.
        """
        await self.page.locator(locator).type(text)

    async def click_locator(self, locator):
        """
        Click on an element.

        Args:
            locator (str): The locator of the element to click.
        """
        await self.page.locator(locator).click()

    @staticmethod
    def strip_url(url: str) -> str:
        return url.split("?", 1)[0]

    async def sort_offers_from_newest(self):
        ...

    @abstractmethod
    async def scrape_single_offer(self, url):
        ...