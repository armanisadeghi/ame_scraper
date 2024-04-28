# AiMatrixScraper Project: items.py

import scrapy


class AmeScraperItem(scrapy.Item):
    print("[Scrapy Items.py) AmeScraperItem")
    url = scrapy.Field()
    clean_body = scrapy.Field()
    header_structure = scrapy.Field()
    links = scrapy.Field()
    images = scrapy.Field()
    sitemap_links = scrapy.Field()
    schema_org_data = scrapy.Field()
    title = scrapy.Field()
    sitemap_contents = scrapy.Field()
