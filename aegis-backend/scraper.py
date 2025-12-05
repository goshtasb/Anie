# scraper.py - Server-side article scraper for mobile/web users
import httpx
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import re

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


async def scrape_article(url: str) -> dict:
    """
    Scrape article content from a URL.
    Returns: {
        "success": bool,
        "text": str,
        "title": str,
        "domain": str,
        "error": str (if failed)
    }
    """
    try:
        # Parse domain from URL
        parsed = urlparse(url)
        domain = parsed.netloc

        print(f"🌐 Scraping: {url[:60]}...")

        # Fetch the page with browser-like headers
        async with httpx.AsyncClient(timeout=FETCH_TIMEOUT, follow_redirects=True) as client:
            response = await client.get(url, headers=REQUEST_HEADERS)

            if response.status_code != 200:
                # Check if it's a known paywall site
                is_paywall = any(pw in domain for pw in PAYWALL_DOMAINS)

                if response.status_code in [401, 403] and is_paywall:
                    return {
                        "success": False,
                        "error": f"This site requires a subscription. Use the Chrome extension while logged in to scan paywalled articles."
                    }
                elif response.status_code in [401, 403]:
                    return {
                        "success": False,
                        "error": f"Access denied by {domain}. Try using the Chrome extension instead."
                    }
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: Could not fetch page"
                }

            html = response.text

        # Parse HTML
        soup = BeautifulSoup(html, 'lxml')

        # Extract content
        text = extract_article_content(soup)

        if not text or len(text) < 200:
            return {
                "success": False,
                "error": "Could not extract article content (too short or not an article)"
            }

        # Extract title
        title = extract_title(soup)

        print(f"✅ Scraped: {len(text)} chars from {domain}")

        return {
            "success": True,
            "text": text[:15000],  # Max 15k chars (same as extension)
            "title": title,
            "domain": domain,
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
