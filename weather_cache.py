import os
import json
import time
import hashlib


CACHE_DIR = os.path.join(os.path.dirname(__file__), ".weather_cache")
CACHE_TTL_SECONDS = 600


def _ensure_cache_dir():
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)


def _get_cache_file(key: str):
    _ensure_cache_dir()
    name = hashlib.md5(key.encode("utf-8")).hexdigest() + ".json"
    return os.path.join(CACHE_DIR, name)


def get_cache_key(*args):
    return "|".join(str(a) for a in args)


def get_from_cache(key: str, ttl_seconds: int = None):
    ttl_seconds = ttl_seconds or CACHE_TTL_SECONDS
    path = _get_cache_file(key)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            entry = json.load(f)
        if time.time() - entry.get("time", 0) > ttl_seconds:
            os.remove(path)
            return None
        return entry.get("data")
    except Exception:
        return None


def save_to_cache(key: str, data):
    path = _get_cache_file(key)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"time": time.time(), "data": data}, f, ensure_ascii=False)
    except Exception:
        pass
