"""
Marvel API client.

Handles authentication, request retry logic, and response caching so
views never hammer the upstream API on every page load.

Author: Sai Saketh Gooty Kase
"""

import hashlib
import logging
import time

import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

BASE_URL = "https://gateway.marvel.com/v1/public"
CACHE_TTL = 3600   # seconds — re-fetch from Marvel once per hour
MAX_RETRIES = 3
REQUEST_TIMEOUT = 10  # seconds


def _auth_params() -> dict:
    """Return the three query parameters Marvel requires for every request."""
    ts = str(time.time())
    raw = ts + settings.MARVEL_PRIVATE_KEY + settings.MARVEL_PUBLIC_KEY
    md5 = hashlib.md5(raw.encode("utf-8")).hexdigest()
    return {"apikey": settings.MARVEL_PUBLIC_KEY, "ts": ts, "hash": md5}


def _get(endpoint: str, params: dict | None = None) -> dict | None:
    """
    Make a GET request to the Marvel API with automatic retry on transient
    network errors.  Returns the parsed JSON body or None on failure.
    """
    url = f"{BASE_URL}{endpoint}"
    all_params = {**_auth_params(), **(params or {})}

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.get(url, params=all_params, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.Timeout:
            logger.warning(
                "Marvel API timeout (attempt %d/%d): %s",
                attempt, MAX_RETRIES, endpoint,
            )
        except requests.exceptions.HTTPError as exc:
            logger.error("Marvel API HTTP error for %s: %s", endpoint, exc)
            break
        except requests.exceptions.RequestException as exc:
            logger.error(
                "Marvel API request error (attempt %d/%d) for %s: %s",
                attempt, MAX_RETRIES, endpoint, exc,
            )

    return None


def get_marvel_characters(max_characters: int = 80) -> list:
    """
    Return up to *max_characters* Marvel characters, pulling from the
    in-process cache when possible so we avoid redundant API calls.
    """
    cache_key = f"marvel:characters:{max_characters}"
    cached = cache.get(cache_key)
    if cached is not None:
        logger.debug("Cache hit — character list (max=%d)", max_characters)
        return cached

    characters: list = []
    offset = 0

    while len(characters) < max_characters:
        data = _get("/characters", {"limit": 100, "offset": offset})
        if not data:
            break

        results = data.get("data", {}).get("results", [])
        if not results:
            break

        characters.extend(results)
        offset += 100

        total_available = data.get("data", {}).get("total", 0)
        if offset >= total_available:
            break

    result = characters[:max_characters]
    cache.set(cache_key, result, CACHE_TTL)
    logger.info("Fetched %d characters from Marvel API; cached for %ds", len(result), CACHE_TTL)
    return result


def get_character_by_id(character_id: int) -> dict | None:
    """
    Return a single character dict by Marvel character ID, using the cache
    to avoid repeated API round-trips for the same character.
    """
    cache_key = f"marvel:character:{character_id}"
    cached = cache.get(cache_key)
    if cached is not None:
        logger.debug("Cache hit — character %d", character_id)
        return cached

    data = _get(f"/characters/{character_id}")
    if not data:
        return None

    results = data.get("data", {}).get("results", [])
    character = results[0] if results else None

    if character:
        cache.set(cache_key, character, CACHE_TTL)

    return character
