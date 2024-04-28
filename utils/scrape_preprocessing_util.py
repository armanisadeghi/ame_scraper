import os
import json
import requests
from urllib.parse import urlparse
from datetime import datetime, timedelta
import csv
from pytz import timezone
from db_ops import create_connection, execute_sql

utc = timezone('UTC')
current_utc_time = lambda: datetime.now(utc)

def get_domain_url(url):
    parsed_url = urlparse(url)
    domain_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    return domain_url

def make_preprocess_http_request(url):
    try:
        response = requests.get(url, timeout=10)
        return response
    except requests.RequestException:
        return None


def preprocess_url(url):
    conn = create_connection("ame_scraper.db")
    response = make_preprocess_http_request(url)
    if response is None:
        return

    final_url = response.url
    domain_url = get_domain_url(final_url)

    # Check if domain exists and create or update the domain
    domain_id = execute_sql(conn, "SELECT ROWID FROM domains WHERE url=?", (domain_url,), fetch_one=True)
    if domain_id is None:
        execute_sql(conn, "INSERT INTO domains (url, last_updated) VALUES (?, ?)", (domain_url, current_utc_time()))
        domain_id = execute_sql(conn, "SELECT last_insert_rowid()", fetch_one=True)[0]
    else:
        domain_id = domain_id[0]

    # Update the domain details if needed
    update_preprocess_domain_details(conn, domain_url)

    # Collecting data from the response to insert or update the webpage record
    cookies = '; '.join([f"{c.name}={c.value}" for c in response.cookies])
    redirection_info = ' -> '.join([resp.url for resp in response.history]) if response.history else 'No redirection'
    content_type = response.headers.get('Content-Type', '')
    page_size = len(response.content)
    language = response.headers.get('Content-Language', '')
    link_headers = response.headers.get('Link', '')

    # Check if webpage exists and create or update the webpage
    webpage_id = execute_sql(conn, "SELECT id FROM webpages WHERE url=?", (final_url,), fetch_one=True)
    if webpage_id is None:
        execute_sql(conn, """
            INSERT INTO webpages (url, domain_id, http_status, access_timestamp, content_type, page_size, language, page_specific_cookies, redirection_info, link_headers)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (final_url, domain_id, response.status_code, current_utc_time(), content_type, page_size, language, cookies, redirection_info, link_headers))
    else:
        execute_sql(conn, """
            UPDATE webpages SET
            domain_id=?, http_status=?, access_timestamp=?, content_type=?, page_size=?, language=?, page_specific_cookies=?, redirection_info=?, link_headers=?
            WHERE url=?
        """, (domain_id, response.status_code, current_utc_time(), content_type, page_size, language, cookies, redirection_info, link_headers, final_url))

    conn.close()


def update_preprocess_domain_details(conn, domain_url):
    try:
        response = requests.head(domain_url, timeout=5, allow_redirects=True)
        response.raise_for_status()

        # Extract necessary headers
        server_type = response.headers.get('Server', '')
        rate_limit_info = response.headers.get('X-RateLimit-Limit', '')
        security_policies = response.headers.get('Content-Security-Policy', '')

        # Prepare to update the domain details in the database
        sql_update = """
            UPDATE domains
            SET last_updated = ?, server_type = ?, rate_limit_info = ?, security_policies = ?
            WHERE url = ?
        """
        # Tuple with values corresponding to each placeholder in the SQL statement
        params = (
            current_utc_time(),  # Timestamp of the update
            server_type,         # Type of server
            rate_limit_info,     # Information about rate limiting
            security_policies,   # Security policies in use
            domain_url           # The URL of the domain to update
        )

        # Execute the SQL command
        execute_sql(conn, sql_update, params)

    except requests.RequestException as e:
        print(f"Error fetching details for {domain_url}: {e}")
