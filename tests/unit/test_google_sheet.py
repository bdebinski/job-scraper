from unittest.mock import patch, MagicMock

import pytest

from google_sheets_client import GoogleSheetClient
from main import main

@pytest.mark.asyncio
@patch("main.run_scraper")
@patch("main.GoogleSheetClient")
@patch("main.ScraperConfig")
async def test_main(scraper_config_mock, google_sheet_client_mock, mock_run_scraper):
    mock_config = scraper_config_mock.from_env.return_value
    mock_config.spreadsheet_name = "job-offers"
    mock_config.config = "fake.json"

    mock_google = google_sheet_client_mock.return_value
    mock_spreadsheet = mock_google.spreadsheet

    mock_worksheet = MagicMock()
    mock_worksheet.col_values.return_value = ["url1", "url2"]
    mock_spreadsheet.get_worksheet.return_value = mock_worksheet

    mock_run_scraper.return_value = []
    await main()

    mock_google.open_spreadsheet.assert_called_once_with("job-offers")

@patch("google_sheets_client.os.path.exists")
def test_init_raises_error(mock_exists):
    mock_exists.return_value = False
    with pytest.raises(FileNotFoundError):
        GoogleSheetClient()
    mock_exists.assert_called_once_with('credentials.json')
