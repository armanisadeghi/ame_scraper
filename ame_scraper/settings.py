# # AiMatrixScraper Project: ame_scraper/settings.py
import os
from ame_scraper.proxy import Proxy
from dotenv import load_dotenv
load_dotenv()

BRIGHTDATA_DATACENTER_1_USERNAME = os.getenv("BRIGHTDATA_DATACENTER_1_USERNAME")
BRIGHTDATA_DATACENTER_1_PASSWORD = os.getenv("BRIGHTDATA_DATACENTER_1_PASSWORD")

# This is EXTREMELY EXPENSIVE! DO NOT USE UNLESS EVERYTHING ELSE FAILS AND YOU HAVE APPROVAL FROM ARMANI!
# This is a dedicated residential proxy that should only be used for sites that are impossible otherwise and the data is small.
BRIGHTDATA_ISP_1_USERNAME = os.getenv("BRIGHTDATA_ISP_1_USERNAME")
BRIGHTDATA_ISP_1_PASSWORD = os.getenv("BRIGHTDATA_ISP_1_PASSWORD")

BOT_NAME = "ame_scraper"

SPIDER_MODULES = ["ame_scraper.spiders"]
NEWSPIDER_MODULE = "ame_scraper.spiders"

PROXY_LIST = [
    Proxy(host="brd.superproxy.io", port=22225, username=BRIGHTDATA_DATACENTER_1_USERNAME, password=BRIGHTDATA_DATACENTER_1_PASSWORD),
]

ISP_PROXY_LIST = [
    Proxy(host="brd.superproxy.io", port=22225, username=BRIGHTDATA_ISP_1_USERNAME, password=BRIGHTDATA_ISP_1_PASSWORD),
]



USER_AGENTS = [
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/16E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36 Edge/105.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:105.0) Gecko/20100101 Firefox/105.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_0_0) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Safari/605.1.15",
    "Mozilla/5.0 (Linux; Android 12; SM-G960U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; AS; rv:11.0) like Gecko",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:105.0) Gecko/20100101 Firefox/105.0",
    "Mozilla/5.0 (X11; Linux x86_64; rv:105.0) Gecko/20100101 Firefox/105.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36 OPR/82.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_0_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36 Brave/105.0.0.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/99.0.9999.999 Chrome/99.0.9999.999 Safari/537.36 Edg/99.0.9999.999",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/99.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_0_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15",
    "Mozilla/5.0 (Linux; Android 10; SM-G960U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.9999.999 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; AS; rv:11.0) like Gecko",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:99.0) Gecko/20100101 Firefox/99.0",
    "Mozilla/5.0 (X11; Linux x86_64; rv:99.0) Gecko/20100101 Firefox/99.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.9999.999 Safari/537.36",
]

ROBOTSTXT_OBEY = False

DOWNLOADER_MIDDLEWARES = {
    "ame_scraper.middlewares.AidreamScraperDownloaderMiddleware": 543,
    "ame_scraper.middlewares.RandomProxyMiddleware": 400,
    "ame_scraper.middlewares.RandomUserAgentMiddleware": 500,
    "ame_scraper.middlewares.useragent.UserAgentMiddleware": None,
}

ITEM_PIPELINES = {
    "ame_scraper.pipelines.AiDreamScraperPipeline": 300,
}

REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"
