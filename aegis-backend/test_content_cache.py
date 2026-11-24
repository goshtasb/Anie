"""Tests for the V5.9r5 content cache: the same article text always returns the same stored result."""
import sys, types

# services.py connects to Supabase at import; stub the client libraries for tests.
sys.modules.setdefault("supabase", types.SimpleNamespace(create_client=None, Client=object))
sys.modules.setdefault("dotenv", types.SimpleNamespace(load_dotenv=lambda: None))
import services


class FakeTable:
    def __init__(self, rows): self.rows, self._op, self._filter, self._payload = rows, None, None, None
    def select(self, *_): self._op = "select"; return self
    def delete(self): self._op = "delete"; return self
    def insert(self, payload): self._op, self._payload = "insert", payload; return self
    def eq(self, col, val): self._filter = (col, val); return self
    def execute(self):
        col, val = self._filter or (None, None)
        if self._op == "insert":
            self.rows.append(dict(self._payload, created_at="2020-01-01T00:00:00+00:00"))
            return types.SimpleNamespace(data=[self._payload])
        match = [r for r in self.rows if col is None or r.get(col) == val]
        if self._op == "delete":
            for r in match: self.rows.remove(r)
        return types.SimpleNamespace(data=match)


class FakeDB:
    def __init__(self): self.rows = []
    def table(self, _): return FakeTable(self.rows)


def test_hash_ignores_case_and_whitespace_only():
    a = services.get_content_hash("The  Fed held rates.\nMarkets rose.", "Fed", "5.9r5")
    b = services.get_content_hash("the fed held rates. markets rose.", "FED", "5.9r5")
    c = services.get_content_hash("The Fed cut rates. Markets rose.", "Fed", "5.9r5")
    assert a == b and a != c and a.startswith("text:")

def test_hash_changes_with_scoring_version():
    assert services.get_content_hash("x" * 200, "t", "5.9r5") != services.get_content_hash("x" * 200, "t", "6.0")

def test_same_text_returns_stored_result_with_no_expiry(monkeypatch):
    monkeypatch.setattr(services, "supabase", FakeDB())
    data = {"ani_score": 79, "verdict": "Organic Reporting"}
    services.save_content_cache("Article body " * 20, "Title", "5.9r5", data, 79)
    # stored row is years old: unlike the URL cache, content results never expire
    assert services.check_content_cache("article   body " * 20, "title", "5.9r5") == data
    assert services.check_content_cache("Different body " * 20, "Title", "5.9r5") is None

def test_error_results_are_never_cached(monkeypatch):
    db = FakeDB()
    monkeypatch.setattr(services, "supabase", db)
    services.save_content_cache("Body " * 50, "T", "5.9r5", {"ani_score": 50, "verdict": "Analysis Error"}, 50)
    assert db.rows == []

def test_no_supabase_means_no_cache(monkeypatch):
    monkeypatch.setattr(services, "supabase", None)
    assert services.check_content_cache("Body " * 50, "T", "5.9r5") is None


# --- V5.13: only real scores are stored, and the URL cache respects the engine version ---
def test_incomplete_results_are_never_cached(monkeypatch):
    db = FakeDB()
    monkeypatch.setattr(services, "supabase", db)
    services.save_content_cache("Body " * 50, "T", "5.13", {"ani_score": 50, "verdict": "Analysis Incomplete"}, 50)
    services.save_to_cache("https://example.com/a", {"ani_score": 50, "verdict": "Analysis Incomplete"}, 50)
    assert db.rows == []


def test_url_cache_from_another_engine_version_is_a_miss(monkeypatch):
    from datetime import datetime, timezone
    db = FakeDB()
    monkeypatch.setattr(services, "supabase", db)
    now = datetime.now(timezone.utc).isoformat()
    db.rows.append({"url_hash": services.get_nuclear_hash("https://example.com/a"), "created_at": now,
                    "ani_score": 70, "scan_data": {"ani_score": 70, "verdict": "Moderate Spin", "engine_version": "5.12"}})
    assert services.check_cache("https://example.com/a", "5.13") is None
    assert services.check_cache("https://example.com/a", "5.12")["ani_score"] == 70
