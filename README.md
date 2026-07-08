Here's a repo we can use for our dashboard!

I put my film code in the /pages directory under a folder called film. It might work out well
if we have /gaming, /music, and /ai in there when we're all ready for those ones.

To avoid potential merge conflicts, we can try running our code pages independent from that main hub page,
app_tech_disruptions. To do this, make sure to do these two things:

1. Paste this code from my film.py file into the code for your pages:

   ```python
   if __name__ == "__main__":
    import os
    import dash

    # Point at the shared assets/ folder at the project root so standalone
    # runs still pick up the same CSS as the hub app.
    app = dash.Dash(
        __name__,
        external_stylesheets=[dbc.themes.LITERA],
        assets_folder=os.path.join(os.path.dirname(__file__), "..", "..", "assets"),
    )
    app.layout = layout()
    register_callbacks(app)
    app.run(debug=True)
   ```




   This block allows the py file to be run either from that main hub page, or by itself by making sure it
   still points at the shared placeholder css file I have.

3. If you import stuff from other folders, relative imports won't work if you try running the file by itself. In
   my film file I fixed this by using this try and except block here:

   ```python
   try:
    from .film_data.tmdb_fetcher import fetch_cgi_movies, fetch_tmdb_reviews
   except ImportError:
    from film_data.tmdb_fetcher import fetch_cgi_movies, fetch_tmdb_reviews
   ```

   This code just has the two different versions of importing so both will work.

Anyway, to run the dashboard from the terminal:

In terminal, once you're in the ph-dash folder, run "venv\Scripts\activate". 
Then, go to the directory with the file you want to run the dashboard from (so just ph-dash for 
running it with the hub page and /pages/your_directory for running your page by itself), and run it 
with "python your_file_name" (like "python film.py") and the dashboard server will start on a local host address you can click on. 

I just wanted to put that there just in case it's helpful. 
