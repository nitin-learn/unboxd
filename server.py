from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup
import json
import os
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)

DEFAULT_URL = "https://letterboxd.com/fcbarcelona/list/movies-everyone-should-watch-at-least-once/"
TMDB_API_KEY = os.getenv("TMDB_API_KEY")

def fetch_movie_titles(url):
    """Fetch the webpage and extract movie titles from <img alt="movie_name">."""
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return [f"Error {response.status_code}: Unable to fetch page."]
    
    soup = BeautifulSoup(response.text, "html.parser")
    
    movies = [img["alt"] for img in soup.find_all("img", alt=True)]
    
    return movies[1:]  

def get_movie_id(movie_name):
    """Fetch the TMDB movie ID by finding the exact title match efficiently."""
    search_url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={movie_name}"
    search_response = requests.get(search_url).json()

    search_results = search_response.get("results", [])

    if not search_results:
        return []  # Return empty list if no results found

    # Use next() to return the first match and stop searching early
    matched_movie = next(
        (movie for movie in search_results if movie.get("title", "").casefold() == movie_name.casefold()),
        None
    )

    return matched_movie["id"] if matched_movie else []  

def get_streaming_services(movie_name):
    search_url = DEFAULT_URL
    search_url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={movie_name}/"
    search_response = requests.get(search_url).json()
    search_results = search_response.get("results", [])

    if not search_results:
        return []
    

    movie_id = get_movie_id(movie_name)

    api_url = f"https://api.themoviedb.org/3/movie/{movie_id}/watch/providers?api_key={TMDB_API_KEY}"
    api_response = requests.get(api_url).json()

    movie_data = api_response.get("results", {}).get("IN", {}).get("flatrate", [])      
    services = [] 
    
    for service in movie_data:
        services.append(service['provider_name'])

    return services

@app.route('/', methods=['GET', 'POST'])
def home():
    url = DEFAULT_URL 
    if request.method == 'POST':
        url = request.form.get('letterboxd_url', DEFAULT_URL)  

    movies = fetch_movie_titles(url)

    data = []

    for movie in movies:
        services = get_streaming_services(movie)
        data.append({"movie": movie, "services": services})

    return render_template("movies.html", data=data, url=url)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

    