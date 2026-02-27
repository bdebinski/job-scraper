import os
from dataclasses import dataclass

from scrapers.justjoinit_scraper import JustJoinItScraper
from scrapers.pracuj_scraper import PracujScraper


@dataclass
class ScraperConfig:
    """Configuration for all jobs scrapers"""

    # Google Sheets
    credentials_path: str = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
    spreadsheet_name: str = os.getenv("SPREADSHEET_NAME", "job-offers")

    # Search params
    search_keywords: str = os.getenv("SEARCH_KEYWORDS", "Test Automation Engineer")
    search_location: str = os.getenv("SEARCH_LOCATION", "Łódź")

    # Scraping
    max_open_pages: int = int(os.getenv("MAX_OPEN_PAGES", "5"))
    scroll_step: int = 400
    SCRAPER_TO_SHEET = {PracujScraper: "Pracuj", JustJoinItScraper: "JustJoinIT"}

    # Timeouts
    page_load_timeout: int = 30000
    element_wait_timeout: int = 5000

    @classmethod
    def from_env(cls):
        """Create config from environment variables"""
        return cls()
