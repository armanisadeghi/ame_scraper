# Stupid for now so it can be deleted, but the point was to check url patterns
import ast
import os
from urllib.parse import urlparse


def get_domain_from_url(url):
    """
    Extract the domain from a URL and return it with its original scheme (HTTP or HTTPS).

    :param url: The URL from which to extract the domain
    :return: Domain with its original scheme, or None if the URL is invalid
    """
    try:
        parsed_url = urlparse(url)
        scheme = parsed_url.scheme  # 'http' or 'https'
        if scheme in ['http', 'https']:
            domain_with_scheme = f"{scheme}://{parsed_url.netloc}"
            return domain_with_scheme
        else:
            return None
    except Exception as e:
        print(f"Error parsing URL: {e}")
        return None


def check_url_patterns(node):
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        if node.func.id in ('path', 're_path'):
            url_pattern = node.args[0].s
            if url_pattern.startswith('/'):
                print('URL pattern should not start with a slash:', url_pattern)
            if node.func.id == 're_path' and '<' in url_pattern:
                print('Use path converters instead of regular expressions in URL patterns:', url_pattern)

def main():
    urls_py_path = 'urls.py'  # sample
    if not os.path.exists(urls_py_path):
        print("The specified path does not exist.")
        return

    with open(urls_py_path, 'r') as f:
        tree = ast.parse(f.read(), filename=urls_py_path)

    for node in ast.walk(tree):
        check_url_patterns(node)

if __name__ == '__main__':
    main()
