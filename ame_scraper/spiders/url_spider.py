import json
import re
from urllib.parse import urljoin
import scrapy
from scrapy.http import Response
import logging
from scrapy.utils.sitemap import sitemap_urls_from_robots, Sitemap
from utils.calculate_md import calculate_md5_hash
from w3lib.html import remove_comments, remove_tags
from utils.check_urls import get_domain_from_url
from db_ops import create_connection, execute_sql
from ame_scraper.items import AmeScraperItem
from ame_scraper.settings import (
    DOWNLOADER_MIDDLEWARES,
    ITEM_PIPELINES,
)


class UrlSpider(scrapy.Spider):
    name = "url_spider"
    custom_settings = {
        "ITEM_PIPELINES": ITEM_PIPELINES,
        "DOWNLOADER_MIDDLEWARES": DOWNLOADER_MIDDLEWARES,
    }
    print(f"[Scrapy URl Spider] Custom settings: {custom_settings}")

    def __init__(self, url=None, *args, **kwargs):
        super(UrlSpider, self).__init__(*args, **kwargs)
        self.start_urls = [url] if url else []
        self.database = "ame_scraper.db"
        self.conn = create_connection(self.database)
        self._sitemap_urls = set()
        self._sitemap_contents = set()

    def start_requests(self):
        yield scrapy.Request(
            url=self.start_urls[0], callback=self.parse, dont_filter=True
        )

    def parse(self, response):
        self._sitemap_urls.clear()
        self._sitemap_contents.clear()
        sitemap_link = response.xpath("//link[@rel='sitemap']/@href").extract_first()
        if sitemap_link:
            yield scrapy.Request(sitemap_link, callback=self._parse_sitemap)
        else:
            robots_url = urljoin(get_domain_from_url(response.url), "/robots.txt")
            yield scrapy.Request(robots_url, self._parse_robots)

    def _parse_sitemap(self, response):
        self._sitemap_contents.add(response.text)

        # Process nested sitemaps
        if response.url.endswith(".xml"):
            sitemap = Sitemap(response.body)
            for url in sitemap:
                url_loc = url["loc"]
                if "sitemap" in url_loc and url_loc not in self._sitemap_urls:
                    self._sitemap_urls.add(url_loc)
                    yield scrapy.Request(url_loc, callback=self._parse_sitemap)
        elif response.url.endswith(".txt"):
            urls = response.text.splitlines()
            for url in urls:
                if "sitemap" in url and url not in self._sitemap_urls:
                    self._sitemap_urls.add(url)
                    yield scrapy.Request(url, callback=self._parse_sitemap)
        else:
            urls = sitemap_urls_from_robots(response.text)
            for url in urls:
                if "sitemap" in url and url not in self._sitemap_urls and url.startswith('http'):
                    self._sitemap_urls.add(url)
                    yield scrapy.Request(url, callback=self._parse_sitemap)

        if self.start_urls:
            yield scrapy.Request(self.start_urls[0], callback=self._parse_url_content)

    def _parse_robots(self, response):
        for url in sitemap_urls_from_robots(response.text):
            yield scrapy.Request(url, callback=self._parse_sitemap)

    def _parse_url_content(self, response):
        domain_id = self._get_or_create_domain(response.url)
        page_id = self._get_or_create_webpage(response.url, domain_id)

        title = response.xpath("//title/text()").get()
        body_content = response.xpath("//body").get()
        clean_body = self._sanitize_html(body_content)
        links = self._get_links_data_from_response(response)
        images = self._get_img_data_from_response(response)
        schema_org_data = self._get_schema_org_data(response)
        header_structure = self._header_html_to_json(response)

        # Insert scrape results
        content_hash = calculate_md5_hash(clean_body)
        execute_sql(self.conn, """
            INSERT INTO scrape_results (webpage_id, title, content, content_hash, content_length) 
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(webpage_id) DO UPDATE SET 
            content = excluded.content, content_hash = excluded.content_hash, title = excluded.title
            """, (page_id, title, clean_body, content_hash, len(clean_body)))
        # Output item
        item = AmeScraperItem({
            "url": response.url,
            "title": title,
            "clean_body": clean_body,
            "header_structure": header_structure,
            "links": links,
            "images": images,
            "schema_org_data": schema_org_data,
            "sitemap_links": list(self._sitemap_urls),
            "sitemap_contents": list(self._sitemap_contents),
        })
        yield item

    def _get_or_create_domain(self, url):
        domain_url = get_domain_from_url(url)
        result = execute_sql(self.conn, "SELECT ROWID FROM domains WHERE url=?", (domain_url,), fetch_one=True)
        if result:
            return result[0]
        execute_sql(self.conn, "INSERT INTO domains (url) VALUES (?)", (domain_url,))
        return execute_sql(self.conn, "SELECT last_insert_rowid()", fetch_one=True)[0]

    def _get_or_create_webpage(self, url, domain_id):
        result = execute_sql(self.conn, "SELECT id FROM webpages WHERE url=?", (url,), fetch_one=True)
        if result:
            return result[0]
        execute_sql(self.conn, "INSERT INTO webpages (url, domain_id) VALUES (?, ?)", (url, domain_id))
        return execute_sql(self.conn, "SELECT last_insert_rowid()", fetch_one=True)[0]

    @staticmethod
    def _header_html_to_json(response):
        header_info = {
            "title": response.xpath("//title/text()").get(),
            "meta_tags": []
        }

        for meta in response.xpath("//head/meta"):
            meta_info = {}
            name = meta.xpath("@name").get()
            content = meta.xpath("@content").get()
            if name:
                meta_info["name"] = name
            if content:
                meta_info["content"] = content
            if meta_info:
                header_info["meta_tags"].append(meta_info)

        return json.dumps(header_info)

    @staticmethod
    def _sanitize_html(html_content):
        if not html_content:
            return ""
        sanitized_content = re.sub(r"\s+", " ", html_content)

        return sanitized_content.strip()

    @staticmethod
    def _get_img_data_from_response(response: Response):
        images = []
        for img in response.xpath("//img"):
            img_data = {
                "src": urljoin(response.url, img.xpath("@src").get()),
                "alt": img.xpath("@alt").get() or "",
                "class_attr": img.xpath("@class").get() or "",
            }
            if id_ := img.xpath("@id").get():
                img_data["id_attr"] = id_
            images.append(img_data)
        return images

    def _get_links_data_from_response(self, response: Response):
        links = []
        for link in response.xpath("//a"):
            text = self._sanitize_html(link.xpath("text()").get())
            if not text:
                continue
            link_data = {
                "text": self._sanitize_html(link.xpath("text()").get()),
                "href": urljoin(response.url, link.xpath("@href").get()),
                "class_attr": link.xpath("@class").get() or "",
            }
            if id_ := link.xpath("@id").get():
                link_data["id_attr"] = id_
            links.append(link_data)
        return links

    @staticmethod
    def _get_schema_org_data(response):
        schema_org_data = []
        for script in response.xpath("//script[@type='application/ld+json']/text()").extract():
            try:
                cleaned_content = remove_comments(remove_tags(script))
                data = json.loads(cleaned_content)
                schema_org_data.append(data)
            except json.JSONDecodeError:
                logging.warning(f"JSON-LD decoding failed at {response.url}")
        return schema_org_data
