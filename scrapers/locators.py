from dataclasses import dataclass

@dataclass(frozen=True)
class OfferPageLocators:
    employer: str
    position: str
    salary: str
    requirements: str

PRACUJ_LOCATORS = OfferPageLocators(
    employer= "[data-test=\"text-employerName\"]",
    requirements = "[data-test=\"section-requirements\"]",
    salary = "[data-test=\"text-earningAmount\"]",
    position = "[data-test=\"text-positionName\"]",
)
