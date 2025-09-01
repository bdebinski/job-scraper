import gspread
from gspread import Worksheet, WorksheetNotFound

# columns = ["employer", "position", "earning", "requirements", "url", "status"]
#
# rows = [[job.get(col, "") for col in columns] for job in jobs]
# worksheet = sh.get_worksheet(0)
# worksheet.insert_rows(columns, 1)
# # check if offer is unique
# worksheet.insert_rows(rows, 2)


class GoogleSheetClient:
    def __init__(self):
        self.gc = gspread.oauth()
        self.spreadsheet = None

    def open_spreadsheet(self, sheet_name) -> None:
        try:
            self.spreadsheet =  self.gc.open(sheet_name)
        except gspread.exceptions.SpreadsheetNotFound:
            print('Sheet with provided name is not found')

    def get_worksheet(self, index: int) -> Worksheet | None:
        try:
            return self.spreadsheet.get_worksheet(index)
        except WorksheetNotFound:
            print('Worksheet not found')