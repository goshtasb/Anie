# scraper.py - Server-side article scraper for mobile/web users
import httpx
import trafilatura
from urllib.parse import urlparse

# User agent to avoid blocks
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Timeout for fetching pages
FETCH_TIMEOUT = 15.0


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

        # Extract article text using trafilatura
        # This is the same technique used by major news aggregators
        extracted = trafilatura.extract(
            html,
            include_comments=False,
            include_tables=False,
            no_fallback=False,
            favor_recall=True,  # Get more content rather than less
            output_format="txt"
        )

        if not extracted or len(extracted) < 200:
            return {
                "success": False,
                "error": "Could not extract article content (too short or not an article)"
            }

        # Extract title using trafilatura's metadata extraction
        metadata = trafilatura.extract_metadata(html)
        title = metadata.title if metadata and metadata.title else "Untitled Article"

        print(f"✅ Scraped: {len(extracted)} chars from {domain}")

        return {
            "success": True,
            "text": extracted[:15000],  # Max 15k chars (same as extension)
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
