import json
import hashlib
import os
from datetime import datetime, timedelta
from threading import Lock
from typing import Optional, Dict, Any

_CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "analysis_cache.json")
_CACHE_TTL_HOURS = int(os.getenv("CACHE_TTL_HOURS", "24"))
_lock = Lock()
_cache: Dict[str, Any] = {}


def _init():
    global _cache
    try:
        with open(_CACHE_FILE, "r") as f:
            _cache = json.load(f)
        print(f"[Cache] Loaded {len(_cache)} entries from disk.")
    except (FileNotFoundError, json.JSONDecodeError):
        _cache = {}

_init()


def _make_key(product_name: str, preferences: Dict) -> str:
    raw = product_name.strip().lower() + json.dumps(preferences, sort_keys=True)
    return hashlib.md5(raw.encode()).hexdigest()


def _flush():
    with open(_CACHE_FILE, "w") as f:
        json.dump(_cache, f)


def get(product_name: str, preferences: Dict) -> Optional[Dict]:
    key = _make_key(product_name, preferences)
    entry = _cache.get(key)
    if not entry:
        return None
    age = datetime.now() - datetime.fromisoformat(entry["timestamp"])
    if age > timedelta(hours=_CACHE_TTL_HOURS):
        return None
    return entry["data"]


def set(product_name: str, preferences: Dict, data: Dict) -> None:
    key = _make_key(product_name, preferences)
    with _lock:
        _cache[key] = {"timestamp": datetime.now().isoformat(), "data": data}
        _flush()
