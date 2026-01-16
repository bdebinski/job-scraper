from playwright.async_api import Page

from .locators import OfferPageLocators
from .models import JobOffer

class PracujOfferParser:
    "Extracts data from single offer page."

    def __init__(self, page: Page, locators: OfferPageLocators):
        self.page = page
        self.locators = locators

    async def parse(self) -> JobOffer:
        return JobOffer(
            employer=await self.page.locator(self.locators.employer).inner_text(),
            position=await self.page.locator(self.locators.position).inner_text(),
            salary=await self._get_salary(),
            requirements=await self.page.locator(self.locators.requirements).inner_text(),
            url=self.page.url
        )

    async def _get_salary(self):
        elements = self.page.locator(self.locators.salary)
        texts = await elements.all_inner_texts()
        return "".join(texts)
