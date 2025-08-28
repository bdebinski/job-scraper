from base_scraper import BaseScraper


class PracujScraper(BaseScraper):
    search_locator = "[data-test=\"input-kw\"] [data-test=\"input-field\"]"
    search_button = "[data-test=\"search-button\"]"
    cookie_locator = "[data-test=\"button-submitCookie\"]"
    section_offers_locator = "[data-test=\"section-offers\"]"
    offers_locator = "[data-test=\"link-offer\"]"
    all_jobs = []
    def navigate(self):
        self.go_to_page("http://pracuj.pl")

    def search(self, keywords, location):
        self.type_text(self.search_locator, keywords)
        self.click_locator(self.search_button)

    def accept_cookies(self):
        self.click_locator(self.cookie_locator)

    def get_jobs_listing(self):
        self.page.locator(self.section_offers_locator).locator('[data-test="link-offer"]').first.wait_for()
        return self.page.locator(self.section_offers_locator).locator('[data-test="link-offer"]')

    def get_offer_data(self):
        max_page = self.get_max_page()
        for page_number in range(max_page):
            offers_list = self.get_jobs_listing()
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
                self.go_next_page()

    def get_position_name(self):
        return self.page.locator("[data-test=\"text-positionName\"]").inner_text()

    def get_earning_amount(self):
        elements = self.page.locator("[data-test=\"text-earningAmount\"]")
        earning_amount = elements.all_inner_texts()
        return "".join(earning_amount)

    def get_job_requirement(self):
        return self.page.locator("[data-test=\"section-requirements\"]").inner_text()

    def get_employer_name(self):
        return self.page.locator("[data-test=\"text-employerName\"]").inner_text()

    def get_url(self):
        return self.page.url

    def get_max_page(self):
        try:
            max_page = int(self.page.locator("[data-test=\"top-pagination-max-page-number\"]").inner_text(timeout=100))
        except:
            max_page = 1
        return max_page

    def go_next_page(self):
        self.page.locator("[data-test=\"top-pagination-next-button\"]").click()