import re
import time
import requests
from bs4 import BeautifulSoup
import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

_BASE = "https://letterboxd.com"

# Full browser-like headers so Cloudflare/Letterboxd doesn't drop the request
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
}

_session = requests.Session()
_session.headers.update(_HEADERS)
_analyzer = SentimentIntensityAnalyzer()


def _clean_for_search(title: str) -> str:
    """Strip a trailing year like '2004' that the user may have included in the title."""
    return re.sub(r"\s+\d{4}$", "", title.strip())


def _get_film_slug(title: str) -> str | None:
    """
    Search Letterboxd for the film and return its slug.
    Tries the films-only search endpoint, then falls back to the general search.
    """
    query = _clean_for_search(title)
    search_paths = [
        f"/search/films/{requests.utils.quote(query)}/",
        f"/search/{requests.utils.quote(query)}/",
    ]
    # Selectors tried in order to find the film-slug value
    slug_selectors = [
        (".film-poster[data-film-slug]", "data-film-slug"),
        ("[data-film-slug]", "data-film-slug"),
        (".film-poster[data-target-link]", "data-target-link"),
    ]

    for path in search_paths:
        try:
            resp = _session.get(f"{_BASE}{path}", timeout=12)
            if resp.status_code != 200:
                print(f"[Letterboxd] search returned {resp.status_code} for '{query}'")
                continue
            soup = BeautifulSoup(resp.text, "html.parser")
            for selector, attr in slug_selectors:
                el = soup.select_one(selector)
                if el:
                    value = el.get(attr, "")
                    # data-target-link looks like "/film/garfield-the-movie/" — extract slug
                    slug = value.strip("/").split("/")[-1] if "/" in value else value
                    if slug:
                        print(f"[Letterboxd] found slug '{slug}' for '{title}'")
                        return slug
            # Debug: show a snippet so we can see what we actually got
            print(f"[Letterboxd] no slug selector matched for '{query}' at {path}")
            print(f"  HTML snippet: {resp.text[:500]!r}")
        except Exception as e:
            print(f"[Letterboxd] search error for '{query}': {e}")
        time.sleep(0.5)

    return None


def _parse_star_rating(item) -> float | None:
    """Extract numeric star rating (0.5–5) from a review list item."""
    # Letterboxd encodes rating as rated-N class (1–10) where N/2 = stars
    rating_el = item.select_one(".rating")
    if rating_el:
        cls = " ".join(rating_el.get("class", []))
        m = re.search(r"rated-(\d+)", cls)
        if m:
            return int(m.group(1)) / 2.0
        # Fallback: count star characters
        text = rating_el.get_text(strip=True)
        stars = text.count("★") + text.count("½") * 0.5
        if stars > 0:
            return stars
    return None


def _scrape_reviews(slug: str, max_pages: int = 5) -> list:
    reviews = []
    for page in range(1, max_pages + 1):
        url = f"{_BASE}/film/{slug}/reviews/page/{page}/"
        try:
            resp = _session.get(url, timeout=12)
            if resp.status_code != 200:
                print(f"[Letterboxd] reviews page returned {resp.status_code} for '{slug}'")
                break
            soup = BeautifulSoup(resp.text, "html.parser")

            # Try multiple selectors in case Letterboxd updates their markup
            items = (
                soup.select("li.film-detail")
                or soup.select(".film-detail")
                or soup.select("li[class*='film-detail']")
            )

            if not items:
                print(f"[Letterboxd] no review items found at {url}")
                print(f"  HTML snippet: {resp.text[:500]!r}")
                break

            for item in items:
                # Try multiple body-text selectors
                body = (
                    item.select_one(".body-text")
                    or item.select_one("div[class*='body-text']")
                    or item.select_one(".review-text")
                )
                if not body:
                    continue
                text = body.get_text(" ", strip=True)
                if not text:
                    continue

                scores = _analyzer.polarity_scores(text)
                reviews.append({
                    "slug": slug,
                    "text_snippet": text[:300],
                    "stars": _parse_star_rating(item),
                    "compound": scores["compound"],
                    "positive": scores["pos"],
                    "negative": scores["neg"],
                    "neutral": scores["neu"],
                })
        except Exception as e:
            print(f"[Letterboxd] scrape error '{slug}' page {page}: {e}")
            break
        time.sleep(0.7)

    return reviews


def fetch_letterboxd_sentiment(titles: list) -> pd.DataFrame:
    """
    For each movie title, find the Letterboxd slug, scrape reviews,
    and run VADER sentiment analysis.
    Returns a DataFrame with one row per review.
    """
    all_rows = []
    for title in titles:
        slug = _get_film_slug(title)
        if not slug:
            print(f"[Letterboxd] no slug found for '{title}' — skipping")
            continue
        reviews = _scrape_reviews(slug)
        print(f"[Letterboxd] scraped {len(reviews)} reviews for '{title}' (slug: {slug})")
        for r in reviews:
            r["title"] = title
        all_rows.extend(reviews)
        time.sleep(1.2)

    return pd.DataFrame(all_rows) if all_rows else pd.DataFrame()
