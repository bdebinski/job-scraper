from unittest.mock import AsyncMock, MagicMock

import pytest

from pracuj_scraper import PracujScraper

@pytest.mark.asyncio
async def test_get_position_name():
    fake_page = MagicMock()
    fake_browser = MagicMock()
    fake_locator = AsyncMock()
    fake_page.locator.return_value = fake_locator
    scraper = PracujScraper(fake_page, fake_browser)
    fake_locator.inner_text.return_value = 'python developer'
    result = await scraper.get_position_name(fake_page)

    scraper.page.locator.assert_called_once_with(scraper.offer_position_name)
    scraper.page.locator.return_value.inner_text.assert_awaited_once()
    assert result == 'python developer'