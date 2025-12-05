# scraper.py - Server-side article scraper for mobile/web users
import httpx
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import re

# User agent to avoid blocks
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Timeout for fetching pages
FETCH_TIMEOUT = 15.0

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
    # Remove noise elements
    for tag in NOISE_TAGS:
        for element in soup.find_all(tag):
            element.decompose()

    # Remove elements with noisy classes
    for class_name in NOISE_CLASSES:
        for element in soup.find_all(class_=re.compile(class_name, re.I)):
            element.decompose()

    # Remove elements with noisy IDs
    for id_name in NOISE_IDS:
        for element in soup.find_all(id=re.compile(id_name, re.I)):
            element.decompose()

    # Remove aria-hidden elements
    for element in soup.find_all(attrs={'aria-hidden': 'true'}):
        element.decompose()

    # Try to find the main article content
    article = (
        soup.find('article') or
        soup.find(attrs={'itemprop': 'articleBody'}) or
        soup.find(class_=re.compile(r'article|story|post|content', re.I)) or
        soup.find('main') or
        soup.body
    )

    if not article:
        return ""

    # Extract text from paragraphs for cleaner content
    paragraphs = article.find_all('p')
    if paragraphs:
        text = ' '.join(p.get_text() for p in paragraphs)
    else:
        text = article.get_text()

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

        # Fetch the page
        async with httpx.AsyncClient(timeout=FETCH_TIMEOUT, follow_redirects=True) as client:
            response = await client.get(url, headers={
                "User-Agent": USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
            })

            if response.status_code != 200:
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
