import os
import hashlib
from datetime import datetime, timedelta, timezone
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


def get_stable_hash(url: str) -> str:
    """
    Hash the CANONICAL URL for stable caching.

    This survives:
    - Page refreshes (ads change)
    - Tracking params (?ref=twitter)
    - Different entry points to same article

    The frontend (content.js) extracts <link rel="canonical">
    which is the article's True Name that never changes.
    """
    # Strip trailing slashes for consistency
    clean_url = url.rstrip('/')
    return hashlib.md5(clean_url.encode('utf-8')).hexdigest()


def check_cache(url: str):
    """Check cache using stable URL hash with 24-hour TTL."""
    if not supabase:
        print("⚠️ Cache Check: Supabase not configured, skipping cache")
        return None

    url_hash = get_stable_hash(url)
    print(f"🔍 Cache Check: hash={url_hash[:12]}... for URL: {url[:60]}...")

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
    """Save result using stable URL hash."""
    if not supabase:
        return

    url_hash = get_stable_hash(url)

    try:
        # Upsert: replace existing entry (handles re-scans after TTL expiry)
        supabase.table("scan_cache").upsert({
            "url_hash": url_hash,
            "url": url,
            "ani_score": ani_score,
            "scan_data": data
        }, on_conflict="url_hash").execute()
        print(f"💾 Saved to Cache (Canonical): {url[:60]}...")
    except Exception as e:
        # Fallback to insert if upsert fails
        try:
            supabase.table("scan_cache").insert({
                "url_hash": url_hash,
                "url": url,
                "ani_score": ani_score,
                "scan_data": data
            }).execute()
            print(f"💾 Saved to Cache (Insert): {url[:60]}...")
        except Exception as e2:
            print(f"Cache Save Error: {e2}")


def clear_cache(url: str) -> bool:
    """Manually clear a cached URL (for testing/debugging)."""
    if not supabase:
        return False

    url_hash = get_stable_hash(url)

    try:
        supabase.table("scan_cache").delete().eq("url_hash", url_hash).execute()
        print(f"🗑️ Cache Cleared: {url[:60]}...")
        return True
    except Exception as e:
        print(f"Cache Clear Error: {e}")
        return False
