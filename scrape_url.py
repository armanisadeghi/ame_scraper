from multiprocessing import Process

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from ame_scraper.spiders.url_spider import UrlSpider
from utils.scrape_use_case import ScrapeUseCase


class UrlScrapeUseCase(ScrapeUseCase):
    def __init__(self, url: str):
        self._url = url

    def execute(self):
        self._preprocess()
        self._process()

    def _preprocess(self):
        from utils.scrape_preprocessing_util import preprocess_url
        preprocess_url(self._url)

    def _process(self):
        p = Process(target=self.run_spider)
        p.start()
        p.join()

    def run_spider(self):
        process = CrawlerProcess(get_project_settings())

        # Pass the custom URL to the spider
        process.crawl(UrlSpider, url=self._url)
        process.start()



if __name__ == '__main__':
    #url = 'https://pypi.org/project/markdown-it-py/'
    url = 'https://mealprepdelivery.com'
    use_case = UrlScrapeUseCase(url)
    use_case.execute()


