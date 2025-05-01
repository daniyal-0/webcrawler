import re
from urllib.parse import urlparse, urljoin, urldefrag
from bs4 import BeautifulSoup
import os


VALID_DOMAINS = [
    "ics.uci.edu",
    "cs.uci.edu",
    "informatics.uci.edu",
    "stat.uci.edu",
]
VALID_PATH = "today.uci.edu/department/information_computer_sciences/"

PAGES_DIR = "pages"


def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

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

    if resp.status == 200:
        os.makedirs(PAGES_DIR, exist_ok=True)

        # build filename from url
        p = urlparse(url)
        fn = (p.netloc + p.path).replace("/", "_").strip("_") + ".html"

        # write the HTML
        with open(os.path.join(PAGES_DIR, fn), "wb") as f:
            f.write(resp.raw_response.content)

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

        
        if parsed.path.lower().endswith('/covid19/index.html'):
            return False
            
        if parsed.scheme not in set(["http", "https"]):
            return False

        # Must be in allowed domains or specific path
        netloc_plus_path = parsed.netloc + parsed.path
        if not (parsed.netloc == domain or parsed.netloc.endswith("." + domain)
            for domain in VALID_DOMAINS):
            return False

        fullURL = url
        # Avoid calendar dates mm-dd-yyyy
        if re.search(r"\d{2}-\d{2}-\d{4}", fullURL):
            return False
        
        # Avoid calendar dates yyyy-mm
        if re.search(r"\d{4}-\d{2}(?!-\d{2})", fullURL):
            return False
        
        # filter out yyyy-mm-dd + blacklist WICS event pages and dead/useless pages
        if re.search(r"\d{4}-\d{2}-\d{2}", fullURL):
            return False


        blacklist = ["wics.ics.uci.edu/event", "wics.ics.uci.edu/events", "wiki.ics.uci.edu/doku.php",
        "?ical=1", "action=download", "gitlab.ics.uci.edu", "code.ics.uci.edu",
        "statistics-stage.ics.uci.edu", "cbcl.ics.uci.edu/doku.php", "grape.ics.uci.edu/wiki",
        "?action=login", "?action=edit", "news.nacs.uci.edu", "http://www.ics.uci.edu/~eppstein/pix"]
        for badLink in blacklist:
            if badLink in fullURL:
                return False

        
        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz|md|m|mpg|can|cp|py|h|c|cpp|ppsx|smi|sdf|mol|psp|bib|grm|npy|pps|ps|php)$", parsed.path.lower())

    except TypeError:
        print ("TypeError for ", parsed)
        raise
