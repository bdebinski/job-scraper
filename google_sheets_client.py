import os

import gspread
from gspread import Worksheet, WorksheetNotFound, SpreadsheetNotFound

class GoogleSheetClient:
    def __init__(self, credentials_path=None):
        creds_path = credentials_path or os.getenv("GOOGLE_CREDENTIALS_PATH", 'credentials.json')

        if not os.path.exists(creds_path):
            raise FileNotFoundError(f"Credentials file not found: {creds_path}. "
                                    "Set GOOGLE_CREDENTIALS_PATH env variable")
        self.gc = gspread.service_account(creds_path)
        self.spreadsheet = None

    def open_spreadsheet(self, sheet_name) -> None:
        try:
            self.spreadsheet =  self.gc.open(sheet_name)
        except SpreadsheetNotFound:
            print('Sheet with provided name is not found')

    def get_worksheet(self, index: int) -> Worksheet | None:
        try:
            return self.spreadsheet.get_worksheet(index)
        except WorksheetNotFound:
            print('Worksheet not found')
