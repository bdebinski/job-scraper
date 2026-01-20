from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class NavigationLocators:
    search_input: str
    search_button: str
    location_input: str
    cookie_locator: str
    offers_list: str
    sort_button: str
    sort_option: str
    # locators for pracuj.pl
    next_page: Optional[str] = None
    max_page: Optional[str] = None

@dataclass(frozen=True)
class OfferPageLocators:
    employer: str
    position: str
    salary: str
    requirements: str

# --- PRACUJ.PL ---
PRACUJ_NAV = NavigationLocators(
    search_input="[data-test=\"input-kw\"] [data-test=\"input-field\"]",
    search_button="[data-test=\"search-button\"]",
    cookie_locator="[data-test=\"button-submitCookie\"]",
    offers_list="[data-test='section-offers'] [data-test='link-offer']",
    next_page="[data-test=\"top-pagination-next-button\"]",
    max_page="[data-test=\"top-pagination-max-page-number\"]",
    location_input="[data-test=\"input-wp\"] [data-test=\"input-field\"]",
    sort_button="[data-test='button-sort-type']",
    sort_option="role=treeitem[name*='Najnowsze']",
)

PRACUJ_OFFER = OfferPageLocators(
    employer= "[data-test=\"text-employerName\"]",
    requirements = "[data-test=\"section-requirements\"]",
    salary = "[data-test=\"text-earningAmount\"]",
    position = "[data-test=\"text-positionName\"]",
)

# --- JUST JOIN IT ---
JJIT_OFFER = OfferPageLocators(
    employer="div:has(h1) >> a[href*='/brands/']:not([name='aboutUs']) >> nth=0",
    requirements = "text=Tech stack >> .. >> h4",
    salary="xpath=/html/body/div[3]/div/div/div[4]/div/div[3]/div[2]/div[1]/div/div[2]/div",
    position = "h1",
)

JJIT_NAV = NavigationLocators(
    search_input="role=button[name*='Search: Job title, company,']",
    location_input="role=combobox[name='Location']",
    search_button="role=button[name='Search']",
    offers_list="a.offer-card",
    cookie_locator="role=button[name='Accept all']",
    sort_button="[name='sort_filter_button']",
    sort_option="[role='menuitem':has-text('Latest')]",
)
