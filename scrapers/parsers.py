import playwright.async_api
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

class JustJoinItOfferParser:
    "Extracts data from single offer page."

    def __init__(self, page: Page, locators: OfferPageLocators):
        self.page = page
        self.locators = locators

    async def parse(self) -> JobOffer:
        return JobOffer(
            employer=await self.page.locator(self.locators.employer).inner_text(),
            position=await self.page.locator(self.locators.position).inner_text(),
            salary=await self._get_salary(),
            requirements=await self._get_requirements(),
            url=self.page.url
        )
    async def _get_requirements(self):
        requirements = await self.page.locator(self.locators.requirements).all_inner_texts()
        return "\n".join(requirements)

    async def _get_salary(self):
        b2b = await self._parse_b2b_salary()
        perm = await self._parse_perm_salary()
        salary = b2b + '\n' + perm
        return salary

    async def _parse_b2b_salary(self):
        try:
            return await self.page.get_by_text("Net per month - B2B").locator("..").first.inner_text(timeout=2000)
        except playwright.async_api.TimeoutError as e:
            return ""

    async def _parse_perm_salary(self):
        try:
            return await self.page.get_by_text("Gross per month").locator("..").first.inner_text(timeout=2000)
        except playwright.async_api.TimeoutError as e:
            return ""
