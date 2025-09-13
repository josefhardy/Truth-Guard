# Import built-in modules for URL parsing and IP handling
from urllib.parse import urlparse  # To break a URL into components
import requests                    # For sending HTTP requests
import ipaddress                   # To check if an IP is private or loopback

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
