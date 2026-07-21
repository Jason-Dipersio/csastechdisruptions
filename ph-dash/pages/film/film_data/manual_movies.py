import pandas as pd

# Fallback/supplement list for notable CGI-heavy films that TMDB's keyword
MANUAL_CGI_MOVIES = [
    {"title": "Jurassic Park", "year": 1993},
    {"title": "The Matrix", "year": 1999},
    {"title": "The Lord of the Rings: The Fellowship of the Ring", "year": 2001},
    {"title": "The Lord of the Rings: The Two Towers", "year": 2002},
    {"title": "The Lord of the Rings: The Return of the King", "year": 2003},
    {"title": "Avatar", "year": 2009},
    {"title": "Life of Pi", "year": 2012},
    {"title": "Gravity", "year": 2013},
    {"title": "Interstellar", "year": 2014},
    {"title": "The Jungle Book", "year": 2016},
    {"title": "Avengers: Endgame", "year": 2019},
    {"title": "The Lion King", "year": 2019},
    {"title": "Dune", "year": 2021},
    {"title": "Avatar: The Way of Water", "year": 2022},
    {"title": "Garfield", "year": 2004},
    {"title": "Garfield: A Tail of Two Kitties", "year": 2006},
    {"title": "Star Wars: Episode I – The Phantom Menace", "year": 1999},
    {"title": "Star Wars: Episode II – Attack of the Clones", "year": 2002},
    {"title": "Star Wars: Episode III – Revenge of the Sith", "year": 2005},
    {"title": "Jurassic World", "year": 2015},
    {"title": "Jurassic World: Fallen Kingdom", "year": 2018},
    {"title": "Jurassic World Dominion", "year": 2022},
    {"title": "Jurassic Park III ", "year": 2001},
    {"title": "The Lost World: Jurassic Park", "year": 1997},
    {"title": "Alvin and the Chipmunks ", "year": 2007},
    {"title": "Alvin and the Chipmunks: The Squeakquel", "year": 2009},
    {"title": "Alvin and the Chipmunks: Chipwrecked", "year": 2011},
    {"title": "Alvin and the Chipmunks: The Road Chip", "year": 2015},
    {"title": "Pirates of the Caribbean: The Curse of the Black Pearl", "year": 2003},
    {"title": "Pirates of the Caribbean: Dead Man’s Chest", "year": 2006},
    {"title": "Pirates of the Caribbean: At World’s End", "year": 2007},
    {"title": "Pirates of the Caribbean: On Stranger Tides", "year": 2011},
    {"title": "Pirates of the Caribbean: Dead Men Tell No Tales", "year": 2017},
    {"title": "Transformers", "year": 2007},
    {"title": "Transformers: Revenge of the Fallen", "year": 2009},
    {"title": "Transformers: Dark of the Moon", "year": 2011},
    {"title": "Transformers: Age of Extinction", "year": 2014},
    {"title": "Transformers: The Last Knight", "year": 2017},
    {"title": "Rise of the Planet of the Apes", "year": 2011},
    {"title": "Dawn of the Planet of the Apes", "year": 2014},
    {"title": "War for the Planet of the Apes", "year": 2017},
    {"title": "The Lord of the Rings: The Fellowship of the Ring", "year": 2001},
    {"title": "The Lord of the Rings: The Return of the King", "year": 2003},
    {"title": "The Lord of the Rings: The Two Towers", "year": 2003},
    {"title": "The Hobbit: An Unexpected Journey", "year": 2012},
    {"title": "The Hobbit: The Desolation of Smaug", "year": 2013},
    {"title": "The Hobbit: The Battle of the Five Armies", "year": 2014},
    {"title": "Harry Potter and the Prisoner of Azkaban", "year": 2004},
    {"title": "Harry Potter and the Philosopher’s Stone", "year": 2001},
    {"title": "Harry Potter and the Goblet of Fire", "year": 2005},
    {"title": "Harry Potter and the Chamber of Secrets", "year": 2002},
    {"title": "Harry Potter and the Deathly Hallows: Part 2", "year": 2011},
    {"title": "Harry Potter and the Order of the Phoenix", "year": 2007},
    {"title": "Harry Potter and the Half-Blood Prince", "year": 2009},
    {"title": "Harry Potter and the Deathly Hallows: Part 1", "year": 2010},


]

_COLUMNS = ["id", "title", "year", "vote_average", "vote_count", "popularity", "source"]


def get_manual_movies_df() -> pd.DataFrame:
    if not MANUAL_CGI_MOVIES:
        return pd.DataFrame(columns=_COLUMNS)

    df = pd.DataFrame(MANUAL_CGI_MOVIES)
    df["id"] = None
    df["vote_average"] = pd.NA
    df["vote_count"] = pd.NA
    df["popularity"] = pd.NA
    df["source"] = "manual"
    return df[_COLUMNS]
