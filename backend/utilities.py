# Import built-in modules for URL parsing and IP handling
from urllib.parse import urlparse  # To break a URL into components
import requests                    # For sending HTTP requests
import ipaddress                   # To check if an IP is private or loopback
import tldextract 
import time 
import whois 
import datetime

_tld_abuse_cache = {
    "timestamp": 0,
    "data": {}  # initially empty, will be populated when fetching live data
}

# -----------------------------
# Validator function
# -----------------------------

def validator(url, headers):
    """
    Validates a URL by performing multiple checks:
    1. Syntax and scheme check
    2. Private/local IP or localhost check
    3. Reachability and HTML content check
    Returns: (True/False, message)
    """

    # ---- 1. Syntax check ----
    parsed = urlparse(url)  # Break URL into components: scheme, netloc, path, etc.
    if not parsed.scheme or not parsed.netloc:
        return False, "Invalid URL format"  # Missing scheme (http/https) or domain
    if not url.startswith(("http://", "https://")):
        return False, "URL must begin with 'http' or 'https'"  # Only allow web URLs

    # ---- 2. Private or local host check ----
    try:
        host = parsed.hostname  # Extract hostname from URL (e.g., www.bbc.co.uk or 127.0.0.1)
        ip = ipaddress.ip_address(host)  # Try to convert host to IP
        # If the IP is private (10.x.x.x, 192.168.x.x) or loopback (127.0.0.1), reject
        if ip.is_private or ip.is_loopback:
            return False, "URL is a local or private IP"
    except ValueError:
        # Host is not an IP address, could be a domain
        if host in ["localhost", "127.0.0.1"]:  # Catch common local hosts
            return False, "URL points to a local host"

    # ---- 3. Reachability and content-type check ----
    try:
        # Send a GET request to the URL with custom headers
        # allow_redirects=True follows redirects automatically
        # timeout=5 prevents hanging on slow responses
        res = requests.get(url, headers=headers, timeout=5, allow_redirects=True)

        # Check if server returned 200 OK and the content type is HTML
        if res.status_code == 200 and "text/html" in res.headers.get("Content-Type", "").lower():
            # URL is valid, reachable, and points to an HTML page
            return True, f"Valid and reachable URL: {res.url}"  # Return the final URL after redirects
        else:
            return False, f"Error: {res.status_code}"  # Status not 200 or not HTML
    except requests.RequestException as e:
        # Handles network issues (timeout, DNS failure, connection error)
        return False, f"Request failed: {e}"

def domain_analysis(url):

    safe_browsing_api_key = "AIzaSyDew5sveLuhqBrJQ-Aa72aTvTG3SWIc7I0"
    score = 0
    weights = {
        "https" : 20,
        "tld" : 25,
        "patterns" : 25,
        "age" : 30
        }

    parsed = urlparse(url)

    if parsed.scheme == "https":
        score += weights["https"]
        print("URl begins with 'https' = 20 points")
    elif parsed.scheme == "https":
        score += int(weights["http"]*0.25)
        print("URL begins with 'http' = 5 points")


    tld_score, tld_score_emssage = score_tld(url)
    score += int(weights["tld"]*tld_score/25)
    print(f"{tld_score_emssage} = {tld_score} points")

    pattern_score, pattern_message = check_url_safebrowsing(url, safe_browsing_api_key)
    score += int(weights["patterns"]*pattern_score/25)
    print(f"{pattern_message} = {pattern_score} points")

    ext = tldextract.extract(url)
    domain = f"{ext.domain}.{ext.suffix}"

    try:
        w = whois.whois(domain)
        creation_date = w.creation_date

        if isinstance(creation_date, list):
            creation_date = creation_date[0]

        if not creation_date:
            age, age_message, age_score = 1, "No creation date found, default points awarded = 15", 15

        else:
            age = (datetime.datetime.now() - creation_date).days/365.25

            if age < 0.5:
                age_score, age_message = 5, f"site is {age} years old, -> 5 points"
            elif age < 1:
                age_score, age_message = 10, f"site is {age} years old -> 10 points"
            elif age < 2:
                age_score, age_message = 15, f"site is {age} years old, -> 15 points"
            elif age < 5:
                age_score, age_message = 20, f"site is {age} years old -> 20 points"
            elif age < 10:
                age_score, age_message = 25, f"site is {age} years old, -> 25 points"
            else:
                age_score, age_message = 30, f"site is {age} years old, -> 30 points"

            print(f"site age: {age} = {age_score} points")
    except Exception as e:
        age_score, age_message = 15, f"WHOIS lookup failed, neutral score ({e})"

    score += (weights["age"]*age_score/30)

    return score

