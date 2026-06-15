import re
import urllib.parse
from difflib import SequenceMatcher

import requests
import yt_dlp
from requests import Response
from requests.exceptions import RequestException


HEADERS = {
    "User-Agent": "FreeMusicApp/1.0 (contact@example.com)"
}


def _safe_request(
    url: str,
    *,
    params: dict | None = None,
    headers: dict | None = None,
    timeout: int = 10,
) -> Response | None:
    try:
        return requests.get(url, params=params, headers=headers or HEADERS, timeout=timeout)
    except RequestException as exc:
        print(f"Remote request failed ({url}): {exc}")
        return None


def _normalize(text: str | None) -> str:
    text = text or ""
    return re.sub(r"[^a-z0-9]", "", text.lower())


def _similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def _extract_artist(recording: dict) -> str:
    credits = recording.get("artist-credit") or []
    if credits and isinstance(credits[0], dict):
        artist_obj = credits[0].get("artist") or {}
        if artist_obj.get("name"):
            return artist_obj["name"]
    return "Unknown"


def search_song(query: str):
    """Search MusicBrainz for song metadata (title + artist)."""
    url = "https://musicbrainz.org/ws/2/recording/"
    params = {
        "query": query,
        "fmt": "json",
        "limit": 5,
    }

    response = _safe_request(url, params=params)
    if response is None or response.status_code != 200:
        return None

    recordings = (response.json() or {}).get("recordings", [])
    if not recordings:
        return None

    target = _normalize(query)
    best_match: dict | None = None
    best_score = 0.0

    for recording in recordings:
        title = recording.get("title", "")
        artist = _extract_artist(recording)
        combined = f"{title} {artist}"
        score = _similarity(target, _normalize(combined))
        if score > best_score:
            best_score = score
            best_match = {
                "title": title,
                "artist": artist,
                "score": score,
            }

    # Require a strong match — 0.55 avoids garbage MusicBrainz results
    if best_match and best_score >= 0.55:
        return {"title": best_match["title"], "artist": best_match["artist"]}
    return None


def _youtube_search_ytdlp(query: str, max_results: int = 5) -> list[dict]:
    """Use yt-dlp to search YouTube — the most reliable method."""
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
        "skip_download": True,
        "default_search": f"ytsearch{max_results}",
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(f"ytsearch{max_results}:{query}", download=False)
            entries = result.get("entries") or []
            return [
                {
                    "video_id": entry.get("id"),
                    "title": entry.get("title", ""),
                    "uploader": entry.get("uploader") or entry.get("channel") or "Unknown",
                    "duration": entry.get("duration"),
                    "url": entry.get("url") or entry.get("webpage_url"),
                }
                for entry in entries
                if entry.get("id")
            ]
    except Exception as exc:
        print(f"yt-dlp search failed: {exc}")
        return []


def _is_embed_allowed(video_id: str) -> bool:
    """Check if a YouTube video can be embedded via oEmbed API."""
    params = {
        "url": f"https://www.youtube.com/watch?v={video_id}",
        "format": "json",
    }
    resp = _safe_request(
        "https://www.youtube.com/oembed",
        params=params,
        timeout=5,
    )
    if resp is None:
        # Network error — give it the benefit of the doubt
        return True
    return resp.status_code == 200


def get_youtube_embed(
    title: str | None,
    artist: str | None,
    *,
    fallback_query: str | None = None,
):
    """Find a YouTube video for the given song and return embed info."""
    # Build search queries — raw user query first, then MusicBrainz metadata
    queries = []
    if fallback_query:
        queries.append(fallback_query.strip())
    if title and artist and artist != "Unknown":
        queries.append(f"{title} {artist}")
    if title:
        queries.append(f"{title} official audio")

    # Deduplicate while preserving order
    queries = list(dict.fromkeys([q for q in queries if q]))
    signature = queries[0] if queries else "music"

    for query in queries:
        results = _youtube_search_ytdlp(query, max_results=5)
        for item in results:
            video_id = item["video_id"]

            # Check embeddability
            if not _is_embed_allowed(video_id):
                continue

            return {
                "embed_url": f"https://www.youtube.com/embed/{video_id}",
                "search_url": f"https://www.youtube.com/watch?v={video_id}",
                "title": item["title"],
                "artist": item["uploader"],
            }

    # Fallback — no embeddable video found, return search URL
    search_query = urllib.parse.quote_plus(signature)
    return {
        "embed_url": None,
        "search_url": f"https://www.youtube.com/results?search_query={search_query}",
        "title": title or signature,
        "artist": artist or "Unknown",
    }


def handle_input(user_input: str):
    prompt = (user_input or "").strip()
    if not prompt:
        raise ValueError("Song query cannot be empty.")

    song = search_song(prompt)
    yt = get_youtube_embed(
        song["title"] if song else None,
        song["artist"] if song else None,
        fallback_query=prompt,
    )

    result = {
        "type": "song",
        "youtube_embed": yt["embed_url"],
        "youtube_search": yt["search_url"],
        "title": song["title"] if song else yt["title"],
        "artist": song["artist"] if song else yt["artist"],
    }
    return result


def music_gen(user_input: str):
    """Public entry point used by the FastAPI router."""
    return handle_input(user_input)



if __name__ == "__main__":
    print("\n🎵 FREE Music Finder")
    print("Enter a song name or a few lyrics\n")

    user_input = input(">> ")

    result = handle_input(user_input)

    print("\n🎧 SONG SUGGESTION")
    print("Title :", result["title"])
    print("Artist:", result["artist"])
    print("YouTube Embed:", result["youtube_embed"])
    print("Watch Page :", result["youtube_search"])
