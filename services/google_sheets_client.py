import os
from loguru import logger
import gspread
from gspread import Spreadsheet, Worksheet, WorksheetNotFound, SpreadsheetNotFound

from core.config import ScraperConfig


class GoogleSheetClient:
    def __init__(self, config: ScraperConfig = ScraperConfig.from_env()) -> None:
        creds_path = config.credentials_path or os.getenv(
            "GOOGLE_CREDENTIALS_PATH", "credentials.json"
        )

        if not os.path.exists(creds_path):
            raise FileNotFoundError(
                f"Credentials file not found: {creds_path}. "
                "Set GOOGLE_CREDENTIALS_PATH env variable"
            )
        self.gc = gspread.service_account(creds_path)
        self.spreadsheet = self.open_spreadsheet(config.spreadsheet_name)

    def open_spreadsheet(self, sheet_name) -> Spreadsheet:
        try:
            return self.gc.open(sheet_name)
        except SpreadsheetNotFound:
            logger.error("Sheet with provided name is not found.")
            raise

    def get_worksheet(self, index: int) -> Worksheet:
        try:
            worksheet = self.spreadsheet.get_worksheet(index)
            logger.debug(f"Retrieved worksheet at index {index}.")
            return worksheet
        except WorksheetNotFound:
            logger.error(f"Worksheet at index: {index} not found.")
            raise
