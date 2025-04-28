import re
from urllib.parse import urlparse, urljoin, urldefrag
from bs4 import BeautifulSoup
import hashlib
from collections import Counter
from urllib.parse import urlunparse

# 1 MBs
MAX_PAGE_BYTES = 1_048_576
CRAWLED_LINKS: set[str] = set()
LONGEST_DOC: tuple[str, int] = ("", 0)
WORD_COUNTS: Counter = Counter()
SEEN_HASH: set[str] = set()
_WORD_RE = re.compile(r"\b\w+\b")

BLOCK_CAL = re.compile(r'/calendar/|/events/|\d{4}/\d{2}/\d{2}|tribe-bar-date=\d{4}-\d{2}-\d{2}')

VALID_DOMAINS = [
    "ics.uci.edu",
    "cs.uci.edu",
    "informatics.uci.edu",
    "stat.uci.edu",
]
VALID_PATH = "today.uci.edu/department/information_computer_sciences/"

# Commonly used words lacking in semantic value and filtered out of
STOP_WORDS = {
    "about", "above", "after", "again", "against", "all", "also", "am", "an",
    "and", "any", "are", "around", "as", "at",
    "be", "because", "been", "before", "being", "below", "between", "both",
    "but", "by",
    "can", "cannot", "could",
    "did", "do", "does", "doing", "down", "during",
    "each",
    "few", "for", "from", "further",
    "had", "has", "have", "having", "he", "her", "here", "hers", "him",
    "his", "how",
    "if", "in", "into", "is", "it", "its",
    "just",
    "may", "might", "more", "most", "must", "my",
    "no", "nor", "not", "now",
    "of", "off", "on", "once", "only", "or", "other", "our", "out", "over",
    "own",
    "same", "she", "should", "so", "some", "such",
    "than", "that", "the", "their", "them", "then", "there", "these", "they",
    "this", "those", "through", "to", "too",
    "under", "until", "up",
    "very",
    "was", "we", "were", "what", "when", "where", "which", "while", "who",
    "whom", "why", "with", "would",
    "you", "your"
}

def pull_text_content(resp) -> str:
    """Return visible text from HTML page"""
    if resp.status != 200 or resp.raw_response is None:
        return ""

    ctype = resp.raw_response.headers.get("Content-Type", "").lower()
    if "text/html" not in ctype:
        return ""

    try:
        if int(resp.raw_response.headers.get("Content-Length", 0)) > MAX_PAGE_BYTES:
            return ""
    except ValueError:
        pass

    soup = BeautifulSoup(resp.raw_response.content, "html.parser")
    for tag in soup(["script", "style", "img", "nav"]):
        tag.decompose()

    return soup.get_text(" ", strip=True)

def break_into_words(text: str) -> list[str]:
    """Tokenise into lowercase nums/letters."""
    return _WORD_RE.findall(text.lower())

def accumulate_tokens(toks: list[str]) -> None:
    """Update WORD_COUNTS, not including single char tokens and stop words."""
    WORD_COUNTS.update(
        t for t in toks
        if len(t) > 1 and t not in STOP_WORDS
    )

def hash_text(text: str) -> str:
    """Secure Hash Algorithm, digest size of 256 bits."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def scraper(url, resp):
    text_content = pull_text_content(resp)
    words = break_into_words(text_content)
    content_hash = hash_text(text_content)
    accumulate_tokens(words)

    for link in valid_links:
        CRAWLED_LINKS.add(link)

def extract_next_links(url, resp):
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content

    output_links = []
    
    if resp.status != 200:
        # return if the page did not load properly
        return output_links
    
    try:
        soup = BeautifulSoup(resp.raw_response.content, "html.parser")
        for link_tag in soup.find_all("a"):
            href = link_tag.get("href")
            if href:
                # Make absolute URL based on base `url`
                absolute_url = urljoin(url, href)
                # Remove fragments
                absolute_url, _ = urldefrag(absolute_url)
                output_links.append(absolute_url)
    except Exception as e:
        print(f"Error while parsing {url}: {e}")

    return output_links

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False

        # Must be in allowed domains or specific path
        netloc_plus_path = parsed.netloc + parsed.path
        if not (any(domain in parsed.netloc for domain in VALID_DOMAINS) or VALID_PATH in netloc_plus_path):
            return False

        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())

    except TypeError:
        print ("TypeError for ", parsed)
        raise

