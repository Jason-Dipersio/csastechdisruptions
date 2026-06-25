import time
import requests
import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

_analyzer = SentimentIntensityAnalyzer()

STEAM_SEARCH_URL = "https://store.steampowered.com/api/storesearch/"
STEAM_REVIEWS_URL = "https://store.steampowered.com/appreviews/{appid}"


def find_steam_appid(game_name: str) -> tuple[int | None, str | None]:
    """
    Searches Steam's store for a game by name.
    Returns (appid, matched_title) or (None, None) if not found.
    """
    try:
        resp = requests.get(
            STEAM_SEARCH_URL,
            params={"term": game_name, "l": "english", "cc": "US"},
            timeout=10,
        )
        resp.raise_for_status()
        items = resp.json().get("items", [])
        if items:
            return items[0]["id"], items[0]["name"]
    except Exception as e:
        print(f"[Steam search] '{game_name}': {e}")
    return None, None


def fetch_reviews(appid: int, max_reviews: int = 150) -> list[dict]:
    """
    Fetches English user reviews for a Steam app using cursor-based pagination.
    Steam's public review endpoint requires no API key.
    """
    params = {
        "json": 1,
        "language": "english",
        "review_type": "all",
        "purchase_type": "all",
        "num_per_page": 100,
        "filter": "recent",
        "cursor": "*",
    }

    reviews = []
    while len(reviews) < max_reviews:
        try:
            resp = requests.get(
                STEAM_REVIEWS_URL.format(appid=appid),
                params=params,
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"[Steam reviews] appid {appid}: {e}")
            break

        batch = data.get("reviews", [])
        if not batch:
            break

        for r in batch:
            reviews.append({
                "text": r.get("review", ""),
                "voted_up": r.get("voted_up", None),
                "votes_up": r.get("votes_up", 0),
                "timestamp": r["author"].get("last_played", r.get("timestamp_created", 0)),
            })

        next_cursor = data.get("cursor", "")
        if not next_cursor or next_cursor == params["cursor"] or len(batch) < 100:
            break
        params["cursor"] = next_cursor
        time.sleep(0.2)

    return reviews[:max_reviews]


def fetch_game_sentiments(game_names: list[str], max_reviews: int = 150) -> pd.DataFrame:
    """
    For each game name:
      1. Finds its Steam App ID
      2. Fetches up to max_reviews English user reviews
      3. Runs VADER on each review's text
    Returns a DataFrame with one row per review, plus per-game aggregated columns.
    """
    rows = []
    not_found = []

    for name in game_names:
        appid, matched_title = find_steam_appid(name)
        if appid is None:
            not_found.append(name)
            continue

        reviews = fetch_reviews(appid, max_reviews=max_reviews)
        for r in reviews:
            text = r["text"].strip()
            if not text:
                continue
            scores = _analyzer.polarity_scores(text)
            rows.append({
                "game": name,
                "steam_title": matched_title,
                "appid": appid,
                "compound": scores["compound"],
                "positive": scores["pos"],
                "negative": scores["neg"],
                "neutral": scores["neu"],
                "voted_up": r["voted_up"],
                "review_snippet": text[:200],
            })

        time.sleep(0.4)

    if not_found:
        print(f"[Steam] No app found for: {', '.join(not_found)}")

    return pd.DataFrame(rows)
