from bs4 import BeautifulSoup, NavigableString, Comment
import pandas as pd
from uuid import uuid4
import json
from tabulate import tabulate
import re
import html
import string
import os
from pathlib import Path
from dotenv import load_dotenv
from common.utils.my_utils import print_file_link

load_dotenv()
from aidream.settings.base import BASE_DIR


class ContentExtractor:
    def __init__(self):
        self.soup = None
        self.website = "no_site"
        self.url = "no_url"
        self.unique_page_name = "no_unique_name"
        self.temp_scrapes = BASE_DIR / "temp/scrapes/organized"
        self.temp_structured = BASE_DIR / "temp/scrapes/structured"
        self.temp_text = BASE_DIR / "temp/scrapes/text"
        self.page_title = "no_title"
        self.structured_json_path = ""
        self.organized_text_path = ""
        self.organized_json_path = ""
        self.site_filters = BASE_DIR / "temp/scrapes/site_filters.json"
        self.site_class_filters = {}
        self.site_partial_class_filters = {}
        self.element_id_filters = {}
        self.site_div_filters = {}
        self.site_name_filters = {}
        self.site_a_filters = {}
        self.site_text_filters = {}
        self.site_role_filters = {}
        self.site_include_filters = {}
        self.debug_prints = False
        self.filter_prints = True
        self.current_header = None
        self.uuid = uuid4()
        self.page_dict = {}
        self.current_header = "unassociated"
        self.apply_filter_a = False
        self.apply_filter_class = False
        self.apply_filter_content = False
        self.apply_filter_div = False

    def initialize_json_files(self):
        overview = {
            "uuid": str(self.uuid),
            "website": self.website,
            "url": self.url,
            "unique_page_name": self.unique_page_name,
            "page_title": self.page_title
        }

        organized_json_structure = {
            "overview": overview,
        }
        with open(self.organized_json_path, 'w', encoding='utf-8') as f:
            json.dump(organized_json_structure, f, indent=4, ensure_ascii=False)

        structured_json_structure = {
            "overview": overview,
            "tables": {},
            "lists": {},
            "ordered_lists": {}
        }
        with open(self.structured_json_path, 'w', encoding='utf-8') as f:
            json.dump(structured_json_structure, f, indent=4)

    def save_to_json(self):
        self.page_title = re.sub(r'[^a-zA-Z0-9]', '_', self.page_title)[:60]

        with open(self.organized_json_path, "r", encoding='utf-8') as f:
            existing_data = json.load(f)

        if "unassociated" in self.page_dict:
            unassociated = self.page_dict.pop("unassociated")
        else:
            unassociated = existing_data.pop("unassociated", [])

        updated_data = {**existing_data, **self.page_dict,
                        "unassociated": unassociated
                        }

        with open(self.organized_json_path, "w", encoding='utf-8') as f:
            json.dump(updated_data, f, indent=4)

        print_file_link(self.organized_json_path)

    def add_to_json(self, header_key, data, data_type):
        with open(self.structured_json_path, 'r+') as file:
            json_data = json.load(file)

            header_key = getattr(self, 'current_header', 'default_header')

            if header_key not in json_data[data_type]:
                json_data[data_type][header_key] = []

            json_data[data_type][header_key].append(data)

            file.seek(0)
            file.truncate()

            json.dump(json_data, file, indent=4)

    def format_json_as_text(self, data, indent=0, is_root=True):
        lines = []

        def add_heading(heading, indent_level):
            if not is_root:
                lines.append('')
            lines.append(' ' * indent_level + heading)

        def process_list(items, indent_level):
            for item in items:
                if isinstance(item, dict) and 'list_items' in item:
                    for list_item in item['list_items']:
                        lines.append(' ' * indent_level + '- ' + list_item)
                else:
                    lines.append(' ' * indent_level + '- ' + str(item))

        if isinstance(data, dict):
            for key, value in data.items():
                add_heading(key, indent)
                if isinstance(value, dict):
                    lines.extend(self.format_json_as_text(value, indent + 2, is_root=False))
                elif isinstance(value, list):
                    process_list(value, indent + 2)
                else:
                    lines.append(' ' * (indent + 2) + str(value))
        elif isinstance(data, list):
            process_list(data, indent)

        return lines

    def save_to_text(self):
        print(f"[saving text] JSON Path: {self.organized_json_path}")
        try:
            with open(self.organized_json_path, 'r', encoding='utf-8') as file:
                json_data = json.load(file)
        except FileNotFoundError:
            print("JSON file not found.")
            return

        formatted_lines = self.format_json_as_text(json_data)

        with open(self.organized_text_path, 'w', encoding='utf-8') as file:
            file.write('\n'.join(formatted_lines))

        print_file_link(self.organized_text_path)

    def clean_text(self, text):
        text = html.unescape(text)
        text = re.sub(r'(<[^>]+>)', r' \1 ', text)
        text = re.sub(r'<[^>]+>', '', text)
        text = (text.replace(u'\u201c', '"').replace(u'\u201d', '"')
                .replace(u'\u2013', '-').replace(u'\u2014', '-')
                .replace(u'\u00A0', ' ')

                .replace(u'\u00A0', ' ')
                .replace(u'\u2018', "'").replace(u'\u2019', "'"))
        text = re.sub(r'[^\x00-\x7F]+', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        if text == "-" or text == "–" or text == "/":
            text = ""
        # print(f"[DEBUG cleaned text] |{text}|")
        return text

    def add_page_content(self, content, content_type="text"):
        if isinstance(content, str):
            content = self.clean_text(content)
            if not content:
                return
        if self.current_header not in self.page_dict:
            self.page_dict[self.current_header] = []
        if content_type == "text":
            if content:
                self.page_dict[self.current_header].append(content)
        elif content_type == "list":
            filtered_list = [self.clean_text(item) for item in content if self.clean_text(item)]
            if filtered_list:
                self.page_dict[self.current_header].append({
                    "list_items": filtered_list
                })

    def load_soup_from_text(self, filename):
        print(f"\n[preparing parse] ---------------------------------------------------------------------------------------\n")
        print(f"[loading text] File:")
        print_file_link(filename)

        with open(filename, 'r', encoding='utf-8') as file:
            content = file.read()

        parts = content.split('<!--METADATA_START', 1)
        if len(parts) >= 2:
            if 'METADATA_END-->' in parts[1]:
                metadata, html_content = parts[1].split('METADATA_END-->', 1)
            else:
                print("[Error] Metadata end marker not found. Please check the file format.")
                metadata = parts[1]
                html_content = ''

            metadata_dict = {}
            for line in metadata.split('\n'):
                line = line.strip()  # Trim whitespace
                if ': ' in line:  # Additional check to ensure line contains a key-value pair
                    key, value = line.split(': ', 1)
                    metadata_dict[key] = value.strip()

            self.url = metadata_dict.get('url', None)
            self.website = metadata_dict.get('website', None)
            self.path = metadata_dict.get('path', None)
            self.domain_type = metadata_dict.get('domain_type', None)
            self.unique_page_name = metadata_dict.get('unique_page_name', None)

            self.soup = BeautifulSoup(html_content, 'html.parser')
        else:
            self.soup = BeautifulSoup(content, 'html.parser')

        self.parse_scrape(self.soup, self.website, self.url, self.unique_page_name)

    def scrape_local_html_file(self, filepath, url=None, website=None, path=None, unique_page_name=None):
        with open(filepath, 'r', encoding='utf-8') as file:
            content = file.read()

        self.url = url
        self.website = website
        self.path = path
        self.domain_type = None
        self.unique_page_name = unique_page_name
        self.soup = BeautifulSoup(content, 'html.parser')
        self.parse_scrape(self.soup, self.website, self.url, self.unique_page_name)

    def parse_scrape(self, soup, website, url, unique_page_name):
        print(f"[parsing] Site: {website}, Page: {unique_page_name}")
        print(f"[parsing] ULR: {url}")
        self.soup = soup
        self.website = website
        self.url = url
        self.unique_page_name = unique_page_name
        self.load_filters()
        self.structured_json_path = self.temp_structured / f'structured_{self.unique_page_name}.json'
        self.organized_text_path = self.temp_text / f'structured_{self.unique_page_name}.txt'
        self.organized_json_path = self.temp_scrapes / f'organized_{self.unique_page_name}.json'
        self.initialize_json_files()
        print(f"\n[starting extraction] =======================================================================================\n")
        self.extract_basics()
        self.extract_content()
        print(f"\n[extraction complete] =======================================================================================\n")
        self.save_to_json()
        self.save_to_text()

    def load_filters(self):
        filters_loaded = False

        with open(self.site_filters, 'r') as file:
            filters = json.load(file)

            for site_filter in filters:
                if site_filter.get("site_name") == self.website:
                    self.site_class_filters = site_filter.get("class", None)
                    self.site_partial_class_filters = site_filter.get("partial_class", None)
                    self.element_id_filters = site_filter.get("id", None)
                    self.site_div_filters = site_filter.get("div", None)
                    self.site_name_filters = site_filter.get("name", None)
                    self.site_a_filters = site_filter.get("a_element", None)
                    self.site_text_filters = site_filter.get("text", None)
                    self.site_role_filters = site_filter.get("role", None)
                    self.site_include_filters = site_filter.get("include", None)
                    filters_loaded = True
                    break

        if filters_loaded:
            print(f"[filters] Loaded filters for {self.website}")
        else:
            print(f"[filters] No specific filters found for {self.website}, using defaults.")

    def extract_basics(self):
        title = self.soup.find('title')
        if title:
            self.page_title = title.get_text()
            print(f"Title: {self.page_title}\n")
            self.page_dict["Title"] = self.page_title

        for header_tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            for header in self.soup.find_all(header_tag):
                if not self.filter_content(header):
                    header_text = header.get_text().strip()
                    header_key = f"{header_tag.upper()}: {header_text}"
                    if header_key not in self.page_dict:
                        self.page_dict[header_key] = []

    def filter_content(self, element):
        if not self.apply_filter_content:
            return False

        name_include_override = ['html', 'body', 'title'] + [f for f in (self.site_include_filters or []) if f]
        role_exclusion = [
                             'menuitem', 'dialog', 'menu', 'button', 'figure', 'icon', 'picture', 'navigation', 'toolbar', 'menubar'
                         ] + [f for f in (self.site_role_filters or []) if f]

        name_exclusion = [
                             'script', 'style', 'svg', 'head', 'nav', 'footer', 'select', 'button', 'figure', 'fieldset', 'form', 'section', 'mbox-text-span', 'sidebar-section'
                         ] + [f for f in (self.site_name_filters or []) if f]

        if element.name in name_include_override:
            return False
        if element.parent in name_exclusion:
            self.filter_print("filter_name", element.parent.name)
            return True
        if element.name in name_exclusion:
            self.filter_print("filter_name", element.name)
            return True
        if element.role in role_exclusion:
            self.filter_print("filter_role", element.role)
            return True
        if element.has_attr('role') and element['role'] in role_exclusion:
            self.filter_print("filter_role", element['role'])
            return True
        if element.has_attr('tabindex'):
            self.filter_print("filter_element", element['tabindex'])
            return True
        if self.filter_by_class(element):
            self.filter_print("filter_class", element['class'])
            return True
        if self.filter_a_elements(element):
            self.filter_print("filter_a", element.get('id', ''))
            return True
        if self.filter_div_elements(element):
            self.filter_print("filter_div", element.get('id', ''))
            return True
        return self.site_specific_filter(element)

    def filter_by_class(self, element):
        if not self.apply_filter_class:
            return False

        exact_class_indicators = [
                                     'share', 'social', 'advert', 'promo', 'overlay', 'widget', 'footer', 'header', 'menu', 'modal', 'popup', 'figure', 'icon', 'mbox-text-span',
                                 ] + [f for f in (self.site_class_filters or []) if f]

        partial_class_indicators = [
                                       'share', 'social', 'advert', 'promo', 'overlay', 'widget', 'footer', 'header', 'menu', 'modal', 'popup', 'figure', 'icon', 'announcement', 'drawer',
                                       'size-chart', 'size-guide', 'cookie', 'privacy', 'terms', 'disclaimer', 'copyright', 'legal', 'footer', 'header', 'menu', 'modal', 'popup', 'figure', 'icon',
                                       'product-recommendations', 'sidebar-section',
                                       'recommendations', 'icons'
                                   ] + [f for f in (self.site_partial_class_filters or []) if f]

        class_list = element.get('class', [])

        if any(indicator == class_name for indicator in exact_class_indicators for class_name in class_list):
            self.filter_print("filter_class", class_list)
            return True

        for class_name in class_list:
            for indicator in partial_class_indicators:
                if class_name.startswith(indicator + "-") or class_name.endswith("-" + indicator) \
                        or class_name.startswith(indicator + "_") or class_name.endswith("_" + indicator) \
                        or class_name == indicator:
                    self.filter_print("filter_partial_class", class_list)
                    return True

        return False

    def filter_a_elements(self, element):
        if not self.apply_filter_a:
            return False

        if element.name != 'a':
            return False
        if element.has_attr('tabindex'):
            self.filter_print("filter_element", element['tabindex'])
            return True

        exact_a_indicators = []
        partial_a_indicators = ['icon']

        return self.filter_by_class(element) or \
            any(indicator == element.get('id') for indicator in exact_a_indicators) or \
            any(indicator in element.get('id', '') for indicator in partial_a_indicators)

    def filter_div_elements(self, element):
        if not self.apply_filter_div:
            return False

        if element.name != 'div':
            return False
        return self.filter_by_class(element)

    def site_specific_filter(self, element):
        self.site_filters = {
            'healthline.com': self.filter_healthline,
            'nazarianplasticsurgery': "",
            'allgreenrecycling': "",
            'cosmeticinjectables': "",
            'theskinspot': "",
            'datadestruction': "",
            'vasaro': "",
            'spa26': "",
            'prpinjectionmd': "",
            'aimatrixengine': "",
            'webmd': "",
            'plasticsurgery': "",
            'mayoclinic': "",
            'americanboardcosmeticsurgery': "",
            'medlineplus': "",
            'clevelandclinic': "",
            'hopkinsmedicine': "",
            'wikipedia': "",
            'fda': "",
        }

        filter_func = self.site_filters.get(self.website)
        if filter_func:
            return filter_func(element)
        return False

    def pypi_parser(self, html, h2_text):
        h2_tag = self.soup.find('h2', string=h2_text)

        if not h2_tag:
            print(f"No <h2> tag with the text '{h2_text}' found.")
            return

        for sibling in h2_tag.find_next_siblings():
            print(sibling.get_text(strip=True))

    def filter_healthline(self, element):
        site_specific_text = self.site_text_filters
        if element.name == 'div' and element.get('data-testid') == 'byline':
            return True
        if element.name == 'div' and element.get('id') == 'read-next':
            return True
        if element.class_ == 'css-css-1foa3wo':
            return True
        # if element.text in site_specific_text:
        # return True
        # if element.parent and element.parent.text in site_specific_text:
        # return True
        return False

    def filter_for_anotherexample_com(self, element):
        print("Filtering for anotherexample.com")
        pass

    def debug_print(self, debug_type, value):
        debug_styles = {
            "text": "===== TEXT: {value}|End Text",
            "element_p": "===== ELEMENT P: {value}|End Element P",
            "element_a": "===== ELEMENT A: {value}|End Element A",
            "element_span": "===== ELEMENT SPAN: {value}|End Element Span",
            "header_tag": "\n[DEBUG header tag] {value}\n",
            "table": "\n[DEBUG Table]\n",
            "list": " --> ",
            "ordered_list": " --> ",
            'element_pre': "===== ELEMENT PRE: {value}|End Element Pre"
        }

        if self.debug_prints:
            format_string = debug_styles.get(debug_type, "===== UNDEFINED ELEMENT: {value}")
            debug_message = format_string.format(value=value)
            print(f"\n-------------------------------------------------------DEBUG PRINT-------------------------------------------------------\n")
            print(debug_message)
            print(f"\n-------------------------------------------------------DEBUG PRINT-------------------------------------------------------\n")

    def filter_print(self, filter_type, value):
        # print(f"\n-------------------------------------------------------DEBUG PRINT-------------------------------------------------------\n")
        filter_styles = {
            "visibility_general": "--- Visibility: {value}|",
            "visibility_hidden": "--- Visibility: {value}|",
            "filter_class": "--- Filter Class: {value}|",
            "filter_id": "--- Filter ID: {value}|",
            "filter_role": "--- Filter Role: {value}|",
            "filter_name": "--- Filter Name: {value}|",
            "filter_text": "--- Filter Text: {value}|",
            "filter_include": "--- Filter Include: {value}|",
            "filter_exclude": "--- Filter Exclude: {value}|",
            "filter_element": "--- Filter Element: {value}|",
            "filter_div": "--- Filter Div: {value}|",
            "filter_a": "--- Filter A: {value}|",
            "filter_site": "--- Filter Site: {value}|",
            "filter_partial_class": "--- Filter Partial Class: {value}|",
            "filter_partial_a": "--- Filter Partial A: {value}|",
            "filter_partial_div": "--- Filter Partial Div: {value}|",
            "filter_partial_site": "--- Filter Partial Site: {value}|",
            "filter_partial_text": "--- Filter Partial Text: {value}|",
            "filter_partial_role": "--- Filter Partial Role: {value}|",
        }

        if self.filter_prints:
            format_string = filter_styles.get(filter_type, "--- Unknown Filter: {value}|")
            debug_message = format_string.format(value=value)
            print(debug_message)
        # print(f"\n-------------------------------------------------------DEBUG PRINT-------------------------------------------------------\n")

    def extract_content(self):
        body = self.soup.find('body')
        if body:
            self._extract_from_element(body)

    def _is_visible(self, element):
        def is_element_hidden(el):
            if self.filter_content(el):
                return True

            if el.has_attr('style'):
                style = el['style'].lower()
                if 'display: none' in style or 'visibility: hidden' in style or 'opacity: 0' in style:
                    self.filter_print("visibility_hidden", style)
                    return True
                if 'position: absolute' in style and ('left: -9999px' in style or 'top: -9999px' in style):
                    self.filter_print("visibility_hidden", style)
                    return True

            if el.has_attr('aria-hidden') and el['aria-hidden'].lower() == 'true':
                self.filter_print("visibility_hidden", el['aria-hidden'])
                return True
            if 'hidden' in el.attrs:
                self.filter_print("visibility_hidden", el['hidden'])
                return True

            if el.has_attr('class'):
                class_attr = ' '.join(el['class']).lower()
                if 'hidden' in class_attr:
                    self.filter_print("visibility_hidden", class_attr)
                    return True

            if el.name not in ['svg', 'script']:
                for child in el.find_all(True, recursive=False):
                    if child.get('aria-hidden', '').lower() == 'true':
                        continue
                    if 'display: none' in child.get('style', '').lower():
                        self.filter_print("visibility_hidden", child.get('style', ''))
                        return True

            return False

        for parent in element.parents:
            if is_element_hidden(parent):
                return False

        return not is_element_hidden(element)

    def _extract_from_element(self, element):
        if self.filter_content(element):
            return

        if element.name == 'table':
            if not self.filter_content(element) and self._is_visible(element):
                self.extract_tables(element)
            return

        for child in element.children:
            if isinstance(child, Comment):
                continue

            if isinstance(child, NavigableString):
                text = child.strip()
                if text:
                    text = child.get_text()
                    text = ' '.join(text.split())
                    cleaned_text = self.clean_text(text)
                    if cleaned_text and self._is_visible(element):
                        self.add_page_content(cleaned_text)
                        print(f"{cleaned_text}")
                        self.debug_print("text", cleaned_text)

            elif child.name == 'pre':
                print(f"\n[preformatted text]")
                is_code_block = False
                parent_div = child.find_parent('div')
                if parent_div and any(cls in parent_div.get('class', []) for cls in ['highlight', 'code']):
                    is_code_block = True
                if 'lang' in child.attrs:
                    is_code_block = True
                if is_code_block and self._is_visible(child):
                    code_text = child.get_text()
                    code_text = ' '.join(code_text.split())  # Normalize whitespace
                    self.add_page_content(code_text, content_type="code")
                    print(f"[code snippet]\n{code_text}\n")
                    self.debug_print("element_pre", code_text)


            elif child.name == 'ul':
                if not self.filter_content(child) and self._is_visible(child) and self._is_visible(element):
                    li_count = len([li for li in child.find_all('li', recursive=False)])
                    if li_count > 1:
                        print(f"\n[list]")
                        self.extract_ul_list(child)

            elif child.name == 'ol':
                if not self.filter_content(child) and self._is_visible(child):
                    print(f"\n[ordered list]")
                    self.extract_ol_list(child)

            elif child.name == 'li':
                if not self.filter_content(child) and self._is_visible(child):
                    text = child.get_text()
                    text = ' '.join(text.split())
                    cleaned_text = self.clean_text(text)
                    if cleaned_text:
                        self.add_page_content(cleaned_text, content_type="list")
                        print(f" --> {cleaned_text}")

            elif child.name in ['p']:
                if not self.filter_content(child) and self._is_visible(child):
                    text = child.get_text()
                    text = ' '.join(text.split())
                    cleaned_text = self.clean_text(text)
                    if cleaned_text:
                        self.add_page_content(cleaned_text)
                        print(f"{cleaned_text}\n")
                        self.debug_print("element_p", cleaned_text)

            elif child.name in ['a']:
                if not self.filter_content(child) and self._is_visible(child):
                    text = child.get_text()
                    text = ' '.join(text.split())
                    cleaned_text = self.clean_text(text)
                    if cleaned_text:
                        self.add_page_content(cleaned_text)
                        print(f"{cleaned_text}")
                        self.debug_print("element_a", cleaned_text)

            elif child.name in ['span']:
                if not self.filter_content(child) and self._is_visible(child):
                    text = child.get_text()
                    text = ' '.join(text.split())
                    cleaned_text = self.clean_text(text)
                    if cleaned_text:
                        self.add_page_content(cleaned_text)
                        print(f"{cleaned_text}")
                        self.debug_print("element_span", cleaned_text)

            elif child.name and child.name.startswith('h') and child.name[1:].isdigit():
                if not self.filter_content(child) and self._is_visible(child):
                    text = child.get_text()
                    text = ' '.join(text.split())
                    cleaned_text = self.clean_text(text)
                    if cleaned_text:
                        self.current_header = f"{child.name.upper()}: {cleaned_text}"
                        if self.current_header not in self.page_dict:
                            self.page_dict[self.current_header] = []
                        print(f"\n[header tag] {self.current_header}\n")
            else:
                self._extract_from_element(child)

    def extract_tables(self, element):
        print(element)
        pre_table_texts = []
        for sibling in element.find_previous_siblings():
            if sibling.name == "p":
                pre_table_texts.insert(0, sibling.get_text(strip=True))  # Pre-table text

        data = []
        headings = [th.get_text(strip=True) for th in element.find_all('tr')[0].find_all('td')]

        for row in element.find_all('tr')[1:]:
            cells = row.find_all('td')
            row_data = {headings[i]: cell.get_text(separator='\n', strip=True) for i, (_, cell) in enumerate(zip(headings, cells))}
            data.append(row_data)

        df = pd.DataFrame(data)

        table_data = {
            "pre": " ".join(pre_table_texts),
            "table": data
        }
        self.add_page_content(table_data, content_type='tables')

        if self.current_header not in self.page_dict:
            self.page_dict[self.current_header] = []

        self.page_dict[self.current_header].append({
            "tables": data
        })

        pd.set_option('display.max_colwidth', None)
        pd.set_option('display.width', None)
        self.add_to_json(header_key=self.current_header, data=table_data, data_type='tables')

        table_content = tabulate(df, headers='keys', tablefmt='grid')

        print(f"\n[Table]\n{table_content}\n")
        return

    def extract_ul_list(self, ul_element):
        data = {
            "pre": "",
            "list": [],
            "post": ""
        }

        for li in ul_element.find_all("li"):
            text = li.get_text()
            text = ' '.join(text.split())
            clean_text = self.clean_text(text)
            print(f" --> {clean_text}")
            data["list"].append(clean_text)

        pre_list_text_element = ul_element.find_previous_sibling("p")
        if pre_list_text_element:
            text = pre_list_text_element.get_text()
            text = ' '.join(text.split())
            clean_text = self.clean_text(text)
            data["pre"] = clean_text

        post_list_text_element = ul_element.find_next_sibling("p")
        if post_list_text_element:
            text = post_list_text_element.get_text()
            text = ' '.join(text.split())
            clean_text = self.clean_text(text)
            data["post"] = clean_text

        if self.current_header not in self.page_dict:
            self.page_dict[self.current_header] = []
        self.page_dict[self.current_header].append({
            "list": data["list"]
        })

        self.add_to_json(header_key=self.current_header, data=data, data_type='lists')

    def extract_ol_list(self, ol_element):
        data = {
            "pre": "",
            "list": [],
            "post": ""
        }

        for idx, li in enumerate(ol_element.find_all("li")):
            text = li.get_text()
            text = ' '.join(text.split())
            clean_text = self.clean_text(text)
            item_text = f"{idx + 1}. {clean_text}"
            print(f" --> {item_text}")
            data["list"].append(item_text)

        pre_list_text_element = ol_element.find_previous_sibling("p")
        if pre_list_text_element:
            text = pre_list_text_element.get_text()
            text = ' '.join(text.split())
            clean_text = self.clean_text(text)
            data["pre"] = clean_text

        post_list_text_element = ol_element.find_next_sibling("p")
        if post_list_text_element:
            text = post_list_text_element.get_text()
            text = ' '.join(text.split())
            clean_text = self.clean_text(text)
            data["post"] = clean_text

        if self.current_header not in self.page_dict:
            self.page_dict[self.current_header] = []
        self.page_dict[self.current_header].append({
            "list": data["list"]
        })

        self.add_to_json(header_key=self.current_header, data=data, data_type='ordered_lists')


def get_text_file_paths(master_list_filepath=r"D:\OneDrive\dev\PycharmProjects\aidream\temp\scrapes\soup\_list.txt"):
    try:
        with open(master_list_filepath, 'r', encoding='utf-8') as file:
            text_file_paths = [line.strip() for line in file if line.strip()]
        return text_file_paths
    except FileNotFoundError:
        print(f"[Error] File not found: {master_list_filepath}")
        return []
    except Exception as e:
        print(f"[Error] An error occurred: {e}")
        return []


def use_local_html_file():
    extractor = ContentExtractor()
    extractor.scrape_local_html_file(
        filepath=r"D:\a_starter\ama\private-report.html",
        url="private-report.html",
        website="ellie-private",
        path="report-1",
        unique_page_name="ellie-private-report-1"
    )


if __name__ == '__main__':
    text_file_paths = [
    ]

    if not text_file_paths:
        text_file_paths = get_text_file_paths()

    extractor = ContentExtractor()

    print(f"Opening last Text Entry")
    extractor.load_soup_from_text(text_file_paths[0])

    # use_local_html_file()
