# --------------------------------------------------------
# Imports
# --------------------------------------------------------
from ast import parse
import requests
from bs4 import BeautifulSoup
import json
import re
from urllib.parse import urlparse
import tldextract

# --------------------------------------------------------
# Function: fetch_author
# --------------------------------------------------------
def fetch_author(url, soup):
    """
    Extracts the author(s) of an article from any website.
    Strategy order:
        1) JSON-LD structured data
        2) <meta> tags in <head>
        3) Visible HTML elements with 'author' in class or id
        4) Fallback: Playwright headless browser rendering
    """
    try:
        # --------------------------------------------------------
        # STRATEGY 1: Look for JSON-LD structured data in <script>
        # --------------------------------------------------------
        scripts = soup.find_all("script", type="application/ld+json")
        for script in scripts:
            try:
                data = json.loads(script.string)
                
                # Handle JSON-LD as list of dicts
                if isinstance(data, list):
                    for item in data:
                        author = item.get("author")
                        if author:
                            if isinstance(author, list):
                                return ", ".join(
                                    a.get("name") for a in author if "name" in a
                                )
                            elif isinstance(author, dict):
                                return author.get("name")
                            elif isinstance(author, str):
                                return author

                # Handle JSON-LD as a single dict
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
                continue  # Skip invalid JSON-LD scripts

        # --------------------------------------------------------
        # STRATEGY 2: Check <meta> tags in <head>
        # --------------------------------------------------------
        meta_author = (
            soup.find("meta", {"name": "author"})
            or soup.find("meta", {"property": "article:author"})
        )
        if meta_author and meta_author.get("content"):
            return meta_author["content"]

        # --------------------------------------------------------
        # STRATEGY 3: Look for visible HTML elements with "author"
        # --------------------------------------------------------
        possible_authors = soup.find_all(attrs={"class": re.compile("author", re.I)}) + \
                           soup.find_all(attrs={"id": re.compile("author", re.I)})

        for tag in possible_authors:
            text = tag.get_text(separator=" ", strip=True)
            text = re.sub(r'https?://\S+', '', text)  # Remove URLs
            text = re.sub(r'^[Bb][Yy]\s+', '', text)  # Remove "By " prefix
            text = text.strip()
            if text:
                return text

        # --------------------------------------------------------
        # STRATEGY 4: Fallback to Playwright headless browser
        # --------------------------------------------------------
        # Note: Requires playwright installed and imported
        # from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=60000)
            html = page.content()
            browser.close()
        soup = BeautifulSoup(html, "html.parser")

        # Retry visible HTML search
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
        # If no author found
        # --------------------------------------------------------
        return "Author not found."

    except Exception as e:
        return f"Error: {e}"

# --------------------------------------------------------
# Function: fetch_title
# --------------------------------------------------------
def fetch_title(url, soup):
    """
    Extracts the title of the article using meta tags.
    Checks Open Graph and Twitter meta properties.
    """
    meta_title = (
        soup.find("meta", {"property": "og:title"})
        or soup.find("meta", {"property": "twitter:title"})
    )
    if meta_title and meta_title.get("content"):
        return meta_title["content"]

# --------------------------------------------------------
# Function: fetch_date
# --------------------------------------------------------
def fetch_date(url, soup):
    """
    Extracts the publish date of the article.
    Strategy order:
        1) JSON-LD structured data
        2) <meta> tags
        3) <time> tags in HTML
    """
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string)
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and "datePublished" in item:
                        return item["datePublished"]
            elif isinstance(data, dict):
                if "datePublished" in data:
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
            return time_tag.get_text(strip=True)
    return "Date not found"

# --------------------------------------------------------
# Function: fetch_body
# --------------------------------------------------------
def fetch_body(url, soup):
    """
    Extracts the main text body of the article.
    Strategy order:
        1) JSON-LD 'articleBody'
        2) <article> tag
        3) Common <div> classes
        4) <section> tag
        5) Largest <div> fallback
    """
    # JSON-LD
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string)
            if isinstance(data, list):
                for item in data:
                    if item.get("@type") == "NewsArticle":
                        return item.get("articleBody", "").strip()
            elif isinstance(data, dict) and data.get("@type") == "NewsArticle":
                return data.get("articleBody", "").strip()
        except json.JSONDecodeError:
            continue

    # <article> tag
    article = soup.find("article")
    if article:
        paragraphs = [p.get_text(strip=True) for p in article.find_all("p")]
        if paragraphs:
            return "\n".join(paragraphs)

    # Common <div> classes
    div_classes = ["article-body", "story-body", "post-content", "content", "main-content"]
    for class_name in div_classes:
        div = soup.find("div", class_=class_name)
        if div:
            paragraphs = [p.get_text(strip=True) for p in div.find_all("p")]
            if paragraphs:
                return "\n".join(paragraphs)

    # <section> tag
    section = soup.find("section")
    if section:
        paragraphs = [p.get_text(strip=True) for p in section.find_all("p")]
        if paragraphs:
            return "\n".join(paragraphs)

    # Largest <div> fallback
    divs = soup.find_all("div")
    if divs:
        largest_div = max(divs, key=lambda d: len(d.get_text(strip=True)))
        paragraphs = [p.get_text(strip=True) for p in largest_div.find_all("p")]
        if paragraphs:
            return "\n".join(paragraphs)

    return None

# --------------------------------------------------------
# Function: fetch_domain
# --------------------------------------------------------
def fetch_domain(url):
    """
    Extracts the root domain from a URL.
    Removes subdomains like 'www' automatically.
    """
    extracted = tldextract.extract(url)
    root_domain = f"{extracted.domain}.{extracted.suffix}"
    return root_domain

# --------------------------------------------------------
# Main execution / example usage
# --------------------------------------------------------
url = "https://www.bbc.co.uk/news/articles/ce845w70g0yo"

# Headers to mimic a real browser request
headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/117.0 Safari/537.36"
    )
}

# Fetch page content
res = requests.get(url, headers=headers, timeout=10)
if res.status_code != 200:
    print(f"Error fetching article: {res.status_code}")

# Parse HTML with BeautifulSoup
soup = BeautifulSoup(res.text, "html.parser")

# Print extracted information
print(f"-> Title: {fetch_title(url, soup)}")
print("-> Author:", fetch_author(url, soup))
print(f"-> Date: {fetch_date(url, soup)}")
print(f"-> Body:\n{fetch_body(url, soup)}")
print(f"-> Domain: {fetch_domain(url)}")
