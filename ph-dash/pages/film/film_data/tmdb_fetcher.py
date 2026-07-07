import time
import requests
import pandas as pd

TMDB_BASE = "https://api.themoviedb.org/3"

_CGI_TERMS = [
    "computer generated imagery",
    "cgi",
    "digital effects",
    "digital cinematography",
]


def _fetch_keyword_ids(api_key: str) -> list:
    ids = set()
    for term in _CGI_TERMS:
        try:
            resp = requests.get(
                f"{TMDB_BASE}/search/keyword",
                params={"api_key": api_key, "query": term},
                timeout=10,
            )
            resp.raise_for_status()
            for kw in resp.json().get("results", []):
                ids.add(kw["id"])
        except Exception as e:
            print(f"[TMDB] keyword '{term}': {e}")
        time.sleep(0.1)
    return list(ids)


def fetch_cgi_movies(
    api_key: str,
    start_year: int = 1993,
    end_year: int = 2026,
    max_pages_per_year: int = 3,
    min_votes: int = 50,
) -> pd.DataFrame:
    """
    Discover movies tagged with CGI-related TMDB keywords for each year in range.
    Returns one row per unique movie with title, year, vote_average, vote_count, popularity.
    """
    kw_ids = _fetch_keyword_ids(api_key)
    if not kw_ids:
        return pd.DataFrame()

    kw_string = "|".join(str(i) for i in kw_ids)
    rows = []

    for year in range(start_year, end_year + 1):
        for page in range(1, max_pages_per_year + 1):
            params = {
                "api_key": api_key,
                "with_keywords": kw_string,
                "primary_release_year": year,
                "sort_by": "vote_count.desc",
                "vote_count.gte": min_votes,
                "page": page,
            }
            try:
                resp = requests.get(
                    f"{TMDB_BASE}/discover/movie", params=params, timeout=10
                )
                resp.raise_for_status()
                data = resp.json()
            except Exception as e:
                print(f"[TMDB] discover year={year} page={page}: {e}")
                break

            results = data.get("results", [])
            if not results:
                break

            for m in results:
                rows.append({
                    "id": m.get("id"),
                    "title": m.get("title", ""),
                    "year": year,
                    "vote_average": m.get("vote_average"),
                    "vote_count": m.get("vote_count"),
                    "popularity": m.get("popularity"),
                })

            if page >= data.get("total_pages", 1):
                break
            time.sleep(0.15)

    if not rows:
        return pd.DataFrame()

    return pd.DataFrame(rows).drop_duplicates("id").reset_index(drop=True)


def fetch_tmdb_reviews(api_key: str, title_id_pairs: list) -> pd.DataFrame:
    """
    Fetch TMDB member reviews for a list of (title, movie_id) pairs.
    Runs VADER sentiment on each review's content.
    Returns one row per review with title, year, author, content snippet,
    compound score, and TMDB author rating (0–10, nullable).
    """
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    _va = SentimentIntensityAnalyzer()

    rows = []
    for title, movie_id, year in title_id_pairs:
        try:
            resp = requests.get(
                f"{TMDB_BASE}/movie/{movie_id}/reviews",
                params={"api_key": api_key, "language": "en-US"},
                timeout=10,
            )
            resp.raise_for_status()
            results = resp.json().get("results", [])
        except Exception as e:
            print(f"[TMDB reviews] '{title}': {e}")
            results = []

        for r in results:
            content = r.get("content", "").strip()
            if not content:
                continue
            scores = _va.polarity_scores(content)
            author_details = r.get("author_details") or {}
            rows.append({
                "title": title,
                "year": year,
                "author": r.get("author", ""),
                "content_snippet": content[:300],
                "tmdb_rating": author_details.get("rating"),  # 0–10 or None
                "compound": scores["compound"],
                "positive": scores["pos"],
                "negative": scores["neg"],
                "neutral": scores["neu"],
                "created_at": r.get("created_at", ""),
            })
        time.sleep(0.15)

    return pd.DataFrame(rows) if rows else pd.DataFrame()
