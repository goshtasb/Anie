import os
import hashlib
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

# Graceful fallback if Supabase keys aren't set in Render yet
if url and key and "your-project-id" not in url:
    supabase: Client = create_client(url, key)
else:
    supabase = None
    print("⚠️ Supabase not configured. Caching disabled.")

def get_url_hash(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()

def check_cache(url: str):
    if not supabase: return None
    url_hash = get_url_hash(url)
    try:
        response = supabase.table("scan_cache").select("*").eq("url_hash", url_hash).execute()
        if len(response.data) > 0:
            return response.data[0]["scan_data"]
    except Exception:
        pass
    return None

def save_to_cache(url: str, data: dict, ani_score: int):
    if not supabase: return
    url_hash = get_url_hash(url)
    try:
        supabase.table("scan_cache").insert({
            "url_hash": url_hash,
            "url": url,
            "ani_score": ani_score,
            "scan_data": data
        }).execute()
    except Exception:
        pass
