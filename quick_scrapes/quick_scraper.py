import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re
import logging
import urllib.parse
import datetime
from common.utils.my_utils import pretty_print_data
from dotenv import load_dotenv

load_dotenv()
from aidream.settings.base import BASE_DIR
from quick_scrapes.parse_sample import ContentExtractor
from common.utils.my_utils import print_file_link


class Scraper:
    def __init__(self, ):
        self.USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.3"
        self.URL_PATTERN = r'(?:(http[s]?://)?(?:[a-zA-Z0-9.-]+(?:\.[a-zA-Z]{2,4}))|(?:www\.[a-zA-Z0-9.-]+(?:\.[a-zA-Z]{2,4})))'
        self.page_content = None
        self.soup = None
        self.url = None
        self.website = None
        self.path = None
        self.domain_type = None
        self.unique_page_name = None
        self.temp_scrapes = BASE_DIR / "temp/scrapes/structured_scrapes"
        self.temp_structured = BASE_DIR / "temp/scrapes/tables_and_lists"
        self.temp_soup = BASE_DIR / "temp/scrapes/soup"
        self.extractor = ContentExtractor
        self.method_map = {
            'get_full_scrape': self.get_full_scrape,
            'get_header_html': self.get_header_html,
            'get_body_html': self.get_body_html,
            'get_footer_html': self.get_footer_html,
            'get_h1': self.get_h1,
            'get_image_links': self.get_image_links,
            'get_images_and_alt_text': self.get_images_and_alt_text,
            'get_filtered_images': self.get_filtered_images,
            'get_internal_links': self.get_internal_links,
            'get_external_links': self.get_external_links,
            'get_video_links': self.get_video_links,
            'get_main_headers': self.get_main_headers,
            'get_all_headers': self.get_all_headers,
            'extract_phone_numbers': self.extract_phone_numbers,
            'extract_addresses': self.extract_addresses,
            'extract_emails': self.extract_emails,
            'find_sitemap_link': self.find_sitemap_link,
            'get_tables': self.get_tables,
            'extract_content_by_headers': self.extract_content_by_headers,
            'save_soup_to_text': self.save_soup_to_text,
        }

    async def scrape_url(self, url):
        self.url = url
        print(f"Attempting to scrape: {url}")
        async with aiohttp.ClientSession() as session:
            try:
                self.url = self.clean_and_extract_url_details(url)
                headers = {
                    "User-Agent": self.USER_AGENT
                }

                async with session.get(self.url, headers=headers) as response:
                    self.page_content = await response.text()
                    if self.page_content:
                        self.soup = BeautifulSoup(self.page_content, "html.parser")
                        print(f"Page content set for URL: {url}")
                    else:
                        print(f"No content retrieved for URL: {url}")
            except aiohttp.ClientError as e:
                logging.error(f"Client error during scraping {url}: {e}")
            except Exception as e:
                logging.error(f"Error during scraping {url}: {e}")

    def clean_and_extract_url_details(self, url):
        from urllib.parse import urlparse
        import tldextract

        parsed_url = urlparse(url)
        self.url = parsed_url.scheme + "://" + parsed_url.netloc + parsed_url.path
        extracted = tldextract.extract(self.url)
        self.website = f"{extracted.domain}.{extracted.suffix}" if extracted.suffix else extracted.domain
        self.domain_type = extracted.suffix
        self.path = parsed_url.path
        combined = self.website + self.path
        self.unique_page_name = re.sub(r'[^a-zA-Z0-9]', '_', combined)

        return self.url

    async def process_requests(self, url, options, task='scrape', text_file=None):
        self.url = url

        result = {
            'signature': 'QuickScraper',
            'processing': True,
            'value': None,
            'processed_values': {}
        }

        if task == 'scrape':
            await self.scrape_url(url)
            if self.page_content is None:
                result['processing'] = False
                return result

            await self.save_soup_to_text()

            print(f"[PARSE SCRIPT] Starting Extractor ----------------------------------------------")
            extractor_instance = self.extractor()
            extractor_instance.parse_scrape(soup=self.soup, website=self.website, url=self.unique_page_name, unique_page_name=self.unique_page_name)
            print(f"[PARSE SCRIPT] Extractor Finished ----------------------------------------------")

            # clean_data, char_count, title = await self.clean_scrape()
            # result['value'] = {'clean_data': clean_data, 'char_count': char_count, 'title': title}

        elif task == 'process_only' and text_file:
            self.load_soup_from_text(text_file)
        else:
            raise ValueError("Invalid task or missing text file for 'process_only' task.")

        if options:
            for option in options:
                if option in self.method_map:
                    method = self.method_map[option]  # How is this going to pass the argument necessary for filename to self.load_soup_from_text?
                    processed_value = await method()
                    result['processed_values'][option] = processed_value

            result['processing'] = False

        return result

    async def save_soup_to_text(self):
        if not self.soup:
            raise ValueError("[Error] Soup object is empty. Make sure to scrape a page first.")

        current_time = datetime.datetime.now().strftime('%y%m%d_%H%M')
        filepath = self.temp_soup / f'soup_{self.unique_page_name}_{current_time}.txt'

        metadata = f"""<!--METADATA_START
        url: {self.url}
        website: {self.website}
        path: {self.path}
        domain_type: {self.domain_type}
        unique_page_name: {self.unique_page_name}
        METADATA_END-->\n"""
        html_content = str(self.soup)

        full_soup_content = metadata + html_content

        with open(filepath, 'w', encoding='utf-8') as file:
            file.write(str(full_soup_content))

        list_filepath = self.temp_soup / '_list.txt'

        try:
            with open(list_filepath, 'r', encoding='utf-8') as file:
                existing_filepaths = file.readlines()
        except FileNotFoundError:
            existing_filepaths = []

        with open(list_filepath, 'w', encoding='utf-8') as file:
            file.write(str(filepath) + '\n')
            file.writelines(existing_filepaths)

        print_file_link(filepath)

    def load_soup_from_text(self, filename):
        with open(filename, 'r', encoding='utf-8') as file:
            self.soup = BeautifulSoup(file.read(), 'html.parser')

    async def clean_scrape(self):
        main_content = self.soup.find(attrs={
            'id': 'main-content'
        }) or self.soup
        content_tags = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'li']

        texts = set()  # Use a set to automatically ensure uniqueness
        for tag in content_tags:
            for element in main_content.find_all(tag):
                if not element.find_parents(['nav', 'footer', 'header', 'aside']):
                    text = element.get_text(strip=True)
                    if text:
                        texts.add(text)

        # Convert the set back to a list if order is important, though it may not preserve exact document order
        clean_data = '\n'.join(texts)  # Joining texts with newline for spacing
        char_count = sum(len(text) for text in texts)
        title = self.soup.title.string if self.soup.title else "No Title Found"

        return clean_data, char_count, title

    async def extract_content_by_headers(self):
        from bs4 import NavigableString, Tag

        def is_header(tag):
            return tag.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']

        def header_level(tag_name):
            return int(tag_name[1])

        def extract_text_until_next_header(start_element, level):
            text_content = []
            sibling = start_element.next_sibling
            while sibling:
                if isinstance(sibling, Tag):
                    if is_header(sibling) and header_level(sibling.name) <= level:
                        break
                    if sibling.name == 'a':
                        link_text = f"Link: {sibling.get_text(separator=' ', strip=True)}"
                        text_content.append(link_text)
                    else:
                        text_content.append(sibling.get_text(separator=' ', strip=True))
                elif isinstance(sibling, NavigableString):
                    text_content.append(str(sibling).strip())
                sibling = sibling.next_sibling
            return '\n'.join(filter(None, text_content))

        if not self.soup:
            return None, "Soup is not set. Please scrape a URL first."

        content_dict = {}
        plain_text_output = ""
        headers = self.soup.find_all(is_header)

        for header in headers:
            level = header_level(header.name)
            header_text = header.get_text().strip()

            # Find text even if nested within tags like <div> or <a>
            if not header_text:
                header_text = ''.join(header.stripped_strings)

            following_content = extract_text_until_next_header(header, level)

            plain_text_output += f"\n\nHeader {level}: {header_text}\n{following_content}\n"

            content_dict[header_text] = following_content

        print(f"[PLAIN TEXT LOCAL] Direct from quick scraper ----------------------------------------------")
        print(f"\n\nPlain Text Output:\n{plain_text_output}\n\n")
        print(f"[PLAIN TEXT LOCAL] Direct from quick scraper ----------------------------------------------")

        return content_dict, plain_text_output

    async def get_full_scrape(self):
        return self.soup.prettify()

    async def get_tables(self):

        # This has been hard-coded for only one type of table so it's pretty much useless for most pages
        tables = self.soup.find_all('div', attrs={
            'role': 'table',
            'class': 'dvmd_tm_table'
        })

        all_tables_data = []

        for table in tables:
            columns_data = []

            columns = table.find_all('div', class_='dvmd_tm_tblock dvmd_tm_cblock')

            for col in columns:
                col_dict = {}
                rows = col.find_all('div', class_='dvmd_tm_tcell')
                current_header = None
                for row in rows:
                    if row.get('scope') == 'row':
                        current_header = row.get_text(strip=True)
                    else:
                        value = row.get_text(strip=True)
                        col_dict[current_header] = value

                if col_dict:
                    columns_data.append(col_dict)

            all_tables_data.append(columns_data)

        return all_tables_data

    async def get_header_html(self):
        return str(self.soup.head)

    async def get_body_html(self):
        return str(self.soup.body)

    async def get_footer_html(self):
        footer = self.soup.find('footer')
        return str(footer) if footer else None

    async def get_h1(self):
        header = self.soup.find('h1')
        return header.text if header else None

    async def get_image_links(self):
        image_links = set()

        for tag in self.soup.find_all(['img', 'div', 'span', 'a']):
            for attr in ['src', 'data-src', 'nitro-lazy-src', 'style']:
                if tag.has_attr(attr):
                    img_url = tag[attr]
                    if 'url(' in img_url:
                        img_url = img_url.split('url(')[-1].split(')')[0].strip('"\'')
                    if not any(ext in img_url for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                        continue
                    img_url = urllib.parse.urljoin(self.url, img_url)
                    image_links.add(img_url)
        return list(image_links)

    async def get_images_and_alt_text(self):
        image_links = await self.get_image_links()  # No URL needed
        images_info = []

        for link in image_links:
            img_tags = self.soup.find_all('img', {
                'src': link
            }) or self.soup.find_all('img', {
                'data-src': link
            }) or self.soup.find_all('img', {
                'nitro-lazy-src': link
            })
            for img in img_tags:
                alt_text = img.get('alt', '')
                images_info.append((link, alt_text))

        return images_info

    async def get_filtered_images(self):
        images_info = await self.get_images_and_alt_text()  # No URL needed
        exclude_keywords = ['icon', 'ico', 'logo', 'spinner', 'location', 'phone', 'email']

        filtered_images = [(src, alt) for src, alt in images_info if not any(keyword.lower() in alt.lower() for keyword in exclude_keywords)]
        return filtered_images

    async def get_internal_links(self):
        domain = self.extract_domain()
        links = self.soup.find_all('a', href=True)
        return [link['href'] for link in links if link['href'].startswith('/') or domain in link['href']]

    async def get_external_links(self):
        domain = self.extract_domain()
        links = self.soup.find_all('a', href=True)
        return [link['href'] for link in links if not (link['href'].startswith('/') or domain in link['href'])]

    async def get_video_links(self):
        videos = self.soup.find_all('video') + self.soup.find_all('iframe')  # This finds both <video> tags and <iframe> which might embed videos
        return [video['src'] for video in videos if video.has_attr('src')]

    async def get_main_headers(self):
        headers_by_tag = {}
        for tag in ['h1', 'h2', 'h3', 'h4']:
            headers = self.soup.find_all(tag)
            headers_by_tag[tag] = [header.text.strip() for header in headers]

        return headers_by_tag

    async def get_all_headers(self):
        headers_by_tag = {}
        for tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            headers = self.soup.find_all(tag)
            headers_by_tag[tag] = [header.text.strip() for header in headers]

        return headers_by_tag

    def extract_domain(self):
        parsed_uri = urllib.urlparse(self.url)
        return '{uri.scheme}://{uri.netloc}'.format(uri=parsed_uri)

    async def extract_phone_numbers(self):
        phone_pattern = re.compile(r'\(?\b\d{3}\)?[-.\s]*\d{3}[-.\s]*\d{4}\b')  # Simple regex pattern for US phone numbers
        return re.findall(phone_pattern, self.page_content) if self.page_content else []

    async def extract_addresses(self):
        address_pattern = re.compile(r'\d{1,5}\s(\b\w*\b\s){1,2}\w*\.?')  # Simple regex for addresses (e.g., "123 Main St.")
        return re.findall(address_pattern, self.page_content) if self.page_content else []

    async def extract_emails(self):
        email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')  # Simple regex pattern for email
        return re.findall(email_pattern, self.page_content) if self.page_content else []

    async def find_sitemap_link(self):
        # Patterns to find different types of sitemap links
        sitemap_patterns = [
            r'sitemap.*\.xml',  # XML Sitemaps
            r'sitemap.*\.html?',  # HTML Sitemaps
            r'/feed/?',  # RSS Feeds
            r'/rss/?',  # RSS Feeds
            r'/atom/?',  # Atom Feeds
            r'/video_sitemap.*\.xml',  # Video Sitemaps
            r'/news_sitemap.*\.xml',  # News Sitemaps
            r'/image_sitemap.*\.xml'  # Image Sitemaps
        ]

        robots_txt_url = f"{self.extract_domain().rstrip('/')}/robots.txt"
        await self.scrape_url(robots_txt_url)  # Fetch robots.txt
        if self.page_content:
            for line in self.page_content.splitlines():
                if line.strip().lower().startswith('sitemap:'):
                    sitemap_url = line.split(':', 1)[1].strip()
                    return sitemap_url

        if self.soup:
            links = self.soup.find_all('a', href=True)
            for link in links:
                for pattern in sitemap_patterns:
                    if re.search(pattern, link['href'], re.IGNORECASE):
                        return link['href']

            meta_tags = self.soup.find_all('link', {
                'rel': 'alternate'
            }, href=True)
            for meta_tag in meta_tags:
                for pattern in sitemap_patterns:
                    if re.search(pattern, meta_tag['href'], re.IGNORECASE):
                        return meta_tag['href']

        return None

    def scrape_cleanup(self, data):
        cleaned_data = []
        for sublist in data:
            cleaned_sublist = []
            for item in sublist:
                if isinstance(item, str):
                    cleaned_item = item.replace('\xa0', ' ')
                    cleaned_item = cleaned_item.replace('&amp;', '&')
                    cleaned_item = cleaned_item.replace('&gt;', '>')
                    cleaned_item = cleaned_item.replace('&lt;', '<')
                    cleaned_item = re.sub(r'\s+', ' ', cleaned_item)
                    cleaned_item = re.sub(r'\n+', '\n', cleaned_item)
                    cleaned_item = cleaned_item.replace('™', '')
                    cleaned_item = cleaned_item.replace('©', '')
                    cleaned_item = ''.join(char for char in cleaned_item if ord(char) < 128)
                    cleaned_sublist.append(cleaned_item)
                else:
                    cleaned_sublist.append(item)
            cleaned_data.append(cleaned_sublist)

        print("Scrape cleanup completed!")
        return cleaned_data


class SimpleScraper:
    def __init__(self):
        self.USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.3"
        self.URL_PATTERN = r'(?:(http[s]?://)?(?:[a-zA-Z0-9.-]+(?:\.[a-zA-Z]{2,4}))|(?:www\.[a-zA-Z0-9.-]+(?:\.[a-zA-Z]{2,4})))'

    async def scrape_url(self, url):
        print(f"Attempting to scrape: {url}")
        url = self.extract_url(url)

        async with aiohttp.ClientSession() as session:
            try:
                headers = {
                    "User-Agent": self.USER_AGENT
                }
                async with session.get(url, headers=headers) as response:
                    page_content = await response.text()
                    soup = BeautifulSoup(page_content, "html.parser")
                    self.soup = soup
                    title = soup.find('h1')
                    if title is None:
                        title = soup.title.string if soup.title else "No Title Found"
                    else:
                        title = title.text
                    paragraphs = soup.find_all('p')
                    data = [[title]]
                    char_count = sum(len(p.get_text()) for p in paragraphs)
                    data.extend([[p.get_text()] for p in paragraphs])
                    data.insert(0, [url])

                    return data, char_count, title
            except aiohttp.ClientError as e:
                logging.error(f"Client error during scraping {url}: {e}")
                return None, 0, None
            except Exception as e:
                logging.error(f"Error during scraping {url}: {e}")
                return None, 0, None

    def scrape_cleanup(self, data):
        cleaned_data = []
        for sublist in data:
            cleaned_sublist = []
            for item in sublist:
                if isinstance(item, str):
                    cleaned_item = item.replace('\xa0', ' ')
                    cleaned_item = cleaned_item.replace('&amp;', '&')
                    cleaned_item = cleaned_item.replace('&gt;', '>')
                    cleaned_item = cleaned_item.replace('&lt;', '<')
                    cleaned_item = re.sub(r'\s+', ' ', cleaned_item)
                    cleaned_item = re.sub(r'\n+', '\n', cleaned_item)
                    cleaned_item = cleaned_item.replace('™', '')
                    cleaned_item = cleaned_item.replace('©', '')
                    cleaned_item = ''.join(char for char in cleaned_item if ord(char) < 128)
                    cleaned_sublist.append(cleaned_item)
                else:
                    cleaned_sublist.append(item)
            cleaned_data.append(cleaned_sublist)

        print("Scrape cleanup completed!")
        return cleaned_data

    def extract_url(self, text):
        url_pattern = re.compile(self.URL_PATTERN)
        match = url_pattern.search(text)
        if match:
            url = match.group()
            if not url.startswith(('http://', 'https://')):
                if url.startswith('www.'):
                    url = 'http://' + url
                else:
                    url = 'http://www.' + url
            return url
        logging.warning("No URL found in the provided text.")
        return None


async def scrape_page(url: str, options: list) -> dict:
    """
    Asynchronously scrapes a webpage based on specified options.

    Args:
        url (str): The URL of the webpage to scrape.
        options (list): A list of strings specifying what content to scrape from the webpage.
            Example = ['get_image_links', 'get_main_headers', 'get_tables', 'get_filtered_images']
                - get_full_scrape: Performs a comprehensive scrape of the entire webpage.
                - get_header_html: Extracts the HTML content of the page header.
                - get_body_html: Retrieves the HTML content of the page body.
                - get_footer_html: Extracts the HTML content of the page footer.
                - get_h1: Fetches all H1 tags from the page.
                - get_image_links: Gathers all image links on the page.
                - get_images_and_alt_text: Collects images along with their alt text.
                - get_filtered_images: Retrieves images filtered by certain criteria.
                - get_internal_links: Finds all internal links on the webpage.
                - get_external_links: Identifies all external links on the webpage.
                - get_video_links: Extracts links to video content on the page.
                - get_main_headers: Gathers primary headers (H1, H2) from the page.
                - get_all_headers: Collects all headers (H1-H6) from the webpage.
                - extract_phone_numbers: Extracts phone numbers found on the page.
                - extract_addresses: Retrieves physical addresses mentioned on the webpage.
                - extract_emails: Gathers email addresses from the page.
                - find_sitemap_link: Looks for a sitemap link within the webpage.
                - get_tables: Extracts table data from the page.
    Returns:
        dict: A dictionary containing the scraped contents based on provided options. The keys in the dictionary
              correspond to the options (e.g., 'get_image_links' would store the scraped image links).

    """
    """
    Options are to be structured as a list of strings:

    """
    scraper = Scraper()
    scrape_results = await scraper.process_requests(url, options)
    return scrape_results


async def scrape_multiple_pages(urls: list, options: dict) -> list:
    """
    Asynchronously scrapes multiple web pages.

    Args:
        urls (list): List of URL strings to be scraped.
        options (list): A list of strings specifying what content to scrape from the webpage.
            Example = ['get_image_links', 'get_main_headers', 'get_tables', 'get_filtered_images']

    Returns:
        list: A list containing the results of scraping each URL, ordered correspondingly.
    """
    import asyncio
    tasks = [scrape_page(url, options) for url in urls]
    scrape_results_dict = await asyncio.gather(*tasks)
    return scrape_results_dict


async def simple_scrape_single_page(url):
    scraper = SimpleScraper()
    data, char_count, title = await scraper.scrape_url(url)
    cleaned_content = scraper.scrape_cleanup(data)

    print(f"Successfully scraped: {url}")
    print(f"Title: {title}")
    print(f"Character Count: {char_count}")
    pretty_print_data(cleaned_content)

    print(f"\n\nData: {data}\n\n")

    return cleaned_content


async def main(url, options, task='scrape', text_file=None):
    scraper = Scraper()
    result = await scraper.process_requests(url, options, task, text_file)
    return result


if __name__ == "__main__":
    url = "https://pypi.org/project/markdown-it-py/"
    options = ['get_image_links', 'get_main_headers', 'extract_content_by_headers', 'get_tables', 'get_filtered_images']
    options_2 = ['extract_content_by_headers']

    # cleaned_content = asyncio.run(simple_scrape_single_page(url))

    result = asyncio.run(main(url, options_2, task='scrape', text_file='soup.txt'))

    # clean_data = result['value']['clean_data']

    # For loading from saved soup and processing
    # result = asyncio.run(main(url, options, task='process_only', text_file='soup.txt'))

    # body_html = result['processed_values']['get_body_html']

    # pretty_print_data(result)
    # pretty_print_data(clean_data)
    # print(f"\n\nCleaned Data:\n{clean_data}\n\n")
    # print(f"\n\nBody HTML:\n{body_html}\n\n")
