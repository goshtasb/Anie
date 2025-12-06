# scraper.py - Server-side article scraper for mobile/web users
import httpx
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import re
import json

# =============================================================================
# JINA.AI INTEGRATION - The Smart Bridge
# =============================================================================
# Jina (r.jina.ai) is a specialized API that:
# 1. Uses a Headless Browser (executes JavaScript)
# 2. Cleans the content (strips ads, nav, popups)
# 3. Handles bot detection (proper browser fingerprinting)
# 4. Returns clean markdown text
# =============================================================================

JINA_BASE_URL = "https://r.jina.ai/"
JINA_TIMEOUT = 20.0  # Jina can be slow on JS-heavy pages

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

# Domains that block cloud server IPs (return 200 but garbage content)
# These sites require archive.today as PRIMARY source
CLOUD_BLOCKED_DOMAINS = [
    'cnn.com', 'edition.cnn.com',
    'bbc.com', 'bbc.co.uk',
    'reuters.com',
    'apnews.com',
    'nbcnews.com',
    'cbsnews.com',
    'abcnews.go.com',
    'foxnews.com',
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


def is_cloud_blocked_domain(domain: str) -> bool:
    """Check if domain is known to block cloud server IPs."""
    domain_lower = domain.lower()
    for blocked in CLOUD_BLOCKED_DOMAINS:
        if blocked in domain_lower:
            return True
    return False


def clean_text(text: str) -> str:
    """Normalize whitespace in extracted text."""
    # Replace multiple spaces/newlines with single space
    text = re.sub(r'\s+', ' ', text)
    # Remove leading/trailing whitespace
    text = text.strip()
    return text


def is_garbled_text(text: str) -> bool:
    """
    Detect if text is garbled/binary garbage (e.g., from blocked CDNs).
    Returns True if text appears to be non-readable garbage.
    """
    if not text or len(text) < 100:
        return True

    # Sample the first 500 chars
    sample = text[:500]

    # Count printable ASCII characters (letters, numbers, basic punctuation)
    printable_count = sum(1 for c in sample if c.isalnum() or c in ' .,!?\'"-:;()')

    # If less than 60% of characters are printable, it's likely garbage
    ratio = printable_count / len(sample) if sample else 0

    if ratio < 0.6:
        print(f"⚠️ Garbled text detected: {ratio:.0%} printable chars")
        return True

    return False


async def scrape_via_jina(url: str) -> dict:
    """
    Scrape article using Jina.ai's reader API.
    Jina handles JavaScript rendering and content cleaning automatically.

    Returns: {
        "success": bool,
        "text": str,
        "title": str,
        "source": "jina",
        "error": str (if failed)
    }
    """
    jina_url = f"{JINA_BASE_URL}{url}"
    print(f"🤖 Scraping via Jina Bridge: {url[:50]}...")

    headers = {
        "User-Agent": "Mozilla/5.0 (Compatible; AnieBot/1.0)",
        "X-Retain-Images": "none",  # We don't need images
        "Accept": "text/plain",
    }

    try:
        async with httpx.AsyncClient(timeout=JINA_TIMEOUT) as client:
            response = await client.get(jina_url, headers=headers)

            if response.status_code == 200:
                text = response.text

                # Check if Jina returned an error as JSON
                if text.startswith('{"'):
                    try:
                        data = json.loads(text)
                        if data.get("code") or data.get("error"):
                            error_msg = data.get("message", data.get("error", "Unknown Jina error"))
                            print(f"⚠️ Jina API error: {error_msg[:100]}")
                            return {"success": False, "error": f"Jina: {error_msg[:100]}"}
                    except json.JSONDecodeError:
                        pass  # Not JSON, continue processing

                # Check minimum length
                if len(text) < 500:
                    print(f"⚠️ Jina returned too short: {len(text)} chars")
                    return {"success": False, "error": "Article content too short (paywall?)"}

                # Extract title from Jina's markdown format
                # Jina returns: Title: ...\n\nURL Source: ...\n\nMarkdown Content: ...
                title = "Untitled"
                lines = text.split('\n')
                for line in lines[:5]:
                    if line.startswith('Title:'):
                        title = line[6:].strip()
                        break

                # Clean up the markdown - remove metadata headers
                content_start = text.find('\n\n')
                if content_start > 0:
                    # Skip past multiple header sections
                    clean_text = text
                    for _ in range(3):  # Skip up to 3 header sections
                        next_section = clean_text.find('\n\n', 1)
                        if next_section > 0 and next_section < 200:
                            clean_text = clean_text[next_section+2:]
                        else:
                            break
                else:
                    clean_text = text

                print(f"✅ Jina success: {len(clean_text)} chars, title: {title[:50]}...")
                return {
                    "success": True,
                    "text": clean_text[:15000],
                    "title": title,
                    "source": "jina"
                }

            else:
                print(f"⚠️ Jina HTTP error: {response.status_code}")
                return {"success": False, "error": f"Jina HTTP {response.status_code}"}

    except httpx.TimeoutException:
        print("⚠️ Jina timeout")
        return {"success": False, "error": "Jina timeout"}
    except Exception as e:
        print(f"⚠️ Jina error: {e}")
        return {"success": False, "error": f"Jina error: {str(e)}"}


def extract_from_json_ld(soup: BeautifulSoup) -> tuple[str, str]:
    """
    Extract article content from JSON-LD structured data.
    Many modern sites (CNN, BBC, etc.) embed full article text in JSON-LD for SEO.
    Returns: (text, title) or (None, None) if not found
    """
    try:
        # Find all JSON-LD script tags
        json_ld_scripts = soup.find_all('script', type='application/ld+json')
        print(f"🔍 Found {len(json_ld_scripts)} JSON-LD scripts")

        for i, script in enumerate(json_ld_scripts):
            try:
                # Get the text content - script.string may be a Script object
                script_text = script.get_text() if hasattr(script, 'get_text') else str(script.string)
                if not script_text:
                    print(f"  Script {i}: empty text")
                    continue
                print(f"  Script {i}: {len(script_text)} chars, starts with: {script_text[:50]}...")
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
    Scrape article content from a URL with smart fallback chain:
    1. JINA.AI (handles JS rendering + content cleaning)
    2. Archive.today (for blocked domains)
    3. Direct fetch with JSON-LD extraction

    Returns: {
        "success": bool,
        "text": str,
        "title": str,
        "domain": str,
        "source": str (jina/archive/direct),
        "error": str (if failed)
    }
    """
    try:
        # Parse domain from URL
        parsed = urlparse(url)
        domain = parsed.netloc

        print(f"🌐 Scraping: {url[:60]}...")

        # =================================================================
        # STEP 1: Try Jina.ai FIRST (best quality, handles JS sites)
        # =================================================================
        jina_result = await scrape_via_jina(url)
        if jina_result["success"]:
            return {
                "success": True,
                "text": jina_result["text"],
                "title": jina_result["title"],
                "domain": domain,
                "source": "jina",
                "canonical_url": url
            }

        # Jina failed - log and continue to fallbacks
        print(f"⚠️ Jina failed: {jina_result.get('error', 'unknown')}, trying fallbacks...")

        # =================================================================
        # STEP 2: Fallback to Archive.today / Direct scraping
        # =================================================================
        html = None
        source = "direct"

        # Fetch the page with browser-like headers
        async with httpx.AsyncClient(timeout=FETCH_TIMEOUT, follow_redirects=True) as client:

            # STRATEGY: For known cloud-blocked domains, try archive FIRST
            # These sites return 200 but garbage HTML to cloud IPs
            if is_cloud_blocked_domain(domain):
                print(f"🛡️ Known cloud-blocked domain ({domain}), trying archive FIRST...")
                html, source = await try_archive_fallback(url, client)

                if html:
                    print(f"✅ Archive hit for cloud-blocked domain!")
                else:
                    # Archive miss - try direct anyway (might work for some articles)
                    print(f"⚠️ Archive miss, falling back to direct fetch...")
                    response = await client.get(url, headers=REQUEST_HEADERS)
                    if response.status_code == 200:
                        html = response.text
                        source = "direct"
                        print(f"📄 Direct fallback: {len(html)} chars of HTML")
            else:
                # Normal domains - try direct first
                response = await client.get(url, headers=REQUEST_HEADERS)

                if response.status_code == 200:
                    html = response.text
                    print(f"📄 Received {len(html)} chars of HTML")
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

        # Check for garbled/binary garbage (common with blocked CDNs)
        if is_garbled_text(text):
            is_known_blocked = is_cloud_blocked_domain(domain)
            if is_known_blocked:
                return {
                    "success": False,
                    "error": f"{domain} blocks automated requests. Use the Chrome extension to scan this article directly from your browser."
                }
            return {
                "success": False,
                "error": "Could not extract readable content. Site may be blocking automated requests."
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
