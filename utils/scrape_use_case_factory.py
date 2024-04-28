from enum import Enum

from url_scrape_use_case import UrlScrapeUseCase
from utils.csv_scrape_use_case import CSVScrapeUseCase
from utils.search_results_use_case import SearchResultsScrapeUseCase


class ScrapeInputTypes(Enum):
    SINGLE_URL = "single_url"
    CSV = "csv"
    SEARCH_RESULTS = "search_results"


use_case_mapping = {
    ScrapeInputTypes.SINGLE_URL.value: UrlScrapeUseCase,
    ScrapeInputTypes.CSV.value: CSVScrapeUseCase,
    ScrapeInputTypes.SEARCH_RESULTS.value: SearchResultsScrapeUseCase
}


def scraping_use_case_factory(input_type: str):
    use_case = use_case_mapping.get(input_type)
    if not use_case:
        raise NotImplementedError
    return use_case
