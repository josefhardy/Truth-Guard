from turtle import back
from urllib.parse import urlparse
import requests
import ipaddress
import tldextract
import time
import whois
import datetime
import scraper as scraper 
import re
import unicodedata
from bs4 import BeautifulSoup

# -----------------------------
# Simple TLD cache
# -----------------------------
_tld_abuse_cache = {"timestamp": 0, "data": {}}

# -----------------------------
# Validator function
# -----------------------------
def validator(url, headers):
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return False, "Invalid URL format"
    if not url.startswith(("http://", "https://")):
        return False, "URL must begin with 'http' or 'https'"

    try:
        host = parsed.hostname
        try:
            ip = ipaddress.ip_address(host)
            if ip.is_private or ip.is_loopback:
                return False, "URL is a local or private IP"
        except ValueError:
            if host in ["localhost", "127.0.0.1"]:
                return False, "URL points to a local host"

        res = requests.get(url, headers=headers, timeout=5, allow_redirects=True)
        content_type = res.headers.get("Content-Type", "").lower()
        if res.status_code == 200 and "text/html" in content_type:
            return True, res.url
        else:
            return False, f"Error: {res.status_code}"
    except requests.RequestException as e:
        return False, f"Request failed: {e}"

# -----------------------------
# Fetch abuse data
# -----------------------------
def fetch_surbl_most_abused_tlds(force_refresh=False):
    global _tld_abuse_cache
    now = time.time()
    if not force_refresh and _tld_abuse_cache["data"] and (now - _tld_abuse_cache["timestamp"] < 24 * 3600):
        return _tld_abuse_cache["data"]

    abuse_dict = {}
    try:
        csv_url = "https://www.surbl.org/tld?format=csv"
        resp = requests.get(csv_url, timeout=10)
        resp.raise_for_status()
        lines = resp.text.splitlines()
        for line in lines[1:]:
            parts = line.strip().split(",")
            if len(parts) >= 2:
                tld = parts[0].lower()
                try:
                    abuse_dict[tld] = int(parts[1])
                except ValueError:
                    continue
        _tld_abuse_cache["timestamp"] = now
        _tld_abuse_cache["data"] = abuse_dict
    except Exception:
        abuse_dict = _tld_abuse_cache["data"]
    return abuse_dict

# -----------------------------
# Score TLD
# -----------------------------
def score_tld(url):
    ext = tldextract.extract(url)
    tld = ext.suffix.lower()

    trusted_tlds = {"gov", "edu", "mil"}
    if tld in trusted_tlds or any(tld.endswith("." + tt) for tt in trusted_tlds):
        return 25, f"TLD '{tld}' is restricted and highly trusted."

    abuse_data = fetch_surbl_most_abused_tlds(force_refresh=False)

    # Direct match in abuse data
    if tld in abuse_data and abuse_data:
        max_count = max(abuse_data.values())
        abuse_rate = abuse_data[tld] / max_count
        score = int((1 - abuse_rate) * 25)
        return score, f"TLD '{tld}' abuse rate {abuse_rate:.4f}, score {score}/25"

    # Compound TLD fallback
    parts = tld.split(".")
    if len(parts) > 1:
        primary_tld = parts[-1]
        if primary_tld in abuse_data and abuse_data:
            max_count = max(abuse_data.values())
            abuse_rate = abuse_data[primary_tld] / max_count
            score = int((1 - abuse_rate) * 25)
            return score, f"Compound TLD '{tld}', primary '{primary_tld}' abuse rate {abuse_rate:.4f}, score {score}/25"
        else:
            safe_ccTLDs = {"uk", "de", "fr", "ca", "au", "us", "jp", "nl", "se"}
            if primary_tld in safe_ccTLDs:
                return 20, f"Compound TLD '{tld}' with primary '{primary_tld}' assumed safe → 20/25"

    return 12, f"TLD '{tld}' not found in live abuse dataset, neutral fallback"

# -----------------------------
# Google Safe Browsing
# -----------------------------
def check_url_safebrowsing(url, api_key):
    endpoint = "https://safebrowsing.googleapis.com/v4/threatMatches:find"
    payload = {
        "client": {"clientId": "YourAppName", "clientVersion": "1.0"},
        "threatInfo": {
            "threatTypes": ["MALWARE", "SOCIAL_ENGINEERING", "UNWANTED_SOFTWARE"],
            "platformTypes": ["ANY_PLATFORM"],
            "threatEntryTypes": ["URL"],
            "threatEntries": [{"url": url}]
        }
    }
    params = {"key": api_key}
    try:
        resp = requests.post(endpoint, json=payload, params=params, timeout=6)
        resp.raise_for_status()
        data = resp.json()
        if "matches" in data:
            return 5, f"URL flagged as malicious by Google Safe Browsing: {data['matches']}"
        else:
            return 25, "URL not found in Google Safe Browsing database"
    except requests.RequestException as e:
        return 12, f"Could not check URL dynamically: {e}"

