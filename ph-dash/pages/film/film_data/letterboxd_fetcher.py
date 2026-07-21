import json
import re
import time

import pandas as pd
import requests

LETTERBOXD_BASE = "https://letterboxd.com"

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
}

_LD_JSON_RE = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.S)

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def _slugify(title: str) -> str:
    slug = title.lower().replace("&", "and")
    slug = _SLUG_RE.sub("-", slug).strip("-")
    return slug


def _slug_candidates(title: str, year) -> list:
    base = _slugify(title)
    if pd.notna(year):
        return [f"{base}-{int(year)}", base]
    return [base]


def _extract_ld_json(html: str) -> dict | None:
    match = _LD_JSON_RE.search(html)
    if not match:
        return None
    raw = match.group(1).replace("/* <![CDATA[ */", "").replace("/* ]]> */", "").strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def fetch_letterboxd_film(title: str, year, session: requests.Session) -> dict:
    candidates = _slug_candidates(title, year)
    for i, slug in enumerate(candidates):
        if i > 0:
            time.sleep(0.3) 
        url = f"{LETTERBOXD_BASE}/film/{slug}/"
        try:
            resp = session.get(url, timeout=10)
        except requests.RequestException:
            continue
        if resp.status_code != 200:
            continue

        data = _extract_ld_json(resp.text)
        if not data:
            continue

        release_date = data.get("dateCreated") or ""
        lb_year = int(release_date[:4]) if release_date[:4].isdigit() else None

        if pd.notna(year) and lb_year is not None and abs(lb_year - int(year)) > 1:
            continue

        agg = data.get("aggregateRating") or {}
        if agg.get("ratingValue") is None:
            continue

        return {
            "lb_slug": slug,
            "lb_rating": agg.get("ratingValue"),
            "lb_rating_count": agg.get("ratingCount"),
            "lb_review_count": agg.get("reviewCount"),
            "lb_genres": ", ".join(data.get("genre") or []),
            "lb_year": lb_year,
            "lb_matched": True,
        }

    return {
        "lb_slug": None,
        "lb_rating": None,
        "lb_rating_count": None,
        "lb_review_count": None,
        "lb_genres": "",
        "lb_year": None,
        "lb_matched": False,
    }


def cap_films(df: pd.DataFrame, max_films: int) -> pd.DataFrame:
    if len(df) <= max_films:
        return df
    if "source" in df.columns:
        manual = df[df["source"] == "manual"].head(max_films)
        other = df[df["source"] != "manual"]
    else:
        manual, other = df.iloc[0:0], df
    remaining = max(max_films - len(manual), 0)
    return pd.concat([manual, other.head(remaining)], ignore_index=True)


def fetch_letterboxd_ratings(df: pd.DataFrame, delay: float = 0.75, max_films: int | None = None) -> pd.DataFrame:
    if df.empty:
        return df

    if max_films is not None:
        df = cap_films(df, max_films)

    session = requests.Session()
    session.headers.update(_HEADERS)

    records = []
    for _, row in df.iterrows():
        try:
            records.append(fetch_letterboxd_film(row["title"], row.get("year"), session))
        except Exception as e:
            print(f"[Letterboxd] '{row['title']}': {e}")
            records.append({
                "lb_slug": None, "lb_rating": None, "lb_rating_count": None,
                "lb_review_count": None, "lb_genres": "", "lb_year": None,
                "lb_matched": False,
            })
        time.sleep(delay)

    lb_df = pd.DataFrame(records)
    return pd.concat([df.reset_index(drop=True), lb_df], axis=1)
