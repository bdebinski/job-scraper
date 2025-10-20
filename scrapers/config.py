import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class ScraperConfig:
    """Configuration for all jobs scrapers"""
    def __init__(self):
        # Google Sheets
        self.credentials_path: str = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
        self.spreadsheet_name: str = os.getenv("SPREADSHEET_NAME", "job-offers")

        # Search params
        self.search_keywords: str = os.getenv("SEARCH_KEYWORDS", 'python test')
        self.search_location: str = os.getenv("SEARCH_LOCATION", "Łódź")

        # Scraping
        self.max_open_pages: int = int(os.getenv("MAX_OPEN_PAGES", '5'))
        self.scroll_step: int = 400

        # Timeouts
        self.page_load_timeout: int = 30000
        self.element_wait_timeout: int = 5000

    @classmethod
    def from_env(cls):
        """Create config from environment variables"""
        return cls()
