import json
from pathlib import Path


def _cache_file_path() -> Path:
    # backend/app/utils/cache_utils.py -> backend/
    backend_root = Path(__file__).resolve().parents[2]
    return backend_root / "median_price_cache.json"


def load_cache() -> dict:
    cache_file = _cache_file_path()
    if not cache_file.exists():
        return {}
    try:
        return json.loads(cache_file.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_cache(cache: dict) -> None:
    cache_file = _cache_file_path()
    cache_file.write_text(json.dumps(cache, indent=2), encoding="utf-8")


def get_cached(key: str):
    cache = load_cache()
    return cache.get(key)


def set_cache(key: str, value) -> None:
    cache = load_cache()
    cache[key] = value
    save_cache(cache)
