class BaseScraper:
    """
    Base class for web scrapers.

    Provides basic page interaction methods and defines the interface
    for scraper subclasses that implement job search, listing retrieval,
    and pagination.
    """

    def __init__(self, page):
        """
        Initialize the scraper with a Playwright page instance.

        Args:
            page: Playwright Page object used for web interactions.
        """
        self.page = page

    def search(self, keywords, location):
        """
        Perform a job search on the website.

        Args:
            keywords (str): Search keywords.
            location (str): Job location.

        Raises:
            NotImplementedError: Must be implemented in subclass.
        """
        raise NotImplementedError

    def get_jobs_listing(self):
        """
        Retrieve a list of job elements from the search results.

        Raises:
            NotImplementedError: Must be implemented in subclass.
        """
        raise NotImplementedError

    def get_job_details(self):
        """
        Extract details from a single job offer.

        Raises:
            NotImplementedError: Must be implemented in subclass.
        """
        raise NotImplementedError

    def next_page(self):
        """
        Navigate to the next page of search results.

        Raises:
            NotImplementedError: Must be implemented in subclass.
        """
        raise NotImplementedError

    def accept_cookies(self):
        """
        Accept cookie consent on the website.

        Raises:
            NotImplementedError: Must be implemented in subclass.
        """
        raise NotImplementedError

    def get_max_page(self):
        """
        Get the maximum number of pages available in search results.

        Raises:
            NotImplementedError: Must be implemented in subclass.
        """
        raise NotImplementedError

    def go_to_page(self, url):
        """
        Navigate to a specific URL.

        Args:
            url (str): The URL to navigate to.
        """
        self.page.goto(url)

    def type_text(self, locator, text):
        """
        Type text into an input field.

        Args:
            locator (str): The locator of the input element.
            text (str): The text to type.
        """
        self.page.locator(locator).type(text)

    def click_locator(self, locator):
        """
        Click on an element.

        Args:
            locator (str): The locator of the element to click.
        """
        self.page.locator(locator).click()