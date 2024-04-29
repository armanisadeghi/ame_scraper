# AiMatrixScraper Project: ame_scraper/pipelines.py
import datetime
import json
import logging
from utils.check_urls import get_domain_from_url
from utils.calculate_md import calculate_md5_hash
from db_ops import create_connection, execute_sql


class AiDreamScraperPipeline:
    def __init__(self):
        self.database = "ame_scraper.db"
        self.conn = create_connection(self.database)
        print("[Scrapy Pipeline] AiDreamScraperPipeline initialized with database connection.")

    def process_item(self, item, spider):
        logging.info(f"Processing item: {item}")
        domain_url = get_domain_from_url(item["url"])

        # Ensure the domain exists and get its id
        domain_id = execute_sql(self.conn, "SELECT ROWID FROM domains WHERE url=?", (domain_url,), fetch_one=True)
        if not domain_id:
            execute_sql(self.conn, "INSERT INTO domains (url) VALUES (?)", (domain_url,))
            domain_id = execute_sql(self.conn, "SELECT last_insert_rowid()", fetch_one=True)[0]
        else:
            domain_id = domain_id[0]

        # Ensure the webpage exists or create it
        page_id = execute_sql(self.conn, "SELECT last_insert_rowid()", fetch_one=True)[0]
        if not page_id:
            current_time = datetime.datetime.now()  # Assuming datetime has been imported
            execute_sql(self.conn, """
                INSERT INTO webpages (url, domain_id, access_timestamp, http_status, last_updated) VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(url) DO UPDATE SET domain_id=excluded.domain_id, access_timestamp=excluded.access_timestamp, http_status=excluded.http_status, last_updated=excluded.last_updated""", (item["url"], domain_id, current_time, 200, current_time))  # Assuming HTTP status 200 and the current timestamp
            page_id = execute_sql(self.conn, "SELECT last_insert_rowid()", fetch_one=True)[0]

        content = item["clean_body"]
        content_hash = calculate_md5_hash(content)

        # Insert or update the scrape result with the new content hash and other details
        execute_sql(self.conn, """
            INSERT INTO scrape_results (webpage_id, title, content, content_hash, content_length)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(webpage_id) DO UPDATE SET 
            content=excluded.content, content_hash=excluded.content_hash, title=excluded.title
        """, (page_id, item["title"], content, content_hash, len(content)))

        # Process links
        for link in item["links"]:
            execute_sql(self.conn, "INSERT INTO links (page_id, text, href) VALUES (?, ?, ?)", (page_id, link['text'], link['href']))

        # Process images
        try:
            image_data = [(page_id, img['src'], img['alt']) for img in item["images"]]
        except:
            print()
        for img in image_data:
            execute_sql(self.conn, "INSERT INTO images (page_id, src, alt) VALUES (?, ?, ?)", img)

        # Insert HeadingStructure data
        if "header_structure" in item:
            header_structure_json = json.dumps(item["header_structure"])
            execute_sql(self.conn, "INSERT INTO heading_structures (result_id, data) VALUES (?, ?) on conflict do update set data=excluded.data", (page_id, header_structure_json))

        # Insert StructuredData data
        if "schema_org_data" in item:
            schema_org_json = json.dumps(item["schema_org_data"])
            execute_sql(self.conn, "INSERT INTO structured_data (result_id, schema_org_data) VALUES (?, ?) on conflict (result_id) do update set schema_org_data=excluded.schema_org_data", (page_id, schema_org_json))

        # Insert SitemapContent data
        if "sitemap_contents" in item:
            for sitemap_content in item["sitemap_contents"]:
                execute_sql(self.conn, "INSERT INTO sitemap_contents (domain_id, content) VALUES (?, ?)", (domain_id, sitemap_content))

        # Insert SitemapURL data
        if "sitemap_links" in item:
            for sitemap_link in item["sitemap_links"]:
                execute_sql(self.conn, "INSERT INTO sitemap_urls (domain_id, url) VALUES (?, ?)", (domain_id, sitemap_link))

        return item
