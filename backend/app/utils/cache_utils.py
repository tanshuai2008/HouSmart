import json
import time
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[2]
CACHE_FILE = BACKEND_DIR / "median_price_cache.json"

# Default TTL: 24 hours
CACHE_TTL_SECONDS = 24 * 60 * 60


def load_cache() -> dict:
    if not CACHE_FILE.exists():
        return {}

    try:
        with CACHE_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def save_cache(cache: dict) -> None:
    try:
        with CACHE_FILE.open("w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2)
    except OSError:
        # If cache can't be written, fail silently (cache is an optimization).
        return


def get_cached_value(key: str, ttl_seconds: int = CACHE_TTL_SECONDS):
    cache = load_cache()
    if key not in cache:
        return None

    entry = cache[key]

    # Back-compat: older cache format stored raw values.
    if not isinstance(entry, dict) or "data" not in entry:
        return entry

    timestamp = entry.get("timestamp")
    if isinstance(timestamp, (int, float)) and ttl_seconds is not None:
        if (time.time() - timestamp) > ttl_seconds:
            return None

    return entry.get("data")


def set_cached_value(key: str, data) -> None:
    cache = load_cache()
    cache[key] = {"timestamp": time.time(), "data": data}
    save_cache(cache)


# Backwards-compatible aliases used by older code.
def get_cached(key: str):
    return get_cached_value(key)


def set_cache(key: str, value) -> None:
    set_cached_value(key, value)