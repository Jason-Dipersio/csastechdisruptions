"""
One-time ETL script -- run manually, not imported by the app.

Rotten Tomatoes movies and critic reviews dataset (Kaggle):
https://www.kaggle.com/datasets/stefanoleone992/rotten-tomatoes-movies-and-critic-reviews-dataset

The raw critic reviews CSV is ~1.1M rows / ~220MB, too large to ship in the
repo or load at Dash startup. This script aggregates it down to one row per
(movie, year) with a %Fresh figure, which is a few hundred KB and safe to commit.

review_score is dropped entirely: critics report it in incompatible scales
(3/4, B+, 8/10, ...) and it's missing on most rows, so it can't be averaged
meaningfully. review_type (Fresh/Rotten) is present on virtually every review
and is what Rotten Tomatoes itself uses to compute Tomatometer, so %Fresh per
year is used as the "average review score over time" metric instead.

Usage:
    python build_rotten_tomatoes_yearly.py

Expects rotten_tomatoes_movies.csv and rotten_tomatoes_critic_reviews.csv
(from the Kaggle download) to already be in this directory. Writes
rotten_tomatoes_yearly_fresh.csv next to them.
"""
import os

import pandas as pd

DATA_DIR = os.path.dirname(__file__)
MOVIES_CSV = os.path.join(DATA_DIR, "rotten_tomatoes_movies.csv")
REVIEWS_CSV = os.path.join(DATA_DIR, "rotten_tomatoes_critic_reviews.csv")
OUTPUT_CSV = os.path.join(DATA_DIR, "rotten_tomatoes_yearly_fresh.csv")

CHUNK_SIZE = 200_000

# Only movies whose reviews span at least this many distinct years make it
# into the output -- a single-year movie has no "over time" trend to show,
# and this keeps the dropdown in the app to a manageable, meaningful list.
MIN_YEARS = 2


def main():
    print(f"Reading {MOVIES_CSV} ...")
    movies = pd.read_csv(
        MOVIES_CSV,
        usecols=["rotten_tomatoes_link", "movie_title", "original_release_date"],
        dtype={"rotten_tomatoes_link": "string", "movie_title": "string"},
    )
    movies["original_release_date"] = pd.to_datetime(
        movies["original_release_date"], errors="coerce"
    )
    movies = movies.dropna(subset=["movie_title"]).drop_duplicates("rotten_tomatoes_link")

    print(f"Streaming {REVIEWS_CSV} in chunks of {CHUNK_SIZE} rows ...")
    partial_counts = []
    total_rows = 0
    for chunk in pd.read_csv(
        REVIEWS_CSV,
        usecols=["rotten_tomatoes_link", "review_type", "review_date"],
        dtype={"rotten_tomatoes_link": "string", "review_type": "string"},
        parse_dates=["review_date"],
        chunksize=CHUNK_SIZE,
    ):
        total_rows += len(chunk)
        chunk = chunk.dropna(subset=["review_date", "review_type"])
        chunk["year"] = chunk["review_date"].dt.year
        chunk["is_fresh"] = chunk["review_type"] == "Fresh"

        grouped = (
            chunk.groupby(["rotten_tomatoes_link", "year"])
            .agg(fresh_count=("is_fresh", "sum"), total_count=("is_fresh", "size"))
            .reset_index()
        )
        partial_counts.append(grouped)
        print(f"  processed {total_rows:,} review rows so far...")

    print("Combining chunk aggregates ...")
    by_year = pd.concat(partial_counts, ignore_index=True)
    by_year = (
        by_year.groupby(["rotten_tomatoes_link", "year"])
        .agg(fresh_count=("fresh_count", "sum"), total_count=("total_count", "sum"))
        .reset_index()
    )
    by_year["pct_fresh"] = (100 * by_year["fresh_count"] / by_year["total_count"]).round(1)

    # Keep only movies with reviews spanning >= MIN_YEARS distinct years.
    years_per_movie = by_year.groupby("rotten_tomatoes_link")["year"].nunique()
    keep_links = years_per_movie[years_per_movie >= MIN_YEARS].index
    by_year = by_year[by_year["rotten_tomatoes_link"].isin(keep_links)]

    result = by_year.merge(movies, on="rotten_tomatoes_link", how="left")
    result = result.dropna(subset=["movie_title"])
    result["release_year"] = result["original_release_date"].dt.year
    result = result[
        ["rotten_tomatoes_link", "movie_title", "release_year", "year",
         "fresh_count", "total_count", "pct_fresh"]
    ].sort_values(["movie_title", "year"])

    result.to_csv(OUTPUT_CSV, index=False)
    n_movies = result["rotten_tomatoes_link"].nunique()
    print(
        f"Wrote {OUTPUT_CSV}: {len(result):,} movie-year rows across "
        f"{n_movies:,} movies (reviews spanning >= {MIN_YEARS} years)."
    )


if __name__ == "__main__":
    main()
