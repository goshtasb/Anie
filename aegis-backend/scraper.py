# scraper.py - Server-side article scraper for mobile/web users
import httpx
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import re
import json

# User agent to avoid blocks - must look like a real browser
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Full browser-like headers
REQUEST_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
}

# Timeout for fetching pages
FETCH_TIMEOUT = 15.0

# Known paywall domains - give users a helpful message
PAYWALL_DOMAINS = [
    'wsj.com', 'nytimes.com', 'ft.com', 'bloomberg.com',
    'economist.com', 'barrons.com', 'theathletic.com',
    'washingtonpost.com', 'latimes.com'
]

# Elements to remove (ads, nav, comments, etc.)
NOISE_TAGS = [
    'script', 'style', 'noscript', 'iframe', 'svg', 'canvas',
    'nav', 'footer', 'header', 'aside', 'form', 'button',
    'figure', 'figcaption'
]

NOISE_CLASSES = [
    'ad', 'ads', 'advertisement', 'ad-container', 'ad-wrapper',
    'social-share', 'share-buttons', 'social-links',
    'comments', 'comment-section', 'disqus',
    'related-articles', 'recommended', 'trending', 'popular',
    'newsletter', 'popup', 'modal', 'cookie-banner',
    'subscription', 'paywall', 'sidebar', 'widget',
    'stock', 'ticker', 'quote', 'market', 'price', 'chart'
]

NOISE_IDS = [
    'comments', 'sidebar', 'footer', 'header', 'nav',
    'ad', 'ads', 'advertisement'
]


def clean_text(text: str) -> str:
    """Normalize whitespace in extracted text."""
    # Replace multiple spaces/newlines with single space
    text = re.sub(r'\s+', ' ', text)
    # Remove leading/trailing whitespace
    text = text.strip()
    return text


def extract_from_json_ld(soup: BeautifulSoup) -> tuple[str, str]:
    """
    Extract article content from JSON-LD structured data.
    Many modern sites (CNN, BBC, etc.) embed full article text in JSON-LD for SEO.
    Returns: (text, title) or (None, None) if not found
    """
    try:
        # Find all JSON-LD script tags
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                # Get the text content - script.string may be a Script object
                script_text = script.get_text() if hasattr(script, 'get_text') else str(script.string)
                if not script_text:
                    continue
                data = json.loads(script_text)

                # Handle arrays of objects
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and item.get('articleBody'):
                            text = item.get('articleBody', '')
                            title = item.get('headline', '')
                            if text and len(text) > 200:
                                print(f"📦 JSON-LD extraction: {len(text)} chars")
                                return clean_text(text), title

                # Handle single object
                elif isinstance(data, dict):
                    # Direct articleBody
                    if data.get('articleBody'):
                        text = data.get('articleBody', '')
                        title = data.get('headline', '')
                        if text and len(text) > 200:
                            print(f"📦 JSON-LD extraction: {len(text)} chars")
                            return clean_text(text), title

                    # Check @graph array (common pattern)
                    if data.get('@graph'):
                        for item in data['@graph']:
                            if isinstance(item, dict) and item.get('articleBody'):
                                text = item.get('articleBody', '')
                                title = item.get('headline', '')
                                if text and len(text) > 200:
                                    print(f"📦 JSON-LD @graph extraction: {len(text)} chars")
                                    return clean_text(text), title

            except json.JSONDecodeError:
                continue

    except Exception as e:
        print(f"⚠️ JSON-LD extraction error: {e}")

    return None, None


def extract_article_content(soup: BeautifulSoup) -> str:
    """Extract main article content from parsed HTML."""
    # FIRST: Find the main article container BEFORE removing anything
    # This prevents noise removal from accidentally destroying the article
    article = (
        soup.find('article') or
        soup.find(attrs={'itemprop': 'articleBody'}) or
        soup.find(class_=re.compile(r'^(article|story|post)-?(body|content)?$', re.I)) or
        soup.find('main') or
        soup.body
    )

    if not article:
        return ""

    # Make a copy to work with so we don't destroy the original
    from copy import copy
    article_copy = copy(article)

    # NOW remove noise elements from within the article
    for tag in NOISE_TAGS:
        for element in article_copy.find_all(tag):
            element.decompose()

    # Remove elements with noisy classes (use word boundaries to avoid false positives)
    # e.g., "ad-container" should match, but "content-article" should NOT match "ad"
    for class_name in NOISE_CLASSES:
        # Match class names that ARE the noise word or have it with separators
        pattern = re.compile(rf'(^|[-_]){class_name}([-_]|$)', re.I)
        for element in article_copy.find_all(class_=pattern):
            element.decompose()

    # Remove elements with noisy IDs
    for id_name in NOISE_IDS:
        pattern = re.compile(rf'(^|[-_]){id_name}([-_]|$)', re.I)
        for element in article_copy.find_all(id=pattern):
            element.decompose()

    # Remove aria-hidden elements
    for element in article_copy.find_all(attrs={'aria-hidden': 'true'}):
        element.decompose()

    # Extract text from paragraphs for cleaner content
    paragraphs = article_copy.find_all('p')
    if paragraphs:
        text = ' '.join(p.get_text() for p in paragraphs)
    else:
        text = article_copy.get_text()

    return clean_text(text)


