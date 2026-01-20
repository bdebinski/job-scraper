#test strip url
import pytest

from scrapers.base_scraper import BaseScraper


@pytest.mark.parametrize("url, expected_url", [("https://url.pl/some_data?xyz", "https://url.pl/some_data"),
                                                ("https://justjoin.it/job-offer/warszawa-javascript-0a939ea0?filters", "https://justjoin.it/job-offer/warszawa-javascript-0a939ea0"),
                                                ("https://www.pracuj.pl/praca/assembly,1004580674?s=3bed36ad&searchId=MTc2ODgxODg0MzQ4OC42NTk0", "https://www.pracuj.pl/praca/assembly,1004580674")
                                         ])
def test_strip_url(url, expected_url):
    stripped_url = BaseScraper.strip_url(url)
    assert stripped_url == expected_url


def test_validate_params_with_valid_params():
    params = BaseScraper._validate_scraper_params("test", "city")
    assert params == ("test", "city")

@pytest.mark.parametrize("keywords, location", [("test", ""),
                                                ("", "test"),
                                                ("", "")
                                         ])
def test_validate_params_with_invalid_params(keywords, location):
    with pytest.raises(ValueError):
        BaseScraper._validate_scraper_params(keywords, location)
