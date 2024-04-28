import csv
from multiprocessing import Process

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from ame_scraper.spiders.url_spider import UrlSpider
from utils.scrape_use_case import ScrapeUseCase


class CSVScrapeUseCase(ScrapeUseCase):
    def __init__(self, file):
        self._file = file
        self.urls = []

    def execute(self):
        self._preprocess()
        self._start_process()

    def _preprocess(self):
        """Load URLs from a CSV file and store them in a list."""
        with open(self._file, newline='') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if not row:
                    raise ValueError("CSV row is empty. URL should be in the first column")
                self.urls.append(row[0])

    def _start_process(self):
        """Start the crawling process using multiprocessing."""
        processes = []
        for url in self.urls:
            p = Process(target=self.run_spider, args=(url,))
            processes.append(p)
            p.start()

        for p in processes:
            p.join()

    def run_spider(self, url):
        """Run the spider for a single URL."""
        process = CrawlerProcess(get_project_settings())
        process.crawl(UrlSpider, url=url)
        process.start()

# Usage example:
if __name__ == "__main__":
    csv_use_case = CSVScrapeUseCase('urls.csv')
    csv_use_case.execute()
