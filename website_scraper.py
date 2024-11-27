import time
from bs4 import BeautifulSoup
import re, requests, json
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
load_dotenv()

def get_content(url):
    """
    Fetches the HTML content of a given URL.
    Args:
        url (str): The URL of the website to fetch content from.
    Returns:
        str or None: The HTML content of the website if the request is successful (status code 200),
                     otherwise None.
    """
    headers = {'User-Agent': 'MyApp/1.0'}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return None
    html_content = response.text
    return html_content


def get_text_from_html(html_content: str) -> str:
    """
    Extracts visible text from HTML content.
    Args:
        html_content (str): The HTML content to extract text from.
    Returns:
        str: The visible text extracted from the HTML content.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    visible_text = soup.get_text()  # Extract all visible text
    visible_text = re.sub(r'\n{3,}', '\n', visible_text)
    return visible_text

def get_links_from_website(url:str) -> list:
    """
    Extracts all links from a website.
    Args:
        url (str): The URL of the website.
    Returns:
        list: A list of links found on the website.
    """
    html_content = get_content(url)
    if html_content is None:
        return []
    soup = BeautifulSoup(html_content, 'html.parser')
    links = soup.find_all('a', href=True)
    soup = BeautifulSoup(get_content(url), 'html.parser')
    links = soup.find_all('a', href=True)
    return [link['href'] for link in links if link['href'].startswith(url)]

def process_link(link:str, base_url:str, content_map:dict):
    """
    Processes a given link by fetching its content, extracting text and sub-links, 
    and updating the content map with the extracted information.
    Args:
        link (str): The URL of the link to process.
        base_url (str): The base URL to filter sub-links.
        content_map (dict): A dictionary to store the processed content and links.
    Returns:
        dict or None: The updated content map if the link was processed successfully, 
                      or None if the link was already in the content map or if the content could not be fetched.
    """

    if link in content_map:
        return None
    html_content = get_content(link)
    if html_content is None:
        return None

    text = get_text_from_html(html_content)
    sub_links = get_links_from_website(link)
    filtered_sub_links = [l for l in sub_links if l.startswith(base_url)]

    content_map[link] = {
        'text': text,
        'links': filtered_sub_links
    }
    return content_map

def create_content_map(links:list[str], base_url:str, base_text:str, base_links:list[str]) -> dict:
    """
    Creates a content map by processing a list of links and associating them with their respective text and links.
    Args:
        links (list): A list of URLs to process.
        base_url (str): The base URL to initialize the content map.
        base_text (str): The text content associated with the base URL.
        base_links (list): A list of links associated with the base URL.
    Returns:
        dict: A dictionary where keys are URLs and values are dictionaries containing 'text' and 'links' keys.
    """
    
    # Initialize the content map with the base URL's data
    content_map = {
        base_url: {
            'text': base_text,
            'links': base_links
        }
    }
    with ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(process_link, link, base_url, content_map)
            for link in links
        ]
        for future in futures:
            try:
                future.result()  # Ensure all threads complete
            except Exception as e:
                print(f"Error processing a link: {e}")
    return content_map

def run_content_map_creation(base_url:str,output_file_path=None)-> dict:
    """
    Fetches the content from the base URL, extracts links, and creates a content map.
    This function performs the following steps:
    1. Fetches the HTML content from the base URL.
    2. Extracts text and links from the base HTML content.
    3. Filters the links to include only those that start with the base URL.
    4. Uses a ThreadPoolExecutor to fetch the content of each link concurrently.
    5. Filters the links to include only those with a status code of 200.
    6. Creates a content map from the filtered links, base URL, base text, and base links.
    7. Optionally writes the content map to a JSON file if an output file path is provided.
    Args:
        base_url (str): The base URL to fetch content from.
        output_file_path (str, optional): The file path to write the content map to. Defaults to None.
    Returns:
        dict: The content map created from the base URL and its links.
    """
    status_codes = {}
    base_html_content = get_content(base_url)
    if base_html_content is None:
        print(f"Failed to fetch base URL: {base_url}")
        return

    base_text = get_text_from_html(base_html_content)
    base_links = get_links_from_website(base_url)
    base_links = [link for link in base_links if link.startswith(base_url)]
    start = time.time()
    with ThreadPoolExecutor() as executor:
        futures = {executor.submit(requests.get, link): link for link in base_links}
        for future in futures:
            link = futures[future]
            response = future.result()
            status_codes[link] = response.status_code
    end = time.time()
    base_links = [link for link in base_links if status_codes[link] == 200]
    content_map = create_content_map(base_links, base_url, base_text, base_links)
    # Write the content map to a JSON file
    if output_file_path:
        with open(output_file_path, 'w', encoding='utf-8') as json_file:
            json.dump(content_map, json_file, indent=4, ensure_ascii=False)
    return content_map


