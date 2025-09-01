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

    @abstractmethod
    async def extract_job_data(self):
        """
        Extract details from a single job offer.

        Raises:
            NotImplementedError: Must be implemented in subclass.
        """
        ...

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

    @abstractmethod
    async def filter_jobs(self):
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