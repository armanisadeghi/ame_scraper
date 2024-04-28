# AiMatrixScraper Project: ame_scraper/proxy.py

# brightdata.com
class Proxy:
    def __init__(
        self, host: str, port: int, username: str = None, password: str = None
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        print(f"[Scrapy Proxy] {self}")
