import requests
from bs4 import BeautifulSoup
import json
import re
from playwright.sync_api import sync_playwright


def fetch_author(url, soup):
    """
    Try to extract the author of an article from any website.
    Strategy order: JSON-LD ? Meta tags ? HTML fallback ? Playwright fallback.
    """

    try:

        # ---------------------------------------------------------
        # 2) STRATEGY 1: Look for JSON-LD structured data in <script>
        # ---------------------------------------------------------
        scripts = soup.find_all("script", type="application/ld+json")
        for script in scripts:
            try:
                # Load the JSON from inside the <script> tag
                data = json.loads(script.string)

                # JSON-LD can be a list of dicts
                if isinstance(data, list):
                    for item in data:
                        author = item.get("author")
                        if author:
                            # Handle multiple authors
                            if isinstance(author, list):
                                return ", ".join(
                                    a.get("name") for a in author if "name" in a
                                )
                            # Handle single author dict
                            elif isinstance(author, dict):
                                return author.get("name")
                            # Handle author as plain string
                            elif isinstance(author, str):
                                return author

                # Or JSON-LD can be a single dict
                elif isinstance(data, dict):
                    author = data.get("author")
                    if author:
                        if isinstance(author, list):
                            return ", ".join(
                                a.get("name") for a in author if "name" in a
                            )
                        elif isinstance(author, dict):
                            return author.get("name")
                        elif isinstance(author, str):
                            return author

            except (json.JSONDecodeError, TypeError):
                # If JSON is invalid, just skip this script tag
                continue

        # ----------------------------------------------
        # 3) STRATEGY 2: Check <meta> tags in <head>
        # ----------------------------------------------
        meta_author = (
            soup.find("meta", {"name": "author"})
            or soup.find("meta", {"property": "article:author"})
        )
        if meta_author and meta_author.get("content"):
            return meta_author["content"]

        # --------------------------------------------------------
        # 4) STRATEGY 3: Look for visible HTML elements with "author"
        # --------------------------------------------------------
        # Find elements whose class or id contains the word "author"
        possible_authors = soup.find_all(attrs={"class": re.compile("author", re.I)}) + \
                           soup.find_all(attrs={"id": re.compile("author", re.I)})

        for tag in possible_authors:
            # Extract the visible text inside the element
            text = tag.get_text(separator=" ", strip=True)

            # Clean it up:
            text = re.sub(r'https?://\S+', '', text)       # remove URLs
            text = re.sub(r'^[Bb][Yy]\s+', '', text)       # remove "By " prefix
            text = text.strip()

            if text:
                return text

        # --------------------------------------------------------
        # 5) STRATEGY 4: Fallback to Playwright (headless browser)
        # --------------------------------------------------------
        # If all else fails, use Playwright to fully render the page
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)  # start headless Chrome
            page = browser.new_page()
            page.goto(url, timeout=60000)               # open the page
            html = page.content()                       # get rendered HTML
            browser.close()

        # Re-parse the rendered HTML
        soup = BeautifulSoup(html, "html.parser")

        # Look again for elements with "author" in class or id
        possible_authors = soup.find_all(attrs={"class": re.compile("author", re.I)}) + \
                           soup.find_all(attrs={"id": re.compile("author", re.I)})

        for tag in possible_authors:
            text = tag.get_text(separator=" ", strip=True)
            text = re.sub(r'https?://\S+', '', text)
            text = re.sub(r'^[Bb][Yy]\s+', '', text)
            text = text.strip()

            if text:
                return text

        # --------------------------------------------------------
        # 6) If no author found, return fallback message
        # --------------------------------------------------------
        return "Author not found."

    except Exception as e:
        # Catch any unexpected error
        return f"Error: {e}"

def fetch_title(url, soup):
        meta_title = (
            soup.find("meta", {"property": "og:title"})
            or soup.find("meta", {"property": "twitter:title"})
            )
        if meta_title and meta_title.get("content"):
            return meta_title["content"]

def fetch_date(url, soup):
    for script in soup.findall("script", type = "application/ld+json"):

        try:
            data = json.loads(script.string)

            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and "dataPublished" in item:
                        return item["datePubliched"]
            elif isinstance(data, dict):
                if "datePublished" in date:
                        return data["datePublished"]
        except:
            continue 


    meta_date = (
            soup.find("meta", {"property":"article:published_time"})
            or soup.find("meta", {"property":"og:updated_time"})
            or soup.find("meta", {"name": "date"})
        )
    if meta_date and meta_date.get("content"):
        return meta_date["content"]

    time_tag = soup.find("time")
    if time_tag:
        if time_tag.get("datetime"):
            return time_tag["datetime"]
        else:
            return time_tag.get_text(strip = True)
    return "Date not found"
    




url = "https://www.bbc.co.uk/news/articles/ce845w70g0yo"

headers = {
        "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/117.0 Safari/537.36"
            )
    }

res = requests.get(url, headers = headers, timeout = 10)

if res.status_code != 200:
    print(f"Error fetching article title:{res.status_code}")

soup = BeautifulSoup(res.text, "html.parser")

print(f"-> Title: {fetch_title(url, soup)}")
print("-> Author:", fetch_author(url, soup))
print(f"-> Date: {fetch_date(url, soup)}")
