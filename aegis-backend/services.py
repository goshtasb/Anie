# services.py
import os
import hashlib
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# Supabase client - initialized lazily to allow running without DB during dev
_supabase_client = None

def get_supabase():
    """
    Lazy initialization of Supabase client.
    Returns None if credentials not configured (allows local dev without DB).
    """
    global _supabase_client

    if _supabase_client is not None:
        return _supabase_client

    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")

    if not url or not key or "your-project-id" in url:
        print("⚠️  Supabase not configured - running in local-only mode")
        return None

    try:
        from supabase import create_client
        _supabase_client = create_client(url, key)
        print("✅ Supabase client initialized")
        return _supabase_client
    except Exception as e:
        print(f"⚠️  Supabase initialization failed: {e}")
        return None


def get_url_hash(url: str) -> str:
    """Create a consistent hash for the URL to use as a cache key."""
    # Normalize URL: strip trailing slashes, lowercase
    normalized = url.lower().rstrip('/')
    return hashlib.md5(normalized.encode()).hexdigest()


def check_cache(url: str) -> Optional[dict]:
    """
    Check if we have already analyzed this URL.
    Returns the JSON payload if found, None if not.
    """
    supabase = get_supabase()
    if not supabase:
        return None

    try:
        url_hash = get_url_hash(url)
        response = supabase.table("scan_cache").select("*").eq("url_hash", url_hash).execute()

        if response.data and len(response.data) > 0:
            print(f"✅ Cache Hit: {url[:50]}...")
            return response.data[0]["scan_data"]
    except Exception as e:
        print(f"⚠️  Cache lookup failed: {e}")

    return None


def save_to_cache(url: str, data: dict, ani_score: int) -> bool:
    """
    Save the analysis result to Supabase cache.
    Returns True on success, False on failure.
    """
    supabase = get_supabase()
    if not supabase:
        return False

    try:
        url_hash = get_url_hash(url)
        supabase.table("scan_cache").insert({
            "url_hash": url_hash,
            "url": url,
            "ani_score": ani_score,
            "scan_data": data
        }).execute()
        print(f"✅ Cached result for: {url[:50]}...")
        return True
    except Exception as e:
        # Likely duplicate key - that's fine, means it was cached by another request
        print(f"⚠️  Cache save failed (may be duplicate): {e}")
        return False


# --- GUEST MODE CREDIT SYSTEM ---
# Uses device_id instead of authenticated user_id

def get_or_create_guest(device_id: str) -> dict:
    """
    Get or create a guest profile based on device_id.
    Returns the guest profile with credits.
    """
    supabase = get_supabase()
    if not supabase:
        # Local dev mode: return mock unlimited credits
        return {"device_id": device_id, "credits": 999}

    try:
        # Check if guest exists
        response = supabase.table("guests").select("*").eq("device_id", device_id).execute()

        if response.data and len(response.data) > 0:
            return response.data[0]

        # Create new guest with 5 free credits
        new_guest = {
            "device_id": device_id,
            "credits": 5
        }
        supabase.table("guests").insert(new_guest).execute()
        print(f"✅ New guest created: {device_id[:8]}...")
        return new_guest

    except Exception as e:
        print(f"⚠️  Guest lookup/create failed: {e}")
        # Fail open for MVP - don't block scans due to DB issues
        return {"device_id": device_id, "credits": 5}


def check_credits(device_id: str) -> int:
    """
    Check how many credits a guest has.
    Returns credit count (0 if none).
    """
    guest = get_or_create_guest(device_id)
    return guest.get("credits", 0)


def deduct_credit(device_id: str) -> bool:
    """
    Decrement credit count by 1.
    Returns True if successful, False if no credits or error.
    """
    supabase = get_supabase()
    if not supabase:
        # Local dev mode: always succeed
        return True

    try:
        # Get current credits
        response = supabase.table("guests").select("credits").eq("device_id", device_id).execute()

        if not response.data or response.data[0]["credits"] <= 0:
            return False

        current_credits = response.data[0]["credits"]

        # Deduct one credit
        supabase.table("guests").update({
            "credits": current_credits - 1
        }).eq("device_id", device_id).execute()

        print(f"✅ Credit deducted for {device_id[:8]}... ({current_credits - 1} remaining)")
        return True

    except Exception as e:
        print(f"⚠️  Credit deduction failed: {e}")
        # Fail open for MVP
        return True


def add_credits(device_id: str, amount: int) -> bool:
    """
    Add credits to a guest account (for future payment integration).
    """
    supabase = get_supabase()
    if not supabase:
        return True

    try:
        response = supabase.table("guests").select("credits").eq("device_id", device_id).execute()

        if not response.data:
            return False

        current_credits = response.data[0]["credits"]

        supabase.table("guests").update({
            "credits": current_credits + amount
        }).eq("device_id", device_id).execute()

        print(f"✅ Added {amount} credits to {device_id[:8]}...")
        return True

    except Exception as e:
        print(f"⚠️  Credit addition failed: {e}")
        return False
