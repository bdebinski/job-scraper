from playwright.sync_api import Locator

from base_scraper import BaseScraper

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
    offers_locator = "[data-test=\"link-offer\"]"
    next_page_button = "[data-test=\"top-pagination-next-button\"]"
    max_page_locator = "[data-test=\"top-pagination-max-page-number\"]"
    employer_name = "[data-test=\"text-employerName\"]"
    offer_requirements = "[data-test=\"section-requirements\"]"
    offer_salary = "[data-test=\"text-earningAmount\"]"
    offer_position_name = "[data-test=\"text-positionName\"]"

    def navigate(self) -> None:
        """Navigate to the main page of pracuj.pl."""
        self.go_to_page("http://pracuj.pl")

    def search(self, keywords, location) -> None:
        """
        Enter keywords and execute job search.

        Args:
            keywords (str): The search keywords.
            location (str): The location for job search (currently unused in method).
        """
        self.type_text(self.search_locator, keywords)
        self.click_locator(self.search_button)

    def accept_cookies(self) -> None:
        """Accept cookie consent on the website."""
        self.click_locator(self.cookie_locator)

    def jobs_list(self) -> Locator:
        """
        Retrieve a list of job offer elements from the current page.

        Returns:
            Locator: Playwright locator containing all job offer elements.
        """
        self.page.locator(self.section_offers_locator).locator('[data-test="link-offer"]').first.wait_for()
        return self.page.locator(self.section_offers_locator).locator('[data-test="link-offer"]')

    def extract_job_data(self) -> None:
        """
        Iterate through all pages and offers to extract job data.

        Stores extracted jobs in the `all_jobs` attribute.
        """
        max_page = self.get_max_page()
        for page_number in range(max_page):
            offers_list = self.jobs_list()
            number_of_offers = offers_list.count()
            for i in range(number_of_offers):
                offers_list.nth(i).click()
                job_data = {
                    "employer": self.get_employer_name(),
                    "position": self.get_position_name(),
                    "earning": self.get_earning_amount(),
                    "requirements": self.get_job_requirement(),
                    "url": self.get_url()
                }
                self.all_jobs.append(job_data)
                self.page.go_back()
            if page_number < max_page - 1:
                self.next_page()

    def get_position_name(self) -> str:
        """Return the position name of the current job offer."""
        return self.page.locator(self.offer_position_name).inner_text()

    def get_earning_amount(self) -> str:
        """Return the earning amount of the current job offer as a single string."""
        elements = self.page.locator(self.offer_salary)
        earning_amount = elements.all_inner_texts()
        return "".join(earning_amount)

    def get_job_requirement(self) -> str:
        """Return the job requirements of the current job offer."""
        return self.page.locator(self.offer_requirements).inner_text()

    def get_employer_name(self) -> str:
        """Return the employer's name of the current job offer."""
        return self.page.locator(self.employer_name).inner_text()

    def get_url(self) -> str:
        """Return the URL of the current job offer."""
        return self.page.url

    def max_page(self) -> int:
        """
        Retrieve the maximum number of pages available for the search.

        Returns:
            int: Maximum page number. Defaults to 1 if not found.
        """
        try:
            max_page = int(self.page.locator(self.max_page_locator).inner_text(timeout=100))
        except:
            max_page = 1
        return max_page

    def next_page(self) -> None:
        """Click the button to go to the next page of job listings."""
        self.page.locator(self.next_page_button).click()