def score_tld(url):
    """
    Score a domain's TLD credibility.
    Handles ccTLDs and compound TLDs (like .co.uk).
    Live-data-first, cache-assisted.
    Returns: score 0-25, explanation.
    """
    ext = tldextract.extract(url)
    # ext.suffix gives full public suffix, e.g. 'co.uk'
    tld = ext.suffix.lower()

    # Restricted / highly trusted TLDs
    trusted_tlds = {"gov", "edu", "mil"}
    # Also handle restricted ccTLDs if you want: e.g. .gov.uk
    if tld in trusted_tlds or any(tld.endswith("." + tt) for tt in trusted_tlds):
        return 25, f"TLD '{tld}' is restricted and highly trusted."

    # Fetch live abuse data
    abuse_data = fetch_surbl_most_abused_tlds()

    # Direct match
    if tld in abuse_data:
        max_count = max(abuse_data.values()) if abuse_data else 1
        abuse_rate = abuse_data[tld] / max_count
        score = int((1 - abuse_rate) * 25)
        explanation = f"TLD '{tld}' abuse rate {abuse_rate:.4f}, score {score}/25"
        return score, explanation

    # Attempt to fallback to last part of TLD for compound TLDs
    parts = tld.split(".")
    if len(parts) > 1:
        primary_tld = parts[-1]  # e.g., 'uk' from 'co.uk'
        if primary_tld in abuse_data:
            max_count = max(abuse_data.values()) if abuse_data else 1
            abuse_rate = abuse_data[primary_tld] / max_count
            score = int((1 - abuse_rate) * 25)
            explanation = f"Compound TLD '{tld}', primary TLD '{primary_tld}' abuse rate {abuse_rate:.4f}, score {score}/25"
            return score, explanation

    # If all fails, neutral fallback
    return 12, f"TLD '{tld}' not found in live abuse dataset, neutral fallback"

def fetch_surbl_most_abused_tlds(force_refresh=False):
    """
    Fetch live TLD abuse data from SURBL.
    Cache is used to avoid repeated API calls within 24h.
    Returns: {tld: abuse_count}
    """
    global _tld_abuse_cache
    now = time.time()

    # Return cached data if it's fresh and no force refresh
    if not force_refresh and _tld_abuse_cache["data"] and (now - _tld_abuse_cache["timestamp"] < 24 * 3600):
        return _tld_abuse_cache["data"]

    abuse_dict = {}
    try:
        # Replace with actual SURBL CSV endpoint
        csv_url = "https://www.surbl.org/tld?format=csv"
        resp = requests.get(csv_url, timeout=10)
        resp.raise_for_status()  # Raise exception if status != 200

        lines = resp.text.splitlines()
        for line in lines[1:]:  # skip header
            parts = line.strip().split(",")
            if len(parts) >= 2:
                tld = parts[0].lower()
                try:
                    abuse_dict[tld] = int(parts[1])
                except ValueError:
                    continue

        # Update the cache
        _tld_abuse_cache["timestamp"] = now
        _tld_abuse_cache["data"] = abuse_dict

    except Exception as e:
        # Fallback: use existing cache if network fails
        abuse_dict = _tld_abuse_cache["data"]

    return abuse_dict

def check_url_safebrowsing(url, api_key):
    """
    Check a URL against Google Safe Browsing.
    Returns: (score, explanation)
    """
    endpoint = "https://safebrowsing.googleapis.com/v4/threatMatches:find"
    
    payload = {
        "client": {
            "clientId": "YourAppName",
            "clientVersion": "1.0"
        },
        "threatInfo": {
            "threatTypes": ["MALWARE", "SOCIAL_ENGINEERING", "UNWANTED_SOFTWARE"],
            "platformTypes": ["ANY_PLATFORM"],
            "threatEntryTypes": ["URL"],
            "threatEntries": [
                {"url": url}
            ]
        }
    }
    
    params = {"key": api_key}
    
    try:
        resp = requests.post(endpoint, json=payload, params=params, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        
        if "matches" in data:
            # URL is listed as malicious
            return 5, f"URL flagged as malicious by Google Safe Browsing: {data['matches']}"
        else:
            # URL not listed
            return 25, "URL not found in Google Safe Browsing database"
    
    except requests.RequestException as e:
        # If API fails, assign neutral score
        return 12, f"Could not check URL dynamically: {e}"




# -----------------------------
# Example usage
# -----------------------------
url = "https://www.bbc.co.uk/news/articles/c5y8r2gk0vyo"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/117.0 Safari/537.36"
}

# Call the validator function
isValid, response = validator(url, headers)

# Print the result
print(isValid, ": ", response)


domain_analysis_score = domain_analysis(url)

print(f"Domain analysis score: {domain_analysis_score}")
