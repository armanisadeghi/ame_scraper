import requests
import random
from bs4 import BeautifulSoup
from common.utils.my_utils import pretty_print_data

# This script partially works and works well for some things, but if we really wanted to use it, there has to be time spent on a lot of specifics.
# probably a few days of work.
# Also, I have a feeling they change these numbers so we would have to have a way of quickly finding and updating them.
# They should probably come from a config dictionary, not the code.
# Also, every few searches, the results get really weird and different so I think they are detecting the bot. (We need to recognize those and do something with it)


user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1'
]
accept_text = [
    'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
]

headers_Get_2 = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:49.0) Gecko/20100101 Firefox/49.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}


headers_Get = {
    'User-Agent': random.choice(user_agents),
    'Accept': random.choice(accept_text),
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1', # Do Not Track Request Header
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-User': '?1',
    'Sec-Fetch-Dest': 'document'
}


def extract_search_results(result):
    extracted_results = []
    level_1_divs = result.find_all('div', recursive=False)
    if not level_1_divs:
        print("No Level 1 divs found.")
    for level_1_div in level_1_divs:
        level_2_divs = level_1_div.find_all('div', recursive=False)
        if not level_2_divs:
            print("Level 1 div present, but no Level 2 divs found.")
            print(level_1_div)
        for level_2_div in level_2_divs:
            result_data = {}
            description_element = level_2_div.find(lambda tag: tag.name == 'div' and 'VwiC3b' in tag.get('class', []), recursive=True)
            if description_element:
                description_text = description_element.get_text(separator=" ", strip=True)
                result_data['description'] = description_text
            else:
                # if div class is "Wt5Tfe" then it's a people also ask section
                if level_2_div.get('class') == ['Wt5Tfe']:
                    print("People also ask:")
                    # recursively search for class span "CSkcDe" to get the all of the questions:
                    questions = level_2_div.find_all('span', class_='CSkcDe')
                    for question in questions:
                        print(question.get_text(strip=True))
                        result_data['type'] = "People also ask"
                        result_data['type'] = question.get_text(strip=True)
                        extracted_results.append(result_data.copy())
                elif level_2_div.get('class') == ['uVMCKf']:
                    print("YouTube Videos:")
                    # recursively search for data_surl to get the all of the video links:
                    video_links = level_2_div.find_all('a', class_='BVG0Nb', recursive=True)
                    for video_link in video_links:
                        print(video_link['href'])
                        result_data['type'] = "YouTube Videos"
                        result_data['url'] = video_link['href']
                        extracted_results.append(result_data.copy())

                # look for div classes that start with "Ww4FFb" to get discussions and forums
                elif level_2_div.get('class') and level_2_div.get('class')[0].startswith('Ww4FFb'):
                    print("Discussions and forums:")
                    result_data['type'] = "Discussions and forums"
                    text_element = level_2_div.find_all('div', class_='r0uZsf', recursive=True)


                else:
                    print("Level 2 div present, but no description or People also ask found. Must be something else.")
                    # print the first 1,000 chars of the div
                    print(f"Div: {level_2_div.get_text()[:1000]}")

            level_3_divs = level_2_div.find_all('div', recursive=False)
            if not level_3_divs:
                print("Level 2 div present, but no Level 3 divs found.")
                print(level_2_div)
            for level_3_div in level_3_divs:
                elements = level_3_div.find_all('div', recursive=False)
                if not elements:
                    print("Level 3 div present, but no inner div elements found.")
                    print(level_3_div)
                for element in elements:
                    title_element = element.find('h3')
                    if title_element:
                        title_text = title_element.get_text(strip=True)
                        result_data['title'] = title_text

                    url_element = element.find('a', href=True)
                    if url_element:
                        result_data['url'] = url_element['href']
                        if result_data:
                            extracted_results.append(result_data.copy())
                            print(f"Title: {result_data.get('title', 'None')}")
                            print(f"Description: {result_data.get('description', 'None')}")
                            print(f"URL: {result_data.get('url', 'None')}")
                    #else:
                        # print the first 100 characters of the element
                        #print(f"Element: {element.get_text()[:100]}")

    return extracted_results


def google(q):
    print("Searching for:", q)
    s = requests.Session()
    q = '+'.join(q.split())
    url = 'https://www.google.com/search?q=' + q + '&ie=utf-8&oe=utf-8'
    r = s.get(url, headers=headers_Get)
    print(f"Request URL: {url} | Status Code: {r.status_code}")
    print(f"=" * 50)
    print()

    if r.status_code == 200:
        soup = BeautifulSoup(r.text, "html.parser")
        output = []
        main_container = soup.find('div', class_='main')
        if main_container:
            search_results = main_container.select('.GyAeWb .s6JM6d .eqAnXb .dURPMd')
            for i, result in enumerate(search_results):
                individual_results = result.find_all('div', recursive=False)

                for j, individual_result in enumerate(individual_results):
                    print(f"Result {j + 1}:")
                    result_data = extract_search_results(individual_result)
                    output.extend(result_data)
                    print(f"-" * 50)

            return output, soup
        else:
            print("Main Container not found. Diagnosing the issue...\n")
            print(soup)
            all_divs = soup.find_all('div')
            for i, div in enumerate(all_divs):
                print(f"Div {i + 1}: Class='{div.get('class')}', ID='{div.get('id')}'")
                if i >= 100:
                    print("...and more")
                    break
            return [], None
    else:
        print("Failed to retrieve content")
        return [], None


if __name__ == '__main__':
    query = 'lip filler'
    output, soup = google(query)

    if output:
        pretty_print_data(output)
    else:
        print("No results found or there was an error in fetching the results.")
