import requests
from bs4 import BeautifulSoup


#gets author name from given article 
def get_author(soup) -> str:
 
    author_meta = soup.find("meta", attrs={"name":"author"})
    if author_meta and author_meta.get("content"):
        return author_meta["content"].strip()

    author_tag = soup.find("span", class_ = "author-name")
    if author_tag:
        return author_tag.get_text(strip=True)

    og_author = soup.find("meta", property='article:author')
    if og_author and og_author.get("content"):
        return og_author["content"].strip()
        if value.Startswith("http"):
            return "Unknown"

    bbc_author = soup.find("span", class_="ssrcss-1pjc44v-Contributor")
    if bbc_author:
        return bbc_author.get_text(strip=True)

    # If nothing worked
    return "Unknown"

import requests
from bs4 import BeautifulSoup

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/117.0 Safari/537.36"
    )
}

article = "https://www.bbc.co.uk/news/articles/ce845w70g0yo"

response = requests.get(article, headers=headers, allow_redirects=True)

print("Status code:", response.status_code)
print("Final URL:", response.url)  # Should still be bbc.co.uk, not facebook.com

soup = BeautifulSoup(response.text, "html.parser")

author_name = get_author(soup)
print(author_name)