def extract_title(soup: BeautifulSoup) -> str:
    """Extract article title from HTML."""
    # Try Open Graph title first
    og_title = soup.find('meta', property='og:title')
    if og_title and og_title.get('content'):
        return og_title['content']

    # Try Twitter title
    tw_title = soup.find('meta', attrs={'name': 'twitter:title'})
    if tw_title and tw_title.get('content'):
        return tw_title['content']

    # Try h1 tag
    h1 = soup.find('h1')
    if h1:
        return clean_text(h1.get_text())

    # Fall back to title tag
    title = soup.find('title')
    if title:
        return clean_text(title.get_text())

    return "Untitled Article"


async def try_archive_fallback(url: str, client: httpx.AsyncClient) -> tuple[str, str]:
    """
    Try to fetch article from archive.today as a fallback for paywalled content.
    Returns: (html, source) or (None, None) if failed
    """
    archive_url = f"https://archive.today/newest/{url}"
    print(f"📦 Trying archive fallback: {archive_url[:50]}...")

    try:
        response = await client.get(archive_url, headers=REQUEST_HEADERS, timeout=12.0)
        if response.status_code == 200:
            print("✅ Archive hit!")
            return response.text, "archive.today"
    except Exception as e:
        print(f"⚠️ Archive fallback failed: {e}")

    return None, None


async def scrape_article(url: str) -> dict:
    """
    Scrape article content from a URL with smart fallback.
    If direct access fails (403/401), tries archive.today as backdoor.

    Returns: {
        "success": bool,
        "text": str,
        "title": str,
        "domain": str,
        "source": str (direct/archive),
        "error": str (if failed)
    }
    """
    try:
        # Parse domain from URL
        parsed = urlparse(url)
        domain = parsed.netloc

        print(f"🌐 Scraping: {url[:60]}...")

        html = None
        source = "direct"

        # Fetch the page with browser-like headers
        async with httpx.AsyncClient(timeout=FETCH_TIMEOUT, follow_redirects=True) as client:
            response = await client.get(url, headers=REQUEST_HEADERS)

            if response.status_code == 200:
                html = response.text
            elif response.status_code in [401, 403, 429]:
                # BLOCKED! Try the archive backdoor
                print(f"⚠️ Direct access blocked ({response.status_code}). Trying archives...")
                html, source = await try_archive_fallback(url, client)

                if not html:
                    # Archive also failed - give helpful error
                    is_paywall = any(pw in domain for pw in PAYWALL_DOMAINS)
                    if is_paywall:
                        return {
                            "success": False,
                            "error": f"This site requires a subscription and no archive is available. Use the Chrome extension while logged in."
                        }
                    return {
                        "success": False,
                        "error": f"Access denied by {domain}. Try using the Chrome extension instead."
                    }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: Could not fetch page"
                }

        if not html:
            return {
                "success": False,
                "error": "Could not fetch page content"
            }

        # Parse HTML
        soup = BeautifulSoup(html, 'lxml')

        # FIRST: Try JSON-LD extraction (works for JS-heavy sites like CNN)
        text, json_title = extract_from_json_ld(soup)

        # FALLBACK: Try HTML paragraph extraction
        if not text or len(text) < 200:
            text = extract_article_content(soup)
            json_title = None

        if not text or len(text) < 200:
            return {
                "success": False,
                "error": "Could not extract article content (too short or not an article)"
            }

        # Extract title (prefer JSON-LD title if available)
        title = json_title if json_title else extract_title(soup)

        print(f"✅ Scraped: {len(text)} chars from {domain} (via {source})")

        return {
            "success": True,
            "text": text[:15000],  # Max 15k chars (same as extension)
            "title": title,
            "domain": domain,
            "source": source,
            "canonical_url": url
        }

    except httpx.TimeoutException:
        return {
            "success": False,
            "error": "Timeout: Page took too long to load"
        }
    except Exception as e:
        print(f"❌ Scrape error: {e}")
        return {
            "success": False,
            "error": f"Scrape failed: {str(e)}"
        }