# -----------------------------
# Domain analysis
# -----------------------------
def domain_analysis(url, safe_browsing_api_key=None):
    score = 0
    weights = {"https": 20, "tld": 25, "patterns": 25, "age": 30}
    parsed = urlparse(url)

    # Start with full denominator
    denominator = sum(weights.values())
    whois_failed = False

    # HTTPS check
    if parsed.scheme == "https":
        score += weights["https"]
        print("URL begins with 'https' = 20 points\n")
    elif parsed.scheme == "http":
        score += int(weights["https"] * 0.25)
        print("URL begins with 'http' = 5 points\n")
    else:
        print("No HTTP scheme detected -> 0 points\n")

    # TLD score
    tld_score, tld_msg = score_tld(url)
    score += int(weights["tld"] * tld_score / 25)
    print(f"{tld_msg} = {tld_score} points\n")

    # Safe Browsing score
    if safe_browsing_api_key:
        pattern_score, pattern_msg = check_url_safebrowsing(url, safe_browsing_api_key)
    else:
        pattern_score, pattern_msg = 25, "Safe Browsing not checked; assuming not flagged"
    score += int(weights["patterns"] * pattern_score / 25)
    print(f"{pattern_msg} = {pattern_score} points\n")

    # WHOIS domain age
    age_score = None
    try:
        ext = tldextract.extract(url)
        domain = f"{ext.domain}.{ext.suffix}"
        w = whois.whois(domain)
        creation_date = None
        if hasattr(w, "creation_date"):
            creation_date = w.creation_date
            if isinstance(creation_date, list):
                creation_date = creation_date[0]
        if not creation_date and hasattr(w, "registry_creation_date"):
            creation_date = w.registry_creation_date
            if isinstance(creation_date, list):
                creation_date = creation_date[0]

        # Parse string dates robustly
        if isinstance(creation_date, str):
            try:
                creation_date = datetime.datetime.strptime(creation_date[:19], "%Y-%m-%d %H:%M:%S")
            except Exception:
                creation_date = None

        if creation_date:
            age = (datetime.datetime.now() - creation_date).days / 365.25
            if age < 0.5:
                age_score = 5
            elif age < 1:
                age_score = 10
            elif age < 2:
                age_score = 15
            elif age < 5:
                age_score = 20
            elif age < 10:
                age_score = 25
            else:
                age_score = 30
            print(f"site age: {age:.2f} years = {age_score} points\n")
        else:
            raise ValueError("No creation date found")
    except Exception as e:
        print(f"WHOIS lookup failed -> removing age factor ({e})\n")
        denominator -= weights["age"]
        whois_failed = True

    # Only add age if available
    if age_score is not None:
        score += int(weights["age"] * age_score / 30)

    # Convert to percentage
    percentage = (score / denominator) * 100

    # Apply 10% deduction if WHOIS failed
    if whois_failed:
        percentage *= 0.9
        print("⚠️ WHOIS failed → 10% penalty applied\n")

    return round(percentage, 2)
# -----------------------------
# -----------------------------
# Example usage
# -----------------------------

def clean_text(raw_html):
    # Store raw text for debugging
    raw_text = raw_html

    # Parse HTML
    soup = BeautifulSoup(raw_html, "html.parser")

    # Remove unwanted elements by tag
    for tag in ['nav', 'aside', 'footer', 'form', 'header', 'noscript', 'script', 'style']:
        for el in soup.find_all(tag):
            el.decompose()

    # Remove elements by common class or id patterns
    patterns = re.compile(r"(menu|nav|share|ad|footer|header|sidebar|promo|cookie|banner|subscribe|social)", re.I)
    for el in soup.find_all(attrs={"class": patterns}):
        el.decompose()
    for el in soup.find_all(attrs={"id": patterns}):
        el.decompose()

    # Get text and normalize whitespace
    text = soup.get_text(separator=' ', strip=True)
    text = re.sub(r'\s+', ' ', text)

    # Normalize unicode (fixes things like “Â£” for “£”)
    text = unicodedata.normalize("NFKC", text)
    text = text.encode("latin1", errors="ignore").decode("utf-8", errors="ignore")

    return text

safe_browsing_api_key = "AIzaSyDew5sveLuhqBrJQ-Aa72aTvTG3SWIc7I0"

url = "https://www.bbc.co.uk/news/articles/c5y8r2gk0vyo"
headers = {"User-Agent": "Mozilla/5.0"}

isValid, response = validator(url, headers)
print(isValid, ": ", response, "\n")

if isValid:
    #final_score = domain_analysis(response, safe_browsing_api_key)
    #print(f"\n🌐 Final domain analysis score: {final_score}/100")
    print()

res = requests.get(url, headers=headers, timeout=10)
if res.status_code != 200:
    print(f"Error fetching article: {res.status_code}")


# Parse HTML with BeautifulSoup
soup = BeautifulSoup(res.text, "html.parser")

raw_text = scraper.fetch_body(url, soup)

cleaned_text = clean_text(raw_text)

print("This is the clean txt")
print(cleaned_text)
