import os
import hashlib
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

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
    """Check cache using stable URL hash."""
    if not supabase:
        return None

    url_hash = get_stable_hash(url)

    try:
        response = supabase.table("scan_cache").select("*").eq("url_hash", url_hash).execute()
        if len(response.data) > 0:
            print(f"✅ Cache Hit (Canonical URL): {url[:60]}...")
            return response.data[0]["scan_data"]
    except Exception as e:
        print(f"Cache Check Error: {e}")

    return None


def save_to_cache(url: str, data: dict, ani_score: int):
    """Save result using stable URL hash."""
    if not supabase:
        return

    url_hash = get_stable_hash(url)

    try:
        supabase.table("scan_cache").insert({
            "url_hash": url_hash,
            "url": url,
            "ani_score": ani_score,
            "scan_data": data
        }).execute()
        print(f"💾 Saved to Cache (Canonical): {url[:60]}...")
    except Exception as e:
        # Likely duplicate - that's fine
        print(f"Cache Save (may be duplicate): {e}")
