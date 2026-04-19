"""
tmdb.py
-------
Wrapper around The Movie Database (TMDB) API.
Used to auto-fill movie details when staff add a new movie.

Docs: https://developer.themoviedb.org/reference/intro/getting-started
"""

import os
import httpx
from fastapi import HTTPException

TMDB_API_KEY = os.getenv("TMDB_API_KEY", "")
TMDB_BASE    = "https://api.themoviedb.org/3"
TMDB_IMG     = "https://image.tmdb.org/t/p/w500"

# MPAA ratings we care about (TMDB returns weird stuff for TV etc., we filter)
VALID_RATINGS = {"G", "PG", "PG-13", "R", "NC-17"}


def _require_key():
    if not TMDB_API_KEY:
        raise HTTPException(500,
            "TMDB_API_KEY is not set. Add it to your .env file.")


async def _get(path: str, params: dict) -> dict:
    """Helper to call TMDB and raise on errors."""
    params = {**params, "api_key": TMDB_API_KEY}
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(f"{TMDB_BASE}{path}", params=params)
    if r.status_code != 200:
        raise HTTPException(502, f"TMDB error: {r.text}")
    return r.json()


async def _us_rating(movie_id: int) -> str | None:
    """Look up the US MPAA rating (G/PG/PG-13/R) for a movie."""
    try:
        data = await _get(f"/movie/{movie_id}/release_dates", {})
    except HTTPException:
        return None
    for country in data.get("results", []):
        if country.get("iso_3166_1") == "US":
            for rd in country.get("release_dates", []):
                cert = (rd.get("certification") or "").strip()
                if cert in VALID_RATINGS:
                    return cert
    return None


def _poster_url(poster_path: str | None) -> str | None:
    return f"{TMDB_IMG}{poster_path}" if poster_path else None


async def search_movies(query: str, limit: int = 6) -> list[dict]:
    """Search TMDB. Returns a list of simplified movie results."""
    _require_key()
    data = await _get("/search/movie", {"query": query, "include_adult": "false"})
    results = []
    for m in data.get("results", [])[:limit]:
        results.append({
            "tmdb_id":     m["id"],
            "title":       m.get("title") or "Untitled",
            "year":        (m.get("release_date") or "")[:4],
            "poster":      _poster_url(m.get("poster_path")),
            "description": m.get("overview") or "",
        })
    return results


async def get_movie_details(tmdb_id: int) -> dict:
    """Fetch full details for one movie (adds runtime + rating)."""
    _require_key()
    data = await _get(f"/movie/{tmdb_id}", {})
    rating = await _us_rating(tmdb_id)
    return {
        "tmdb_id":     data["id"],
        "title":       data.get("title") or "Untitled",
        "year":        (data.get("release_date") or "")[:4],
        "runtime":     data.get("runtime") or 0,
        "rating":      rating or "PG-13",   # fallback if no US rating
        "poster":      _poster_url(data.get("poster_path")),
        "description": data.get("overview") or "",
    }


async def lookup_by_title(title: str) -> dict | None:
    """Auto-lookup: search + fetch full details for the top result."""
    matches = await search_movies(title, limit=1)
    if not matches:
        return None
    return await get_movie_details(matches[0]["tmdb_id"])
