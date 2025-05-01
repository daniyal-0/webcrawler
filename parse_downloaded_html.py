import re
import os
from bs4 import BeautifulSoup
from tqdm import tqdm
from collections import Counter

PAGES_DIR = "pages"

STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "aren't",
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", "by",
    "can't", "cannot", "could", "couldn't", "did", "didn't", "do", "does", "doesn't", "doing", "don't",
    "down", "during", "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't", "have",
    "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here", "here's", "hers", "herself", "him",
    "himself", "his", "how", "how's", "i", "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't",
    "it", "it's", "its", "itself", "let's", "me", "more", "most", "mustn't", "my", "myself", "no", "nor",
    "not", "of", "off", "on", "once", "only", "or", "other", "ought", "our", "ours", "ourselves", "out",
    "over", "own", "same", "shan't", "she", "she'd", "she'll", "she's", "should", "shouldn't", "so",
    "some", "such", "than", "that", "that's", "the", "their", "theirs", "them", "themselves", "then",
    "there", "there's", "these", "they", "they'd", "they'll", "they're", "they've", "this", "those",
    "through", "to", "too", "under", "until", "up", "very", "was", "wasn't", "we", "we'd", "we'll",
    "we're", "we've", "were", "weren't", "what", "what's", "when", "when's", "where", "where's", "which",
    "while", "who", "who's", "whom", "why", "why's", "with", "won't", "would", "wouldn't", "you",
    "you'd", "you'll", "you're", "you've", "your", "yours", "yourself", "yourselves", "a", "b", "c",
    "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w",
    "x", "y", "z", "'"
}

LOW_VALUE_DOMAINS = {"studentcouncil.ics.uci.edu"}

def html_to_text(html_bytes: bytes) -> str:
    """
    Convert raw HTML bytes to cleaned plain text.
    Removes <script> and <style> blocks, collapses whitespace.
    """
    soup = BeautifulSoup(html_bytes, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    raw = soup.get_text(separator=" ")
    return " ".join(raw.split())


def process_pages():
    """
    Iterate through saved pages, skip low-value traps,
    track the page with max words, accumulate word counts,
    and print top 50 words.
    """
    max_count = 0
    max_file = None
    word_counter = Counter()

    files = [f for f in os.listdir(PAGES_DIR) if f.endswith('.html')]

    for fname in tqdm(files, desc="Processing pages"):
        # remove all pdf files
        path = os.path.join(PAGES_DIR, fname)
        raw = open(path, 'rb').read()

        # PDF‐magic check: skip any file whose payload starts with %PDF-
        if raw.lstrip().startswith(b'%PDF-'):
            tqdm.write(f"Skipping PDF blob: {fname}")
            continue

        # Extract subdomain from filename (pattern: netloc_path.html)
        subdomain = fname.split('_', 1)[0]
        if subdomain in LOW_VALUE_DOMAINS:
            tqdm.write(f"Skipping known low-value domain: {fname}")
            continue

        path = os.path.join(PAGES_DIR, fname)
        html = open(path, 'rb').read()
        text = html_to_text(html).lower()

        words = re.findall(r"[a-z']+", text)
        count = len(words)

        # Heuristic: skip repetitive-list traps
        if count > 1000:
            unique_ratio = len(set(words)) / count
            if unique_ratio < 0.05:
                tqdm.write(f"Skipping low-value trap: {fname} ({count} words, {unique_ratio:.2%} unique)")
                continue

        # Update largest page
        if count > max_count:
            max_count = count
            max_file = fname
            tqdm.write(f"New max: {max_file} ({max_count} words)")
        tqdm.write(f"Current max: {max_file} ({max_count})")

        # Accumulate word frequencies
        word_counter.update(words)

    # Filter out stopwords and list top 50 words
    filtered = Counter({w: c for w, c in word_counter.items() if w not in STOPWORDS})
    top50 = filtered.most_common(50)

    tqdm.write("\nTop 50 words (excluding stopwords):")
    for rank, (word, freq) in enumerate(top50, start=1):
        tqdm.write(f"{rank:2d}. {word}: {freq}")


if __name__ == '__main__':
    process_pages()
