import gspread
from gspread import Worksheet, WorksheetNotFound, SpreadsheetNotFound

class GoogleSheetClient:
    def __init__(self):
        self.gc = gspread.service_account('job-scraper-470320-69bdf1515c05.json')
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
