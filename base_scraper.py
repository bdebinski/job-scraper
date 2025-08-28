class BaseScraper:
    def __init__(self, page):
        self.page = page

    def search(self, keywords, location):
        raise NotImplementedError

    def get_jobs_listing(self):
        raise NotImplementedError

    def get_job_details(self):
        raise NotImplementedError

    def next_page(self):
        raise NotImplementedError

    def accept_cookies(self):
        raise NotImplementedError

    def get_max_page(self):
        raise NotImplementedError

    def go_to_page(self, url):
        self.page.goto(url)

    def type_text(self, locator, text):
        self.page.locator(locator).type(text)

    def click_locator(self, locator):
        self.page.locator(locator).click()
