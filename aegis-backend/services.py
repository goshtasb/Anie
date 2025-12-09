import os
import hashlib
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# Cache TTL: 24 hours (stories evolve, search indices update)
CACHE_TTL_HOURS = 24

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

if url and key and "your-project-id" not in url:
    supabase: Client = create_client(url, key)
    print("✅ Supabase connected. Caching enabled.")
else:
    supabase = None
    print("⚠️ Supabase not configured. Caching disabled.")


def get_nuclear_hash(url: str) -> str:
    """
    NUCLEAR URL SANITIZER - Aggressive normalization for cache consistency.

    Reduces 'https://www.CNN.com/story/?id=123&ref=twitter' to 'cnn.com/story'

    This ensures:
    - Website scans (with ?cid=ios_app params)
    - Extension scans (canonical URLs)
    - Mobile scans (shared links with tracking)
    ALL resolve to the SAME cache key.
    """
    try:
        parsed = urlparse(url.lower().strip())

        # 1. Strip 'www.' from netloc
        netloc = parsed.netloc.replace('www.', '')

        # 2. Strip trailing slash from path
        path = parsed.path.rstrip('/')

        # 3. Rebuild WITHOUT scheme (http/https), params, query, or fragment
        # We only keep: netloc + path
        clean_string = f"{netloc}{path}"

        print(f"🔬 Nuclear Sanitizer: '{url[:50]}...' -> '{clean_string}'")

        # 4. Hash it
        return hashlib.md5(clean_string.encode('utf-8')).hexdigest()
    except Exception as e:
        print(f"⚠️ Nuclear hash fallback: {e}")
        return hashlib.md5(url.encode('utf-8')).hexdigest()


def check_cache(url: str):
    """Check cache using NUCLEAR URL hash with 24-hour TTL."""
    if not supabase:
        print("⚠️ Cache Check: Supabase not configured, skipping cache")
        return None

    url_hash = get_nuclear_hash(url)
    print(f"🔍 Cache Check: hash={url_hash} for URL: {url[:80]}...")

    try:
        response = supabase.table("scan_cache").select("*").eq("url_hash", url_hash).execute()
        if len(response.data) > 0:
            cached_entry = response.data[0]
            cached_score = cached_entry.get("ani_score", "?")
            print(f"📦 Cache Entry Found: score={cached_score}")

            # Check TTL - cache expires after 24 hours
            created_at = cached_entry.get("created_at")
            if created_at:
                # Parse ISO timestamp from Supabase
                try:
                    cache_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    now = datetime.now(timezone.utc)
                    age_hours = (now - cache_time).total_seconds() / 3600
                    print(f"⏱️ Cache Age: {age_hours:.1f} hours (TTL: {CACHE_TTL_HOURS}h)")

                    if age_hours > CACHE_TTL_HOURS:
                        print(f"⏰ Cache EXPIRED ({age_hours:.1f}h > {CACHE_TTL_HOURS}h) - Deleting...")
                        # Delete stale entry
                        supabase.table("scan_cache").delete().eq("url_hash", url_hash).execute()
                        print("🗑️ Stale cache entry deleted, will call Grok fresh")
                        return None
                except Exception as e:
                    print(f"⚠️ Cache TTL parse error: {e}")
            else:
                print("⚠️ Cache entry has no created_at - treating as expired (legacy entry)")
                supabase.table("scan_cache").delete().eq("url_hash", url_hash).execute()
                return None

            print(f"✅ Cache HIT (valid, {age_hours:.1f}h old): returning cached score={cached_score}")
            return cached_entry["scan_data"]
        else:
            print("📭 Cache MISS: No entry found, will call Grok")
    except Exception as e:
        print(f"❌ Cache Check Error: {e}")

    return None


def save_to_cache(url: str, data: dict, ani_score: int):
    """Save result using NUCLEAR URL hash."""
    if not supabase:
        print("⚠️ Cache Save: Supabase not configured, skipping")
        return

    url_hash = get_nuclear_hash(url)
    print(f"💾 Attempting cache save: hash={url_hash} score={ani_score}")

    try:
        # Delete any existing entry first (clean slate)
        supabase.table("scan_cache").delete().eq("url_hash", url_hash).execute()

        # Insert fresh entry
        result = supabase.table("scan_cache").insert({
            "url_hash": url_hash,
            "url": url,
            "ani_score": ani_score,
            "scan_data": data
        }).execute()

        # Verify it was saved
        verify = supabase.table("scan_cache").select("ani_score").eq("url_hash", url_hash).execute()
        if verify.data and len(verify.data) > 0:
            print(f"✅ Cache VERIFIED: hash={url_hash[:16]}... score={verify.data[0].get('ani_score')}")
        else:
            print(f"⚠️ Cache NOT FOUND after save! hash={url_hash[:16]}...")

    except Exception as e:
        import traceback
        print(f"❌ Cache Save FAILED: {e}")
        traceback.print_exc()


def clear_cache(url: str) -> bool:
    """Manually clear a cached URL (for testing/debugging)."""
    if not supabase:
        return False

    url_hash = get_nuclear_hash(url)

    try:
        supabase.table("scan_cache").delete().eq("url_hash", url_hash).execute()
        print(f"🗑️ Cache Cleared: {url[:60]}...")
        return True
    except Exception as e:
        print(f"Cache Clear Error: {e}")
        return False


# --- DATA EXHAUST: Event Ledger ---
def log_scan_event(
    user_id: str,
    url: str,
    score: int,
    action: str,
    origin_location: str,
    request_headers: dict,
    tracking_params: dict = None,
    article_title: str = None,
    vectors: dict = None
):
    """
    Fire-and-forget logger for the 'Firehose' table.
    Captures EVERY interaction (cache hits + new scans) for analytics/B2B data.

    V4.1 Enterprise Data Hygiene: Stores url_hash for instant aggregation.
    V4.7 ROLLBACK: Removed V4.6 fields that may not exist in table.
    """
    if not supabase:
        return

    try:
        # V4.1: Calculate the "SKU" (Nuclear Hash) for B2B aggregation
        url_hash = get_nuclear_hash(url)

        # Extract analytics from headers (Cloudflare/Render headers)
        country = request_headers.get('cf-ipcountry', 'Unknown')
        user_agent = request_headers.get('user-agent', 'Unknown')

        # Determine device type from user agent
        ua_lower = user_agent.lower()
        if 'mobile' in ua_lower or 'android' in ua_lower or 'iphone' in ua_lower:
            device_type = 'mobile'
        elif 'extension' in ua_lower or 'chrome' in ua_lower:
            device_type = 'extension'
        else:
            device_type = 'web'

        # V4.7: Core fields only - no V4.6 experimental fields
        supabase.table("scan_events").insert({
            "user_id": user_id or "anonymous",
            "url": url,
            "url_hash": url_hash,
            "ani_score": score,
            "action_type": action,
            "origin_location": origin_location,
            "geo_country": country,
            "device_type": device_type,
            "meta": {"user_agent": user_agent[:500]}
        }).execute()
        print(f"✅ Event logged: {action} score={score}")
    except Exception as e:
        import traceback
        print(f"❌ Event Log FAILED: {e}")
        traceback.print_exc()


