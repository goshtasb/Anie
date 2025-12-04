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


def get_content_hash(text: str) -> str:
    """
    Hash the article TEXT, not the URL.
    This guarantees: Same content = Same hash = Cache hit.

    We strip whitespace and take first 10000 chars to ensure
    minor variations don't break the cache.
    """
    # Normalize: strip whitespace, take consistent chunk
    clean_text = text.strip()[:10000]
    return hashlib.md5(clean_text.encode('utf-8')).hexdigest()


def check_cache(text: str):
    """Check cache based on TEXT hash, not URL."""
    if not supabase:
        return None

    content_hash = get_content_hash(text)

    try:
        # Reuse 'url_hash' column to store content hash (avoids DB migration)
        response = supabase.table("scan_cache").select("*").eq("url_hash", content_hash).execute()
        if len(response.data) > 0:
            print(f"✅ Cache Hit (Hash: {content_hash[:8]}...)")
            return response.data[0]["scan_data"]
    except Exception as e:
        print(f"Cache Check Error: {e}")

    return None


def save_to_cache(url: str, text: str, data: dict, ani_score: int):
    """Save result using TEXT hash for consistent retrieval."""
    if not supabase:
        return

    content_hash = get_content_hash(text)

    try:
        supabase.table("scan_cache").insert({
            "url_hash": content_hash,  # Content hash, not URL hash
            "url": url,                 # Keep URL for reference/debugging
            "ani_score": ani_score,
            "scan_data": data
        }).execute()
        print(f"💾 Saved to Cache (Hash: {content_hash[:8]}...)")
    except Exception as e:
        # Likely duplicate key - that's fine, means it's already cached
        print(f"Cache Save (may be duplicate): {e}")
