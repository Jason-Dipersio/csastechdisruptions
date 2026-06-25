import time
import requests
import pandas as pd

RAWG_BASE = "https://api.rawg.io/api"

# Tag slugs RAWG uses to signal a game's perspective/dimension
_3D_TAGS = {
    "3d", "3d-graphics", "first-person", "first-person-shooter",
    "third-person", "third-person-shooter", "fps", "tps", "3d-platformer",
}
_2D_TAGS = {
    "2d", "2d-platformer", "side-scroller", "side-scrolling",
    "side-scrolling-platformer", "top-down", "top-down-view",
    "isometric", "platformer-2d",
}


def _classify(tags: list) -> str:
    slugs = {t["slug"] for t in tags}
    if slugs & _3D_TAGS:
        return "3D"
    if slugs & _2D_TAGS:
        return "2D"
    return "Unknown"


def fetch_rawg_games(
    api_key: str,
    start_year: int = 1994,
    end_year: int = 2000,
    max_pages: int = 10,
) -> pd.DataFrame:
    """
    Fetches games with Metacritic scores from RAWG for the given year window.
    Returns a DataFrame with one row per game.
    max_pages * 40 = max games fetched (default 400).
    """
    params = {
        "key": api_key,
        "dates": f"{start_year}-01-01,{end_year}-12-31",
        "metacritic": "1,100",
        "ordering": "-metacritic",
        "page_size": 40,
    }

    rows = []
    for page in range(1, max_pages + 1):
        params["page"] = page
        try:
            resp = requests.get(f"{RAWG_BASE}/games", params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"[RAWG] page {page} error: {e}")
            break

        results = data.get("results", [])
        if not results:
            break

        for g in results:
            rows.append({
                "name": g["name"],
                "slug": g.get("slug", ""),
                "released": g.get("released"),
                "metacritic": g.get("metacritic"),
                "platforms": [p["platform"]["name"] for p in g.get("platforms", [])],
                "dimension": _classify(g.get("tags", [])),
            })

        time.sleep(0.25)

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    df["released"] = pd.to_datetime(df["released"], errors="coerce")
    df["year"] = df["released"].dt.year.astype("Int64")
    return df
