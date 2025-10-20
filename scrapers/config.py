import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class ScraperConfig:
    """Configuration for all jobs scrapers"""
    def __init__(self):
        # Google Sheets
        credentials_path: str = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
        spreadsheet_name: str = os.getenv("SPREADSHEET_NAME", "job-offers")

        # Search params
        search_keywords: str = os.getenv("SEARCH_KEYWORDS", 'python test')
        search_location: str = os.getenv("SEARCH_LOCATION", "Łódź")

        # Scraping
        max_open_pages: int = int(os.getenv("MAX_OPEN_PAGES", '5'))
        scroll_step: int = 400

        # Timeouts
        page_load_timeout: int = 30000
        element_wait_timeout: int = 5000

    @classmethod
    def from_env(cls):
        """Create config from environment variables"""
        return cls()
